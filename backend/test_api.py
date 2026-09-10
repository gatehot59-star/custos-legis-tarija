#!/usr/bin/env python3
"""Tests de la API, CONTRA UN SERVIDOR DE VERDAD.

No hay mocks del servidor: se levanta `ThreadingHTTPServer` en un puerto y se le
pegan requests HTTP reales con `urllib`. Un test que llama a la funcion Python
directamente no prueba el ruteo, ni los codigos de estado, ni los headers, ni el
parseo del cuerpo, que es donde estan la mitad de los defectos de una API.

LO QUE ESTOS TESTS **NO** PRUEBAN, y hay que decirlo fuerte:
  **el aislamiento entre bufetes.** Corren contra `SqliteAlmacen`, que NO tiene
  RLS: el filtro por tenant es un `WHERE` de Python que escribi yo. Un verde aca
  probaria mi propio WHERE, no la politica del motor. El aislamiento real se
  prueba en `test_rls.py` contra **PostgreSQL 16** con su falsador `FUGA-CKPT`.

  Lo que SI se prueba aca es el CABLEADO: que la API no deje pasar sin sesion,
  que el gate de acciones externas bloquee, que la compuerta se aplique en
  `/buscar`, y que un bufete no vea el caso del otro **por la via de la API**
  (que es una capa distinta del RLS y tambien puede estar mal).

DOS DEFECTOS DE ESTOS MISMOS TESTS, cazados al correr los falsadores:
  1. El asistente que sembraba NO tenia matricula, asi que el falsador que
     desactiva el chequeo de ROL seguia dando verde: fallaba por la matricula
     ausente, no por el rol. **Veredicto correcto por la razon equivocada**, la
     novena vez del mismo patron en este repo. Ahora hay dos usuarios, uno para
     cada barrera.
  2. Tres falsadores CRASHEABAN el test en vez de fallar una asercion, porque al
     abrir un permiso la respuesta cambiaba de forma y `d["error"]` reventaba.
     Sin `ETIQUETAS_ROJAS`, el arnes del CI lo leia como "fallo pero NO por lo
     que el sabotaje rompe". Un test que crashea da un rojo sin nombre. De ahi
     el helper `err()`.

Correr: python3 test_api.py   (exit 0 verde, exit 1 rojo)
"""
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

import almacen as AL
import api as API

fallos: list[str] = []
etiquetas: set[str] = set()
verdes = 0


def chk(nombre, obtenido, esperado, etiqueta=None):
    global verdes
    if obtenido == esperado:
        verdes += 1
        print(f"  OK   {nombre}: {obtenido}")
    else:
        fallos.append(f"{nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")
        if etiqueta:
            etiquetas.add(etiqueta)
        print(f"  ROJO [{etiqueta or '-'}] {nombre}: "
              f"obtuve {obtenido!r}, esperaba {esperado!r}")


# ---------------------------------------------------------------------------
# DOBLE DEL CORPUS. El real esta CERRADO al publico desde 2026-09-10 06:29 UTC,
# asi que no se puede medir contra el. Este doble devuelve la FORMA del contrato
# documentado en corpus_cliente.py, con un caso normativo y uno jurisprudencial.
# ---------------------------------------------------------------------------
class CorpusDoble:
    def __init__(self, caido=False):
        self.caido = caido

    def buscar(self, q, limit=10):
        if self.caido:
            raise API.CorpusCerrado("doble: corpus cerrado (503)")
        return {"total_pasajes": 2, "resultados": [
            {"uid": "ld-tarija-439", "tipo_norma": "Ley Departamental",
             "numero": "439", "fecha": "2013-11-19", "materia": "presupuestario",
             "fuente_url": "https://gaceta.bo/x", "sha256": "aa11",
             "pasaje": "LEY N 439 DE 19 DE NOVIEMBRE DE 2013. Por cuanto, la "
                       "Asamblea Legislativa Plurinacional, ha sancionado la "
                       "siguiente Ley: DECRETA: ARTICULO 90."},
            {"uid": "as-0099-2013", "tipo_norma": "Auto Supremo",
             "numero": "0099/2013", "fecha": "2013-03-01", "materia": "penal",
             "fuente_url": "https://tsj.bo/y", "sha256": "bb22",
             "pasaje": "VISTOS: el recurso interpuesto por Richard Mamani Correa "
                       "contra Ramon Mamani Delgado. Delito: robo agravado. "
                       "Recurso: Casacion. Magistrado Relator Dr. Juan Perez Soto."},
        ]}


