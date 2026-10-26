# 12 · Sitio v6: MERCOSUR, Corpus Tarija en su propia pestaña y cuenta de usuarios

Fecha: 25-oct-2026. Agente: BRAIN. Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-27797. Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=6

## Estado en una línea

El sitio v6 está diseñado, revisado y guardado. La VM sigue sirviendo v5 a propósito. La cuenta (registro, ingreso, base de datos y cobro) todavía no está construida.

## Pedido (Abraham, 25-oct-2026, 20:00 ART)

> YA TIENES CREDITO, LA PAGINA WEB DEBE SER SUPERIOR NO DEBE SER COPIA FIEL D EÑLA COMPETENCIA, TAMBIEN FALTA LA PARTE DE LOGEO PARA USARIOS. COBRO, LO DE CORPUS DEBE APARECER SOLO EN UNA PESTAÑA, NO DEBE ESPECIFICAR ARGENTGINA. BUSCA MODELOS SAS. QUE OPEREN EN LEGAL TECH A NIVEL MERCOSUR, ASI DEBE OPERAR LO NUESTRO. TODO LO QUE POSEE LA PAGINA DEBE QUEDAR. PERO SI PERENECE A COPRUS DEBE ESTAR A ISLADO EN SU PROPIA PESTAÑA O SUB PAGINA. DEBE TENER CONECCION DIRECTAA CORPUS TARIJA, PERO SIN OBSTACULIZAR CUANDO SE QUIERA OPERAR O MODIFICA ACTUALIZAR PAGINA O CORPUS

## Lectura declarada (corregible)

- "Modelos SAS" se leyó doble: legal tech con modelo SaaS (cuenta, planes, cobro) y su forma societaria (SAS o equivalente).
- La banda y la demo de Argentina se reemplazan por datos del MERCOSUR y por el Tratado de Asunción: prima "no debe especificar Argentina" sobre "todo debe quedar".
- Registro, ingreso y cobro viven en un servicio aparte (Cuenta Astra). El sitio sólo enlaza: no pide claves ni pagos.

## Qué cambia en el sitio

- Pestañas de carpeta: Astra Legal Tech | Corpus Tarija (En prueba piloto). Todo lo de Corpus vive sólo en `#/corpus-tarija`: consulta, medido, verificador, acceso y preguntas. Los enlaces viejos a `#corpus` llevan a la pestaña.
- Héroe propio, no copiado de nadie: la foja cotejada del Tratado de Asunción, Art. 1, en español y portugués, con su huella SHA-256 y el sello COTEJADA.
- Banda MERCOSUR con la Cruz del Sur (emblema del bloque, Decisión CMC 17/02) dibujada con asteriscos de Astra en posiciones reales J2000.
- Plataforma: "Tres módulos. Ninguno frena a los otros." Sitio, cuenta y Corpus se actualizan por separado.
- Planes sin precios inventados: el precio aparece en la cuenta, en moneda local, cuando el plan se habilita en cada país.
- Se conserva todo lo anterior: seis productos, empresa, inversores, Corpus Legis, método, sectores, preguntas, verificador y ventanas.
- Sin datos de Argentina en el sitio. Sin clientes, testimonios, premios, cifras de uso ni precios inventados. El piloto sólo como estado.

## Desacople: sitio, cuenta y Corpus

- Sitio: HTML estático en `/var/www/astra/` (nginx `location ^~ /astra/`).
- Cuenta: servicio aparte en `/astra/cuenta/` (a construir; ver abajo).
- Corpus Tarija: sigue en `/corpus/` con su propio servicio e ingreso (`/corpus/login/`).
- Un único archivo del sitio (`conexiones.js`) define adonde apuntan Crear cuenta, Ingresar, Planes, Contacto, Privacidad e Ingresar a Corpus Tarija. Si Corpus o la cuenta cambian de lugar, se toca ese archivo y nada más.

## Modelos legal tech que operan en el MERCOSUR

| Empresa | Entidad | Qué tomamos del modelo |
|---|---|---|
| RuleX | BESIMPLER S.A.S. (Bogotá) | edición por país y precio en moneda local (Pro 28.900 ARS, 890 UYU, 69.000 PYG, 119 BOB); cobro con dLocal Go |
| Thomson Reuters Legal One | Thomson Reuters | una sola cuenta para toda la suite (OnePass) |
| vLex | vLex | fuentes oficiales por jurisdicción |
| Lemontech / Webdox | SpA (Chile) | SaaS para estudios y contratos; demo para empresas |
| ZapSign | Truora S.A.S. | prueba en autoservicio para profesionales |
| Docusign | Docusign Brasil Ltda | filial local donde el mercado lo pide |

