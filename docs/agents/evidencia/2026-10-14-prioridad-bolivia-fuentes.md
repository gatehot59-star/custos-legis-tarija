# Fuentes y alcance: prioridad comercial para Bolivia

Consulta: 2026-10-14. [Síntesis](../respuestas/2026-10-14-prioridad-bolivia-corpus-custos.md). [Doc](https://app.clickup.com/90171457413/docs/2kza6fw5-22617).

## Naturaleza de la evidencia

Lecturas de repositorios, código, documentos y páginas oficiales, y consulta del estado del formulario. Las citas son extractos, no copias completas ni capturas de transacciones. No se ejecutó producto, ensayo con abogados ni auditoría jurídica. No se guardaron datos personales de participantes.

## E1. Custos: código actual frente a documentación vieja

Main consultado: b37fce3d968b6b40f42e2b5c81de669bf333a950, merge del MVP persistente fechado 2026-09-28.

Código leído: https://github.com/gatehot59-star/custos-legis-tarija/blob/b37fce3d968b6b40f42e2b5c81de669bf333a950/backend/mvp_server.py

El archivo extiende el handler autenticado, delega las rutas /mvp/ a MVPHTTPState, exige DATABASE_URL_APP y verifica conexión PostgreSQL antes de arrancar. La lectura demuestra implementación, no que el servidor esté actualmente desplegado o sea apto para clientes.

También se leyeron README.md, ESTADO.md y docs/agents/RETOMAR-CUSTOS-LEGIS.md del mismo commit. Contienen datos fechados el 10 y 26 de septiembre y afirmaciones ya superadas, como cero código en el README. No se repitieron como estado actual.

PR consultado en listado abierto: https://github.com/gatehot59-star/custos-legis-tarija/pull/18
Head: b377a2df94d2fd9a0d82c8ba7c0b6e1094bf33eb.
Doc leído: https://app.clickup.com/90171457413/docs/2kza6fw5-15817/2kza6fw5-18197

El Doc dice: "el contrato real de autenticación del Corpus sigue `NO MEDIDO` hasta que el Corpus lo publique". Distingue el conector configurable de una integración real. Lista despliegue y uso por abogado entre pendientes. Estos son datos documentales del 28 de septiembre, no un test repetido hoy.

## E2. Corpus y frontera de productos

Main consultado: c273c659ee90f2259f540cb14c576d6a16dcfb40, fechado 2026-09-23.
Repo: https://github.com/gatehot59-star/corpus-legal-tarija

Se listaron raíz, docs y docs/agents, se leyó README y se revisaron PRs abiertos para no tratar ramas como producto integrado. El README describe pipeline de fuentes públicas, procedencia y exclusión de documentos privados; sus cifras están fechadas al 3 de septiembre. No se usaron como cobertura actual medida.

El README de Custos y RETOMAR fijan productos independientes y dependencia de Custos hacia Corpus. La recomendación mantiene esa frontera; no la modifica.

## E3. Convocatoria y precio tentativo propios

Doc leído: https://app.clickup.com/90171457413/docs/2kza6fw5-16017/2kza6fw5-18377
Título: Dossier Corpus Tarija: invitación al grupo pionero de abogados.

Propuesta: ocho cupos, al menos cinco de Tarija y de uno a tres de Yacuiba, acceso privado gratuito de 48 horas. Incluye tareas de búsqueda, lectura, cita y feedback. Prohíbe cargar expedientes confidenciales y credenciales judiciales.

Extracto: "La referencia inicial es US$10 mensuales o su equivalente en bolivianos; el precio final y las condiciones se confirmarán por escrito antes de cobrar."

Se leyó también corpus-tarija-presentacion-abogados-pioneros.pdf, enlazado en https://app.clickup.com/90171457413/chat/r/2kza6fw5-5157/t/80170046873506. Contiene la misma propuesta; es material de invitación, no resultados del piloto.

## E4. Estado actual del formulario

Formulario: https://app.clickup.com/90171457413/v/fm/2kza6fw5-15977
URL pública de inscripción: https://forms.clickup.com/90171457413/f/2kza6fw5-15977/A9PQZH9NYFWHTCYLDE
Nombre devuelto: Inscripción piloto Corpus Tarija · 8 cupos.

Campos relevantes devueltos por la consulta:

- deleted: false
- formSettings.active: true
- formResultCount: 0

Interpretación limitada: cero envíos por ese formulario al consultar. No prueba que no existan contactos, usuarios o acuerdos fuera de él; no es contabilidad de ventas. No se cambió el formulario ni se añadieron participantes.

## E5. Pixi Legal

URL leída: https://www.pixilegal.com/planes
Título: Planes y precios — Pixi Legal.

Extractos: "Pixi Lector"; "Bs. 20/mes"; "No incluido: Consultas al asistente IA".

La página publica buscador, texto completo y PDF para ese plan. Hay otra enumeración de funciones con IA, pero el precio de ese otro plan no quedó identificado en el contenido extraído; no se le asigna Bs20. Precio publicado no equivale a venta verificada.

## E6. LeyNova

URL leída: https://leynova.com/

Extracto: "Bs 50/mes profesional o Bs 20/mes para estudiantes con correo institucional".

La página presenta el precio como lanzamiento y ofrece consultas con fuentes y análisis de documentos. Sus conteos de normas, fallos, precisión y comparaciones de modelos son afirmaciones propias que no auditamos. No se usan como prueba de superioridad sobre Corpus.

## E7. RuleX

URL leída: https://rulex.org/bolivia
Título: La IA jurídica para abogados en Bolivia.
Fecha que declara la página: 2026-09-01; lectura realizada 2026-10-14.

Extracto: "Pro sale 119 BOB al mes, 595 BOB el semestre y 1.070 BOB el año, con una semana de prueba."

Publicita memoriales Word, expedientes, plazos y vigilancia SIREJ. Es evidencia de competencia por la propuesta, no de que esas funciones se hayan probado. No se adoptan sus afirmaciones jurídicas sobre firma, calendarios o secreto profesional como dictamen propio.

## Lo que no se midió

No hay test comparativo de plataformas, un recuento de abogados compradores, datos de ingresos, costos o retención. No se recorrieron todos los negocios posibles de Bolivia. Tres compras, el piloto y el orden de despliegue son criterios propuestos, no resultados.

Esta evidencia respalda priorizar una prueba comercial de la suite existente. No habilita a declarar rentable, listo o superior al producto.
