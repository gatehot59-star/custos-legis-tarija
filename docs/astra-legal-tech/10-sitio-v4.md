# 10 · Sitio web de Astra Legal Tech v4 (mezcla ETHIX + Pixi Legal)

Fecha: 17-oct-2026 (ART). Estado: **publicado en la VM** el 17-oct-2026 a las 14:39 UTC (11:39 ART), en https://150448fcc6.abacusai.cloud/astra/ (vista previa, noindex).

Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=4 · Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-26557

## Pedido (textual)

> pues nuestra web ser una mezcla entre ethix y pixi legal. pero pon datos de argentinas. y uno de los productos es coprus tarija.ponte pillo y mejora nuestra web. nivel iingeniero con 10 años de experiencias en pagimas web

Y después: "dame el link" (17-oct, 11:27 ART).

## Interpretación declarada (corregible)

- De ETHIX: estilo de empresa de software institucional, módulo interactivo, resultados medidos, CTA de demostración, sectores.
- De Pixi Legal: héroe partido con consulta en vivo, preguntas sugeridas, cita por artículo, "cotejado contra la fuente".
- "Datos de argentinas": datos reales de Argentina con fuente + tres leyes nacionales citadas textual en la demo, rotulada "Demostración".
- Corpus Tarija: producto destacado, estado "en prueba piloto".

## Qué tiene la v4

- Consulta en vivo con dos pestañas (Tarija / Argentina): pregunta, búsqueda, respuesta, cita textual del artículo, ficha de fuente y sello "COTEJADA".
- Verificador SHA-256 en el navegador (Web Crypto): el PDF no sale del equipo; compara contra las huellas de las leyes departamentales 516, 512 y 518.
- Portafolio estilo tienda: Corpus Tarija destacado + Custos Legis, SIAO, AURA, MUDH Mobile y CashGo con estado honesto.
- Banda de datos de Argentina, método en 5 pasos, sectores, banda de inversores (invitación privada, no oferta pública), preguntas frecuentes, cierre.
- Tipografía Encode Sans (Impallari Type, Rosario), Libre Baskerville para texto legal, Source Code Pro para huellas; violeta de sello #4A2DA0.

## Datos medidos (brain-env, 17-oct-2026 13:08–13:09 UTC)

- PDFs de tarija.gob.bo: 516 → 0ad12b49…, 512 → efb76896…, 518 → 7782d05c… (coinciden).
- argentina.gob.ar, 30/03/2026 (INDEC): economía del conocimiento USD 9.600 millones en 2025 (+8,1%, récord), 53% de las exportaciones de servicios, tercer complejo exportador, más de 285.000 puestos formales (SIPA).
- Abogados.com.ar: 126.000 abogados matriculados (FACA, 2023).
- InfoLEG: Ley 25.326 art. 1 (B.O. 02/11/2000); Ley 27.349 art. 33 (B.O. 12/04/2017); Ley 27.506 art. 1, texto actualizado (B.O. 10/06/2019).

## Publicación en la VM (17-oct-2026, 14:39 UTC)

1. Fuentes en brain-env (`/workspace/astra-sitio/fuente/src`): Contenidos.jsx, productos.js y Foja.jsx por reaplicación exacta de los cambios sobre la v3; las otras 10 copiadas; Cielo.jsx y Constelacion.jsx borrados. Respaldo de las fuentes v3 en `fuente/src-v3` y del index v3 en `public/index-v3.html`. Resultado: **16 de 16 archivos con la misma SHA-256 que el artifact v4** (site.css dio rojo hasta copiarla).
2. Build: esbuild 0.27.2 (`--bundle --minify --format=iife --jsx=automatic`), preflight de Tailwind de la v3 y el mismo molde de index (lang es, noindex, OG, favicon del asterisco ahora #4A2DA0, theme-color #F7F6FB, título y descripción nuevos). Index: 246.486 bytes, SHA-256 `458344207faa48959ffcff903a8c558ad6ab680d1318b1285aae1d8fc02b5630`.
3. VM: la v3 publicada tenía `6e9c458db6a73290de086d25b461b074dd37021534cfa016430fc5dca1f3b60b`; respaldada en `/var/backups/astra/index.html.v3-20261017T143926Z` (fuera de la carpeta pública). `/var/www/astra/index.html` queda root:root 644, 246.486 bytes, con la SHA-256 del build.
4. Chequeo público: `/astra/` 200 con bytes idénticos al build (también `?v=4`); `/astra` 301 a `/astra/`; `/` 401; `/corpus/login/` 200.
5. Arranque real: jsdom 24.1.3 sobre los bytes públicos, sin errores: título y h1 nuevos, Corpus Tarija destacado, 5 fichas, pestañas Tarija (activa) y Argentina, primera consulta "¿Qué crea la Ley Departamental 516?", 4 cifras, "USD 9.600 millones", 6 preguntas y el pie.

Volver a la v3: en la VM, `sudo cp /var/backups/astra/index.html.v3-20261017T143926Z /var/www/astra/index.html`.

## PASS

- Todo lo de "Publicación en la VM".
- QA en el sandbox: ventana de Corpus Tarija abre desde el destacado y muestra "En prueba piloto"; Escape la cierra y el foco vuelve al botón.
- Verificador con archivo "abc": "No coincide" y huella ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad (la esperada).
- 390 y 360 px: scrollWidth igual al ancho; cabecera entra a 360 ("Pedir demo"); placeholder corto en pantallas angostas; texto táctil en el verificador.

## FAIL encontrados y corregidos

- El texto "Consultar" se desbordaba del botón circular en celular: una regla al final del CSS pisaba la del media query.
- El CTA de la cabecera quedaba cortado 5 px a 360.
- El título de la Ley 512 se truncaba con puntos suspensivos.
- "Es el PDF oficial" pasó a "Es idéntico al PDF oficial" (es lo que prueba la huella).
- El primer armado del index se frenó por una aserción mal planteada (contaba un `<script` que vive dentro del JS de React); se corrigió antes de subir y ese intento no publicó nada.

## NO MEDIDO

- Verificador con el PDF real dentro del navegador (la rama "coincide" sólo se probó con digest simulado).
- Celular real de Abraham y Safari.
- Dominio astralegaltech.com y buzón contacto@ (todavía no existen; los botones de correo apuntan ahí).

## Pendiente

1. Que Abraham la mire en su celular.
2. Registrar el dominio y crear el buzón antes de difundir el link.
3. Always On en Abacus antes del 23-oct, para que la VM no se apague.
