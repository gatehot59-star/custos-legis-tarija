# 01. Astra Legal Tech S.A.S.: paquete de constitución v3 (IGPJ Salta)

Estado al 16-oct-2026: listo para completar y presentar. **Nada presentado todavía.** Lo presenta Abraham; meta: antes del 31-oct-2026.

- Doc: https://app.clickup.com/90171457413/docs/2kza6fw5-23297 (banner "Versión vigente: paquete v3")
- Origen: corrige los rojos A1 a A4 de la auditoría `docs/auditorias/2026-10-15-01-auditoria-paquete-sas-astra.md` (main `29b65aa`). La v1 y la v2 no se usan.

## Archivos para usar (adjuntos de ClickUp; no se commitean binarios)

| Archivo | Para qué | URL | sha256 (16) |
|---|---|---|---|
| 00 guía y checklist | pasos, costos y lista de control | https://t90171457413.p.clickup-attachments.com/t90171457413/a1815918-75bc-58b8-bd27-0d6e30c23b29/00_Guia_y_checklist_ASTRA_LEGAL_TECH_SAS_v3.docx?view=open | c92addd18ec6c7f6 |
| 01 instrumento constitutivo | modelo oficial de la IGPJ completado sólo en sus campos | https://t90171457413.p.clickup-attachments.com/t90171457413/5a0e7793-7d72-538d-91f7-f9bbe5fbbd0a/01_Instrumento_Constitutivo_ASTRA_LEGAL_TECH_SAS_modelo_oficial_IGPJ.docx?view=open | 93a12b4520a51a02 |
| 02 edicto | Anexo IV, con el objeto completo | https://t90171457413.p.clickup-attachments.com/t90171457413/ada89330-ce85-5494-973b-ac6adaba422b/02_Edicto_ASTRA_LEGAL_TECH_SAS_modelo_Anexo_IV.docx?view=open | 98e5d67d122f4504 |
| 03 aceptación del cargo | la suplente no es socia, por eso va aparte | https://t90171457413.p.clickup-attachments.com/t90171457413/239edc75-9275-5479-8c1f-ef7c469be002/03_Aceptacion_cargo_administradora_suplente.docx?view=open | 60b46bd166dc8cab |
| 04 DDJJ PEP de Abraham | Anexo V | https://t90171457413.p.clickup-attachments.com/t90171457413/166f6df6-7cd8-5a6d-9c2d-856f24d3ca08/04_DDJJ_PEP_Jorge_Abraham_Mendieta.docx?view=open | b73ad34ac63518c0 |
| 05 DDJJ PEP de la suplente | Anexo V | https://t90171457413.p.clickup-attachments.com/t90171457413/9ce744d8-ec5d-5102-bfb2-3bb5e7e719c2/05_DDJJ_PEP_administradora_suplente.docx?view=open | 503c070abad34de6 |

## Campos elegidos

- Denominación: ASTRA LEGAL TECH S.A.S. (el modelo editable usa "S.A.S.", no "SASU").
- Plazo: 99 años desde la constitución, como dice el modelo.
- Objeto: a) tecnología jurídica (legal tech), sin asesoramiento ni patrocinio jurídico; b) inteligencia artificial; c) a h) software, ciberseguridad, servicios informáticos, capacitación, exportación y propiedad intelectual.
- Capital: $800.000 en 800.000 acciones ordinarias nominativas no endosables de $1. Alcanza aunque se presente en noviembre (mínimo legal $782.400 en octubre y $797.600 desde el 1-nov).
- Integración: 25% ($200.000), acreditado con comprobante de depósito bancario.
- Cierre de ejercicio: 31 de diciembre. Tribunales: [Salta], a ajustar si la sede está en otro distrito.
- Administrador titular y autorizado: Jorge Abraham Mendieta. Suplente: su hermana, con nota de aceptación del cargo aparte.
- Datos personales, sede y fechas: en corchetes resaltados; los completa Abraham.

## Pasos

1. Reservar el nombre en la IGPJ: 20 UT = $2.400, vale 30 días.
2. Completar los corchetes de los documentos 01 a 05. No tocar el resto del texto: es el modelo oficial y habilita la vía de 24 h.
3. Firma digital (gratis, turno con biometría): instrumento (Abraham) y aceptación del cargo (hermana).
4. DDJJ PEP: una por administrador, por duplicado, con firma certificada por escribano. Es el único paso con escribano.
5. Depositar el 25% ($200.000) y guardar el comprobante. Constancias de CUIL de los dos.
6. Rentas: impuesto al acto 1,2% = $9.600; inscripción 0,3% = $2.400. Mínimo de cada uno: 20 UT = $2.400 (UT = $120, RG DGR 01/2026).
7. Cargar todo en el Portal de Autogestión de la IGPJ. Retirar el edicto firmado por la IGPJ y publicarlo un día en el Boletín Oficial.
8. Con la inscripción: CUIT de la SAS, cuenta bancaria, Ingresos Brutos y alta como exportador de servicios. Comunicar la inscripción a la UNO (cláusula "Sociedad en formación" del convenio, ver `03-convenio-uno.md`) y recién ahí otorgar el poder (`02-poder-especial-bolivia.md`).

Gastos medidos: $14.400 (reserva + sellos + tasa). Sin medir: dos certificaciones de firma, el edicto y la cuenta bancaria. El depósito del 25% es capital, no gasto.

El convenio con la UNO no espera a la SAS (cambio del 16-oct): lo firma Abraham por sí y en nombre de la sociedad en formación.

## Verificación del paquete (instrumento que podía dar rojo)

- Fuentes: Instrumento Constitutivo Tipo.docx de personasjuridicas.salta.gob.ar (sha256 e37399b999a494de, 31 párrafos, texto normalizado sha256 5bf6186a08548be1); Anexos IV y V de la Res. IGPJ 28/2019 (PDF sha256 d29c8bcc1fc968d1); requisitos en personasjuridicas.salta.gob.ar/sas.html (sha256 20740057f169c7cc).
- Copia del modelo: 31/31 párrafos con el mismo sha256 normalizado que el original leído en brain-env.
- Edicto base sha256 8d49df8bb95d y DDJJ base 1d34db2fc6f7: iguales al PDF.
- Cada reemplazo exige count == 1: si un campo no existe o se repite, el build falla.
- Segmentos fijos del modelo presentes: 43/52. Los 9 faltantes son campos elegidos o la cláusula de socio persona jurídica, que no aplica a una unipersonal.
- Restos de instrucciones del modelo: 0. Edicto: objeto completo, ratio 0,99 contra el artículo tercero (la v2 tenía 0,14). DDJJ PEP: 10/10 segmentos fijos del Anexo V.

## NO VERIFICADO

- Si la IGPJ acepta la DDJJ PEP con firma digital en lugar de certificación notarial.
- El formulario de solicitud (Anexo II): no está publicado; probablemente lo genera el Portal de Autogestión.
- El costo de las certificaciones, del edicto y de la cuenta; el plazo real de inscripción.
- W-01: el paquete lo armó BRAIN, que también hizo la auditoría. Re-auditoría pendiente (SOL o ASTRA).
