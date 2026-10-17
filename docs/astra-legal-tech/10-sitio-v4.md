# 10 · Sitio web de Astra Legal Tech v4 (mezcla ETHIX + Pixi Legal)

Fecha: 17-oct-2026 (ART). Estado: **guardado como artifact v4; NO desplegado todavía en la VM** (la VM sigue sirviendo v3).

## Pedido (textual)

> pues nuestra web ser una mezcla entre ethix y pixi legal. pero pon datos de argentinas. y uno de los productos es coprus tarija.ponte pillo y mejora nuestra web. nivel iingeniero con 10 años de experiencias en pagimas web

## Interpretación declarada (corregible)

- De ETHIX: estilo SaaS institucional, módulo interactivo, resultados medidos, CTA de demostración, sectores.
- De Pixi Legal: héroe partido con consulta en vivo, preguntas sugeridas, cita por artículo, "cotejado contra la fuente".
- "Datos de argentinas": datos reales de Argentina con fuente + tres leyes nacionales citadas textual en la demo, rotulada "Demostración".
- Corpus Tarija: producto destacado, estado "en prueba piloto".

## Qué tiene la v4

- Consulta en vivo con dos pestañas (Tarija / Argentina): pregunta, búsqueda, respuesta, cita textual del artículo, ficha de fuente y sello "COTEJADA".
- Verificador SHA-256 en el navegador (Web Crypto): el PDF no sale del equipo; compara contra las huellas de las leyes departamentales 516, 512 y 518.
- Portafolio estilo tienda: Corpus Tarija destacado + Custos Legis, SIAO, AURA, MUDH Mobile y CashGo con estado honesto.
- Banda de datos de Argentina, método en 5 pasos, sectores, banda de inversores (invitación privada, no oferta pública), preguntas frecuentes, cierre.
- Tipografía Encode Sans (Impallari Type, Rosario), Libre Baskerville para texto legal, Source Code Pro para huellas; violeta de sello #4A2DA0.

Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=4

## Datos medidos (brain-env, 17-oct-2026 13:08–13:09 UTC)

- PDFs de tarija.gob.bo: 516 → 0ad12b49…, 512 → efb76896…, 518 → 7782d05c… (coinciden).
- argentina.gob.ar, 30/03/2026 (INDEC): economía del conocimiento USD 9.600 millones en 2025 (+8,1%, récord), 53% de las exportaciones de servicios, tercer complejo exportador, más de 285.000 puestos formales (SIPA).
- Abogados.com.ar: 126.000 abogados matriculados (FACA, 2023).
- InfoLEG: Ley 25.326 art. 1 (B.O. 02/11/2000); Ley 27.349 art. 33 (B.O. 12/04/2017); Ley 27.506 art. 1, texto actualizado (B.O. 10/06/2019).

## PASS

- Ventana de Corpus Tarija abre desde el destacado y muestra "En prueba piloto"; Escape la cierra y el foco vuelve al botón.
- Verificador con archivo "abc": "No coincide" y huella ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad (la esperada).
- Rama "coincide": probada con digest simulado (sólo valida la interfaz, no el cálculo).
- 390 y 360 px: scrollWidth igual al ancho; cabecera entra a 360 ("Pedir demo"); placeholder corto en pantallas angostas; texto táctil en el verificador.

## FAIL encontrados y corregidos

- El texto "Consultar" se desbordaba del botón circular en celular: una regla al final del CSS pisaba la del media query.
- El CTA de la cabecera quedaba cortado 5 px a 360.
- El título de la Ley 512 se truncaba con puntos suspensivos.
- "Es el PDF oficial" pasó a "Es idéntico al PDF oficial" (es lo que prueba la huella).

## NO MEDIDO

- Despliegue v4 en la VM (/astra/ sigue con v3, 210.701 B, sha256 6e9c458d…).
- Verificador con el PDF real dentro del navegador.
- Celular real de Abraham y Safari.

## Pendiente

1. Escribir las fuentes v4 en brain-env (/workspace/astra-sitio/fuente/src), borrar Cielo.jsx y Constelacion.jsx, verificar sha256 contra el artifact.
2. Build con el mismo pipeline (lang es, OG, noindex, favicon), backup de /var/www/astra/index.html, copiar, verificar sha256, chequear /astra/ 200, /corpus/login/ 200 y / 401.
3. Fila 10 en el README de esta carpeta y actualizar el Doc del sitio.