También relevados: Legale.io, Brevity (socio Colab en Paraguay), VaFirma (EidersConsulting SAS, Uruguay), Tiver.cloud y MiFirma.

Patrón común: entidad central con socios locales; edición por jurisdicción; autoservicio o prueba para profesionales y convenio o demo para instituciones; moneda local; una cuenta para todo; la trazabilidad como parte del producto. Así queda planteado Astra en el sitio.

## Vehículo, datos personales y cobro por país

- Sociedad: Argentina SAS (Ley 27.349); Uruguay SAS (Ley 19.820); Paraguay EAS (Ley 6.480/2020); Brasil SLU (Lei 13.874/2019, art. 1.052 CC); Bolivia no tiene SAS (S.R.L. o empresa unipersonal, vía SEPREC).
- Datos personales: Ley 25.326; LGPD 13.709/2018; Ley 18.331; Paraguay Ley 7.593/2025 (rige 24 meses después de su publicación del 27-nov-2025); Bolivia sin ley integral (NO VERIFICADO).
- Cobro: Mercado Pago cubre AR, BR y UY, con suscripciones; dLocal cubre los cinco; Stripe sólo Brasil entre los cinco; PayPal empresa en Bolivia y Paraguay; rieles locales Pix, QR del BCB y Bancard.

## Fuentes medidas (25-oct-2026, UTC)

- Tratado de Asunción, español: https://www.parlamentomercosur.org/innovaportal/file/15511/1/tratado_de_asuncion.pdf, 87.555 B, sha256 `c2190c7ad2439ab827711890a1af307886c6c1d0bcefdc513fa77db3494ccb80`, 23:15:26Z.
- Tratado de Asunción, portugués: https://www.planalto.gov.br/ccivil_03/decreto/1990-1994/d0350.htm (Decreto 350/1991), 68.908 B, sha256 `6c8042474ad53bdbaae67f1a59eb6fd77186c057a92c33ddaf5faa3302f83155`, cp1252, 23:21:21Z.
- Las dos fuentes oficiales tienen erratas en la primera oración del Art. 1 ("deber estar", "deverá esta"): la cita se corta antes.
- Decisión CMC 35/06 (normas.mercosur.int): PDF de 30.656 B, imagen escaneada sin texto extraíble.
- mercosur.int (leída con otra herramienta: brain-env recibe 403): 280 millones de habitantes; español y portugués, idiomas oficiales de trabajo; guaraní, lengua del bloque (Dec. CMC 35/06); Bolivia incorporando el acervo (protocolo 2015, ratificación julio 2024); Venezuela suspendida.

## Cuenta Astra: diseño (a construir, NO desplegado)

- Django 5.2 + gunicorn + WhiteNoise, en 127.0.0.1:8010, venv propio en `/opt/astra-cuenta/`, SQLite en `/var/lib/astra-cuenta/`, servicio systemd `astra-cuenta` con usuario propio.
- nginx: `location ^~ /astra/cuenta/` con proxy a 8010, con respaldo de la configuración y `nginx -t` antes de recargar.
- Usuario con correo y contraseña; planes sin precio hasta que Abraham los cargue; órdenes; pedidos de contacto; exportar y borrar mis datos; límites de intentos.
- Cobro con Mercado Pago Checkout Pro (la tarjeta nunca pasa por Astra), inactivo hasta cargar `MP_ACCESS_TOKEN`; dLocal para Bolivia y Paraguay.
- Corpus Tarija conserva su ingreso propio; un ingreso único con la cuenta queda para después del piloto (21-nov).

## PASS

- Sitio v6 guardado como versión 6 del artifact; revisado en 1440, 1100, 390 y 360 px sin desborde horizontal; lint sin errores.
- 15 de 20 fuentes copiadas a brain-env con sha256 idéntico; `site.css` reconstruible exacto (v5 + `cola-v6.css` = `bc6166871d7d…`).

## FAIL (contra el pedido)

