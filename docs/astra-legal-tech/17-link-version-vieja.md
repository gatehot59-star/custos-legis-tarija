# 17 · El link por país llevaba a una versión vieja: la portada guardada en el navegador

26-oct-2026. Pedido de Abraham, 08:22 ART: «NO AGREGUES ESOS PAISES. PERO EL LINK QUE ME PASASTE ME LLEVA A UNA VERSION VIEJA». Arreglo publicado a las 08:31 ART (11:31:38 UTC). Doc de ClickUp: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-27897

## Veredicto

El servidor no estaba viejo: el navegador sí. Había guardado la portada de la v5 como fresca y el link de país la reusaba sin preguntar. Desde las 08:31 ART el salto de los 9 links de país borra esa copia (`Clear-Site-Data: "cache"`) y pide una dirección distinta (`?pais=`), así que no puede volver a caer en ella. Medido en Chromium 153 contra el sitio real, con una caché envenenada a propósito. Firefox y Safari: NO MEDIDO.

## Qué pasaba (medido el 26-oct a las 11:28 UTC desde brain-env, a través de Cloudflare)

- `/` da 200, 315.254 B, sha256 `3c9e30db727a8b3d…`, meta astra-version `v8 · 26-10-2026`, `Cache-Control: no-cache, no-transform` y cf-cache-status DYNAMIC. El servidor ya daba la v8; `/?v=8` e `/index.html` dan el mismo sha.
- `/legal-tech-bolivia` daba 302 a `/#/legal-tech-bolivia`, sin Cache-Control. Lo que va después del `#` no viaja al servidor: el navegador pide `/`.
- Hasta la v6 el HTML salía sin Cache-Control. La v5 tenía Last-Modified 18-oct 02:58 UTC; el navegador la da por fresca el 10 % de su edad (unas 19 a 20 h desde la visita) y en ese plazo la muestra sin consultar. El `no-cache` que entró con la v7 sólo sirve para copias guardadas después: a la que ya estaba fresca el navegador nunca la vuelve a pedir.
- La dirección vieja `https://150448fcc6.abacusai.cloud/astra/` da 301 a `https://astra.icca-engine.com/`.

## Arreglo (nginx de la VM)

`/etc/nginx/conf.d/astra-icca-engine.conf`: sha256 `3e780732e98f1b87…` (v8, 2.734 B) pasó a `13e19accd8225d5e…` (v9, 3.378 B). `nginx -t` OK y reload OK; nginx, astra-cuenta y cloudflared-corpus activos después. Respaldo: `/var/backups/astra/astra-icca-engine.conf.20261026T113138Z`. Copia completa: `evidencia-17/astra-icca-engine.conf`.

- Los 9 links `/legal-tech-<país>` (con o sin barra final) responden 302 a `/?pais=<país>#/legal-tech-<país>` con `Clear-Site-Data: "cache"` y `Cache-Control: no-store`.
- `Clear-Site-Data: "cache"` hace que el navegador borre la caché del sitio antes de seguir el salto: la portada vieja desaparece también para `/`.
- `?pais=` cambia la dirección pedida: aunque un navegador ignore Clear-Site-Data, el link no puede usar la copia vieja de `/`. La app lee la ruta del `#` (`leerHash` en App.jsx) y sus enlaces internos usan `pathname + search + hash`, así que el `?pais=` no cambia nada de lo que se ve.
- No borra cookies ni datos: la sesión de la cuenta sigue.
- Sin cambios: portada (mismo sha), cuenta, Corpus, tipografías y 404. Los headers de seguridad también salen en el 302 (`evidencia-17/vivo_302.json`).

Deshacer:

```sh
sudo cp -a /var/backups/astra/astra-icca-engine.conf.20261026T113138Z /etc/nginx/conf.d/astra-icca-engine.conf
sudo nginx -t && sudo systemctl reload nginx
```

