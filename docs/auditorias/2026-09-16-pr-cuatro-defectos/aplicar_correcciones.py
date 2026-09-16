"""Aplica las cuatro correcciones de Custos sobre el arbol del producto.

Por que un script y no ediciones a mano: cada reemplazo lleva el texto ANTES y
DESPUES completos y **falla si no matchea exactamente una vez**. Un parche que
aplica a medias es peor que uno que no aplica: deja el arbol en un estado que
nadie midio. Se ejecuta con `--verificar` para ver que matchearia sin escribir.

Uso:
    python aplicar_correcciones.py --verificar   # dry-run, no escribe
    python aplicar_correcciones.py               # aplica

NO toca produccion, credenciales ni permisos. Solo tres archivos del backend.

HISTORIA DE UNA CORRECCION MIA, que queda escrita porque importa: la primera
version de este parche condicionaba el arranque del D4 por `modo == "corridos"`.
Eso rompio DOS aserciones de `test_plazos.py` que ya existian, etiquetadas
ARRANQUE-HABIL, y tenian razon: un plazo CIVIL de mas de 15 dias tambien se
computa en dias corridos (art. 90.II Ley 439) pero su arranque sigue siendo el
dia siguiente HABIL (art. 90.I). O sea que "corridos" no implica "arranque
calendario": eso vale para PENAL, por el art. 130 CPP. Un test preexistente
falso mi parche antes de que yo lo declarara verde.
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
BACK = REPO / "backend"

# ---------------------------------------------------------------------------
# DEFECTO 1 - LOGIN REAL SIN DEBILITAR RLS
# ---------------------------------------------------------------------------

A1_PROTOCOL_ANTES = """class Almacen(Protocol):
    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None: ..."""

A1_PROTOCOL_DESPUES = """class BufeteRequerido(ValueError):
    \"\"\"El login no tiene respuesta unica sin el bufete.

    `UNIQUE (tenant_id, email)` es compuesto a proposito: el mismo email puede
    existir en dos bufetes. Preguntar por email suelto no es una consulta con
    una respuesta: es una consulta con varias, y elegir una arbitrariamente es
    el defecto, no la solucion.
    \"\"\"


