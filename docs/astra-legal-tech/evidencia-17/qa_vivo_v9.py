"""qa_vivo_v9.py: abre el link real /legal-tech-bolivia en Chromium (escritorio y celular).

Mide el sujeto exacto: la cadena de saltos que devuelve el sitio en vivo, la version
que termina mostrando, si se ven Ingresar y Crear cuenta, desbordes, pedidos a
terceros y errores de consola. Contexto nuevo, sin cache previa: el caso de la
cache envenenada lo cubre repro_cache.py.

Uso: python3 qa_vivo_v9.py
"""
import json

from playwright.sync_api import sync_playwright

URL = "https://astra.icca-engine.com/legal-tech-bolivia"
SALIDA = "/workspace/astra-sitio/qa-v9/vivo.json"
CLAVES = ("location", "clear-site-data", "cache-control")
LEER = """() => {
  const meta = document.querySelector('meta[name="astra-version"]');
  const h1 = document.querySelector('h1');
  const txt = document.body.innerText;
  const vis = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const ok = r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
    return ok ? (el.innerText || el.textContent).trim() : 'oculto';
  };
  const pie = (txt.match(/Sitio v\\d+[^\\n]*/) || [null])[0];
  return {url: location.href, version_meta: meta && meta.content, h1: h1 && h1.innerText.trim(),
          pie: pie, ingresar: vis('.cab-ingresar'), crear_cuenta: vis('.cab-cta'),
          ancho_doc: document.documentElement.scrollWidth, ancho_vp: innerWidth};
}"""


def main():
    res = {}
    with sync_playwright() as p:
        nav = p.chromium.launch()
        res["chromium"] = nav.version
        for nombre, vp, movil in (("escritorio", {"width": 1280, "height": 800}, False),
                                  ("celular", {"width": 390, "height": 844}, True)):
            ctx = nav.new_context(viewport=vp, is_mobile=movil, has_touch=movil)
            page = ctx.new_page()
            terceros, errores = [], []
            page.on("request", lambda r: terceros.append(r.url)
                    if r.url.startswith("http") and "://astra.icca-engine.com/" not in r.url else None)
            page.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errores.append(str(e)))
            resp = page.goto(URL, wait_until="networkidle")
            cadena, req = [], resp.request
            while req.redirected_from:
                previo = req.redirected_from
                r = previo.response()
                cadena.append({"url": previo.url, "status": r.status if r else None,
                               "headers": {k: v for k, v in (r.headers.items() if r else []) if k in CLAVES}})
                req = previo
            page.wait_for_timeout(800)
            info = page.evaluate(LEER)
            page.screenshot(path=f"/workspace/astra-sitio/qa-v9/vivo-{nombre}.png")
            res[nombre] = {
                "status_final": resp.status,
                "headers_final": {k: v for k, v in resp.headers.items() if k in CLAVES + ("cf-cache-status",)},
                "cadena_redirect": cadena,
                "info": info,
                "pedidos_a_terceros": terceros,
                "errores_consola": errores,
            }
            ctx.close()
        nav.close()
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