```diff
--- v8
+++ v9
@@ -13,6 +13,14 @@
     /index.html   "no-cache, no-transform";
     /404.html     "no-cache, no-transform";
     ~^/cuenta/    "no-transform";
+    "~^/legal-tech-(?:argentina|bolivia|brasil|chile|colombia|mexico|paraguay|peru|uruguay)/?$" "no-store";
+}
+
+# Paginas por pais: el salto borra la copia vieja que el navegador guardo de versiones anteriores.
+# Hasta la v6 el HTML salia sin Cache-Control y el navegador lo daba por fresco unas 20 h sin preguntar.
+map $uri $astra_limpiar {
+    default "";
+    "~^/legal-tech-(?:argentina|bolivia|brasil|chile|colombia|mexico|paraguay|peru|uruguay)/?$" '"cache"';
 }
 
 server {
@@ -29,6 +37,7 @@
     add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
     add_header Referrer-Policy strict-origin-when-cross-origin always;
     add_header Cache-Control $astra_cache always;
+    add_header Clear-Site-Data $astra_limpiar always;
 
     # Quien entre por http va a https (Cloudflare informa el esquema original).
     if ($http_x_forwarded_proto = "http") { return 301 https://$host$request_uri; }
@@ -59,7 +68,8 @@
     location ^~ /fuentes/ { expires 365d; try_files $uri =404; }
 
     # Paginas por pais: la direccion limpia lleva a la ruta del sitio (#/legal-tech-<pais>).
-    location ~ "^/legal-tech-(argentina|bolivia|brasil|chile|colombia|mexico|paraguay|peru|uruguay)/?$" { return 302 /#/legal-tech-$1; }
+    # El ?pais= cambia la direccion pedida: aun sin Clear-Site-Data el navegador no puede usar su copia vieja de /.
+    location ~ "^/legal-tech-(argentina|bolivia|brasil|chile|colombia|mexico|paraguay|peru|uruguay)/?$" { return 302 "/?pais=$1#/legal-tech-$1"; }
 
     location = / { try_files /index.html =404; }
     location / { try_files $uri =404; }
```

## Países

- «No agregues esos países»: el registro sigue con AR, BO, BR, PY, UY y Otro (medido en vivo en `/cuenta/registro/` a las 11:28 UTC). No se agregó Chile, Colombia, México ni Perú.
- El sitio sigue con las 9 páginas de país de la v8 (pedido del 26-oct 02:11 ART: modelo LegalHub más Bolivia). Si «esos países» también era para el sitio, falta la confirmación de Abraham: no se tocó.

## Afirmación, instrumento, ¿podía dar rojo?, veredicto

| Afirmación | Instrumento | ¿Podía dar rojo? | Veredicto |
|---|---|---|---|
| El servidor ya sirve la v8 | GET de `/`, `/?v=8` e `/index.html` por Cloudflare: sha256 y meta | sí (sha o meta viejos) | PASS |
| Lo viejo sale de la caché del navegador | `e2e_cache_vivo.py` pasos 2 y 3 (perfil envenenado, red real) y `repro_cache.py` escenario A | sí: si la caché no se envenena, el control muestra la v8 | medido: el control y el destino del link viejo muestran la v5 falsa; con la red real no le llegó ningún pedido al servidor falso |
| El link nuevo deja en la v8 aunque haya copia vieja | `e2e_cache_vivo.py` paso 4 | sí (podía mostrar la v5 falsa) | PASS: v8, «Legal Tech y Legal Operations en Bolivia.» |
| La portada también queda limpia | `e2e_cache_vivo.py` paso 5 | sí | PASS: v8, «Inteligencia jurídica que rinde cuentas.» |
| Hace falta Clear-Site-Data; el `?pais=` solo no alcanza | `repro_cache.py` escenario D | sí | medido: con sólo `?pais=` el link da v8 pero la portada sigue en v5 |
| Clear-Site-Data llega al navegador a través de Cloudflare | `all_headers()` del 302 en Chromium (`e2e_vivo.json`) | sí (Cloudflare podía sacarlo) | PASS |
| Los 9 links llevan el header y lo demás no | GET de los 9, con barra final, `/legal-tech-narnia`, `/`, `/?pais=bolivia`, `/404.html` y `/cuenta/salud/` | sí | PASS: 9/9; narnia da 404 y el resto sale sin el header |
| Ingresar y Crear cuenta visibles, sin desborde, sin terceros ni errores | `qa_vivo_v9.py` a 1280 y 390 px (`vivo.json`) | sí | PASS: los dos con texto; ancho 1280/1280 y 390/390; 0 pedidos a terceros; 0 errores |
| Lo mismo en Firefox y Safari | `repro_cache.py` con firefox y webkit | no corrieron | NO MEDIDO |

Escenarios de `repro_cache.py` (servidor local que imita los headers medidos; cada celda es lo que muestra la pestaña en los pasos 1 a 4: visita con la v5 publicada, portada con la v8 publicada, toca el link, portada después):