class Almacen(Protocol):
    def usuario_por_email(self, email: str, bufete: str | None = None
                          ) -> tuple[Usuario, str] | None: ..."""

A1_SQLITE_ANTES = """    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None:
        r = self.con.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if not r:
            return None"""

A1_SQLITE_DESPUES = """    def usuario_por_email(self, email: str, bufete: str | None = None
                          ) -> tuple[Usuario, str] | None:
        # Este almacen NO tiene RLS y es de prueba. Acepta `bufete` para tener
        # la MISMA firma que produccion. Si no viene y el email existe en mas de
        # un bufete, se niega en vez de devolver una fila arbitraria: ese
        # `fetchone()` silencioso era el defecto latente del contrato viejo.
        if bufete:
            r = self.con.execute(
                "SELECT u.* FROM users u JOIN tenants t ON t.id = u.tenant_id"
                " WHERE u.email = ? AND lower(t.slug) = lower(?)",
                (email.lower(), bufete)).fetchone()
        else:
            filas = self.con.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.lower(),)).fetchall()
            if len(filas) > 1:
                raise BufeteRequerido(
                    "ese email existe en mas de un bufete: el login necesita el "
                    "bufete para tener una respuesta unica")
            r = filas[0] if filas else None
        if not r:
            return None"""

A1_PG_ANTES = """    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None:
        # Login: es la UNICA consulta sin tenant, porque el tenant se descubre
        # aca. Lee solo estas columnas y solo de usuarios activos.
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT id, tenant_id, email, password_hash, nombre_completo,"
                    " rol, matricula_cab FROM public.users"
                    " WHERE lower(email) = lower(%s) AND activo = TRUE", (email,))
                r = cur.fetchone()
        if not r:
            return None
        return (Usuario(id=str(r["id"]), tenant_id=str(r["tenant_id"]),
                        email=r["email"], nombre=r["nombre_completo"],
                        rol=r["rol"], matricula=r["matricula_cab"]),
                r["password_hash"])"""

A1_PG_DESPUES = """    def usuario_por_email(self, email: str, bufete: str | None = None
                          ) -> tuple[Usuario, str] | None:
        # DEFECTO CORREGIDO. Antes leia public.users SIN app.set_tenant contra
        # una politica con FORCE ROW LEVEL SECURITY: la consulta devolvia CERO
        # filas y el login rechazaba credenciales VALIDAS con 401. Medido: con
        # el rol real 401, con BYPASSRLS 200 (falsador_login.py).
        #
        # El arreglo NO es BYPASSRLS, ni superusuario, ni desactivar RLS, ni
        # ampliar la politica: es resolver el bufete PRIMERO contra
        # public.tenants -- que por diseno no tiene RLS, "la administra el
        # servicio, no un inquilino" -- y recien despues leer public.users
        # DENTRO de ese tenant, con la misma politica activa y por la via
        # normal `_en_tenant`. El privilegio no cambia.
        #
        # De paso cierra la ambiguedad del esquema: UNIQUE (tenant_id, email)
        # permite el mismo email en dos bufetes.
        if not bufete:
            raise BufeteRequerido(
                "el login necesita el bufete: el mismo email puede existir en "
                "dos bufetes (UNIQUE (tenant_id, email)), asi que sin bufete la "
                "consulta no tiene respuesta unica. No se resuelve con "
                "BYPASSRLS ni ampliando el WHERE")
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT id FROM public.tenants"
                    " WHERE lower(slug) = lower(%s)", (bufete,))
                t = cur.fetchone()
        if not t:
            return None
        filas = self._en_tenant(
            str(t["id"]),
            "SELECT id, tenant_id, email, password_hash, nombre_completo,"
            " rol, matricula_cab FROM public.users"
            " WHERE lower(email) = lower(%s) AND activo = TRUE", (email,))
        if not filas:
            return None
        r = filas[0]
        return (Usuario(id=str(r["id"]), tenant_id=str(r["tenant_id"]),
                        email=r["email"], nombre=r["nombre_completo"],
                        rol=r["rol"], matricula=r["matricula_cab"]),
                r["password_hash"])"""

# ---------------------------------------------------------------------------
# DEFECTO 2 - EL RECHAZO POSTERIOR REVOCA LA APROBACION
# ---------------------------------------------------------------------------

A2_ANTES = """    h = sha256(contenido)
    for ev in almacen.aprobaciones(tenant_id, case_id):
        if (ev.get("tipo") == tipo and ev.get("sha256_entrada") == h
                and ev.get("decision") == "aprobado" and ev.get("matricula")):
            return ev
    raise GateBloqueado(
        f"accion '{tipo}' BLOQUEADA: no hay aprobacion de un abogado con "
        f"matricula sobre este contenido exacto (sha256 {h[:12]}...). "
        "Aprobar un borrador y ejecutar otro no cuenta: el hash tiene que "
        "coincidir. Fundamento: Ley 387 arts. 6 y 32.II")"""

A2_DESPUES = """    h = sha256(contenido)
    # DEFECTO CORREGIDO. Antes recorria TODO el historial buscando cualquier
    # 'aprobado' y devolvia el primero que encontraba, asi que SALTABA un
    # rechazo POSTERIOR sobre el mismo contenido: el abogado que se arrepiente
    # no podia frenar nada. Medido: aprobar -> rechazar -> accion daba 200.
    #
    # Ahora se resuelve la ULTIMA decision aplicable por (tenant, caso, tipo,
    # hash) con orden determinista declarado ACA, sin depender del ORDER BY del
    # almacen: timestamp DESC y, ante empate exacto, id DESC.
    aplicables = [ev for ev in almacen.aprobaciones(tenant_id, case_id)
                  if ev.get("tipo") == tipo and ev.get("sha256_entrada") == h]
    if not aplicables:
        raise GateBloqueado(
            f"accion '{tipo}' BLOQUEADA: no hay NINGUNA decision de un abogado "
            f"con matricula sobre este contenido exacto (sha256 {h[:12]}...). "
            "Aprobar un borrador y ejecutar otro no cuenta: el hash tiene que "
            "coincidir. Fundamento: Ley 387 arts. 6 y 32.II")
    aplicables.sort(key=_clave_decision, reverse=True)
    ultima = aplicables[0]
    if ultima.get("decision") != "aprobado":
        raise GateBloqueado(
            f"accion '{tipo}' BLOQUEADA: la ULTIMA decision sobre este "
            f"contenido exacto (sha256 {h[:12]}...) es un RECHAZO. Un rechazo "
            "posterior revoca la aprobacion anterior; para volver a habilitar "
            "hay que registrar una aprobacion nueva. Fundamento: Ley 387 "
            "arts. 6 y 32.II")
    if not ultima.get("matricula"):
        raise GateBloqueado(
            f"accion '{tipo}' BLOQUEADA: la aprobacion vigente no tiene "
            "matricula de abogado. Fundamento: Ley 387 arts. 6 y 32.II")
    return ultima"""

A2_HELPER_ANTES = """class GateBloqueado(RuntimeError):
    pass"""

A2_HELPER_DESPUES = """class GateBloqueado(RuntimeError):
    pass