def montar(corpus=None):
    al = AL.SqliteAlmacen(permitir_sin_rls=True)
    a = al.sembrar_bufete("estudio-a", "Estudio A", "socio@a.bo", "clave-a-1234",
                          rol="socio", matricula="MJ-11111")
    b = al.sembrar_bufete("estudio-b", "Estudio B", "socio@b.bo", "clave-b-1234",
                          rol="socio", matricula="MJ-22222")
    # DOS usuarios extra a proposito, y la diferencia importa:
    #   - `asist@a.bo` TIENE matricula. Asi la unica barrera es el ROL.
    #   - `sinmat@a.bo` es socio SIN matricula. Asi la unica barrera es la
    #     MATRICULA.
    # Sin esa separacion el test daba verde por la razon equivocada: sacando el
    # chequeo de rol seguia fallando por la matricula ausente, y el falsador no
    # discriminaba. Es la novena vez que aparece el mismo patron en este repo.
    al.sembrar_bufete("estudio-a2", "Asistente con matricula", "asist@a.bo",
                      "clave-c-1234", rol="asistente", matricula="MJ-99999")
    al.sembrar_bufete("estudio-a3", "Socio sin matricula", "sinmat@a.bo",
                      "clave-d-1234", rol="socio", matricula=None)
    app = API.App(almacen=al, corpus=corpus or CorpusDoble())
    srv = API.servir(app, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return al, app, srv, srv.server_address[1], a, b


def err(d) -> str:
    """El campo `error` o cadena vacia.

    POR QUE ESTE HELPER EXISTE: la v1 de estos tests hacia `d["error"]` directo.
    Cuando un falsador ABRIA un permiso, la respuesta pasaba de 401 a 201 y el
    `d["error"]` reventaba con KeyError. El test CRASHEABA en vez de fallar una
    asercion, asi que **no imprimia ETIQUETAS_ROJAS** y el arnes del CI lo leia
    como "fallo, pero NO por lo que el sabotaje rompe". Un test que crashea no
    informa: da un rojo sin nombre, que es casi tan inutil como un verde falso.
    """
    return (d or {}).get("error", "") if isinstance(d, dict) else ""


def pedir(puerto, metodo, ruta, cuerpo=None, token=None):
    url = f"http://127.0.0.1:{puerto}{ruta}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    if datos:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


al, app, srv, P, bufA, bufB = montar()

print("=== 1. /salud es publico y declara lo que NO midio ===")
c, d = pedir(P, "GET", "/salud")
chk("200", c, 200)
chk("dice el % publicable de la compuerta",
    d["compuerta_privacidad"]["publicables_pct"], 17.3)
chk("lista las acciones externas bloqueadas",
    "presentar_escrito" in d["acciones_externas_bloqueadas_sin_matricula"], True)
chk("declara sus NO MEDIDO", len(d["no_medido"]) >= 3, True)

print("\n=== 2. SIN SESION no se lee nada ===")
for ruta in ("/casos", "/buscar?q=usucapion", "/uso",
             "/plazo?notificacion=2026-09-10&dias=3&materia=civil"):
    c, d = pedir(P, "GET", ruta)
    chk(f"401 en {ruta[:26]}", c, 401, "SIN-SESION-401")
c, d = pedir(P, "POST", "/casos", {"nro_expediente": "x"})
chk("401 al crear caso sin sesion", c, 401, "SIN-SESION-401")
c, d = pedir(P, "GET", "/casos", token="token-inventado")
chk("401 con token inventado", c, 401, "SIN-SESION-401")

print("\n=== 3. Login ===")
c, d = pedir(P, "POST", "/sesion", {"email": "socio@a.bo", "password": "mala"})
chk("password mala -> 401", c, 401, "LOGIN")
c, d = pedir(P, "POST", "/sesion", {"email": "nadie@x.bo", "password": "x"})
chk("email inexistente -> 401", c, 401, "LOGIN")
chk("y el mensaje NO dice si el email existe",
    err(d), "email o contrasena incorrectos", "LOGIN-NO-FILTRA")
c, d = pedir(P, "POST", "/sesion",
             {"email": "socio@a.bo", "password": "clave-a-1234"})
chk("login correcto -> 200", c, 200, "LOGIN")
tokA = d["token"]
chk("trae la matricula", d["usuario"]["matricula"], "MJ-11111")
c, d2 = pedir(P, "POST", "/sesion",
              {"email": "socio@b.bo", "password": "clave-b-1234"})
tokB = d2["token"]
c, d3 = pedir(P, "POST", "/sesion",
              {"email": "asist@a.bo", "password": "clave-c-1234"})
tokAsist = d3["token"]
c, d4 = pedir(P, "POST", "/sesion",
              {"email": "sinmat@a.bo", "password": "clave-d-1234"})
tokSinMat = d4["token"]
chk("cuatro tokens distintos", len({tokA, tokB, tokAsist, tokSinMat}), 4)

print("\n=== 4. LA COMPUERTA se aplica en /buscar ===")
c, d = pedir(P, "GET", "/buscar?q=casacion", token=tokA)
chk("200", c, 200)
por_uid = {r["uid"]: r for r in d["resultados"]}
chk("la LEY viene con texto",
    por_uid["ld-tarija-439"]["texto"] is not None, True, "COMPUERTA-EN-API")
chk("y con decision publico", por_uid["ld-tarija-439"]["decision_compuerta"],
    "publico", "COMPUERTA-EN-API")
chk("el AUTO SUPREMO viene SIN texto",
    por_uid["as-0099-2013"]["texto"], None, "COMPUERTA-EN-API")
chk("y el nombre de la parte NO aparece en toda la respuesta",
    "Mamani" in json.dumps(d), False, "CERO-NOMBRES-EN-API")
chk("pero SI la cadena de custodia",
    bool(por_uid["as-0099-2013"]["fuente_url"]), True)
chk("el contador de retenidos es 1", d["compuerta"]["retenidos"], 1,
    "COMPUERTA-EN-API")
chk("la consulta NO se devuelve en claro, solo su hash",
    "casacion" in json.dumps(d), False, "SENSOR-NO-GUARDA-TEXTO")

print("\n=== 5. EL SENSOR de uso (T1 de Fable) ===")
chk("la busqueda quedo registrada", al.uso_total(), 1, "SENSOR")
c, d = pedir(P, "GET", "/uso", token=tokA)
chk("y /uso lo reporta", d["consultas_registradas"], 1, "SENSOR")
fila = al.con.execute("SELECT q_hash FROM uso_consultas").fetchone()
chk("guarda un sha256 de 64 chars, no el texto", len(fila["q_hash"]), 64,
    "SENSOR-NO-GUARDA-TEXTO")
chk("y no es el texto", fila["q_hash"] == "casacion", False,
    "SENSOR-NO-GUARDA-TEXTO")

print("\n=== 6. Casos: un bufete NO ve los del otro (via API) ===")
c, caso = pedir(P, "POST", "/casos",
                {"nro_expediente": "201/2026", "juzgado": "Juzgado Civil 3ro",
                 "materia": "civil"}, token=tokA)
chk("201 al crear", c, 201)
cid = caso["id"]
c, d = pedir(P, "GET", "/casos", token=tokA)
chk("A ve su caso", [x["nro_expediente"] for x in d["casos"]], ["201/2026"],
    "AISLAMIENTO-API")
c, d = pedir(P, "GET", "/casos", token=tokB)
chk("B NO ve nada", d["casos"], [], "AISLAMIENTO-API")
c, d = pedir(P, "POST", "/casos", {"nro_expediente": "x"}, token=tokA)
chk("faltan campos -> 400", c, 400)
c, d = pedir(P, "POST", "/casos",
             {"nro_expediente": "9/2026", "juzgado": "J", "materia": "laboral"},
             token=tokA)
chk("materia sin motor -> se crea CON advertencia",
    "advertencia_materia" in d, True, "MATERIA-SIN-MOTOR")

print("\n=== 7. /plazo: nunca una fecha muda ===")
c, d = pedir(P, "GET", "/plazo?notificacion=2026-09-10&dias=3&materia=civil",
             token=tokA)
chk("200", c, 200)
chk("trae el computo dia por dia", len(d["computo"]) >= 3, True, "COMPUTO-VISIBLE")
chk("y el fundamento cita el 90.II", "90.II" in d["fundamento"], True)
chk("2026 sin circular -> NO_MEDIDO", d["estado"], "NO_MEDIDO", "PLAZO-HONESTO")
chk("y no se declara confiable", d["confiable"], False, "PLAZO-HONESTO")
c, d = pedir(P, "GET", "/plazo?notificacion=2023-12-01&dias=10&materia=civil",
             token=tokA)
chk("un plazo de 2023 pasa por la vacacion judicial cargada",
    any("suspendido" in x["marca"] for x in d["computo"]), True, "VACACION-EN-API")
c, d = pedir(P, "GET",
             "/plazo?notificacion=2026-09-10&dias=10&materia=contencioso_administrativo",
             token=tokA)
chk("materia no modelada -> NO_MEDIDO, sin fecha", d["vencimiento"], None,
    "TERCER-REGIMEN-EN-API")
chk("y dice por que", "MOMENTO A MOMENTO" in d["motivo"], True,
    "TERCER-REGIMEN-EN-API")
c, d = pedir(P, "GET", "/plazo?dias=3&materia=civil", token=tokA)
chk("sin fecha de notificacion -> 400", c, 400)

print("\n=== 8. EL GATE: ninguna accion externa sin matricula ===")
memorial = "SENOR JUEZ: en el proceso 201/2026 solicito se tenga por presentado..."
c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "presentar_escrito", "contenido": memorial,
              "case_id": cid}, token=tokA)
