# Astra Legal Tech SAS - paquete v3 sobre el modelo oficial de la IGPJ (16-oct-2026)

Corrige los rojos A1 a A4 de `docs/auditorias/2026-10-15-01-auditoria-paquete-sas-astra.md` (main `29b65aa`). Reemplaza al paquete v2: no firmar ni presentar la v2.

Fuentes:
- Modelo de instrumento: personasjuridicas.salta.gob.ar/assets/files/Instrumento Constitutivo Tipo.docx (sha256 e37399b999a494de..., 31 parrafos, texto normalizado sha256 5bf6186a08548be1).
- Edicto: Anexo IV de la Res. IGPJ 28/2019 (PDF sha256 d29c8bcc1fc968d1...).
- DDJJ PEP: Anexo V de la misma resolucion.
- Requisitos: personasjuridicas.salta.gob.ar/sas.html (sha256 20740057f169c7cc...).

## Verificacion (instrumento que podia dar rojo)

- Copia del modelo al sandbox: 31/31 parrafos con el mismo sha256 normalizado que el original leido en brain-env.
- Edicto base: sha256 8d49df8bb95d, igual al PDF. DDJJ base: 1d34db2fc6f7, igual al PDF.
- Cada reemplazo exige count == 1: si el campo no existe o se repite, el build falla.
- Segmentos fijos del modelo presentes en el instrumento completado: 43/52. Los 9 faltantes son campos elegidos o la clausula de socio persona juridica, que no aplica a una unipersonal: "bajo el numero", "con sede social", "representada por el Sr", "quien/es resuelve/n", "(pesos en letras)", "(cantidad en letras)", "EI/los socios suscriben", el inciso (b) y el parentesis "(no suprimir esta oracion)" (la oracion queda).
- Frases fijas usadas por la auditoria: 10/11. Falta "articulo 299 de la Ley General de Sociedades", que vive en la clausula de socio persona juridica.
- Restos de instrucciones del modelo (Aclaracion, ACLARACION, Completar antes, no suprimir, socias/os, quien/es): 0.
- Edicto: objeto transcripto completo, ratio 0,99 contra el articulo tercero (la v2 tenia 0,14).
- DDJJ PEP: 10/10 segmentos fijos del Anexo V.

## Campos elegidos

- Denominacion ASTRA LEGAL TECH S.A.S. (el modelo editable usa "S.A.S.", no "SASU").
- Plazo 99 anos desde la constitucion.
- Objeto: incisos a) a h) de la v2 (legal tech sin asesoramiento juridico, IA, software, ciberseguridad, servicios informaticos, capacitacion, exportacion, propiedad intelectual).
- Capital $800.000 en 800.000 acciones ordinarias nominativas no endosables de $1.
- Integracion del 25% acreditada con comprobante de deposito bancario.
- Cierre de ejercicio 31-dic. Tribunales: [Salta], a ajustar si la sede esta en otro distrito.
- Titular y autorizado: Jorge Abraham Mendieta. Suplente: la hermana; como no es socia, va una nota de aceptacion del cargo aparte (aclaracion del modelo).
- Datos personales, sede y fechas quedan en corchetes resaltados para que los complete Abraham.

## Archivos (adjuntos de ClickUp; no se commitean binarios)

| Archivo | URL | sha256 (16) |
|---|---|---|
| 00 guia y checklist | https://t90171457413.p.clickup-attachments.com/t90171457413/a1815918-75bc-58b8-bd27-0d6e30c23b29/00_Guia_y_checklist_ASTRA_LEGAL_TECH_SAS_v3.docx?view=open | c92addd18ec6c7f6 |
| 01 instrumento (modelo oficial) | https://t90171457413.p.clickup-attachments.com/t90171457413/5a0e7793-7d72-538d-91f7-f9bbe5fbbd0a/01_Instrumento_Constitutivo_ASTRA_LEGAL_TECH_SAS_modelo_oficial_IGPJ.docx?view=open | 93a12b4520a51a02 |
| 02 edicto (Anexo IV) | https://t90171457413.p.clickup-attachments.com/t90171457413/ada89330-ce85-5494-973b-ac6adaba422b/02_Edicto_ASTRA_LEGAL_TECH_SAS_modelo_Anexo_IV.docx?view=open | 98e5d67d122f4504 |
| 03 aceptacion del cargo de la suplente | https://t90171457413.p.clickup-attachments.com/t90171457413/239edc75-9275-5479-8c1f-ef7c469be002/03_Aceptacion_cargo_administradora_suplente.docx?view=open | 60b46bd166dc8cab |
| 04 DDJJ PEP Abraham | https://t90171457413.p.clickup-attachments.com/t90171457413/166f6df6-7cd8-5a6d-9c2d-856f24d3ca08/04_DDJJ_PEP_Jorge_Abraham_Mendieta.docx?view=open | b73ad34ac63518c0 |
| 05 DDJJ PEP suplente | https://t90171457413.p.clickup-attachments.com/t90171457413/9ce744d8-ec5d-5102-bfb2-3bb5e7e719c2/05_DDJJ_PEP_administradora_suplente.docx?view=open | 503c070abad34de6 |
| resumen general v2 | https://t90171457413.p.clickup-attachments.com/t90171457413/ba465a88-37fe-5cc7-a5c3-96f312a9ad3d/astra-legal-tech-resumen-2026-10-16-v2.md?view=open | |

## Requisitos y costos

- Reserva de nombre: 20 UT = $2.400, vale 30 dias (numero de tramite finalizado, art. 9 b).
- Instrumento y aceptacion: firma digital (gratis, turno con biometria).
- DDJJ PEP: una por administrador, por duplicado, certificada por escribano (sas.html). Unico paso con escribano.
- Acreditacion del 25% ($200.000): comprobante de deposito bancario.
- Constancias de CUIL de ambos.
- Rentas: impuesto al acto 1,2% = $9.600; inscripcion 0,3% = $2.400 (minimos 20 UT = $2.400; UT $120).
- Edicto: lo entrega firmado la IGPJ y se publica un dia en el Boletin Oficial.
- Medido: $14.400. Sin medir: dos certificaciones, edicto, cuenta bancaria.

## NO VERIFICADO

- Si la IGPJ acepta la DDJJ PEP con firma digital en lugar de certificacion notarial.
- Formulario de Solicitud (Anexo II, art. 9 a): no esta publicado en el PDF; probablemente lo genera el Portal de Autogestion.
- Costo de certificaciones, edicto y cuenta; plazo real.
- W-01: este paquete lo arma BRAIN, que tambien hizo la auditoria. Re-auditoria pendiente (SOL o ASTRA).
