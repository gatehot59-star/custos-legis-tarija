"""repro_cache.py: reproduce la "version vieja" que ve el usuario y prueba el arreglo.

Instrumento: navegadores reales (Playwright) contra un servidor local que imita los
headers medidos en vivo el 26-10-2026 en astra.icca-engine.com:
  - la v5 se sirvio con Last-Modified 18-oct 02:58 UTC y SIN Cache-Control
    (frescura heuristica del navegador: 10% de la edad, unas 19-20 h);
  - la v8 se sirve con Cache-Control "no-cache, no-transform";
  - antes del arreglo, /legal-tech-<pais> respondia 302 a /#/legal-tech-<pais> sin mas.

Escenarios del salto /legal-tech-bolivia:
  A  como estaba hasta el 26-10 11:31 UTC (sin Clear-Site-Data, sin query)
  B  con Clear-Site-Data "cache"
  C  con Clear-Site-Data "cache" y ?pais= en el destino (el arreglo publicado)
  D  solo ?pais= (sin Clear-Site-Data)
  E  los headers EXACTOS que devuelve hoy el sitio en vivo (vivo_302.json)

Por que puede dar ROJO: el paso 2 (control) muestra si el navegador sirve la copia
vieja sin consultar al servidor; el paso 3 muestra que ve el usuario al tocar el
link; el paso 4, si la portada sigue vieja despues. El registro del servidor dice
que pedidos llegaron de verdad. Si la cache no se envenena, el control da v8 y la
teoria queda refutada.

Uso: python3 repro_cache.py salida.json [vivo_302.json]
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

LM_V5 = "Sun, 18 Oct 2026 02:58:00 GMT"
LM_V8 = "Mon, 26 Oct 2026 05:30:21 GMT"
ESTADO = {"modo": "v5", "salto": "A"}
REGISTRO = []
VIVO = []

SALTOS = {
    "A": ("A_como_estaba", [("Location", "/#/legal-tech-{slug}")]),
    "B": ("B_clear_site_data", [("Location", "/#/legal-tech-{slug}"),
                                ("Clear-Site-Data", '"cache"'), ("Cache-Control", "no-store")]),
    "C": ("C_clear_site_data_y_query", [("Location", "/?pais={slug}#/legal-tech-{slug}"),
                                        ("Clear-Site-Data", '"cache"'), ("Cache-Control", "no-store")]),
    "D": ("D_solo_query", [("Location", "/?pais={slug}#/legal-tech-{slug}")]),
}


def pagina(ver):
    """HTML minimo que dice que version es."""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='astra-version' content='{ver}'><title>{ver}</title></head>"
        f"<body><h1 id='v'>{ver}</h1></body></html>"
    ).encode()


class Servidor(BaseHTTPRequestHandler):
    """Imita al nginx de produccion en lo que importa para la cache."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        return

    def _vacio(self, codigo, extra=None):
        self.send_response(codigo)
        for k, v in (extra or []):
            self.send_header(k, v)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        ruta = self.path.split("?")[0].split("#")[0]
        REGISTRO.append({
            "t": round(time.time(), 3),
            "modo_servidor": ESTADO["modo"],
            "path": self.path,
            "if_none_match": self.headers.get("If-None-Match"),
        })
        if ruta in ("/", "/index.html"):
            ver = ESTADO["modo"]
            etag = '"' + ver + '"'
            if self.headers.get("If-None-Match") == etag:
                extra = [("ETag", etag)]
                if ver == "v8":
                    extra.append(("Cache-Control", "no-cache, no-transform"))
                self._vacio(304, extra)
                return
            cuerpo = pagina(ver)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("ETag", etag)
            if ver == "v5":
                self.send_header("Last-Modified", LM_V5)
            else:
                self.send_header("Last-Modified", LM_V8)
                self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return
        if ruta.startswith("/legal-tech-"):
            slug = ruta[len("/legal-tech-"):].strip("/")
            if ESTADO["salto"] == "E":
                extra = [(k, v) for k, v in VIVO]
            else:
                extra = [(k, v.format(slug=slug)) for k, v in SALTOS[ESTADO["salto"]][1]]
            self._vacio(302, extra)
            return
        self._vacio(404)


def leer(page):
    """Que version muestra la pestania y en que URL quedo."""
    return page.evaluate(
        "() => ({v: (document.getElementById('v') || {}).textContent || null, url: location.href})"
    )


def escenario(nav, base, clave):
    """Visita con v5 publicada, publica v8 y recorre lo que haria el usuario."""
    ESTADO.update(modo="v5", salto=clave)
    ctx = nav.new_context()
    n0 = len(REGISTRO)
    p1 = ctx.new_page()
    p1.goto(base + "/")
    paso1 = leer(p1)
    p1.close()
    ESTADO["modo"] = "v8"
    p2 = ctx.new_page()
    p2.goto(base + "/")
    control = leer(p2)
    p2.close()
    p3 = ctx.new_page()
    t0 = time.time()
    p3.goto(base + "/legal-tech-bolivia")
    p3.wait_for_timeout(400)
    link = leer(p3)
    link["ms"] = round((time.time() - t0) * 1000)
    p3.close()
    p4 = ctx.new_page()
    p4.goto(base + "/")
    despues = leer(p4)
    p4.close()
    ctx.close()
    return {
        "salto_302": VIVO if clave == "E" else SALTOS[clave][1],
        "1_visita_cuando_estaba_v5": paso1,
        "2_control_inicio_con_v8_publicada": control,
        "3_toca_link_legal_tech_bolivia": link,
        "4_inicio_despues": despues,
        "pedidos_que_llegaron_al_servidor": [
            r for r in REGISTRO[n0:] if not r["path"].startswith("/favicon")
        ],
    }


def main(salida, vivo=None):
    if vivo:
        with open(vivo, encoding="utf-8") as f:
            VIVO.extend(tuple(x) for x in json.load(f))
    claves = ["A", "B", "C", "D"] + (["E"] if VIVO else [])
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Servidor)
    puerto = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://localhost:{puerto}"
    res = {"inicio_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "motores": {}}
    with sync_playwright() as p:
        for motor in ("chromium", "firefox", "webkit"):
            try:
                nav = getattr(p, motor).launch()
            except Exception as e:  # motor no instalado: queda NO MEDIDO, no verde
                res["motores"][motor] = {"no_medido": [x for x in (y.strip(" ║╔╗╚╝═").strip() for y in str(e).splitlines()) if x][:14]}
                continue
            fila = {"version": nav.version, "escenarios": {}}
            for clave in claves:
                nombre = "E_headers_copiados_del_vivo" if clave == "E" else SALTOS[clave][0]
                try:
                    fila["escenarios"][nombre] = escenario(nav, base, clave)
                except Exception as e:
                    fila["escenarios"][nombre] = {"error": str(e).strip().splitlines()[0][:300]}
            nav.close()
            res["motores"][motor] = fila
    srv.shutdown()
    res["fin_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    resumen = {}
    for motor, fila in res["motores"].items():
        if "escenarios" not in fila:
            resumen[motor] = fila
            continue
        resumen[motor + " " + fila["version"]] = {
            n: "error" if "error" in e else " ".join([
                e["1_visita_cuando_estaba_v5"]["v"],
                e["2_control_inicio_con_v8_publicada"]["v"],
                e["3_toca_link_legal_tech_bolivia"]["v"],
                e["4_inicio_despues"]["v"],
            ])
            for n, e in fila["escenarios"].items()
        }
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "repro.json", sys.argv[2] if len(sys.argv) > 2 else None)