chk("sin aprobacion -> 403", c, 403, "GATE-BLOQUEA")
chk("y lo llama gate HITL", d["gate"], "HITL", "GATE-BLOQUEA")
chk("el motivo cita la Ley 387", "387" in err(d), True, "GATE-BLOQUEA")

# DOS barreras independientes, probadas por separado para que cada falsador
# tenga algo que romper.
c, d = pedir(P, "POST", "/aprobar",
             {"tipo": "presentar_escrito", "contenido": memorial}, token=tokAsist)
chk("un asistente CON matricula NO puede aprobar -> 401", c, 401, "ROL-APRUEBA")
chk("y el motivo es el ROL, no la matricula", "rol" in err(d), True,
    "ROL-APRUEBA")
c, d = pedir(P, "POST", "/aprobar",
             {"tipo": "presentar_escrito", "contenido": memorial},
             token=tokSinMat)
chk("un socio SIN matricula tampoco -> 401", c, 401, "MATRICULA-OBLIGATORIA")
chk("y ahi el motivo es la MATRICULA", "matricula" in err(d), True,
    "MATRICULA-OBLIGATORIA")

# El socio aprueba.
c, d = pedir(P, "POST", "/aprobar",
             {"tipo": "presentar_escrito", "contenido": memorial,
              "case_id": cid, "fundamento": "revisado art. por art."}, token=tokA)
