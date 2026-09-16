# Tarija: dolores judiciales y estado del arte para Custos Legis

Fecha de consulta: 2026-09-16, America/Buenos_Aires. Exploración documental, no estudio de mercado validado ni prueba de competidores.

## Mi conclusión

Hay problemas reales, pero no un mercado vacío. No posicionaría Custos como otro chat de derecho boliviano ni como una solución a la falta de jueces. La hipótesis que probaría es un asistente operativo del bufete: convertir documentos y notificaciones autorizadas en próximos pasos verificables, con responsables, plazos revisados y evidencia de aprobación. Esa oportunidad todavía no está validada con compradores.

## El dolor comprobable y el que todavía supongo

[El Periódico de Tarija, 21-jul-2026](https://elperiodico.com.bo/tarija-tiene-75-jueces-y-precisa-unos-150-para-adecuada-administracion-de-justicia/) recoge declaraciones de la decana del TSJ: unos 75 jueces y necesidad estimada de 150 a 200, con suspensiones de funcionarios y largos desplazamientos para acceder a justicia. Son declaraciones atribuidas, no un censo auditado por mí. No sumé las republicaciones como fuentes independientes.

[Una nota del 23-jul, republicada por eju.tv desde El País](https://eju.tv/2026/07/retardacion-de-justicia-en-tarija-programan-juicios-para-el-2027/) informa juicios programados para noviembre de 2027 y centralización de salas penales en la capital. No equivale al tiempo promedio de todos los procesos de Tarija.

**Custos no puede crear jueces ni garantizar fechas de audiencia.** Podría reducir trabajo administrativo evitable alrededor de cada proceso, pero no medí cuántas horas pierde hoy un abogado consultando portales, reorganizando documentos o informando al cliente. Tampoco encontré evidencia suficiente para afirmar una tasa local de plazos perdidos. Esas son hipótesis para entrevistas y observación, no hechos que se deducen de la mora judicial.

## Una corrección importante a nuestro contexto

El contexto del repo se apoyaba en el piloto SIGC de Chuquisaca. La [Rendición Pública de Cuentas Inicial 2026 del TSJ](https://tsj.bo/wp-content/uploads/2026/05/RPC-INICIAL2026-web.pdf), en el informe de la magistrada de Tarija, dice literalmente:

> en Tarija el Sistema Informático de Gestión de Causas entró en vigencia, en una primera etapa: delitos de acción privada, para digitalizar estas causas en materia penal.

El documento oficial fue localizado con búsqueda y su pasaje corroborado mediante búsqueda restringida al mismo PDF; la extracción general del PDF quedó truncada antes de ese apartado. No invento un número de página ni afirmo haber leído el informe entero.

Esto invalida describir el despliegue actual como limitado a Chuquisaca. **No demuestra que SIGC cubra todas las materias de Tarija ni que tenga una API disponible para terceros.** La futura compatibilidad no debería diseñarse exclusivamente alrededor de SIREJ. No modifiqué el contexto viejo en esta exploración.

Ya existe también [notificación electrónica oficial](https://www.gob.bo/tramites/notificacion-electronica-del-organo-judicial), con Tarija y Yacuiba entre las oficinas listadas. El [Gestor Procesal del TSJ](https://tsj.bo/ogp/sistema-gestor-procesal/) anuncia seguimiento, presentación de memoriales y Ciudadanía Digital; su alcance TSJ no debe confundirse con cada juzgado departamental. La prensa local [documenta socialización de ROMA en Tarija](https://elperiodico.com.bo/ecosistema-roma-llega-a-jueces-y-la-felcv-para-mayor-eficiencia-y-transparencia/) durante 2025. Son sistemas institucionales distintos, no sinónimos de un único expediente universal.

## Oferta comercial actual: investigar y redactar ya no distingue

Leí las páginas públicas de Pixi y LeyNova. Otros proveedores aparecieron en la búsqueda como candidatos para una prueba comparativa posterior.

- [Pixi Legal](https://www.pixilegal.com/) anuncia investigación boliviana, fuentes oficiales, normativa vigente a la fecha del caso y borradores. Sus cifras de documentos y usuarios son declaraciones comerciales, no mediciones mías.
- [LeyNova](https://leynova.com/) anuncia corpus boliviano, análisis de documentos, control de vigencia y fuentes verificadas; su FAQ publica precio profesional de lanzamiento de **Bs 50/mes** y estudiantil de **Bs 20/mes**. Verifiqué el precio anunciado, no una compra ni su sostenibilidad.
- [Lex AI](https://lexai.com.bo/) ofrece públicamente jurisprudencia boliviana, análisis de PDF/Word y memoriales con fuentes.
- [LEXIUS Bolivia](https://lexius.io/bo/) anuncia búsqueda jurídica, asistente, documentos y funciones de voz.

No probé sus respuestas, privacidad, disponibilidad de pago ni adopción en Tarija. No afirmo que sean superiores o inferiores a Custos. Tampoco que el precio de una herramienta de investigación determine el precio de gestionar un despacho.

**Consecuencia comercial:** «tiene IA, cita leyes y redacta memoriales» ya es una oferta existente. Custos necesitaría demostrar una mejora concreta del trabajo del bufete, no solamente más agentes o más documentos. No está demostrada una ventaja exclusiva en normativa tarijeña.

## Estado del arte técnico: recuperar fuentes no garantiza tener razón

La [evaluación preregistrada publicada en 2025 por investigadores de Stanford](https://law.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/) encontró errores de alucinación superiores al 17% en las herramientas jurídicas evaluadas de LexisNexis y Thomson Reuters, incluso con recuperación de documentos. Es evidencia sobre esas versiones, tareas y jurisdicción, **no una tasa de error de los proveedores bolivianos ni de sus versiones actuales**.

La distinción útil es entre existencia de una cita, fidelidad a su texto, relevancia para el caso y vigencia en la fecha aplicable. Un enlace o un hash solo no demuestran las cuatro. Las ofertas actuales ya prometen fuentes y control temporal; el diferencial defendible sería demostrar su desempeño con casos bolivianos corregidos por profesionales.

Para Custos, mi recomendación de ingeniería es separar cómputos deterministas de plazos, documentos fuente y redacción asistida; validar materia, calendario y procedencia; mostrar el pasaje que sostiene cada afirmación; y bloquear las acciones externas hasta una aprobación vigente del contenido exacto. Son recomendaciones, no funciones nuevas verificadas. La [auditoría técnica previa](https://app.clickup.com/90171457413/docs/2kza6fw5-11817) encontró justamente huecos en la integración y en controles que deberían sostener esas promesas.

## La prueba de negocio que haría antes de ampliar el producto

Propuesta, no trabajo iniciado: observar a cinco profesionales de Tarija con prácticas distintas y reconstruir su última semana con ejemplos anonimizados. Preguntar qué notificación recibieron, cómo registraron su siguiente acción, qué tuvieron que revisar de nuevo, qué herramienta usan y por qué pagarían cambiarla. Cinco entrevistas descubren problemas; no estiman todo el mercado.

Después probar un recorrido acotado: documento aportado por el abogado, extracción de datos, próximo paso, plazo con fuente y revisión, y constancia de aprobación. Usar datos sintéticos hasta resolver login, logs y aislamiento integrado. No depende de obtener acceso automatizado a todos los portales para empezar a validar utilidad.

Medir tiempo total incluyendo la verificación humana, errores y omisiones frente a una referencia profesional, uso repetido y voluntad de pagar un piloto. No elegir precio ni declarar demanda por intuición. Si la mayor carga es traslado o espera por falta de juzgados, reconocer que el producto no resuelve el dolor principal.

## Alcance y cierre

Fuentes públicas consultadas: prensa local, páginas oficiales, ofertas comerciales y una evaluación científica publicada. No hubo contacto con bufetes, altas, pagos, acceso a expedientes ni cambios de producto. El vínculo dolor -> función -> compra sigue siendo una hipótesis. No cambié prioridades ni autoricé integraciones a sistemas judiciales. Este archivo registra la investigación y la corrección documental detectada, no una aprobación técnica o comercial.
