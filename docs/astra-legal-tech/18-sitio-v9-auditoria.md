# 18 · Auditoría TITAN FULL del sitio y v9 publicada

Lunes 26-oct-2026. La v9 se publicó a las 17:11 ART y el arreglo de accesibilidad (v9b) a las 17:48 ART, en https://astra.icca-engine.com/.

## Pedido

> «AUDITA L APAGINA WEB ESTA SOBRECARGADA, NO PARECE PROFESIONAL Y CADA BOTON DEBE SER UNA VENTNA DESPLEGABLE NO IRESE ABAJO CUNADO UNO HACE CLICK EL LOGEO DBE TENER LA OPCION DE LOGEARSE CON CUENTA DE GOOGLE. SOLO DEBEN APARECER LOS PAISES DEL MERCOSUR APLICA TITAN FULL Y LUEGO MEJORA» (Abraham, 26-oct 14:14 ART)

| Pedido | Estado |
|---|---|
| Auditoría | HECHO, medida contra el sitio real |
| Cada botón abre una ventana desplegable | HECHO y publicado: 0 px de salto en los 9 botones de la barra |
| Sólo países del MERCOSUR | HECHO y publicado: 5 Estados Partes; `/legal-tech-chile` responde 404 |
| Ingreso con cuenta de Google | NO HECHO: falta el cliente OAuth en Google Cloud (lo crea Abraham) y el código en la cuenta |
| Mejora publicada | HECHO |

Nota honesta: la publicación de las 17:11 la hizo un turno de BRAIN que se cortó antes de avisar. Este turno la encontró midiendo (sha256 del index en la VM y en la respuesta pública), no la supuso.

## v8 contra v9, mismo instrumento y mismo sitio

Instrumento: `qa-v9/auditoria_sitio.py` en brain-env (Chromium 153 con Playwright, 1280×800 y 390×844, después de recorrer la página) y Lighthouse 13.5.0. v8 medida el 26-oct de 17:18 a 17:23 UTC; v9b, de 20:48 a 20:50 UTC.

| Medida | v8 | v9 publicada |
|---|---|---|
| Alto en escritorio | 13 pantallas (10.381 px) | 3,3 pantallas (2.600 px) |
| Alto en celular | 21,6 pantallas (18.191 px) | 5,6 pantallas (4.713 px) |
| Palabras | 1.382 | 407 |
| Secciones / títulos h2 | 13 / 17 | 4 / 7 |
| Nodos del DOM | 1.113 | 345 |
| Tamaños de letra | 21 | 13 |
| Colores de texto / de fondo | 17 / 13 | 12 / 8 |
| Salto al tocar Productos, Servicios, Países, Planes | 836 a 5.945 px | 0 px, y abre su ventana |
| Peso transferido | 263 KB, 0 terceros | 266 KB, 0 terceros |
| Lighthouse escritorio (rendimiento, accesibilidad, prácticas, SEO) | 98, 100, 100, 66 | 99, 100, 100, 66 |
| Lighthouse celular | 72, 100, 100, 66 | 86, 100, 100, 66 |

Comparadores medidos con el mismo script: Pixi Legal 5,9 y 9 pantallas; ETHIX 8,9 y 12,4; LegalHub 12,7 y 20,1. El SEO 66 es sólo por el noindex, que es deliberado.

## Qué cambió

- Barra de una fila: marca, Productos, Servicios, Países, Planes, Empresa, Corpus Tarija (Piloto), Ingresar y Crear cuenta.
- Cada botón abre su ventana debajo de la barra, con la página quieta en penumbra. Escape, clic afuera o un segundo clic la cierran.
- En pantallas de menos de 1100 px, un botón Menú abre una hoja completa con las mismas ventanas como acordeón.
- Portada en cuatro bloques: noche con la foja cotejada, tres formas de trabajar, cinco Estados Partes y cierre.
- Países: Argentina, Brasil, Paraguay, Uruguay y Bolivia (mercosur.int, leído el 26-oct). Venezuela está suspendida. Chile, Colombia, México y Perú salen del sitio y de nginx.
- Las anclas viejas (`#productos`, `#planes`, `#mercosur` y demás) abren su ventana en vez de bajar.
- No se borró contenido: lo que estaba en la portada vive en las ventanas.

## PASS, FAIL y NO MEDIDO

`afirmación → instrumento → ¿podía dar rojo? → veredicto`