chk("el socio aprueba -> 201", c, 201, "ROL-APRUEBA")
chk("y queda firmado con su matricula", d["aprobacion"]["matricula"], "MJ-11111",
    "HITL-MATRICULA")

c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "presentar_escrito", "contenido": memorial,
              "case_id": cid}, token=tokA)
chk("ahora la accion esta AUTORIZADA", c, 200, "GATE-ABRE-CON-APROBACION")
chk("pero NO ejecutada, y lo dice", d["estado"], "AUTORIZADA_PERO_NO_EJECUTADA",
    "NO-SIMULA-EJECUCION")

print("\n=== 9. LA FUGA OBVIA DEL HITL: aprobar uno y ejecutar otro ===")
# Aprobar un borrador y presentar otro es el agujero de todo esquema de
# aprobacion humana. Aca lo cierra el sha256, no la confianza.
otro = memorial + " Y ADEMAS renuncio al plazo probatorio."
c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "presentar_escrito", "contenido": otro, "case_id": cid},
             token=tokA)
chk("contenido MODIFICADO -> 403 aunque haya aprobacion del original", c, 403,
    "HASH-EXACTO")
chk("y el error muestra el hash que faltaba",
    "sha256" in err(d), True, "HASH-EXACTO")
# Y el tipo tambien tiene que coincidir.
c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "notificar_cliente", "contenido": memorial, "case_id": cid},
             token=tokA)
