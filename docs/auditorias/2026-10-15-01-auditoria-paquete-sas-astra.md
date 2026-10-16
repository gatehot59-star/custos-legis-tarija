# Auditoría 2026-10-15-01 · Paquete SAS de Astra Legal Tech y todo lo tratado desde que se generó

**Pedido de Abraham (15-oct, 23:39 ART):** «audita todo lo tratado desde los documentos generados para crear la SAS».

**Auditor:** BRAIN con la skill AUDITOR-DE-BRAIN. **Conflicto W-01 declarado:** audito trabajo mío. Lo mitigué en parte con un verificador independiente (agente a4, otra instancia, sólo fuentes primarias) y con instrumentos nuevos sobre los artefactos reales, no sobre mis recibos. Igual corresponde que SOL o ASTRA re-audite A1 a A4.

**Alcance:** desde «Ahora crea la saas en salta» (15-oct 21:03 ART) hasta las estimaciones del chat (23:30 ART). El poder entra sólo por el resumen. La evaluación previa del plan queda fuera, salvo donde el paquete depende de ella.

**Sujeto auditado (medido, no leído de recibos):**

| Artefacto | Identidad |
|---|---|
| Rama `docs/2026-10-15-plan-salta-yacuiba` | head `fa265ff`, 12 commits sobre main `b37fce3d`, 0 detrás, **sin PR** |
| Paquete SAS v2 ([DOCX adjunto](https://t90171457413.p.clickup-attachments.com/t90171457413/54ca6d51-8495-5a07-a093-d2279cf68095/Astra_Legal_Tech_SAS_paquete_constitucion.docx?view=open)) | sha256 `b9536376e9e2151b…` |
| Convenio v2 ([DOCX adjunto](https://t90171457413.p.clickup-attachments.com/t90171457413/28714a4b-16c2-52c8-961b-79f802af8cb7/Convenio_UNO_Astra_Legal_Tech_v2.docx?view=open)) | sha256 `6c9584fe19e480d0…` |
| Resumen ([.md adjunto](https://t90171457413.p.clickup-attachments.com/t90171457413/dd7700eb-fc6b-54a8-840c-60a860040467/astra-legal-tech-resumen-2026-10-15.md?view=open), 197 líneas) | sha256 `04f805ea0c24481c…` |
| Docs | [SAS](https://app.clickup.com/90171457413/docs/2kza6fw5-23297) · [convenio](https://app.clickup.com/90171457413/docs/2kza6fw5-23357) · [poder](https://app.clickup.com/90171457413/docs/2kza6fw5-23277) · [plan](https://app.clickup.com/90171457413/docs/2kza6fw5-23257) |

Evidencia cruda: [`2026-10-15-01-evidencia-paquete-sas-astra.txt`](2026-10-15-01-evidencia-paquete-sas-astra.txt).

---

## Veredicto

**ROJO. El paquete para la IGPJ no sirve tal como está para lo que promete: ni entra por la vía de 24 h ni sale sin escribano.** No hay que firmar ni pagar nada con el DOCX actual.

1. **El estatuto no es el modelo oficial y la nota pide igual la vía abreviada.** El DOCX contiene **0 de 11** frases fijas del Anexo III. El modelo editable que publica la IGPJ ([`Instrumento Constitutivo Tipo.docx`](https://personasjuridicas.salta.gob.ar/assets/files/Instrumento%20Constitutivo%20Tipo.docx)) contiene **11 de 11**, igual que el [PDF de la Res. 28/2019](https://personasjuridicas.salta.gob.ar/assets/files/ANEXO%20RESOLUCI%C3%93N%2028-2019%20PERSONAS%20JURIDICA.pdf): el instrumento sí podía dar verde. La Res. 28/2019, art. 8, da el trámite exprés sólo «siempre que el solicitante utilice el modelo tipo de instrumento constitutivo, y el modelo de edicto», y el Anexo III avisa: «Los restantes campos no pueden ser modificados». El edicto tampoco cumple el Anexo IV: resume el objeto en 278 caracteres de 1.921, cuando el modelo pide «Transcribir íntegramente el objeto social». El Doc sabía que había que «pasar el estatuto al modelo del Anexo III»; el DOCX, que es lo que se firma, perdió ese paso.
2. **«Sin escribano» es falso según la [página de la propia IGPJ](https://personasjuridicas.salta.gob.ar/sas.html).** La DDJJ PEP tiene [formulario oficial](https://personasjuridicas.salta.gob.ar/assets/files/DECLARACION%20JURADA%20%20PEP%20UIF.docx) y «se requerirá una DDJJ por cada administrador, certificada por escribano público»: son dos, la de Abraham y la de su hermana. El checklist del DOCX, además, omite dos requisitos de esa página: la acreditación del 25% del capital (constancia de depósito bancario, acta notarial o certificación contable) y las constancias de CUIL o CDI.
3. **SENAPI: había una ASTRA real y el informe dijo que no.** La gaceta 61 terminó de procesarse a las 00:57:55Z, 7 segundos antes del commit `11f4946`. Contiene **ASTRA BY KROMASOL** (publicación 262560, solicitud 201376-2025, titular de México, servicios de agricultura, horticultura y silvicultura). El Doc, escrito 12 minutos después, dice «la 61 quedó sin procesar» y que todas las ASTRA eran fragmentos. No es software, así que no bloquea la marca, pero el informe era falso cuando se escribió.

**Lo que se sostiene:** Ley 27.349 (arts. 34, 37, 40, 41, 46 y 50), capital de $800.000 con 25% integrado, sellado de 1,2% + 0,3% con mínimos de 20 UT ($2.400 cada uno), INPI con 0 coincidencias y control positivo, convenio v2 con fechas del 9-nov al 4-dic, los 11 links de git del resumen y el bloque de método en los 12 commits.

---

## Afirmaciones auditadas

| # | Afirmación (dónde) | Instrumento que citó | ¿Podía dar rojo por eso? | Re-verificación | Veredicto |
|---|---|---|---|---|---|
| A1 | «Vía abreviada 24 h: modelo tipo Anexo III y edicto Anexo IV» ([git `paquete.md` L9](https://github.com/gatehot59-star/custos-legis-tarija/blob/6a229851459bec1401510212fd77e452470f18bd/docs/legal/2026-10-15-sas-salta-paquete.md)); la nota del DOCX pide el «procedimiento abreviado» | lectura de la Res. 28/2019 | No: nunca se comparó el texto del estatuto con el modelo | 0/11 frases fijas en el DOCX; control positivo 11/11 (modelo oficial y PDF); edicto con el objeto al 14% | **REFUTADO** |
| A2 | «Firmar digitalmente instrumento, nota y DDJJ PEP. Así no hace falta certificar firmas ante escribano» (DOCX, paso 3; resumen §4) | sas.html (firma digital admitida) | Sí, y la misma página lo da rojo | DDJJ PEP «certificada por escribano público», una por administrador | **REFUTADO** para las DDJJ; CONFIRMADO para el instrumento |
| A3 | «Gastos inevitables: sellado y edicto» ([Doc SAS](https://app.clickup.com/90171457413/docs/2kza6fw5-23297); resumen §4) | sas.html + aranceles | Sí | faltan reserva de nombre (20 UT = $2.400, a4), 2 certificaciones PEP y la acreditación del 25% | **REFUTADO** (3 de 6 gastos omitidos) |
| A4 | Checklist final del DOCX (10 ítems) como paquete completo | sas.html | Sí | faltan el requisito 3 (acreditación del 25%) y el 4 (CUIL o CDI); la DDJJ PEP tiene formulario oficial | **REFUTADO** (incompleto) |
| A5 | Capital $800.000 ≥ 2 SMVM ($782.400 oct / $797.600 nov), 25% = $200.000 | Res. 4/2026 y arts. 40-41 | Sí | a4 contra fuentes primarias | **CONFIRMADO** |
| A6 | Sellos 1,2% + tasa 0,3%, mínimos de 20 UT; «valor de la UT no verificado» | aranceles IGPJ | Sí | UT $120 (RG DGR 01/2026, a4): $9.600 + $2.400 = $12.000; sas.html confirma las dos tasas | **CONFIRMADO** (el NO VERIFICADO ya se puede cerrar) |
| A7 | Ley 27.349 arts. 34, 37, 46 y 50 (unipersonal, edicto de 1 día, acciones escriturales, suplente obligatorio) | texto legal | Sí | a4 | **CONFIRMADO** (pero «escriturales» rompe el modelo, ver A1) |
| A8 | Firma Digital Remota sin costo, con validación presencial | «se cree», NO VERIFICADO | (no se midió) | a4: gratis, con turno y biometría en una Autoridad de Registro | **CONFIRMADO** |
| A9 | Objeto v2 con legal tech «sin asesoramiento jurídico» e IA | DOCX v2 | Sí | el DOCX v2 lo tiene (incisos a y b, y edicto); el cuerpo del [Doc SAS](https://app.clickup.com/90171457413/docs/2kza6fw5-23297) sigue con el objeto y el edicto v1, sólo una nota avisa | DOCX **CONFIRMADO**; Doc **desactualizado** |
| A10 | «La IA es actividad promovida por la Ley 27.506» | Ley 27.506 | Sí | art. 2, inc. i (a4) | **CONFIRMADO** |
| A11 | Res. UIF 11/2011 (a4: derogada, hoy 35/2023 modificada por 192/2024) | (no aplica) | (no aplica) | 0 citas en nuestros artefactos; la cita vieja es de sas.html | **sin rojo para nosotros** |
| B1 | INPI: «Astra Legal Tech da 0: libre» (resumen §5; [índice git](https://github.com/gatehot59-star/custos-legis-tarija/blob/fa265ff570e479f3350ad6e34c50798cac8c1551/docs/agents/respuestas/2026-10-15-04-resumen-astra-legal-tech.md) L9) | GrillaMarcasAvanzada «contiene» + control META GAMING = 5 actas | Sí para coincidencia de texto; no para similitud fonética, oposición por ASTRA (cl. 35) o ASTRASEC (cl. 42), ni renovaciones | método y control releidos | **0 coincidencias: CONFIRMADO · «libre»: NO MEDIDO** (K-02) |
| B2 | SENAPI 63 a 70: ASTRA LEGAL TECH = 0, LEGAL TECH = 0, las 9 ASTRA son fragmentos | scan.py (pypdf) | Sí | res.json: RASTRAS x2, HANSASTRASSE, FASTRACK x3, EPIGASTRALGIA, ELASTRADOR, CASTRACIÓN | **CONFIRMADO** |
| B3 | «La 62 falló por timeout» | scan.py | Sí | res.json: URLError timeout | **CONFIRMADO** |
| B4 | «La 61 quedó sin procesar» ([Doc SAS](https://app.clickup.com/90171457413/docs/2kza6fw5-23297), 22:10 ART) | ninguno: no se releyó res.json | (no se midió) | 61 procesada a las 00:57:55Z: ASTRA BY KROMASOL, publicación 262560 | **REFUTADO** (canal sin leer, W-01) |
| B5 | «Unas 6.800 menciones de MARCA» en 63 a 70 | scan.py | Sí | res.json suma 7.119 (las 3.391 páginas sí cierran) | **REFUTADO** (menor) |
| B6 | Control SENAPI: «encontró FASTRACK» | scan.py | Sí | prueba que los nombres de signo están en el texto, pero se eligió después de ver el resultado | **CONFIRMADO, control débil** |
| C1 | Convenio v2: piloto 9-nov al 4-dic, informe 7 al 18-dic, cierre antes del 23-dic, cláusula CUARTA de ajuste | DOCX v2 | Sí | python-docx sobre el adjunto | **CONFIRMADO** (ojo: el informe docente cae sobre los finales inferidos, 7 al 20-dic) |
| C2 | Estado vigente del convenio en Docs y git | (ninguno) | (no se midió) | título del [Doc convenio](https://app.clickup.com/90171457413/docs/2kza6fw5-23357): «3 al 27 de noviembre» y su primer link «para imprimir» es la v1; [git `convenio-uno-astra.md`](https://github.com/gatehot59-star/custos-legis-tarija/blob/fa265ff570e479f3350ad6e34c50798cac8c1551/docs/legal/2026-10-15-convenio-uno-astra.md) L11 «ejecucion 3-27 nov» y L14 «Always On antes del 3-nov»; tabla del [plan](https://app.clickup.com/90171457413/docs/2kza6fw5-23257); link del resumen | **REFUTADO como estado vigente** (documento que no se enteró) |
| C3 | «6.2 b) La EMPRESA garantizará la disponibilidad del servicio durante la ejecución» | ninguno | (no se midió) | la única medición (14-oct) es la VM apagada 148 h; Always On sin activar | **NO MEDIDO** (promesa contractual sin instrumento) |
| C4 | Calendario 1/2026 por OCR | tesseract en la VM | Sí | no lo re-corrí; el OCR crudo no está commiteado | **NO MEDIDO** por esta auditoría (W-01) |
| C5 | 2/2026 no publicado; mismo link para todas las sedes | JS de uno.edu.bo | Sí | la única opción extra de Yacuiba es «Test UNO» | **CONFIRMADO** |
| D1 | Poder: «[Razón social] S.A.S.» ([Doc poder](https://app.clickup.com/90171457413/docs/2kza6fw5-23277)) | (ninguno) | (no se midió) | el placeholder sigue aunque el nombre ya está elegido | **desactualizado** (menor) |
| D2 | Apostilla de La Haya entre Argentina y Bolivia; Colegio de Escribanos de Salta o Cancillería por TAD | (redacción) | Sí | a4: Bolivia adhirió en 2017, vigente desde el 7-05-2018 | **CONFIRMADO** |
| E1 | «USD 50 a 70 = Bs 350 a 490, más del doble que Lex AI (Bs 200)» (chat) | cuenta propia | Sí | 348 / 200 = 1,74 veces a USD 50 | **REFUTADO** para la mitad baja del rango |
| E2 | «Lex AI es lo más caro del mercado boliviano» (chat) | Doc del 14-oct | No: vLex no publica precio (a4) | (no se pudo) | **NO MEDIDO** (B-01) |
| E3 | Bruto a 6 meses ≈ USD 4.300 (chat) | cuenta propia | Sí | 808 + 1.560 + 1.200 + 718 = 4.286 | aritmética **CONFIRMADA**; supuestos NO MEDIDOS (0 inscripciones de abogados al 14-oct) |
| E4 | Neto USD 2.500 a 3.000 (chat) | cuenta propia | Sí | no descuenta Always On (~288 créditos por día), que el propio plan declara obligatorio | **REFUTADO** (omisión; precio del crédito NO MEDIDO) |
| E5 | 150 a 300 alumnos en los dos últimos años (chat) | categorías Moodle 2-2026 (22 grupos x 15 a 30) | No: son grupos, no alumnos; los 8 semestres no están verificados | (no se pudo) | **NO MEDIDO** (proxy) |
| E6 | Memoria: «Astra Legal Tech S.A.S. ... en constitución desde 15-oct-2026» | (ninguno) | (no se midió) | no se presentó nada, ni la reserva de nombre | **REFUTADO** (menor): es «a constituir» |
| F1 | Git + Doc por entrega | (regla) | Sí | 11 archivos en la rama y 4 Docs; el resumen completo vive sólo como adjunto, en git hay un índice de 14 líneas | **parcial** |
| F2 | Trabajo integrado | (regla) | Sí | rama 12 commits adelante, sin PR, nada en main | **pendiente sin dueño** |
| F3 | Cierre de turno en el pizarrón | (regla) | Sí | última línea de brain en `reportes`: id 117 (05:18Z del 15-oct); ninguna del trabajo SAS | **REFUTADO** |
| F4 | Commits con bloque de método | (regla) | Sí | 12 de 12 | **CONFIRMADO** |

---

## ¿Qué NO se midió, que importaba?

1. **Si la UNO firma con una SAS extranjera y qué papeles le pide (O-01).** Todo el paquete existe para firmar con la UNO, y nadie le preguntó. Es el falsador más barato del plan (un correo a la vicerrectora de Yacuiba) y en la lista de pendientes está después de reservar el nombre, sacar firmas y presentar la SAS. Si la UNO pide algo que la SAS no tiene, o no firma con extranjeros, la plata ya se gastó.
2. **Si el estatuto pasaba el control de la IGPJ.** Compararlo contra el modelo editable que la IGPJ publica lleva un minuto y da 0 de 11. Nadie bajó ese archivo.
3. **El costo real de la ruta mínima.** De seis gastos (reserva $2.400, sellos $9.600, tasa $2.400, edicto, 2 certificaciones PEP y acreditación del 25%) se sumaron tres.
4. **La disponibilidad que el convenio promete.** No hay monitor de la VM, Always On sigue sin activar y lo que corre en la VM (`c0e44af3`) no está en ninguna rama (diagnóstico del 14-oct).

## Cazado sin encontrar

- binarios en git: 0 (los 11 archivos son .md);
- links de git del resumen rotos: 0 de 11 (`git cat-file -e` en un clon fresco);
- commits sin bloque de método: 0 de 12 (M-03);
- mensajes sin leer en el pizarrón durante el turno: 0 (el último es el 250, del 7-oct);
- citas a Res. UIF 11/2011 en nuestros artefactos: 0;
- errores aritméticos en capital, 25%, sellos, páginas SENAPI, conversión de Bs 3.375 a USD 485 / 233 y bruto de 4.286: 0.

## Lo que esta auditoría NO pudo auditar

- el OCR del calendario 1/2026 (no lo re-corrí);
- las renovaciones INPI: la grilla de renovaciones sólo filtra por fecha y el POST devolvió no-JSON hasta en el control;
- la similitud fonética (INPI) y las marcas SENAPI anteriores a 2026;
- si la IGPJ acepta firma digital en la DDJJ PEP en lugar de la certificación;
- si una unipersonal debe denominarse «SASU» (el modelo lo menciona, la ley no lo exige);
- el costo del edicto, de las certificaciones y de la acreditación del 25%;
- el precio del crédito de Abacus;
- la investigación de mercado previa al paquete (fuera de alcance).

## Qué tiene que corregir BRAIN (no el auditor)

1. Rehacer el instrumento sobre el `Instrumento Constitutivo Tipo.docx` oficial: completar sólo los campos, con el objeto libre (legal tech e IA) y acciones nominativas no endosables. El edicto, según el Anexo IV y con el objeto completo.
2. Checklist: DDJJ PEP en el formulario oficial con certificación notarial (2), acreditación del 25%, constancias de CUIL y reserva de nombre ($2.400).
3. SENAPI: agregar la gaceta 61 (ASTRA BY KROMASOL), corregir a 7.119 menciones y reintentar la 62.
4. Docs y git vencidos: Doc convenio (título y link v1), `convenio-uno-astra.md`, tabla del plan, Doc SAS (objeto v1, paso a paso con escribano, UT), poder (razón social) y resumen («libre», «sin escribano», «gastos inevitables», link del 3 al 27).
5. Abrir PR de la rama para que deje de ser un pendiente sin dueño.
6. Memoria: «en constitución» pasa a «a constituir; nada presentado».
7. Pedir a SOL o ASTRA que re-audite A1 a A4 desde una instancia nueva (W-01).

## Lo que decide Abraham

- No firmar ni pagar nada con el DOCX actual.
- Primero el correo a la UNO o primero la SAS. Recomendación: el correo, esta semana, antes de pagar la reserva.
- Autorizar a BRAIN a rehacer el paquete sobre el modelo oficial.

---

## Método

```
--- METODO TITAN ---
Accion delicada: NO (auditoria; nada presentado, firmado ni enviado)
Modo aplicado:   AUDITOR-DE-BRAIN
Conflicto:       W-01, BRAIN audita trabajo propio; mitigado en parte con a4 (fuentes primarias)
                 e instrumentos nuevos sobre los artefactos reales
Instrumentos:    python-docx sobre los DOCX adjuntos (sandbox ClickUp Brain)
                 git clone + cat-file + ls-tree en clon fresco (brain-env)
                 descarga de sas.html, Instrumento Constitutivo Tipo.docx, DECLARACION JURADA PEP UIF.docx
                 y PDF de la Res. 28/2019 (brain-env); control positivo 11/11 sobre el modelo oficial
                 res.json crudo de SENAPI y mtimes (brain-env)
                 nexus.db por el servicio sqlite (mensajes, reportes)
Maquinas:        sandbox ClickUp Brain + brain-env
```

**Rúbrica de la auditoría (100 puntos, umbral 70): 73, pasa raspando.**

| Criterio | Puntos | Por qué |
|---|---|---|
| Completitud | 18/25 | paquete SAS (DOCX, Doc y git), marcas, convenio, calendario, resumen, chat y proceso; no re-corrí el OCR, las renovaciones INPI, el conteo de alumnos ni el mercado |
| Razonamiento | 21/25 | cada rojo con un instrumento que podía dar verde (control 11/11) o con fuente primaria literal; separé la regla correcta del paquete que no la cumple |
| Documentación | 20/25 | evidencia cruda en el archivo hermano; la del OCR no existe |
| Proceso | 14/25 | W-01: me audito a mí; a4 es independiente en fuentes pero lo lancé yo; no hubo segundo auditor |
