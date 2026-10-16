# 07. Sitio web de Astra Legal Tech (prototipo v1, no publicado)

Estado al 16-oct-2026 15:40 ART: prototipo guardado en ClickUp. No publicado: faltan dominio, buzón y hosting.

- Prototipo: https://app.clickup.com/90171457413/artifact/2kza6fw5-23717 (versión 1)
- Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23737
- Pedido de Abraham (16-oct 15:10): página de vanguardia, tomando lo mejor de una empresa similar y contextualizado a Argentina; "la única imagen de la empresa que seremos, como si ya fuéramos".

## Qué contiene

- Héroe: "Cada cita, con su fuente." y una foja con una ley departamental real de Tarija cosida por un hilo violeta a su ficha de fuente (publicación oficial, fecha de descarga, SHA-256 del PDF, enlace a tarija.gob.bo). Selector entre las leyes N° 516, 512 y 518.
- Tres preguntas antes de citar: qué dice, de dónde sale, de cuándo es.
- Cadena de custodia: fuente oficial, descarga fechada, huella digital, cita verificable, criterio del abogado. Cifra: 1.031 normas departamentales de Tarija.
- Programas académicos para facultades de Derecho (mismas condiciones que el convenio v4).
- Contacto (contacto@astralegaltech.com) y notas al pie con el origen de cada dato.
- Diseño: Archivo (voz de Astra), Source Serif 4 (la ley), IBM Plex Mono (el registro). Papel #F4F2F7, tinta #1B1930, violeta de sello #5A3DA8, lacre #8B3E50 sólo para omisiones [...]. La marca es un asterisco: asteriskos, "estrellita", el signo que en un texto jurídico remite a la fuente.

## Referencias estudiadas (search_web, 16-oct)

- Harvey (harvey.ai): cada afirmación con su cita; "el criterio es siempre del abogado"; seguridad.
- Nino Legal (ninolegal.com, Córdoba): fuente en cada respuesta; cobertura por jurisdicción.
- Civilia (civilia.com.ar): abre el pasaje citado y avisa cuando la fuente no alcanza.
- Tomado: la cita que lleva a la fuente como experiencia central, y el criterio profesional. No tomado: cifras sin fuente ("0% de alucinaciones", "+3.900 abogados"), logos de clientes, testimonios.

## Datos del sitio y su verificación

Normas (indices/manifest.jsonl de gatehot59-star/corpus-legal-tarija; etapa "bajar" en brain-env el 2026-09-02; texto cotejado el 16-oct contra /workspace/corpus-legal/CORPUS_LEGAL_TARIJA_BOLIVIA_2026/11_TEXTO/<md5>.txt en brain-env):

| Ley Departamental | Fecha | Artículos | SHA-256 del PDF |
|---|---|---|---|
| N° 516, Corredor del Pilcomayo | 2026-04-07 | 14 | 0ad12b49be0798e9add659b87b0a14a609bdd85c3961a21e68da36328892ec04 |
| N° 512, Ruta de Actuación Interinstitucional (RAI) | 2026-01-13 | 9 | efb768964eeac6ce58926126ccf85869387e21c45eac12ff249e350edc060407 |
| N° 518, Día de la Copla | 2026-04-09 | 5 | 7782d05cde6d3e2082ad24be33d01c3593142a8e38bf52b3b2695dd4a81d2e56 |

- Las citas del artículo 1 omiten con [...] los tramos donde la extracción del PDF dice "Tarja" en vez de "Tarija": así no se cita texto dudoso.
- Vigencia: el índice tiene vigente = null en los 1.031 registros. NO MEDIDA, por eso el sitio no dice "vigente".
- Recuento del 16-oct sobre el mismo índice: 1.031 registros (más 1 línea no JSON), 511 leyes departamentales y 520 resoluciones del Pleno; 1.031 con SHA-256 de 64 hex (todos distintos); 1.030 con fuente en www.tarija.gob.bo/gaceta-oficial/; 1.031 con etapa "bajar" OK; gestiones 2010 a 2026, con 31 vacías y 1 "2078" (error de extracción). Hay dos registros N° 512: se usa el del 13-ene-2026, que coincide con el texto.
- Criterio de presentación aplicado: sin "fundador", "recién creada", "unipersonal", Salta ni nombres de productos.

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

## NO MEDIDO

- Cómo se ve el sitio publicado en un dominio real y si Google lo indexa antes de la reunión del 19 o 20.
- Si el PDF que hoy sirve tarija.gob.bo sigue teniendo la misma huella que el descargado el 2-sep.
- W-01: BRAIN diseñó y verificó el contenido. Re-auditoría pendiente (SOL o ASTRA).