def _clave_decision(ev: dict) -> tuple[str, str]:
    \"\"\"Orden determinista de decisiones: mas nueva primero.

    `creado_en` en PostgreSQL y `ts` en SQLite son ISO-8601, que ordena bien
    como texto. El `id` desempata cuando dos decisiones comparten timestamp
    exacto: sin ese segundo criterio el resultado dependeria del orden de
    llegada, y un gate que depende de eso no es un gate.
    \"\"\"
    ts = ev.get("creado_en") or ev.get("ts") or ""
    return (str(ts), str(ev.get("id") or ""))"""

# ---------------------------------------------------------------------------
# DEFECTO 3 - EL LOG NO PUEDE CONTENER LA CONSULTA
# ---------------------------------------------------------------------------

A3_ANTES = """        def log_message(self, fmt, *args):  # noqa: A003
            # NO se loguea la query string: puede traer el texto de una busqueda
            # juridica, y eso revela la estrategia de un caso. Misma regla que
            # el `log_format corpus_sin_query` de nginx.
            ruta = urllib.parse.urlparse(self.path).path
            print(f"{self.address_string()} {self.command} {ruta} "
                  f"{fmt % args if args else ''}".strip())"""

A3_DESPUES = """        def _registrar(self, codigo) -> None:
            # Lista BLANCA de campos. Todo lo que no este aca no se imprime.
            ruta = urllib.parse.urlparse(getattr(self, "path", "") or "").path
            metodo = getattr(self, "command", "-") or "-"
            print(f"{self.address_string()} {metodo} {ruta} {codigo}")

        def log_request(self, code="-", size="-"):  # noqa: A003
            # DEFECTO CORREGIDO. La base llama log_message('\"%s\" %s %s',
            # self.requestline, ...), o sea que la linea HTTP COMPLETA -- con la
            # query string -- volvia a entrar por los args y el `fmt % args` la
            # reinsertaba, aunque la ruta estuviera saneada. Medido: el canario
            # aparecia en stdout. Se sobrescribe el punto de entrada real.
            self._registrar(code)

        def log_message(self, fmt, *args):  # noqa: A003
            # NO se formatea NADA del caller: ni fmt ni args. Una busqueda
            # juridica en el log revela la estrategia de un caso, y un token o
            # una password ahi son una fuga permanente.
            self._registrar("-")

        def log_error(self, fmt, *args):  # noqa: A003
            # Los errores tambien traen la requestline. Mismo tratamiento.
            self._registrar("error")"""

# ---------------------------------------------------------------------------
# DEFECTO 4 - ARRANQUE DEL PLAZO CAUTELAR PENAL
# ---------------------------------------------------------------------------

A4_ANTES = """    detalle: list[dict] = []
    cursor = base
    inicio: _dt.date | None = None
    for _ in range(400):
        cursor += _dt.timedelta(days=1)
        marca = _marca(cursor, tarija=tarija, extra=extra, calendario=calendario)
        if marca == "habil":
            inicio = cursor
            break
        detalle.append({"fecha": cursor, "marca": marca + "  <- antes del arranque",
                        "cuenta": False, "n": None})"""

A4_DESPUES = """    detalle: list[dict] = []
    cursor = base
    inicio: _dt.date | None = None
    if materia is Materia.PENAL and modo == "corridos":
        # DEFECTO CORREGIDO. El arranque se buscaba HABIL para TODAS las
        # materias, y en un plazo cautelar penal -- que va en dias CORRIDOS --
        # eso se come los inhabiles del principio: con notificacion del viernes
        # el dia 1 caia el lunes en vez del sabado.
        #
        # Texto vigente del art. 130 CPP (Ley 1970), verificado en tres fuentes
        # independientes y NO modificado por la Ley 1173 ni por la Ley 1226 (las
        # dos enumeran los articulos que tocan y el 130 no esta):
        #
        #   "Los plazos determinados por dias comenzaran a correr al dia
        #    siguiente de practicada la notificacion y venceran a las
        #    veinticuatro horas del ultimo dia habil senalado. Al efecto, se
        #    computara solo los dias habiles, salvo que la ley disponga
        #    expresamente lo contrario o que se refiera a medidas cautelares,
        #    caso en el cual se computaran dias corridos."
        #
        # Dice "al dia siguiente", NO "al dia siguiente HABIL". El dia siguiente
        # habil es el art. 90.I de la Ley 439, que es CIVIL.
        #
        # POR QUE LA CONDICION EXIGE PENAL Y NO SOLO "corridos": un plazo CIVIL
        # de mas de 15 dias tambien se computa corrido (art. 90.II Ley 439),
        # pero su arranque sigue gobernado por el art. 90.I, o sea el dia
        # siguiente HABIL. La primera version de este parche condicionaba solo
        # por `modo` y rompio dos aserciones ARRANQUE-HABIL de test_plazos.py
        # que ya existian y tenian razon. "Corridos" no implica "arranque
        # calendario": eso es del art. 130 CPP, y el art. 130 CPP es penal.
        inicio = base + _dt.timedelta(days=1)
    else:
        for _ in range(400):
            cursor += _dt.timedelta(days=1)
            marca = _marca(cursor, tarija=tarija, extra=extra,
                           calendario=calendario)
            if marca == "habil":
                inicio = cursor
                break
            detalle.append({"fecha": cursor,
                            "marca": marca + "  <- antes del arranque",
                            "cuenta": False, "n": None})"""

A4B_ANTES = """        if materia is Materia.PENAL:
            motivo = ("SUPUESTO DECLARADO (no medido): ultimo dia inhabil en "
                      "computo corrido penal, se prorroga al primer habil")
            adv.append(motivo)"""

A4B_DESPUES = """        if materia is Materia.PENAL:
            # El art. 130 CPP choca CONSIGO MISMO en este borde: manda computar
            # "dias corridos" para cautelares y en la misma oracion dice que
            # vencen "a las veinticuatro horas del ultimo dia HABIL senalado".
            # Resolver esa tension es interpretacion juridica, no aritmetica, y
            # no la firmo yo. Asi que el vencimiento deja de declararse
            # CONFIRMADO: se devuelve incertidumbre explicita.
            motivo = ("VENCIMIENTO NO CONFIRMADO: el ultimo dia del computo "
                      "corrido cae inhabil y el art. 130 CPP es contradictorio "
                      "en ese borde ('dias corridos' vs 'ultimo dia habil'). La "
                      "prorroga de abajo es UN SUPUESTO, no la norma medida: "
                      "confirmar con abogado antes de presentar")
            adv.append(motivo)
            prorroga_penal_incierta = True"""

A4C_ANTES = """    estado = NO_MEDIDO if sin_cobertura else CONFIRMADO"""

A4C_DESPUES = """    estado = (NO_MEDIDO if (sin_cobertura or prorroga_penal_incierta)
              else CONFIRMADO)"""

A4D_ANTES = """    modo, fundamento = _modo_y_fundamento(materia, dias, medida_cautelar)
    hora, aviso_hora = _hora_vencimiento(materia)
    adv: list[str] = []"""

A4D_DESPUES = """    modo, fundamento = _modo_y_fundamento(materia, dias, medida_cautelar)
    hora, aviso_hora = _hora_vencimiento(materia)
    prorroga_penal_incierta = False
    adv: list[str] = []"""

# ---------------------------------------------------------------------------
# DEFECTO 1 (parte api.py) - el endpoint consume el contrato corregido
# ---------------------------------------------------------------------------

A1_API_ANTES = """    def abrir_sesion(self, cuerpo: dict) -> dict:
        email = (cuerpo.get("email") or "").strip()
        pw = cuerpo.get("password") or ""
        par = self.almacen.usuario_por_email(email) if email else None"""

A1_API_DESPUES = """    def abrir_sesion(self, cuerpo: dict) -> dict:
        email = (cuerpo.get("email") or "").strip()
        pw = cuerpo.get("password") or ""
        # El bufete es parte de la identidad, no un extra: el esquema admite el
        # mismo email en dos bufetes. Se acepta `bufete` o su alias `slug`.
        bufete = (cuerpo.get("bufete") or cuerpo.get("slug") or "").strip() or None
        try:
            par = self.almacen.usuario_por_email(email, bufete) if email else None
        except BufeteRequerido as e:
            # 401 y no 400: el mensaje pide el dato que falta SIN decir si ese
            # email existe en algun bufete.
            raise NoAutorizado(str(e)) from e"""

A1_IMPORT_ANTES = """from almacen import Almacen, NoAutorizado, SinTenant, Usuario, verificar_password"""

A1_IMPORT_DESPUES = """from almacen import (Almacen, BufeteRequerido, NoAutorizado, SinTenant,
                     Usuario, verificar_password)"""

PARCHES = [
    ("almacen.py", "D1 protocolo + BufeteRequerido", A1_PROTOCOL_ANTES, A1_PROTOCOL_DESPUES),
    ("almacen.py", "D1 login sqlite", A1_SQLITE_ANTES, A1_SQLITE_DESPUES),
    ("almacen.py", "D1 login postgres sin bypass", A1_PG_ANTES, A1_PG_DESPUES),
    ("api.py", "D1 import", A1_IMPORT_ANTES, A1_IMPORT_DESPUES),
    ("api.py", "D1 endpoint /sesion", A1_API_ANTES, A1_API_DESPUES),
    ("api.py", "D2 helper de orden", A2_HELPER_ANTES, A2_HELPER_DESPUES),
    ("api.py", "D2 ultima decision gana", A2_ANTES, A2_DESPUES),
    ("api.py", "D3 log sin requestline", A3_ANTES, A3_DESPUES),
    ("plazos.py", "D4 flag de incertidumbre", A4D_ANTES, A4D_DESPUES),
    ("plazos.py", "D4 arranque corrido PENAL art 130 CPP", A4_ANTES, A4_DESPUES),
    ("plazos.py", "D4 prorroga penal incierta", A4B_ANTES, A4B_DESPUES),
    ("plazos.py", "D4 estado no confirmado", A4C_ANTES, A4C_DESPUES),
]


def main() -> int:
    verificar = "--verificar" in sys.argv
    fallos = []
    textos: dict[str, str] = {}
    for archivo, etiqueta, antes, despues in PARCHES:
        ruta = BACK / archivo
        if archivo not in textos:
            textos[archivo] = ruta.read_text(encoding="utf-8")
        n = textos[archivo].count(antes)
        if n != 1:
            fallos.append(f"ROJO {archivo}: '{etiqueta}' matchea {n} veces, "
                          "se esperaba exactamente 1")
            continue
        textos[archivo] = textos[archivo].replace(antes, despues, 1)
        print(f"OK   {archivo}: {etiqueta}")
    if fallos:
        for f in fallos:
            print(f)
        print("\nNADA SE ESCRIBIO: un parche parcial deja el arbol sin medir.")
        return 3
    if verificar:
        print(f"\nVERIFICACION OK: los {len(PARCHES)} reemplazos matchean 1 vez. "
              "No escribi.")
        return 0
    for archivo, texto in textos.items():
        (BACK / archivo).write_text(texto, encoding="utf-8")
    print(f"\nAPLICADO en {len(textos)} archivos, {len(PARCHES)} reemplazos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