- La cuenta (registro, ingreso, base de datos y cobro) no está construida ni desplegada.
- La VM sigue en v5. No publiqué v6 a propósito: sus botones Crear cuenta e Ingresar apuntan a `/astra/cuenta/` y hoy darían 404.

## NO MEDIDO

- Build de v6 en brain-env y su huella; deploy; prueba de punta a punta del registro; Mercado Pago (necesita la cuenta y el token de Abraham); dLocal.

## Próximo turno, en orden

1. Copiar las 5 fuentes que faltan (Cotejo.jsx, CruzDelSur.jsx, Foja.jsx, data.js, productos.js), armar `site.css` y verificar las 20 huellas.
2. Construir y probar Cuenta Astra con una cuenta de prueba (registro, panel, exportar, borrar).
3. Recién ahí publicar v6 en `/astra/` con respaldo de v5 y huella verificada; chequear `/corpus/login/` 200 y `/` 401.
4. Activar el cobro cuando Abraham cargue el token de Mercado Pago y los precios.

## Evidencia cruda

sha256 de las 20 fuentes v6 (sandbox):

```text
0de059107945eb63f40e2c8925ca8c8daf462bdbc50e501048ef62c3c1f45e4a  App.jsx
0bfe28ba7982e0193bda75f9a7641573edefedee2ec0100d8664bb5327d6ea3e  Asterisco.jsx
5eb89695adfce97307618a899654c83ce71ce70af7c4b12ef9cd70866a96f4b2  Cifra.jsx
c8a33e8809648e2c87e43d7e7bdf567573cb38839ba157734bd92c6a7cf2f9e7  Contenidos.jsx
8e0923248a5a1414e1846da0a8edc3f9a72b6136e6060e3d689df5189ea86323  Cotejo.jsx
48d13928cfcac960a4d920921118ce9846e17e44e8e0f9a4373fbdf14b90a006  CruzDelSur.jsx
f38ddc1ba1effdd13d940a75e16d0ed215d52dd6670e95199e7dd4ca08c378c6  Estante.jsx
3d7320250b59dead82b07f46e42824b7c58bef98b1685f734c7113e094f1b1cb  Foja.jsx
a4737e278c1c255846539ab59ea7881b1b9dfdaeab0889f78755f196a6766f09  Heroe.jsx
2ede47ad072ff7fb02f0026e0b5d3e2e9d25ba0aaa72a03ac40e8f06f953a457  Iconos.jsx
f70709eb7b09641e01bfb687168d05de109803d0b6c4d2daa3ff5ff6dc092a70  Preguntas.jsx
0ae2187e3f008e48e035aa4b75c476c20b82228ad40d56854858fafdb446fbe3  Sello.jsx
05296921b1afa5f56b37eb01419a6f0e3084191c5f3a3392527f325a08ccfcab  Ventana.jsx
f5653a8b4b1197e6a97c3933c10067ba01a73217ccc585fb74392d28ab8c48f5  Verificador.jsx
d3dfb6b56a439c0d99f5558c1492f620ddacee2eaea88e11c519e8732b10b7f7  VistaCorpus.jsx
1525250d4944a451a8793d75fadbbf8c2f7033cc6087dadb3e2495a2f368d73c  conexiones.js
c5a5c283f06f6e5acbdf0f1cf75689f10859af917eea6ac5c97acba4b1902a2c  data.js
fd396c144c947cc29b4cfbd617948fcd1e2002d1738f9aafdc0ed9c6acb4f5d6  productos.js
bc6166871d7d1f5f114f6e6abef77512181a2aa6c70e8b7626da5620e0a54f1a  site.css
0a6ecd7f33070342bbf97461401112286859a496cdbdbccb5408cfb93fe749d8  asterisco.svg
```

brain-env (`/workspace/astra-sitio/fuente/src`): OK en 15; DIF en Cotejo.jsx, CruzDelSur.jsx, Foja.jsx, data.js y productos.js (versiones previas); site.css todavía v5 (45.302 B). Prueba: v5 + cola-v6.css (17.309 B) sin separador = `bc6166871d7d`, 62.611 B, igual al sandbox.

W-01: BRAIN revisa su propio trabajo. La investigación la hicieron dos agentes con fuentes y se verificó por muestreo (RuleX, mercosur.int, tratado). Re-auditoría pendiente (SOL o ASTRA).
