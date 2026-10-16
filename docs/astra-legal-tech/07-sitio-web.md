# 07. Sitio web de Astra Legal Tech (prototipo v3, no publicado)

Estado al 16-oct-2026 17:15 ART: versión 3 guardada en ClickUp. No publicado: faltan dominio, buzón y hosting.

- Prototipo: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717?version=3 (v1 y v2 quedan en el historial del artifact)
- Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737

## 1. Pedido (Abraham, 16-oct 16:31 ART)

"Pésimo." Lo hecho en la v1 pasa a ser una ventana desplegable de la empresa; otra ventana buscando accionistas; otra que explique Corpus Legis. Del piloto, sólo que está en prueba piloto. Vender Corpus Tarija, Custos Legis, SIAO, AURA, MUDH Mobile, CashGo "y otros dos". Dejar de lado todo lo relacionado con el conectoma. Mostrar cómo se está creando la SAS. "Un poco de humo", con ejemplos de empresas similares a lo que se inscribe en Salta, combinados con sus productos.

Lectura declarada (Abraham puede corregirla): "Corpus Legis" es la suite legal (Corpus Tarija + Custos Legis); "cómo se está creando la SAS" son las líneas del objeto social del instrumento v3 (01), sin datos registrales.

Pedido anterior (16-oct 15:10): página de vanguardia, tomando lo mejor de una empresa similar y contextualizada a Argentina, "como si ya fuéramos". Resultado: v1, rechazada.

## 2. Herramientas declaradas

- search_web: Lemontech, Faraday Security, Harvey, Nino Legal y Civilia (referencias); Infoleg y argentina.gob.ar (Ley 27.349 art. 39 y Ley 26.831 art. 2).
- Lectura en ClickUp: Docs "MUDH-Mobile explicado en criollo" y "CASHGO en criollo", y los docs de SIAO y AURA.
- GitHub MCP: README de siao, lista de repos de gatehot59-star, y 01, 07 y README de esta carpeta. Escritura: este archivo y el README, en un commit, sólo en esta rama.
- Sandbox de ClickUp: artifact CLI (build, tests, capturas CDP, versiones 2 y 3) y Python para el control del bundle.
- MUDH Gateway: una fila en reportes de Nexus. brain-env no se usó para v2 y v3 (las cifras de normas y el dominio son de la v1).
- Sin cuota ajena.

## 3. Qué contiene (v3)

Página:

- Héroe nocturno: "Inteligencia que rinde cuentas." y "Software, inteligencia artificial y ciberseguridad para sectores donde un error cuesta caro." Botones: Explorar productos, Inversores.
- Constelación: cada estrella es un producto y abre su ficha. Las líneas son sólo relaciones reales: Custos Legis consulta Corpus Tarija; SIAO contiene AURA; AURA corre sobre MUDH Mobile. Ámbar = prueba piloto, lavanda = desarrollo, anillo = diseño.
- Franja: 6 productos · 3 verticales · +6.000 documentos jurídicos procesados · Desde Argentina para la región. Base: 6.079 documentos en el snapshot del 9-sep (GENESIS 5.030 Autos Supremos, Gaceta de Tarija 1.034, LexiVox 15).
- Lo que hacemos: el objeto social (01), incisos a) a f): tecnología jurídica, inteligencia artificial, software y plataformas, ciberseguridad, datos e infraestructura, formación. Los incisos g) exportación y h) propiedad intelectual aparecen como "Desde Argentina para la región" y "Tecnología propia".
- Productos por vertical: Corpus Legis (Corpus Tarija, Custos Legis y la suite), Sistemas inteligentes (SIAO, AURA, MUDH Mobile), Crecimiento (CashGo).
- Banda de inversores; contacto (contacto@astralegaltech.com); pie: "Las herramientas de Astra asisten al profesional; no constituyen asesoramiento jurídico."
- Menú: en escritorio, en la cabecera; en celular, una fila bajo la cabecera (probada a 390 y 360 px).