- La portada ya no está sobrecargada → alto medido en el sitio real → sí, la v8 dio 13 y 21,6 → **PASS**.
- Los botones no bajan la página → scroll antes y después de cada uno de los 9 botones de la barra, con una carga nueva por botón → sí, la v8 saltaba de 836 a 5.945 px → **PASS: 0 px**. Los 5 del menú abren su ventana.
- Sólo el MERCOSUR → `/legal-tech-chile` responde 404 y `/legal-tech-bolivia` 302 → sí → **PASS**. En la portada de la vista previa, 0 menciones de Chile, Colombia, México, Perú, Venezuela y Ecuador.
- Sin desborde en el celular → ancho del documento igual al de la pantalla a 390 y a 360 px → sí → **PASS**.
- Botón Menú accesible → Lighthouse lo marcó sin nombre en la v9 (accesibilidad celular 95) → sí, dio rojo → arreglado en la v9b, **PASS: 100**. Prueba local por rol antes de subir: 1 botón llamado Menú, abre el menú, 0 errores de la página.
- La build es reproducible → la build de la fuente de brain-env contiene exactamente el JS y el CSS del index publicado → podía dar 0 → **PASS** (1 y 1).
- Paridad entre la vista previa y la producción → sha256 de los 7 archivos cambiados y de Cabecera.jsx de la v9b → **PASS: iguales**.
- Rendimiento en el celular → dos corridas de Lighthouse sobre la v9 dieron 70 y 86 → la variación entre corridas supera la diferencia con la v8 (72) → **NO CONCLUYENTE**.
- El menú del celular con el script de auditoría → el script busca botones por su texto y el de Menú no tiene texto visible a 390 px → **NO MEDIDO** por ese instrumento. Sí lo mide la prueba local por rol.
- Firefox y Safari (WebKit) → **NO MEDIDO**: no corren en brain-env por librerías del sistema que faltan.
- Los botones ES y PT de la foja anuncian "Español" y "Português" en vez de su texto visible (Lighthouse, peso 0, viene de la v7) → **FAIL menor**, pendiente.

## Rúbrica (TITAN QA)

| Criterio | Puntaje | Evidencia |
|---|---|---|
| Completitud | 6 | Falta el ingreso con Google, uno de los cinco pedidos |
| Ejecutabilidad | 9 | La build reproduce el index publicado; 0 errores de página |
| Seguridad | N/A | El sitio no pide datos; la cuenta no se tocó |
| Testing | 7 | Auditoría y Lighthouse contra el sitio real; sin suite automatizada del sitio |
| Innovación | 8 | Anclas viejas que abren su ventana; build verificada contra lo publicado |
| Documentación | 8 | Este doc, la bitácora de cambios en App.jsx y el Doc de ClickUp |
| Arquitectura | 8 | Paneles en un módulo propio, la misma pieza para la barra y el menú del celular |
| DevOps | N/A | Sitio estático en nginx, con respaldo y forma de deshacer |
| Entrega en repo | 0 | El código del sitio vive en el artifact (versión 10) y en brain-env; el de la cuenta, en brain-env y la VM. Ninguno está en este repo |

Sin total: con el código fuera del repo, la rúbrica no se firma.

## Pendiente

1. Ingreso con Google:
   - Diseño cerrado: flujo OAuth del lado del servidor con state, PKCE S256 y nonce.
   - Las cuentas nuevas eligen un país del MERCOSUR y aceptan la privacidad.
   - El botón aparece sólo cuando está configurado.
   - Una sesión de Google no entra a gestión.
   - Abraham crea el cliente OAuth en Google Cloud con la dirección de vuelta `https://astra.icca-engine.com/cuenta/google/vuelta/`.
2. Registro de la cuenta: sacar "Otro país" de los formularios.
3. Nombre de los botones ES y PT de la foja.
4. Subir a un repo el código del sitio y el de la cuenta.

## Cómo deshacer

- Portada sin el arreglo: `sudo cp -p /var/backups/astra/index.html.v9-20261026T204805Z /var/www/astra/index.html`.
- Volver a la v8: `sudo cp -p /var/backups/astra/index.html.v8-20261026T201102Z /var/www/astra/index.html`.
- nginx con 9 países: `sudo cp -p /var/backups/astra/astra-icca-engine.conf.20261026T201102Z /etc/nginx/conf.d/astra-icca-engine.conf`, después `sudo nginx -t` y `sudo systemctl reload nginx`.

Huellas: index v9 `409d7ea9c6c39f8a`, index v9b en vivo `59ab1a1333a7369b` (326.455 B), nginx con 5 países `6b02ae5d2bcc82c8`.

## Método

- Agente: BRAIN. Herramientas: sandbox de ClickUp (artifact y capturas propias), brain-env (build con esbuild, Playwright, Lighthouse y SSH a la VM) y GitHub MCP para este archivo.
- Acción delicada: publicar en producción. Cada paso tuvo respaldo previo y una prueba local antes de subir.
- W-01: BRAIN mide su propio trabajo. Lighthouse es un instrumento externo, pero la re-auditoría humana o de otro auditor sigue pendiente.
