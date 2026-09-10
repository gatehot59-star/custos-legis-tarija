#!/usr/bin/env python3
"""API de Custos Legis Tarija. Solo stdlib.

--------------------------------------------------------------------------------
POR QUE STDLIB Y NO FastAPI, y es una decision medida, no una preferencia
--------------------------------------------------------------------------------
El diseno original pedia FastAPI. **En el taller donde se escribio esto FastAPI
no esta instalado y no hay red para instalarlo.** Escribir FastAPI aca habria
sido commitear codigo que NO PUEDO EJECUTAR, y la regla del proyecto es que
ningun script se commitea sin correrlo.

Con stdlib esta API se levanta, se le pegan requests reales y se mide de punta a
punta hoy. Ademas el corpus ya corre en produccion con `ThreadingHTTPServer` de
stdlib en la misma VM, asi que no es un experimento.

Efecto colateral bueno: **el D6 de Fable desaparece.** Su defecto era
`Depends(lambda: next(get_db()))`, un generador sin consumir. Sin `Depends` no
existe ese error posible. Si manana se migra a FastAPI, ese defecto vuelve a
estar disponible y hay que cuidarlo.

--------------------------------------------------------------------------------
LOS TRES CONTROLES DUROS, y cada uno con su falsador en CI
--------------------------------------------------------------------------------
  1. NADIE lee datos sin sesion, y ninguna consulta se degrada a "todos los
     bufetes": sin tenant se LEVANTA `SinTenant`, no se amplia el WHERE.
  2. NINGUNA accion externa sale sin un evento de aprobacion por matricula
     registrado ANTES, sobre el sha256 EXACTO del contenido que se va a ejecutar.
     Aprobar un borrador y ejecutar otro es la fuga obvia y esta cerrada.
  3. La jurisprudencia NO se sirve como texto: pasa por la compuerta de
     `anonimizador.py`. La normativa si, porque no tiene partes.

--------------------------------------------------------------------------------
QUE ES NO MEDIDO
--------------------------------------------------------------------------------
  1. `PostgresAlmacen` no se ejecuto aca (`psycopg` no instalado). El SQL es el
     mismo que corre verde en `test_rls.py` contra PostgreSQL 16 real, pero esa
     clase en particular NO fue ejecutada.
  2. El corpus esta CERRADO al publico desde 2026-09-10 06:29 UTC. `/buscar`
     contra el corpus real no se pudo medir; se mide contra un doble que
     devuelve la forma documentada del contrato.
  3. TLS, rate limiting y rotacion de tokens: no estan. Van en nginx, no aca.
  4. Los tokens viven en memoria del proceso: reiniciar el servicio corta todas
     las sesiones. Aceptable para un piloto, NO para produccion con varios
     workers. Declarado.
  5. No hay paginacion en `/casos`. Con 20 expedientes no importa; con 2.000 si.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import secrets
import time
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anonimizador as AN
import calendario_judicial as CAL
import plazos as PZ
from almacen import Almacen, NoAutorizado, SinTenant, Usuario, verificar_password

VERSION = "0.1.0"
SESION_TTL_S = 8 * 3600           # una jornada de trabajo
ROLES_QUE_APRUEBAN = frozenset({"socio", "asociado"})


def ahora() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# SESIONES
# ---------------------------------------------------------------------------


@dataclass
class Sesion:
    token: str
    usuario: Usuario
    expira: float

    @property
    def viva(self) -> bool:
        return time.time() < self.expira


@dataclass
class Sesiones:
    _por_token: dict[str, Sesion] = field(default_factory=dict)

    def abrir(self, u: Usuario) -> Sesion:
        # token_urlsafe usa `secrets`, no `random`: `random` es predecible.
        s = Sesion(token=secrets.token_urlsafe(32), usuario=u,
                   expira=time.time() + SESION_TTL_S)
        self._por_token[s.token] = s
        return s

    def leer(self, token: str | None) -> Sesion:
        if not token:
            raise NoAutorizado("falta el token de sesion")
        s = self._por_token.get(token)
        if s is None:
            raise NoAutorizado("token desconocido")
        if not s.viva:
            del self._por_token[token]
            raise NoAutorizado("sesion expirada")
        return s

    def cerrar(self, token: str) -> None:
        self._por_token.pop(token, None)


# ---------------------------------------------------------------------------
# CORPUS: un puerto, para poder medir sin el corpus vivo
# ---------------------------------------------------------------------------


class CorpusCerrado(RuntimeError):
    pass


@dataclass
class CorpusHTTP:
    """Cliente real. Hoy da 503 porque el corpus esta cerrado al publico."""

    base: str = "https://150448fcc6.abacusai.cloud"

    def buscar(self, q: str, limit: int = 10) -> dict:
        import urllib.error
        import urllib.request
        url = f"{self.base}/buscar?" + urllib.parse.urlencode(
            {"q": q, "limit": limit})
        req = urllib.request.Request(
            url, headers={"User-Agent": f"custos-legis/{VERSION}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 503:
                raise CorpusCerrado(
                    "el corpus esta cerrado al publico (503). Ver "
                    "corpus-legal-tarija/CIERRE-PUBLICO-2026-09-10.md") from e
            raise
        except Exception as e:
            # "No llegue" y "me rechazaron" NO son lo mismo, y el mensaje lo dice.
            raise CorpusCerrado(f"{type(e).__name__}: {e}") from e


# ---------------------------------------------------------------------------
# EL GATE DE ACCIONES EXTERNAS
# ---------------------------------------------------------------------------

ACCIONES_EXTERNAS = frozenset({
    "presentar_escrito", "notificar_cliente", "firmar_digital",
    "enviar_a_juzgado", "consultar_con_credenciales",
})


class GateBloqueado(RuntimeError):
    pass


def exigir_aprobacion(almacen: Almacen, tenant_id: str, tipo: str,
                      contenido: str, case_id: str | None) -> dict:
    """Devuelve la aprobacion valida o LEVANTA. No hay tercera opcion.

    La aprobacion tiene que ser sobre el sha256 EXACTO del contenido. Aprobar un
    borrador y ejecutar otro es la fuga obvia de todo esquema de HITL, y aca
    esta cerrada por el hash, no por confianza.
    """
    h = sha256(contenido)
    for ev in almacen.aprobaciones(tenant_id, case_id):
        if (ev.get("tipo") == tipo and ev.get("sha256_entrada") == h
                and ev.get("decision") == "aprobado" and ev.get("matricula")):
            return ev
    raise GateBloqueado(
        f"accion '{tipo}' BLOQUEADA: no hay aprobacion de un abogado con "
        f"matricula sobre este contenido exacto (sha256 {h[:12]}...). "
        "Aprobar un borrador y ejecutar otro no cuenta: el hash tiene que "
        "coincidir. Fundamento: Ley 387 arts. 6 y 32.II")


# ---------------------------------------------------------------------------
# LA APP
# ---------------------------------------------------------------------------


@dataclass
class App:
    almacen: Almacen
    corpus: object = field(default_factory=CorpusHTTP)
    sesiones: Sesiones = field(default_factory=Sesiones)
    calendario: PZ.CalendarioJudicial = field(
        default_factory=lambda: CAL.calendario("Tarija"))

    # -- rutas -------------------------------------------------------------
    def salud(self) -> dict:
        """Publica. Y declara lo que el sistema NO puede hacer, a proposito:
        un /salud que solo dice "ok" es una invitacion a suponer."""
        return {
            "servicio": "custos-legis-tarija",
            "version": VERSION,
            "ts": ahora(),
            "compuerta_privacidad": AN.IMPACTO_MEDIDO,
            "calendario_judicial": CAL.cobertura("Tarija"),
            "acciones_externas_bloqueadas_sin_matricula": sorted(ACCIONES_EXTERNAS),
            "no_medido": [
                "PostgresAlmacen no ejecutado en el taller (sin psycopg)",
                "corpus cerrado al publico: /buscar no medido contra el real",
                "tokens en memoria del proceso: un reinicio corta las sesiones",
            ],
        }

    def abrir_sesion(self, cuerpo: dict) -> dict:
        email = (cuerpo.get("email") or "").strip()
        pw = cuerpo.get("password") or ""
        par = self.almacen.usuario_por_email(email) if email else None
        # Se verifica el password SIEMPRE, incluso si el usuario no existe, para
        # que el tiempo de respuesta no diga si el email esta registrado.
        guardado = par[1] if par else hash_imposible()
        ok = verificar_password(pw, guardado)
        if not par or not ok:
            # UN solo mensaje para los dos casos. "email no registrado" le
            # confirmaria a un tercero quien trabaja en el bufete.
            raise NoAutorizado("email o contrasena incorrectos")
        s = self.sesiones.abrir(par[0])
        return {"token": s.token, "expira_en_s": SESION_TTL_S,
                "usuario": {"nombre": par[0].nombre, "rol": par[0].rol,
                            "matricula": par[0].matricula},
                "bufete_id": par[0].tenant_id}

    def buscar(self, s: Sesion, q: str, limit: int = 10) -> dict:
        t0 = time.time()
        crudo = self.corpus.buscar(q, limit=limit)
        ms = int((time.time() - t0) * 1000)

        salida, retenidos = [], 0
        for r in crudo.get("resultados", []):
            texto = r.get("pasaje") or ""
            v = AN.evaluar(texto, r.get("materia"),
                           tipo_declarado=r.get("tipo_norma"))
            ficha = AN.ficha_publica(r)
            if v.publicable:
                ficha["texto"] = v.texto_publicable
                ficha["nota"] = "normativo: texto completo"
            else:
                retenidos += 1
                ficha["nota"] = (f"texto RETENIDO ({v.decision.value}): "
                                 + (v.motivos[-1] if v.motivos else ""))
            ficha["decision_compuerta"] = v.decision.value
            salida.append(ficha)

        # SENSOR (T1 de Fable). q_hash y NO el texto: una busqueda juridica
        # revela la estrategia de un caso.
        self.almacen.registrar_uso(s.usuario.tenant_id, sha256(q.lower()),
                                   len(salida), ms)
        return {
            "consulta_hash": sha256(q.lower())[:16],
            "total_pasajes": crudo.get("total_pasajes"),
            "ms": ms,
            "resultados": salida,
            "compuerta": {
                "retenidos": retenidos,
                "de": len(salida),
                "regla": "la capa publica no muestra texto de jurisprudencia; "
                         "para el extracto hace falta aprobacion por matricula",
            },
        }

    def casos(self, s: Sesion) -> dict:
        return {"casos": self.almacen.casos(s.usuario.tenant_id)}

    def crear_caso(self, s: Sesion, cuerpo: dict) -> dict:
        faltan = [k for k in ("nro_expediente", "juzgado", "materia")
                  if not cuerpo.get(k)]
        if faltan:
            raise ValueError("faltan campos: " + ", ".join(faltan))
        # El caso se crea igual, PERO con la advertencia adentro: si la materia
        # no tiene motor de plazos, el abogado tiene que saberlo al cargarla, no
        # al pedir un vencimiento que nunca va a llegar.
        ok, motivo = PZ.materia_modelada(cuerpo["materia"])
        caso = self.almacen.crear_caso(s.usuario.tenant_id, cuerpo)
        if not ok:
            caso["advertencia_materia"] = (
                f"materia '{cuerpo['materia']}' NO tiene motor de plazos: {motivo}")
        return caso

    def plazo(self, s: Sesion, params: dict) -> dict:
        try:
            noti = _dt.date.fromisoformat(params["notificacion"])
            dias = int(params["dias"])
        except (KeyError, ValueError) as e:
            raise ValueError(
                "se requiere notificacion=YYYY-MM-DD y dias=<entero>") from e
        nombre = (params.get("materia") or "").lower()
        ok, motivo = PZ.materia_modelada(nombre)
        if not ok:
            # NO se devuelve una fecha. Una fecha creible y equivocada es peor
            # que ninguna fecha.
            return {"estado": PZ.NO_MEDIDO, "vencimiento": None,
                    "motivo": motivo,
                    "advertencia": "este sistema NO calcula plazos de esa "
                                   "materia. No se devuelve una fecha creible "
                                   "y equivocada."}
        materia = PZ.Materia(nombre)
        cautelar = str(params.get("cautelar", "")).lower() in ("1", "true", "si")
        c = PZ.computo_detallado(noti, dias, materia, medida_cautelar=cautelar,
                                 calendario=self.calendario)
        return {
            "estado": c.estado,
            "confiable": c.confiable,
            "vencimiento": c.vencimiento.isoformat() if c.vencimiento else None,
            "modo": c.modo,
            "fundamento": c.fundamento,
            "advertencias": c.advertencias,
            # El dia por dia viaja SIEMPRE. Un numero pelado no es verificable, y
            # el responsable final del computo es el abogado.
            "computo": [{"fecha": d["fecha"].isoformat(), "marca": d["marca"],
                         "cuenta": d["cuenta"], "n": d["n"]} for d in c.detalle],
        }

    def aprobar(self, s: Sesion, cuerpo: dict) -> dict:
        # DOS barreras independientes. Cada una tiene su falsador, porque si
        # solo hubiera una prueba conjunta, sacar cualquiera de las dos daria
        # verde por la otra: es el defecto que me cazo el test hoy.
        if s.usuario.rol not in ROLES_QUE_APRUEBAN:
            raise NoAutorizado(
                f"el rol '{s.usuario.rol}' no puede aprobar actos procesales")
        if not s.usuario.matricula:
            raise NoAutorizado(
                "el usuario no tiene matricula registrada: la aprobacion se "
                "firma con el numero del Registro Publico de la Abogacia "
                "(Ley 387 art. 13)")
        tipo = cuerpo.get("tipo") or ""
        contenido = cuerpo.get("contenido")
        if not tipo or contenido is None:
            raise ValueError("se requiere tipo y contenido")
        decision = cuerpo.get("decision", "aprobado")
        if decision not in ("aprobado", "rechazado"):
            raise ValueError("decision debe ser 'aprobado' o 'rechazado'")
        ev = self.almacen.registrar_aprobacion(s.usuario.tenant_id, {
            "case_id": cuerpo.get("case_id"),
            "matricula": s.usuario.matricula,
            "usuario_id": s.usuario.id,
            "tipo": tipo,
            "sha256_entrada": sha256(contenido),
            "decision": decision,
            "fundamento": cuerpo.get("fundamento"),
            "ts": ahora(),
        })
        return {"aprobacion": ev,
                "nota": "la responsabilidad del contenido es del abogado que "
                        "firma con su matricula (Ley 387 art. 32.II)"}

    def ejecutar_externa(self, s: Sesion, cuerpo: dict) -> dict:
        tipo = cuerpo.get("tipo") or ""
        if tipo not in ACCIONES_EXTERNAS:
            raise ValueError(f"accion desconocida: {tipo!r}")
        contenido = cuerpo.get("contenido")
        if contenido is None:
            raise ValueError("se requiere contenido")
        ev = exigir_aprobacion(self.almacen, s.usuario.tenant_id, tipo,
                               contenido, cuerpo.get("case_id"))
        # NO se ejecuta nada: no hay integracion con el juzgado ni firma digital,
        # y decirlo es mas honesto que simular un envio. Un "enviado: true"
        # falso seria la peor mentira que este sistema puede decir.
        return {"estado": "AUTORIZADA_PERO_NO_EJECUTADA",
                "aprobada_por_matricula": ev["matricula"],
                "sha256_entrada": ev["sha256_entrada"],
                "motivo": "no existe integracion con SIREJ/SIGC ni firma digital. "
                          "El gate autoriza; la ejecucion no esta construida y no "
                          "se simula."}

    def uso(self, s: Sesion) -> dict:
        n = self.almacen.uso_total()
        return {"consultas_registradas": n,
                "nota": "el sensor guarda q_hash, no el texto de la busqueda. "
                        "Un cero medido vale mas que 6.079 documentos sin sensor."}


def hash_imposible() -> str:
    """Hash valido pero imposible de acertar, para que el login tarde igual
    cuando el email no existe. Sin esto, el tiempo de respuesta dice si un
    email esta registrado en el bufete."""
    return "pbkdf2_sha256$200000$" + "00" * 16 + "$" + "ff" * 32


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def construir_handler(app: App):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = f"custos-legis/{VERSION}"

        def log_message(self, fmt, *args):  # noqa: A003
            # NO se loguea la query string: puede traer el texto de una busqueda
            # juridica, y eso revela la estrategia de un caso. Misma regla que
            # el `log_format corpus_sin_query` de nginx.
            ruta = urllib.parse.urlparse(self.path).path
            print(f"{self.address_string()} {self.command} {ruta} "
                  f"{fmt % args if args else ''}".strip())

        def _responder(self, codigo: int, cuerpo: dict) -> None:
            b = json.dumps(cuerpo, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def _sesion(self) -> Sesion:
            auth = self.headers.get("Authorization") or ""
            token = auth[7:].strip() if auth.lower().startswith("bearer ") else None
            return app.sesiones.leer(token)

        def _cuerpo(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception as e:
                raise ValueError(f"cuerpo JSON invalido: {e}") from e

        def _despachar(self, metodo: str, ruta: str, params: dict):
            # SOLO estas dos rutas viven ARRIBA de la barrera de sesion. Todo lo
            # que este debajo del `self._sesion()` exige token, y eso lo prueba
            # un falsador que hace publica /casos.
            if ruta == "/salud" and metodo == "GET":
                return 200, app.salud()
            if ruta == "/sesion" and metodo == "POST":
                return 200, app.abrir_sesion(self._cuerpo())
            s = self._sesion()
            if ruta == "/sesion" and metodo == "DELETE":
                app.sesiones.cerrar(s.token)
                return 200, {"cerrada": True}
            if ruta == "/buscar" and metodo == "GET":
                q = (params.get("q") or [""])[0]
                if not q:
                    raise ValueError("falta q")
                lim = int((params.get("limit") or ["10"])[0])
                return 200, app.buscar(s, q, min(lim, 50))
            if ruta == "/casos":
                if metodo == "GET":
                    return 200, app.casos(s)
                if metodo == "POST":
                    return 201, app.crear_caso(s, self._cuerpo())
            if ruta == "/plazo" and metodo == "GET":
                return 200, app.plazo(s, {k: v[0] for k, v in params.items()})
            if ruta == "/aprobar" and metodo == "POST":
                return 201, app.aprobar(s, self._cuerpo())
            if ruta == "/acciones/externa" and metodo == "POST":
                return 200, app.ejecutar_externa(s, self._cuerpo())
            if ruta == "/uso" and metodo == "GET":
                return 200, app.uso(s)
            return 404, {"error": f"no existe {metodo} {ruta}"}

        def _manejar(self, metodo: str) -> None:
            u = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(u.query)
            try:
                codigo, cuerpo = self._despachar(metodo, u.path, params)
                self._responder(codigo, cuerpo)
            except NoAutorizado as e:
                self._responder(401, {"error": str(e)})
            except SinTenant as e:
                # 500 y no 403: si esto pasa es un BUG mio, no un permiso que
                # falta. Confundirlos haria que un defecto se lea como "el
                # usuario no tenia acceso", y nadie lo iria a arreglar.
                self._responder(500, {"error": f"defecto interno: {e}"})
            except GateBloqueado as e:
                self._responder(403, {"error": str(e), "gate": "HITL"})
            except CorpusCerrado as e:
                self._responder(503, {"error": str(e), "corpus": "cerrado"})
            except ValueError as e:
                self._responder(400, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                self._responder(500, {"error": f"{type(e).__name__}: {e}"})

        def do_GET(self):     self._manejar("GET")       # noqa: E704,N802
        def do_POST(self):    self._manejar("POST")      # noqa: E704,N802
        def do_DELETE(self):  self._manejar("DELETE")    # noqa: E704,N802

    return H


def servir(app: App, host: str = "127.0.0.1", puerto: int = 8090):
    """Escucha en 127.0.0.1 POR DEFECTO, no en 0.0.0.0.

    El corpus tenia `ThreadingHTTPServer(("0.0.0.0", PORT))` y eso dejo un hueco
    que el 503 de nginx NO tapaba: cualquier cosa en la red de la VM le pegaba al
    backend directo. Aca el default es loopback y salir de ahi es explicito. La
    leccion queda en el codigo, no en un documento que nadie relee.
    """
    return ThreadingHTTPServer((host, puerto), construir_handler(app))


if __name__ == "__main__":
    import os
    import sys
    from almacen import PostgresAlmacen

    dsn = os.environ.get("DATABASE_URL_APP")
    if not dsn:
        print("falta DATABASE_URL_APP. La API NO arranca con un almacen de "
              "prueba: SqliteAlmacen no tiene RLS y el aislamiento de un bufete "
              "no puede depender de un WHERE de Python.", file=sys.stderr)
        sys.exit(2)
    app = App(almacen=PostgresAlmacen(dsn))
    host = os.environ.get("CUSTOS_HOST", "127.0.0.1")
    puerto = int(os.environ.get("CUSTOS_PUERTO", "8090"))
    if host != "127.0.0.1":
        print(f"ATENCION: escuchando en {host}, no en loopback. Eso solo tiene "
              "sentido si nginx esta en otra maquina.", file=sys.stderr)
    print(f"custos-legis {VERSION} en http://{host}:{puerto}")
    servir(app, host, puerto).serve_forever()
