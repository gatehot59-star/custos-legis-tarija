# Astra Legal Tech: documentación vigente

Actualizado el 16-oct-2026. **Esta carpeta es lo único que se usa.** El resto de la rama se borró el 16-oct a pedido de Abraham ("solo debe quedar la documentación que usaré, todo lo auditado"). Los archivos viejos siguen en la historia de git, no en el árbol.

Base: la auditoría `docs/auditorias/2026-10-15-01-auditoria-paquete-sas-astra.md` en main `29b65aa` (veredicto ROJO, corregido con el paquete v3; Doc https://app.clickup.com/90171457413/docs/2kza6fw5-23457) y el re-chequeo de abajo.

| # | Archivo | Qué es | Para usar | Doc de ClickUp |
|---|---|---|---|---|
| 01 | `01-sas-paquete-v3.md` | constitución de la SAS en la IGPJ Salta, sobre el modelo oficial | 6 DOCX (00 a 05) | https://app.clickup.com/90171457413/docs/2kza6fw5-23297 |
| 02 | `02-poder-especial-bolivia.md` | poder para el representante en Bolivia, después de la inscripción | texto del Doc | https://app.clickup.com/90171457413/docs/2kza6fw5-23277 |
| 03 | `03-convenio-uno.md` | convenio marco + específico N° 1, piloto del 23-oct al 21-nov | Convenio_UNO_Astra_Legal_Tech_v3.docx (https://t90171457413.p.clickup-attachments.com/t90171457413/212f7dfe-b2a4-5487-8703-ec12a75d1e3a/Convenio_UNO_Astra_Legal_Tech_v3.docx?view=open) | https://app.clickup.com/90171457413/docs/2kza6fw5-23357 |
| 04 | `04-correo-uno-vicerrectorado.md` | correo al Vicerrectorado de Yacuiba y aviso por WhatsApp | el texto del archivo | https://app.clickup.com/90171457413/docs/2kza6fw5-23357 (al final) |
| 05 | `05-marcas-inpi-senapi.md` | búsquedas de marca en Argentina y Bolivia | - | https://app.clickup.com/90171457413/docs/2kza6fw5-23297 |
| 06 | `06-calendario-uno.md` | calendario de la UNO y fechas del piloto | - | https://app.clickup.com/90171457413/docs/2kza6fw5-23257 |

## Orden de uso

1. Hoy, viernes 16-oct: mandar el correo (04) con el convenio v3 (03) adjunto y avisar por WhatsApp.
2. Antes del viernes 23-oct: Always On activo en Abacus; reunión con la UNO (lunes 19 o martes 20); firma del convenio por Abraham, por sí y en nombre de la SAS en formación.
3. Del 23-oct al 21-nov: piloto. En paralelo, la SAS (01): reserva de nombre, firmas digitales, DDJJ PEP certificadas, depósito del 25% y presentación antes del 31-oct.
4. Del 23-nov al 4-dic: informe de los docentes. Antes del 11-dic: acta de cierre y certificados.
5. Con la SAS inscripta: comunicarlo a la UNO (cláusula "Sociedad en formación") y otorgar y apostillar el poder (02).
6. Marcas (05): búsqueda oficial en SENAPI y registro de Corpus Tarija y Custos Legis antes de hacer propaganda en Tarija.

## Qué se borró de la rama el 16-oct (la historia queda intacta)

Reemplazados por esta carpeta:

- `docs/legal/2026-10-15-sas-salta-paquete.md` (v1 y v2, auditados ROJO), `docs/legal/2026-10-15-sas-salta-ruta-sin-escribano.md` y `docs/legal/2026-10-16-sas-paquete-v3-modelo-oficial.md`: ahora 01.
- `docs/legal/2026-10-15-borrador-poder-especial-representante-bolivia.md`: ahora 02.
- `docs/legal/2026-10-15-convenio-uno-astra.md`: ahora 03, en su v3.
- `docs/legal/2026-10-16-correo-uno-vicerrectorado-yacuiba.md`: ahora 04, con las fechas nuevas.
- `docs/legal/2026-10-15-inpi-astra-legal-tech.md` y `docs/legal/2026-10-15-senapi-astra-legal-tech.md`: ahora 05.
- `docs/legal/2026-10-15-calendario-uno.md`: ahora 06.

Análisis y recibos que no sirven para operar (el análisis del plan y la decisión SAS en Salta quedan en el Doc del plan, https://app.clickup.com/90171457413/docs/2kza6fw5-23257):

- `docs/agents/respuestas/2026-10-15-plan-salta-yacuiba.md`
- `docs/agents/respuestas/2026-10-15-02-ajuste-plan-yacuiba.md`
- `docs/agents/respuestas/2026-10-15-03-sas-salta-vs-tarija.md`
- `docs/agents/respuestas/2026-10-15-04-resumen-astra-legal-tech.md`
- `docs/agents/respuestas/2026-10-16-01-correccion-tras-auditoria-sas.md`

Main no se tocó: la auditoría y su evidencia siguen en `docs/auditorias/`.

## Re-chequeo del 16-oct (instrumento que podía dar rojo)

Instrumento: un script de regex en el sandbox de ClickUp sobre los 6 archivos de esta carpeta y sobre el texto del DOCX v3 (párrafos y tablas). Busca fechas viejas del piloto, el placeholder de razón social y las afirmaciones que la auditoría refutó: marca "libre", 6.800 menciones, UIF 11/2011, art. 4 de la Ley 27.506, "más del doble", Lex AI, Torrez como destinataria, SASU, "en constitución desde" y "garantizará la disponibilidad". También lista los corchetes que quedan y cuenta URLs sin expandir.

Resultado:

- Fechas viejas: sólo en la línea de historial de 03 y en la línea de verificación de 03 que informa que valen 0. Ninguna como fecha vigente. En el DOCX v3: 0.
- Razón social sin completar: 0.
- Afirmaciones refutadas: 0 como afirmación. Las 4 coincidencias son negaciones o historial: "no SASU" (01), "garantizará la disponibilidad pasa a..." (03), "Torrez... no es la destinataria vigente" (04) y "eso no es libre" (05).
- Corchetes: sólo datos de Abraham, de su hermana, del apoderado o de la UNO, y elecciones abiertas (tribunales [Salta], [tres (3)] becas, lugar de firma). En el convenio, las fechas del cronograma van entre corchetes porque se confirman con la UNO.
- URLs sin expandir: 0 en los 6 archivos.

Lo que este re-chequeo no puede poner en rojo: que una norma, un precio o un dato de la UNO haya cambiado después de medirlo. Eso sigue como NO VERIFICADO en cada archivo.

Salida cruda:

```text
== 01-sas-paquete-v3.md 59 lineas sha256 664c5498996a6097
   [refutado] /(?i)sasu/ L21: - Denominación: ASTRA LEGAL TECH S.A.S. (el modelo editable usa "S.A.S.", no "SASU").
   corchetes: ['[Salta]']
   placeholders compresion: 0 | app.clickup.com: 1 | t9017: 12
== 02-poder-especial-bolivia.md 31 lineas sha256 9221227db31044c7
   corchetes: ['[__]', '[nombre]']
   placeholders compresion: 0 | app.clickup.com: 1 | t9017: 0
== 03-convenio-uno.md 60 lineas sha256 6398f173717f3049
   [fecha vieja] /(?<!\d)3 al 27/ L10: - Piloto del 23-oct al 21-nov-2026 (30 días). Historial: la v2 decía 9-nov al 4-dic y la v1, 3 al 27-nov.
   [fecha vieja] /(?<!\d)9-nov/ L10: - Piloto del 23-oct al 21-nov-2026 (30 días). Historial: la v2 decía 9-nov al 4-dic y la v1, 3 al 27-nov.
   [fecha vieja] /(?<!\d)9 de noviembre/ L58: - fechas viejas: "9 de noviembre" 0, "7 al 18" 0, "23 de diciembre" 0; firma por "apoderado en Bolivia" 0;
   [fecha vieja] /(?<!\d)7 al 18/ L58: - fechas viejas: "9 de noviembre" 0, "7 al 18" 0, "23 de diciembre" 0; firma por "apoderado en Bolivia" 0;
   [fecha vieja] /(?<!\d)23 de diciembre/ L58: - fechas viejas: "9 de noviembre" 0, "7 al 18" 0, "23 de diciembre" 0; firma por "apoderado en Bolivia" 0;
   [refutado] /(?i)garantizar[áa] la disponibilidad/ L15: - Específico, 6.2 b): "garantizará la disponibilidad" pasa a "mantendrá el servicio disponible, salvo interrupciones programadas avisadas o causas aje
   corchetes: []
   placeholders compresion: 0 | app.clickup.com: 1 | t9017: 2
== 04-correo-uno-vicerrectorado.md 68 lineas sha256 c6065f94e811a60c
   [refutado] /(?i)torrez/ L17: La Dra. Danixa Torrez Chávez figuraba como vicerrectora en 2023-2024: no es la destinataria vigente.
   corchetes: ['[+54 9 ...]', '[...]']
   placeholders compresion: 0 | app.clickup.com: 1 | t9017: 0
== 05-marcas-inpi-senapi.md 57 lineas sha256 e3363c52e776580b
   [refutado] /(?i)\blibre\b/ L15: Cómo leerlo: 0 coincidencias por caracteres en el buscador del INPI. Eso no es "libre": falta la comparación fonética y el examen del propio INPI.
   corchetes: []
   placeholders compresion: 0 | app.clickup.com: 1 | t9017: 0
== 06-calendario-uno.md 45 lineas sha256 38d915645d8b2002
   corchetes: []
   placeholders compresion: 0 | app.clickup.com: 0 | t9017: 0
== Convenio_UNO_Astra_Legal_Tech_v3.docx 13985 chars
   corchetes: ['[23 de noviembre al 4 de diciembre de 2026]', '[23 de octubre al 21 de noviembre de 2026]', '[M.Sc. Dr.\xa0Sergio Borja Alarcón, o quien ejerza el cargo]', '[Nombre y cargo]', '[Nombre]', '[Yacuiba / Santa Cruz de la Sierra]', '[__]', '[______]', '[antes del 11 de diciembre de 2026]', '[instrumento de designación o poder N° ______]', '[tres (3)]', '[viernes 23 de octubre de 2026]']
```

## Método

- Agente: BRAIN. Pedido: "Sí, avanzá con la limpieza y las fechas" (Abraham, 16-oct 10:33 ART), sobre el plan propuesto en el turno anterior.
- Herramientas: GitHub MCP (push_files para esta carpeta, delete_file para los 14 archivos viejos); brain-env con el clon de custos-legis-tarija para leer la rama (no tiene credenciales para empujar); sandbox de ClickUp para el DOCX v3 (pandoc, python-docx) y para el re-chequeo.
- Acción delicada: borrar archivos de una rama. Acordado por Abraham; no se reescribe historia y no se toca main.
- PASS: carpeta con 6 documentos + índice; re-chequeo sin fechas viejas vigentes ni afirmaciones refutadas.
- NO MEDIDO: el calendario 2/2026 real de la UNO; si la UNO acepta la firma por la sociedad en formación; cuánto tarda en firmar.
- W-01: BRAIN re-chequea su propio trabajo. Re-auditoría pendiente (SOL o ASTRA).