| Escenario | Salto 302 | Pasos 1 a 4 |
|---|---|---|
| A, como estaba | `/#/legal-tech-bolivia` | v5 v5 v5 v5 |
| B | Clear-Site-Data | v5 v5 v8 v8 |
| C | Clear-Site-Data y `?pais=` | v5 v5 v8 v8 |
| D | sólo `?pais=` | v5 v5 v8 v5 |
| E | los headers exactos del vivo | v5 v5 v8 v8 |

## Evidencia cruda (`evidencia-17/`)

| Archivo | Bytes | sha256 |
|---|---|---|
| `repro_cache.py` | 8.129 | `c2b22bf6f904fe47354fbdc60704e6689902f0c6ce09c4f5a448cbadba8e2802` |
| `repro.json` | 6.914 | `4758d1f6193655fc976c4e5faf53d6e0b0ddfdf668f2dfd79456cc505814d59a` |
| `e2e_cache_vivo.py` | 5.636 | `80aa0d3b1c6ed2a87085a865aef4c20e95400e3fcdf8becc2fe370861d5c3cbf` |
| `e2e_vivo.json` | 1.209 | `493266ca235609d8bfd0000417f3aa749133e4290fa76925672bf01174505733` |
| `qa_vivo_v9.py` | 3.496 | `c9b06937c8ba71652dc59f67699444431216d9a359abe18f99a933db63bcd64a` |
| `vivo.json` | 1.543 | `8d194b8f472c8ed1b84d0e2a7f15b80f26661c6ec6f7e847901a2578ea80f6ce` |
| `vivo_302.json` | 349 | `7e214e51661019b402aba1e3f7a397fb80933d51c89d6c1dcf1c9c2efe653afe` |
| `astra-icca-engine.conf` | 3.378 | `13e19accd8225d5e02868513be816dff0bad3a1fa5d4f58295ab94b2b6ba1024` |

Corridas en brain-env (contenedor en UTC), con Playwright 1.63.0 y Chromium 153.0.8010.12:

- `python3 repro_cache.py repro.json vivo_302.json`: exit 0, de 11:39:17 a 11:39:23 UTC.
- `python3 e2e_cache_vivo.py`: exit 0, de 11:36:01 a 11:36:12 UTC. El certificado y el perfil descartables se borran al terminar.
- `python3 qa_vivo_v9.py`: exit 0, entre 11:31:38 y 11:36:01 UTC (su salida no guarda la hora).

Nota de lectura: en `vivo.json` el 302 no muestra `clear-site-data` porque `qa_vivo_v9.py` lee `response.headers`, que en Chromium no lo trae. `e2e_vivo.json` lee `all_headers()` y sí lo muestra.

Salida cruda de los GET antes del arreglo (11:28:56 a 11:29:00 UTC):

```text
https://astra.icca-engine.com/legal-tech-bolivia  302  505 B  location /#/legal-tech-bolivia  cf-cache-status DYNAMIC  (sin cache-control)
https://astra.icca-engine.com/                    200  315254 B  sha 3c9e30db727a8b3d  cache-control no-cache, no-transform  last-modified Mon, 26 Oct 2026 05:30:21 GMT  etag W/"6adee56d-4cf76"  astra-version v8 · 26-10-2026
https://astra.icca-engine.com/?v=8                200  315254 B  sha 3c9e30db727a8b3d  (igual)
https://astra.icca-engine.com/index.html          200  315254 B  sha 3c9e30db727a8b3d  (igual)
https://150448fcc6.abacusai.cloud/astra/          301  location https://astra.icca-engine.com/
https://150448fcc6.abacusai.cloud/astra           301  location https://astra.icca-engine.com/
registro 200 [b'', b'AR', b'BO', b'BR', b'PY', b'UY', b'OT']
```

Salida cruda de los GET después del arreglo (11:31 UTC):

