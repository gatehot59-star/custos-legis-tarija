"""e2e_cache_vivo.py: la prueba sobre el SUJETO EXACTO, el sitio en vivo.

1. Envenena la cache de un Chromium con una "v5" falsa para https://astra.icca-engine.com/
   (servidor local con certificado propio, aceptado por SPKI; Last-Modified 18-oct y sin
   Cache-Control, igual que salio la v5 real).
2. Reabre el MISMO perfil con la red REAL (Cloudflare, tunel, nginx de la VM) y recorre lo
   que hace el usuario: portada, el destino del link viejo y el link nuevo.

Puede dar ROJO: si la cache no se envenena, el control muestra la v8 real; si el arreglo
no funciona en vivo, el link nuevo o la portada siguen mostrando la v5 falsa.

Uso: python3 e2e_cache_vivo.py
"""
import base64
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

D = "/workspace/astra-sitio/qa-v9"
HOST = "astra.icca-engine.com"
LM_V5 = "Sun, 18 Oct 2026 02:58:00 GMT"
FALSA = (
    b"<!doctype html><html><head><meta charset='utf-8'>"
    b"<meta name='astra-version' content='v5-falsa'><title>v5-falsa</title></head>"
    b"<body><h1 id='v'>v5-falsa</h1></body></html>"
)
REG = []
CLAVES = ("location", "clear-site-data", "cache-control")
LEER = (
    "() => ({v: (document.querySelector('meta[name=\"astra-version\"]') || {}).content || null,"
    " h1: (document.querySelector('h1') || {}).innerText || null, url: location.href})"
)


def certificado(tmp):
    """Certificado descartable para el servidor falso y su huella SPKI en base64."""
    key, crt = os.path.join(tmp, "k.pem"), os.path.join(tmp, "c.pem")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
                    "-nodes", "-keyout", key, "-out", crt, "-days", "2", "-subj", "/CN=" + HOST,
                    "-addext", "subjectAltName=DNS:" + HOST], check=True, capture_output=True)
    pub = subprocess.run(["openssl", "x509", "-in", crt, "-pubkey", "-noout"],
                         check=True, capture_output=True).stdout
    der = subprocess.run(["openssl", "pkey", "-pubin", "-outform", "der"], input=pub,
                         check=True, capture_output=True).stdout
    return key, crt, base64.b64encode(hashlib.sha256(der).digest()).decode()


class Falso(BaseHTTPRequestHandler):
    """Sirve la v5 falsa como salia la v5 real: sin Cache-Control."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        return

    def do_GET(self):
        REG.append({"t": round(time.time(), 3), "path": self.path})
        if self.path.split("?")[0] == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Last-Modified", LM_V5)
            self.send_header("ETag", '"v5-falsa"')
            self.send_header("Content-Length", str(len(FALSA)))
            self.end_headers()
            self.wfile.write(FALSA)
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


def abrir(ctx, url, espera=600):
    pg = ctx.new_page()
    r = pg.goto(url, wait_until="load")
    pg.wait_for_timeout(espera)
    dato = pg.evaluate(LEER)
    dato["status"] = r.status if r else None
    previo = r.request.redirected_from if r else None
    if previo is not None and previo.response() is not None:
        dato["salto"] = {"status": previo.response().status,
                         "headers": {k: v for k, v in previo.response().all_headers().items() if k in CLAVES}}
    pg.close()
    return dato


def main():
    tmp = tempfile.mkdtemp(prefix="e2e-", dir=D)
    res = {"inicio_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        key, crt, spki = certificado(tmp)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(crt, key)
        srv.socket = tls.wrap_socket(srv.socket, server_side=True)
        puerto = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        perfil = os.path.join(tmp, "perfil")
        with sync_playwright() as p:
            falsa = [f"--host-resolver-rules=MAP {HOST} 127.0.0.1:{puerto}",
                     f"--ignore-certificate-errors-spki-list={spki}"]
            c1 = p.chromium.launch_persistent_context(perfil, args=falsa)
            res["chromium"] = c1.browser.version if c1.browser else None
            res["1_envenenar_con_v5_falsa"] = abrir(c1, f"https://{HOST}/")
            c1.close()
            n_falso = len(REG)
            c2 = p.chromium.launch_persistent_context(perfil)
            res["2_control_portada_red_real"] = abrir(c2, f"https://{HOST}/")
            res["3_destino_del_link_viejo"] = abrir(c2, f"https://{HOST}/#/legal-tech-bolivia")
            res["4_link_nuevo_legal_tech_bolivia"] = abrir(c2, f"https://{HOST}/legal-tech-bolivia", 1200)
            res["5_portada_despues"] = abrir(c2, f"https://{HOST}/", 1200)
            c2.close()
        srv.shutdown()
        res["pedidos_al_servidor_falso"] = REG
        res["pedidos_al_falso_con_red_real"] = REG[n_falso:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    res["fin_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(D, "e2e_vivo.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