Ventanas desplegables, cada una con enlace directo (#empresa, #inversores, #corpus-legis, #corpus, #custos, #siao, #aura, #mudh, #cashgo):

- Empresa: el núcleo de la v1 (foja verificable con las leyes 516, 512 y 518, ficha de fuente con SHA-256, cadena de custodia, 1.031 normas, principios y notas) y el aviso del objeto social: Astra no presta asesoramiento ni patrocinio jurídico.
- Inversores: tesis ("La inteligencia artificial va a entrar donde un error cuesta caro. Ahí gana la que rinde cuentas."), cuatro razones, qué buscamos, correo y aviso de no oferta pública.
- Corpus Legis: fuente oficial, Corpus Tarija, Custos Legis y el abogado, en ese orden, y el estado.
- Una por producto: estado, lema, qué hace, para quién, cómo se conecta y paso al anterior o al siguiente.

Criterio de presentación aplicado: sin "fundador", "recién creada", "unipersonal" ni Salta. El sitio sí muestra el portafolio (pedido del 16-oct 16:31): la regla de no listar productos rige para correos y mensajes. Nada del conectoma.

## 4. Estado de cada producto (nada dice "disponible")

| Producto | En el sitio | De dónde sale |
|---|---|---|
| Corpus Tarija | En prueba piloto | convenio v4 (03): piloto del 23-oct al 21-nov |
| Custos Legis | En desarrollo | repo custos-legis-tarija |
| SIAO | En desarrollo | repo siao: al 8-sep, userland base y builds de kernel medidos; sin dispositivo |
| AURA | En diseño | sin código al 29-ago |
| MUDH Mobile | En desarrollo | "amarillo, encaminado, no entregable" (Doc MUDH-Mobile en criollo) |
| CashGo | En desarrollo | repo cashgo: sólo la arquitectura 2 (auditoría de anuncios de la biblioteca de Meta a PDF; 26 archivos Python, 144 tests) |

Del piloto el sitio dice sólo "Corpus Tarija se encuentra en prueba piloto": sin universidad, fechas ni alumnos.

## 5. El humo, con límite

Empresas parecidas a lo que inscribe la SAS (software, IA, ciberseguridad y tecnología jurídica):

- Lemontech (Chile): "plataforma legal potenciada con IA" y un producto por tipo de equipo, en tarjetas. Acá: productos por vertical, con tarjeta y ficha.
- Faraday Security (nacida en Argentina): una plataforma con una capa de IA que atraviesa los módulos, humano en el circuito y verbos cortos. Acá: la constelación (productos conectados) y "Humano al mando".
- Harvey: cada afirmación con su cita; el criterio es del abogado. Acá: la ventana Empresa.
- Nino Legal y Civilia: la fuente en cada respuesta. Acá: la foja verificable.

Humo permitido: titulares, tesis, visión y diseño. Ausente a propósito: clientes, testimonios, logos, cifras, oficinas o inversores inventados; "vigente"; "disponible" para lo que no corre.

## 6. Inversores: una invitación a conversar (corrige un supuesto mío)

- REFUTADO, supuesto previo de BRAIN: "la SAS no puede hacer oferta pública porque el art. 39 de la Ley 27.349 remite al inc. 1 del art. 299 de la LGS". Eso decía el texto original de 2017. El texto vigente (sustituido por el art. 36 de la Ley 27.444, B.O. 18-6-2018, según Infoleg) remite sólo a los incisos 3, 4 y 5. El supuesto no llegó a ningún documento ni al texto visible del sitio: estaba en un comentario interno del código, corregido en la v3.
- Lo que sí aplica: la Ley 26.831 de Mercado de Capitales. Su art. 2 cuenta a las acciones entre los valores negociables (leído en argentina.gob.ar); invitar al público a comprarlas es oferta pública y necesita autorización de la CNV.
- Por eso la ventana habla de "socios estratégicos", ofrece conversar por correo y aclara: "Esta sección no constituye una oferta pública de acciones ni de valores negociables. La información se comparte en forma privada e individual con cada interesado."
- NO VERIFICADO textual: la definición completa de oferta pública del art. 2 (la búsqueda la devolvió cortada). Antes de hablar con un inversor concreto, que lo revise un abogado societario.

## 7. Qué se midió (instrumento que podía dar rojo)

- Build, tests y lint del artifact (artifact save): versiones 2 y 3 guardadas. El lint exige que cada clase usada exista en el CSS.
- Recorrido en navegador (artifact cdp, 1440x900): las 7 tarjetas y las 6 estrellas abren la ficha correcta, con su estado; Esc y el botón cierran; con clic real, el foco entra al botón de cerrar, queda dentro de la ventana con Tab y vuelve a la tarjeta al cerrar; el enlace directo se escribe y se borra.
- Capturas revisadas a 1536x864, 1440x900, 1280x800, 390x844 y 360x780, de la página completa y de las ventanas.
- Control del bundle: 0 coincidencias de la lista prohibida. Control positivo: el mismo script encuentra "conectoma" en el comentario de src/productos.js, y los nombres de los productos y los dos avisos legales en el bundle.

Errores que encontró la ronda de capturas, corregidos antes de guardar:

- El desenfoque del velo pintaba detrás de la ventana un reflejo invertido de los botones del héroe: se quitó el desenfoque.
- En Corpus Legis, los pasos de Astra salían blanco sobre blanco (especificidad de CSS).
- Una línea fantasma en los bordes de la ventana (capa animada que quedaba compuesta).
- En celular no había menú; a 360 px el último acceso se cortaba.
- El foco podía salir de la ventana con Tab.

## 8. Evidencia cruda

Control del bundle y huellas de la fuente (sandbox de ClickUp, artifact v3):

```text
$ python3 control_bundle.py  # sandbox ClickUp, 16-oct-2026, artifact v3
bundle dist/index.html bytes 343636 sha256(16) 60bf2f6c085e96b7
  (?i)conectoma = 0
  (?i)connectome = 0
  (?i)dualbrain = 0
  (?i)\bmojo\b = 0
  (?i)drosophila = 0
  (?i)icca = 0
  (?i)\bsalta\b = 0
  (?i)fundador = 0
  (?i)unipersonal = 0
  (?i)reci[eé]n = 0
  (?i)yacuiba = 0
  \bUNO\b = 0
  (?i)en formaci[oó]n = 0
  (?i)vigente = 0
  S\.A\.S = 0
  (?i)kaggle = 0
  (?i)clientes = 0
  (?i)testimonio = 0
  TOTAL prohibidos en el bundle = 0
control positivo (debe ser mayor que 0):
  (?i)conectoma en src/productos.js (comentario) = 1
  Corpus Tarija = 6
  En prueba piloto = 1
  Custos Legis = 3
  SIAO = 2
  AURA = 1
  MUDH Mobile = 2
  CashGo = 1
  no constituye una oferta p = 2
  no constituyen asesoramiento = 1
fuentes (artifact v3):
  src/App.jsx 13141 bytes sha256(16) be11744b0ce02e4b
  src/Asterisco.jsx 687 bytes sha256(16) 0bfe28ba7982e019
  src/Cielo.jsx 944 bytes sha256(16) 842dd7ea18199be4
  src/Constelacion.jsx 2488 bytes sha256(16) c560ee39e7691e44
  src/Contenidos.jsx 8672 bytes sha256(16) 00038a542f598ad7
  src/Foja.jsx 4789 bytes sha256(16) d37d0f37f8fea03a
  src/Ventana.jsx 2922 bytes sha256(16) 05296921b1afa5f5
  src/asterisco.svg 588 bytes sha256(16) 0a6ecd7f33070342
  src/data.js 4588 bytes sha256(16) 1559b4ee04e33cfd
  src/productos.js 5025 bytes sha256(16) 5ab0142426ae070b
  src/site.css 34352 bytes sha256(16) 1be71a0c2ee31348
```

Recorrido de ventanas (artifact cdp, 1440x900, clics por JavaScript; el foco queda vacío porque un clic por JavaScript no enfoca el botón):

```text
Corpus Tarija [En prueba piloto] #corpus
  cerrada=true foco=
Custos Legis [En desarrollo] #custos
  cerrada=true foco=
Corpus Legis. [En prueba piloto] #corpus-legis
  cerrada=true foco=
SIAO [En desarrollo] #siao
  cerrada=true foco=
AURA [En diseño] #aura
  cerrada=true foco=
MUDH Mobile [En desarrollo] #mudh
  cerrada=true foco=
CashGo [En desarrollo] #cashgo
  cerrada=true foco=
estrella → Corpus Tarija
estrella → Custos Legis
estrella → SIAO
estrella → AURA
estrella → MUDH Mobile
estrella → CashGo
```

Teclado con clic real (-c '.tarjeta:nth-child(2)', Tab, Tab, Escape):

```text
"ventana-cerrar | Custos Legis"
"Corpus Tarija"
"cerrada=true foco=tarjeta En desarrolloCustos LegisAgent hash="
```

Menú de celular (scrollWidth contra clientWidth de la fila):

```text
390x844 {"sw":390,"cw":390,"ultimoDer":368}
360x780 antes {"sw":385,"cw":360}
360x780 después {"sw":360,"cw":360}
```

## 9. Archivos generados

El código vive en el artifact (versión 3). No se commitea acá: se sube al repo propio del sitio cuando se publique. Sus huellas (sha256, 16 primeros) están en la evidencia de arriba.

## 10. NO MEDIDO

- Los "otros dos" productos: sin nombre. En GitHub aparecen CorreAI y Hermano; no se agregan sin confirmación. Fuera por el conectoma: drosophila-fep-connectome, DualBrain, icca-engine y Mojo Absoluto.
- Sitio publicado en un dominio real e indexado antes de la reunión del 19 o 20.
- Lector de pantalla real (se probaron teclado, foco y roles).
- Si el PDF que hoy sirve tarija.gob.bo conserva la huella del 2-sep.
- W-01: BRAIN diseñó y verificó. Re-auditoría pendiente (SOL o ASTRA).

## Datos de las normas de la ventana Empresa (sin cambios desde la v1)

Normas (indices/manifest.jsonl de gatehot59-star/corpus-legal-tarija; etapa "bajar" en brain-env el 2026-09-02; texto cotejado el 16-oct contra /workspace/corpus-legal/CORPUS_LEGAL_TARIJA_BOLIVIA_2026/11_TEXTO/<md5>.txt en brain-env):

| Ley Departamental | Fecha | Artículos | SHA-256 del PDF |
|---|---|---|---|
| N° 516, Corredor del Pilcomayo | 2026-04-07 | 14 | 0ad12b49be0798e9add659b87b0a14a609bdd85c3961a21e68da36328892ec04 |
| N° 512, Ruta de Actuación Interinstitucional (RAI) | 2026-01-13 | 9 | efb768964eeac6ce58926126ccf85869387e21c45eac12ff249e350edc060407 |
| N° 518, Día de la Copla | 2026-04-09 | 5 | 7782d05cde6d3e2082ad24be33d01c3593142a8e38bf52b3b2695dd4a81d2e56 |

- Las citas del artículo 1 omiten con [...] los tramos donde la extracción del PDF dice "Tarja" en vez de "Tarija": así no se cita texto dudoso.
- Vigencia: el índice tiene vigente = null en los 1.031 registros. NO MEDIDA, por eso el sitio no dice "vigente".
- Recuento del 16-oct sobre el mismo índice: 1.031 registros (más 1 línea no JSON), 511 leyes departamentales y 520 resoluciones del Pleno; 1.031 con SHA-256 de 64 hex (todos distintos); 1.030 con fuente en www.tarija.gob.bo/gaceta-oficial/; 1.031 con etapa "bajar" OK; gestiones 2010 a 2026, con 31 vacías y 1 "2078" (error de extracción). Hay dos registros N° 512: se usa el del 13-ene-2026, que coincide con el texto.

## Dominio (RDAP, 16-oct 18:17 UTC, desde brain-env)

| Dominio | Resultado |
|---|---|
| google.com (control positivo) | registrado (1997) |
| astralegaltech.com | NO REGISTRADO (404) |
| astralegal.tech | NO REGISTRADO (404) |
| astralegaltech.net | NO REGISTRADO (404) |
| astra-legaltech.com | NO REGISTRADO (404) |
| astralegal.com | registrado (2013-12-11), de un tercero |
| astralegaltech.com.ar, astralegal.com.ar | NO MEDIDO: rdap.nic.ar no respondió, tampoco para el control google.com.ar |

## Para publicar

1. Registrar astralegaltech.com (Abraham; costo aproximado USD 10 a 15 por año, NO MEDIDO).
2. Crear el buzón contacto@astralegaltech.com. El sitio ya apunta ahí: no publicarlo antes.
3. Hosting: repo propio con GitHub Pages (público, sin costo) y el dominio propio; Abraham cambia los registros DNS.
4. Sumar la web a la firma del correo a la UNO.

## Hallazgos laterales (afectan al piloto, no al sitio)

- El convenio v4 (antecedentes 2.2) dice que Corpus Tarija busca "legislación nacional y departamental y de jurisprudencia". COBERTURA.md de corpus-legal-tarija (medido el 3-sep, con aviso del 10-sep) dice que faltan los códigos, la CPE completa y las leyes nacionales. NO MEDIDO si se agregaron después. Si siguen faltando, conviene decir "normativa departamental y jurisprudencia".
- El buscador público está cerrado desde el 2026-09-10 por una fuga de nombres de partes (CIERRE-PUBLICO-2026-09-10.md). Antes del 23-oct hay que confirmar que el piloto corre con la compuerta activa.

## Historia

- v1 (16-oct 15:40): "Cada cita, con su fuente." Foja con las leyes 516, 512 y 518, tres preguntas, cadena de custodia, 1.031, programas académicos, contacto y notas. Rechazada ("pésimo"); su núcleo vive en la ventana Empresa.
- v2 (16-oct 17:03): portafolio, constelación de productos y ventanas desplegables.
- v3 (16-oct 17:08): menú de celular a 360 px y nota legal interna corregida.