```text
('argentina', 302, '/?pais=argentina#/legal-tech-argentina', '"cache"', 'no-store')
('bolivia', 302, '/?pais=bolivia#/legal-tech-bolivia', '"cache"', 'no-store')
('brasil', 302, '/?pais=brasil#/legal-tech-brasil', '"cache"', 'no-store')
('chile', 302, '/?pais=chile#/legal-tech-chile', '"cache"', 'no-store')
('colombia', 302, '/?pais=colombia#/legal-tech-colombia', '"cache"', 'no-store')
('mexico', 302, '/?pais=mexico#/legal-tech-mexico', '"cache"', 'no-store')
('paraguay', 302, '/?pais=paraguay#/legal-tech-paraguay', '"cache"', 'no-store')
('peru', 302, '/?pais=peru#/legal-tech-peru', '"cache"', 'no-store')
('uruguay', 302, '/?pais=uruguay#/legal-tech-uruguay', '"cache"', 'no-store')
con barra 302 /?pais=bolivia#/legal-tech-bolivia "cache"
/ 200 315254 3c9e30db727a8b3d {'cache-control': 'no-cache, no-transform'} v8 · 26-10-2026
/?pais=bolivia 200 315254 3c9e30db727a8b3d {'cache-control': 'no-cache, no-transform'} v8 · 26-10-2026
/legal-tech-narnia 404 2560 400526f50e510d24 {'cache-control': 'no-cache, no-transform'}
/cuenta/salud/ 200 56 881cd5b77c4de9d3 {'cache-control': 'no-store'}
/fuentes/fuentes-web.css 404 2560 400526f50e510d24 {'cache-control': 'max-age=14400, no-transform'}
/404.html 200 2560 400526f50e510d24 {'cache-control': 'no-cache, no-transform'}
corpus login 200 7309
```

## NO MEDIDO

- Firefox, Safari y el navegador interno de la app de ClickUp. Se descargaron Firefox 155.0 y WebKit 26.6 de Playwright (320 MB y 564 MB) y no arrancaron: a brain-env le faltan bibliotecas del sistema (Firefox: libXcursor, libgtk-3, libgdk-3, libpangocairo, libcairo-gobject y libgdk_pixbuf; WebKit: libgstreamer, libgtk-4, libvulkan, libgraphene, ICU 76, libxslt, liblcms2 y libevent, entre otras). Instalarlas pide apt en un contenedor compartido: no se hizo. Las dos descargas se borraron, por eso `repro.json` los muestra como no instalados. Por diseño el `?pais=` evita la copia vieja en el link con cualquier navegador; eso sólo está medido en Chromium.
- Qué dispositivo y navegador usó Abraham, y qué versión vieja tenía guardada.
- Otros visitantes con la portada vieja guardada: no hay instrumento. Esa copia vence sola, unas 20 h después de la última visita anterior al 26-oct 03:18 UTC.
- El alcance exacto del borrado en Chromium (sólo astra.icca-engine.com o todo icca-engine.com). Borra caché, no datos.
- Observado al pasar, sin seguir: un 404 de un `.css` bajo `/fuentes/` llegó con `max-age=14400, no-transform`, que el nginx no pone (lo agrega Cloudflare). No toca al HTML, que sigue `no-cache` y DYNAMIC.

## Rúbrica (sólo configuración: 5 criterios, 60 puntos)

- Completitud 15/15: los 9 países con el header nuevo, con y sin barra final (salida cruda de arriba); respaldo y cómo deshacer en este archivo.
- Ejecutabilidad 15/15: `nginx -t` ok y reload ok en la VM; el conf instalado tiene sha `13e19acc…`, igual al de `evidencia-17/`.
- Seguridad 14/15: los headers de seguridad salen también en el 302 (`vivo_302.json`); Clear-Site-Data sólo pide "cache", sin cookies ni almacenamiento; sin superficie nueva. Menos 1: el alcance exacto del borrado en Chromium no está medido.
- Documentación 10/10: este archivo, el Doc de ClickUp y los comentarios del propio conf.
- Proceso QA 4/5: cada afirmación con su instrumento y su ¿podía dar rojo?. Menos 1: Firefox y Safari NO MEDIDO.

Total 58/60, que da 96,7/100. N/A: Testing 15, Arquitectura 10, DevOps 10 e Innovación 5 (40 puntos), por ser una entrega de configuración.

## Método

- Agente: BRAIN. Herramientas: gateway MUDH (brain-env: Python, Playwright y SSH a la VM), GitHub MCP (este commit) y ClickUp (Doc).
- Acción delicada: no (nginx de un sitio propio, con respaldo y `nginx -t`; no toca autenticación ni datos).
- PASS: link nuevo y portada en v8 con la caché envenenada (Chromium, sitio real); 9/9 saltos con el header; registro sin cambios.
- FAIL: ninguno.
- NO MEDIDO: Firefox, Safari, el navegador de Abraham y el alcance del borrado.
- W-01: los instrumentos son Chromium y nginx, y la salida cruda está en `evidencia-17/`. Qué medir lo eligió el mismo agente: re-auditoría pendiente.