chk("mismo contenido, OTRO tipo de accion -> 403", c, 403, "TIPO-EXACTO")
# Y la aprobacion de A no sirve para B.
c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "presentar_escrito", "contenido": memorial}, token=tokB)
chk("la aprobacion del bufete A NO sirve para B -> 403", c, 403,
    "AISLAMIENTO-APROBACION")
# Un rechazo NO habilita.
rech = "borrador que el socio rechazo"
pedir(P, "POST", "/aprobar",
      {"tipo": "presentar_escrito", "contenido": rech, "decision": "rechazado"},
      token=tokA)
c, d = pedir(P, "POST", "/acciones/externa",
             {"tipo": "presentar_escrito", "contenido": rech}, token=tokA)
chk("un RECHAZO no habilita la accion -> 403", c, 403, "RECHAZO-NO-HABILITA")

print("\n=== 10. Cerrar sesion invalida el token ===")
c, d = pedir(P, "DELETE", "/sesion", token=tokB)
chk("200 al cerrar", c, 200)
c, d = pedir(P, "GET", "/casos", token=tokB)
chk("y despues 401", c, 401, "SESION-CERRADA")

print("\n=== 11. Corpus cerrado -> 503 con el motivo, no un 500 ===")
al2 = AL.SqliteAlmacen(permitir_sin_rls=True)
al2.sembrar_bufete("c", "C", "s@c.bo", "clave-c-9999", matricula="MJ-33333")
app2 = API.App(almacen=al2, corpus=CorpusDoble(caido=True))
srv2 = API.servir(app2, "127.0.0.1", 0)
threading.Thread(target=srv2.serve_forever, daemon=True).start()
P2 = srv2.server_address[1]
c, d = pedir(P2, "POST", "/sesion", {"email": "s@c.bo", "password": "clave-c-9999"})
tok2 = d["token"]
c, d = pedir(P2, "GET", "/buscar?q=x", token=tok2)
chk("503, no 500", c, 503, "CORPUS-CERRADO-503")
chk("y dice que esta cerrado", d["corpus"], "cerrado", "CORPUS-CERRADO-503")

print("\n=== 12. El almacen SIN RLS se niega a ir a produccion ===")
import os
try:
    AL.SqliteAlmacen()
    chk("sin el flag deberia explotar", "no exploto", "RuntimeError",
        "SQLITE-NO-PRODUCCION")
except RuntimeError:
    verdes += 1
    print("  OK   sin permitir_sin_rls explota")
os.environ["CUSTOS_ENTORNO"] = "produccion"
try:
    AL.SqliteAlmacen(permitir_sin_rls=True)
    chk("en produccion deberia explotar IGUAL", "no exploto", "RuntimeError",
        "SQLITE-NO-PRODUCCION")
except RuntimeError:
    verdes += 1
    print("  OK   en CUSTOS_ENTORNO=produccion explota aunque pase el flag")
finally:
    del os.environ["CUSTOS_ENTORNO"]

print("\n=== 13. Sin tenant es un DEFECTO (500), no un permiso (403) ===")
# Si algun dia una consulta llega sin tenant, no puede degradarse a "todos".
try:
    al.casos(None)
    chk("deberia levantar SinTenant", "no levanto", "SinTenant", "SIN-TENANT")
except AL.SinTenant:
    verdes += 1
    print("  OK   el almacen levanta SinTenant en vez de ampliar el WHERE")

srv.shutdown()
srv2.shutdown()
print(f"\n{'='*62}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    if etiquetas:
        print("ETIQUETAS_ROJAS: " + " ".join(sorted(etiquetas)))
    sys.exit(1)
print("VERDE")
