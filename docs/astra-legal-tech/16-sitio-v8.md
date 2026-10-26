# 16 · Sitio v8: servicios y páginas por país (26-oct-2026, 02:30 ART)

Doc de ClickUp: https://app.clickup.com/90171457413/docs/2kza6fw5-23737/2kza6fw5-27877
Artifact: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=8
Probar: https://astra.icca-engine.com/legal-tech-bolivia (igual con argentina, brasil, chile, colombia, mexico, paraguay, peru, uruguay)

## Pedido

Abraham, 26-oct 02:11 ART: tomar de https://legalhub.la/nosotros "cómo conecta con cada país", que "la lista de servicios debe ser ídem más lo nuestro", y su texto de nosotros, "súmale Bolivia".

## Qué hace LegalHub (leído el 26-oct)

- Una página por país en /legal-tech-<país> (Argentina, Uruguay, Brasil, Perú, Chile, México, Colombia) con marco regulatorio, sistemas judiciales, servicios y llamado a reunión; en el pie, la lista de países con bandera.
- Servicios del pie: Inteligencia Artificial, Agentes AI, RAG, Machine Learning, APIs e integraciones, Dashboards, Plataformas a medida, Scraping, ETL & Data Engineering, Consultoría.

## Qué quedó en Astra

- Servicios: esas diez categorías con descripciones propias, más tres de Astra (Verificación con huella SHA-256, OCR de boletines oficiales, Ediciones por jurisdicción). Sección en la portada y columna en el pie.
- Países: Argentina, Bolivia, Brasil, Chile, Colombia, México, Paraguay, Perú y Uruguay. Tarjetas en la portada, columna "Legal Tech <país>" con bandera en el pie y una página por país con diario oficial, normas, justicia y ley de datos personales (enlazados), servicios, estado real de Astra y los otros países. Bolivia: Corpus Tarija en prueba piloto, con enlace a su pestaña; el resto: proyectos a medida por convenio.
- Dirección limpia: nginx manda /legal-tech-<país> a /#/legal-tech-<país> (302); un país inventado da el 404 propio.
- Nosotros (pie y ventana Empresa): "Astra Legal Tech hace Legal Operations e IA jurídica para América Latina. Diseñamos y construimos plataformas a medida, agentes de IA, sistemas RAG, dashboards de legal analytics y automatizaciones para departamentos legales del sector público y privado de Argentina, Bolivia, Brasil, Chile, Colombia, México, Paraguay, Perú y Uruguay. Cada respuesta, con su fuente oficial y su huella." + "© 2026 Astra Legal Tech. Todos los derechos reservados."
- Del texto modelo sale lo que Astra no puede respaldar hoy: "la empresa líder" (publicidad engañosa), "con base en Buenos Aires" (falso y nombra Argentina como sede) y "equipo multidisciplinario de abogados, ingenieros y diseñadores" (no medido). Paraguay se suma por el MERCOSUR: el sitio cita el Tratado de Asunción.
- Banderas: emoji junto al nombre; en tarjetas y fichas, una franja con los tres colores, sin dibujar escudos.

## Datos de cada país (verificados el 26-oct-2026)

- Enlaces: 33 probados desde brain-env; los que fallaron ahí (DOU, SIC, Leyes Federales de México, Gaceta de Paraguay) respondieron desde el lector web. SPIJ (Perú) no respondió desde ninguno y quedó afuera. BACN (Paraguay) dio 523 y quedó afuera. La Gaceta de Bolivia responde sólo por http.
- Datos personales: Argentina Ley 25.326 (AAIP); Bolivia sin ley general vigente (Acción de Protección de Privacidad, CPE art. 130, y proyecto de ley en Diputados); Brasil LGPD Lei 13.709/2018 (ANPD); Chile Ley 19.628 reformada por la Ley 21.719, vigencia diferida al 1-dic-2026 con un proyecto en el Senado para postergarla; Colombia Ley 1581 de 2012 (SIC); México LFPDPPP nueva, DOF 20-03-2025 (Secretaría Anticorrupción y Buen Gobierno); Paraguay Ley 7593/2025, Gaceta N° 287 del 27-nov-2025 (Agencia Nacional en el MITIC); Perú Ley 29733 (ANPD); Uruguay Ley 18.331 (URCDP).

## Fuentes y build

- v8 = fuentes v7 + `editar_v8.py` (sha 2a51b3f0) con `datos-v8.js` (fcc9c3a4), `Servicios.jsx` (3b3b075d), `VistaPais.jsx` (95cbac79) y `cola-v8.css` (e2cd119e). 23 de 23 sha256 iguales entre el sandbox y brain-env.
- App.jsx 9331552c · Contenidos.jsx d22be148 · data.js d0aa7a6f · site.css cc10e424.
- esbuild: app.js 237.494 B (b6f05fde), app.css 59.816 B (a0c31eed). index 315.254 B, sha256 3c9e30db727a8b3d0c2bc4b4520cebacd58afd95b473e2b1aef61c596b7ecedb.
- Conf nginx: 2.734 B, sha256 3e780732e98f1b874e075120a38b1cd2dc403789a3bfed71d0e9795f6b220b49.

## Publicación

- 26-oct 05:30:21 UTC: respaldos `/var/backups/astra/index.html.v7-20261026T053021Z` y `/var/backups/astra/astra-icca-engine.conf.20261026T053021Z`; conf instalada; `nginx -t` OK; recarga; index instalado.
- Deshacer: copiar los dos respaldos, `nginx -t`, recargar nginx.

## Resultado

PASS
- Público = origen: / da 315.254 B con sha 3c9e30db, `no-cache, no-transform`.
- /legal-tech-bolivia y /legal-tech-peru/ dan 302 a /#/legal-tech-<país>; /legal-tech-narnia da 404 (2.560 B, el propio).
- Chromium 153 (Playwright en brain-env) contra el sitio real, 390 y 1280 px: meta v8; menú Productos, Servicios, Países, Planes, MERCOSUR, Empresa, Inversores; 10 servicios + 3 propios; 9 tarjetas de país, sólo Bolivia en prueba piloto; pie con 9 países, 13 servicios, el texto de nosotros y "Todos los derechos reservados"; Ingresar visible; sin "líder" ni "Buenos Aires"; la tarjeta de Bolivia abre su página; 0 pedidos a terceros.
- Las 9 direcciones /legal-tech-<país> en 390 px: título "Legal Tech en <país> · Astra Legal Tech", h1 correcto, fichas con 3 o 4 filas y sus enlaces, estado, 8 países vecinos, 10 servicios, pestaña Astra activa, ancho 390, 0 pedidos a terceros.

FAIL
- La cuenta todavía ofrece sólo Argentina, Bolivia, Brasil, Paraguay, Uruguay y Otro al registrarse: faltan Chile, Colombia, México y Perú.
- En la vista previa, la etiqueta de estado de las tarjetas salió ancha por un nombre de clase repetido (`.pais-estado`); se renombró el contenedor a `.pais-situacion` antes de publicar.

NO MEDIDO
- Que los enlaces oficiales sigan vivos después del 26-oct.
- Cómo se ven las banderas emoji en Windows (muestra letras en lugar de la bandera).

W-01: BRAIN verifica su trabajo con un navegador distinto a la vista previa del artifact. Re-auditoría pendiente.
