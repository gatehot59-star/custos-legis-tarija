# 11 · Sitio v5: botón Ingresar al login real de Corpus Tarija

Fecha: 17-oct-2026, 23:58 ART (18-oct 02:58 UTC). Estado: **publicado en la VM** en https://150448fcc6.abacusai.cloud/astra/.

Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=5 · Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-26597

## Pedido (textual)

> agrega login de usario tal

Y un segundo mensaje, "y", que llegó cortado.

## Lectura declarada (corregible)

Un botón **Ingresar** como el de ETHIX o Pixi Legal, que lleva al login real de Corpus Tarija (`/corpus/login/` en la misma VM). No es un formulario propio: el sitio no pide, no recibe y no guarda contraseñas. Corpus Tarija es el único producto de Astra con usuarios hoy.

## Dónde aparece

- Cabecera en escritorio (desde 1180 px), al lado de "Pedir demostración".
- Primer acceso de la fila de secciones en tableta y celular (y entre 1040 y 1179 px).
- Ficha de Corpus Tarija (tercer botón), tarjeta destacada ("¿Tenés usuario de la prueba piloto? Ingresá"), pie ("Ingresar a Corpus Tarija") y una pregunta frecuente nueva ("¿Cómo ingreso a Corpus Tarija?").
- En el mismo sitio abre en la misma pestaña; desde la vista previa de ClickUp, en una nueva (`src/acceso.js`).

## El login al que lleva (brain-env, 18-oct-2026 02:53 UTC)

- `/corpus/login/` 200, título "Corpus Tarija · Acceso", formulario Django con usuario y contraseña, enlace "Recuperar cuenta" (`/corpus/reset/`) y el aviso "Acceso por invitación: las cuentas de la prueba piloto se entregan en persona".
- No nombra a la UNO, a la universidad ni a Yacuiba.
- **A revisar (no se tocó):** el texto dice "Corpus Tarija reúne la legislación nacional y departamental" y "Gaceta de Tarija, LexiVox nacional y GENESIS del TSJ". La cobertura nacional no está medida: LexiVox aporta 15 documentos en el corte del 9-sep. Es la página del producto, no del sitio; decide Abraham.

## Publicación

1. Cambios aplicados con el mismo script en el sandbox y en brain-env: **17 de 17 fuentes con la misma SHA-256** que el artifact v5 (nuevo: `acceso.js`; cambiados: App.jsx, Contenidos.jsx, Estante.jsx, Iconos.jsx, Preguntas.jsx, data.js, site.css). Respaldo de las fuentes v4 en `fuente/src-v4` y del index v4 en `public/index-v4.html`.
2. Build esbuild con el molde de la v4. Index: 248.776 bytes, SHA-256 `0d4fc6e004b4207c1b92c61d6ce0d4656e5b138393c8e7a1e984968fb0e11773`.
3. VM: la v4 publicada (`458344207faa4895…`) quedó en `/var/backups/astra/index.html.v4-20261018T025858Z`; `/var/www/astra/index.html` queda root:root 644, 248.776 bytes, con la SHA-256 del build.
4. Chequeo público (02:58 UTC): `/astra/` 200 con bytes idénticos al build (también `?v=5`); `/astra` 301 a `/astra/`; `/` 401; `/corpus/login/` 200.
5. jsdom sobre los bytes públicos: sin errores; 5 enlaces al login ("Ingresar" en cabecera y fila, "Ingresá", "Ir al ingreso", "Ingresar a Corpus Tarija"); 0 con `target` porque es el mismo sitio; 7 preguntas.

Volver a la v4: en la VM, `sudo cp /var/backups/astra/index.html.v4-20261018T025858Z /var/www/astra/index.html`.

## PASS

- Todo lo de "Publicación".
- cdp en el sandbox: 1440 px (cabecera 1200/1200), 1180 px (1140/1140), 1040 px (1000/1000 con la fila), 390 y 360 px sin desborde; la ficha de Corpus Tarija muestra "Consultar por Corpus Tarija", "Probar la consulta" e "Ingresar".

## FAIL encontrado y corregido

- A 1040 px la cabecera con Ingresar no entraba: 1076 de 1000 px y el botón de demostración cortado. Entre 1040 y 1179 px se usa la fila de accesos de tableta, con Ingresar primero.

## NO MEDIDO

- Entrar con un usuario real de la prueba piloto (no tengo cuenta y no corresponde crear una).
- Celular real de Abraham.
