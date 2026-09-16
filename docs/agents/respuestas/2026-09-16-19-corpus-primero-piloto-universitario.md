# Corpus primero: piloto cerrado en dos universidades, no esperar la biblioteca perfecta

2026-09-16. Recomendación de auditor-sol a Abraham; **no es una decisión ejecutada de pausar, desplegar ni contactar**.

[Doc público: diagnóstico y propuesta completa](https://app.clickup.com/90171457413/docs/2kza6fw5-12377).

## 1. Pedido

Explicar en criollo qué se logró, en qué estado están Custos y el corpus, y si conviene culminar el corpus para un piloto en al menos dos universidades con sugerencias y errores recogidos dentro del producto.

## 2. Veredicto en criollo

**Sí: priorizaría una versión segura y acotada del corpus para un piloto cerrado en dos universidades. No intentaría terminar toda la cobertura jurídica antes de probarlo.** Custos tiene un núcleo técnico probado, no una solución profesional completa acreditada. El corpus tiene valor propio para humanos, agentes y plataformas; es más directo ponerlo a prueba sin esperar a Custos.

Durante el piloto dejaría Custos en mantenimiento acotado de defectos críticos. Es una recomendación, no un cambio de prioridades aplicado. No usaría el tiempo en más agentes, infraestructura o miles de documentos antes de medir utilidad con personas.

## 3. Custos: qué se logró y qué no

La conversación reprodujo fallos de autenticación, aprobación/rechazo, límites por caso, registro de consultas y fecha penal. Se corrigió producto y se construyeron regresiones. Hubo trabajo de Brain y de este ejecutor: no atribuyo todos los cambios a una sola mano.

La evidencia más reciente es concreta: **24/24 contratos HTTP pasaron con el mismo verificador fijado y el mismo candidato en PostgreSQL17.11 y PostgreSQL16.15**. API por entrypoint real y proceso separado, base real, login real, sin sesiones inyectadas ni imports de tests/recibos del candidato. Se probó separación de tenants, permisos sobre casos y aprobaciones, rechazo que revoca, fecha del contrato sintético y logout. El control siempre-200 fue rechazado.

Eso reduce incertidumbre sobre esas funciones. No acredita el recorrido profesional completo desde la notificación judicial hasta un memorial revisado, todos los plazos legales, usabilidad, demanda, carga, recuperación de backups o despliegue. No equivale a producto listo ni a aislamiento frente a un candidato malicioso con el mismo uid.

El README y `docs/agents/CONTEXTO-CUSTOS-LEGIS.md` siguen diciendo «cero código»: **están desactualizados**, contradichos por la ejecución. El Doc seleccionado de auditoría parcial también tiene evidencia posterior que supera su estado original. Esta respuesta no actualizó esos archivos ni tocó PRs.

## 4. Corpus: activo propio, preparación del piloto todavía no acreditada

Hay pipeline reproducible, OCR con manejo explícito de citas ambiguas, búsqueda, fuentes, cola de revisión e interfaz reutilizable para agentes. **No es solo PDFs ni una dependencia interna de Custos.** Los 6.079 documentos citados por el repositorio corresponden al snapshot del 9-sep; no se recontó hoy la colección.

Los pendientes de calidad afectan fecha, título, clasificación, cobertura y vigencia desconocida. La revisión reciente de fuentes documentó también hashes ausentes o incompletos aceptados en un recorrido, ambigüedad hash PDF/texto y enlaces que pueden acabar en una página general. Parte de las mejoras está en el PR1, confirmado abierto sin merge en esta consulta. No atribuyo automáticamente ese código a main ni al despliegue.

La exposición de nombres en causas sensibles fue real y motivó cierre público. Informes posteriores documentan autenticación y backend en loopback. **Una contraseña no anonimiza el corpus ni convierte toda su colección en material adecuado para compartir con estudiantes.** No medí hoy el servicio vivo ni revisé de nuevo toda la colección.

El pendiente de contraseña administrativa expuesta de Gitea **ya figura rotado el16-sep** con controles positivo/negativo en git. Leí esa medición; no ejecuté otra rotación. El mismo informe conserva sesiones web NO MEDIDO y una superficie SSH pendiente de revisión. No repito como actual el Doc viejo que la declaraba todavía viva.

## 5. Qué significa culminar una versión piloto

No existe un corpus terminado para siempre. Sí puede existir una **versión identificable con alcance honesto, verificable y seguro**. Antes de circular el enlace:

1. Colección revisada y apropiada para compartir. Si no está validada la anonimización de jurisprudencia sensible, excluirla del piloto. Revisar que la selección siga sirviendo a las tareas docentes. Ni dar por pública toda la colección porque viene del Estado ni asumir que toda norma está libre de datos personales.
2. Mostrar fuente exacta, fecha cuando esté verificada, límites del OCR y vigencia desconocida. Sin fabricar vigencia ni presentar un enlace general como si acreditara el documento exacto.
3. Identificar revisión desplegada y verificar rutas reales, autenticación, posibilidad de revocar acceso, recuperación de backup y límites de uso. No una clave compartida sin control entre estudiantes.
4. Feedback operativo con responsable, estados y tratamiento privado. No un formulario abandonado ni reportes sensibles en repos públicos.
5. Acordar con docentes alcance, evaluación, datos mínimos recogidos, retención y contacto para problemas. Piloto experimental de investigación documental, no asesoramiento jurídico ni garantía de cobertura total.

## 6. Diseño propuesto para las dos universidades

**Un corpus y una versión común, dos grupos institucionales distinguibles.** No duplicaría bases por defecto. Acceso y feedback por grupo no significan incorporar expedientes ni multi-tenancy de bufetes al corpus público. Si un acuerdo institucional exige aislamiento adicional, evaluarlo antes de desplegar.

Propuesta, no compromiso ya acordado: cuatro semanas, un docente responsable y10-15 participantes por universidad. Algunas tareas comunes con respuestas esperadas revisadas por docentes y otras búsquedas libres. Una primera sesión pequeña en cada institución, corregir bloqueantes y recién ampliar. Elegir dos equipos que realmente se comprometan a usarlo, idealmente con perfiles distintos, no solo dos nombres prestigiosos.

Medir tiempo hasta encontrar y verificar la fuente frente al método habitual, éxito de la tarea, errores materiales de cita/OCR, búsquedas sin resultado, retorno de participantes y cierre de reportes. **No registrar texto completo de búsquedas jurídicas por defecto.** Informar la instrumentación y usar datos mínimos para la evaluación.

Acordar umbrales antes, como propuesta inicial: cero incidentes críticos de privacidad abiertos; cero errores materiales pendientes en las tareas evaluadas; al menos80% de tareas resueltas con fuente verificable; mejora de tiempo frente al método habitual. No son mediciones logradas ni garantía estadística. Anotar tamaño de muestra y no confundir una muestra revisada con toda la colección.

Sumar al menos dos abogados o docentes en ejercicio para tareas reales no confidenciales. **Que lo usen estudiantes no demuestra que un bufete pagaría.** La vía agentes/plataformas requiere después una prueba de integración propia: el piloto académico no valida por sí solo todos los mercados.

No se eligieron, contactaron ni comprometieron universidades.

## 7. Feedback dentro del corpus: sí, con devolución

En resultados/documentos: «Reportar un problema». En búsqueda vacía: «No encontré lo que buscaba». En menú: «Sugerir mejora» y, si hay cuenta, «Mis reportes».

Guardar ID de reporte, versión del corpus, documento/pasaje si aplica, categoría, descripción y estado. Contacto opcional o el acordado para cuentas del piloto; institución para analizar grupos, no para exponer participantes. No copiar búsquedas automáticamente, no pedir expedientes ni pruebas sensibles. Contexto de búsqueda adicional solo mediante elección informada.

Categorías: OCR, cita/enlace incorrecto, fecha/título, posible vigencia errónea, documento faltante, problema de uso, privacidad, sugerencia. Estados: recibido, en revisión, corregido o descartado con motivo. Responsable asignado y revisión diaria de privacidad/bloqueantes, semanal de sugerencias, como compromiso que debe acordarse antes de abrir.

Un reporte no reescribe la fuente: revisión humana y rastro de corrección. Para privacidad, política de retirada preventiva de la vista del piloto mientras se evalúa, preservando original y evidencia. Los reportes no deben publicarse automáticamente en git ni en issues públicos. La interfaz vive dentro del corpus; eso no obliga a guardar los datos de participantes en el repo o dataset público.

Inspeccioné por menciones `sistema/api/servidor.py`, `sistema/api/esquema.sql` y `sistema/web/index.html` de main y no encontré un circuito explícito de feedback. **Es una búsqueda lexical limitada, no prueba estructural de inexistencia.** La cola de revisión documental existente tampoco demuestra un circuito de reportes de usuarios. PR y servicio vivo no se auditaron para esta función.

## 8. Herramientas y máquina

Lectura directa de archivos y metadatos de GitHub por conexión autorizada y por urllib en brain-env, más lectura de Docs ClickUp. Sin OCR nuevo, benchmark, carga, tests nuevos de producto ni cambios de servicio. Escrituras: este archivo y Doc público. No contacto externo ni cambios de prioridades o despliegue. TITAN LIGERO, rúbrica N/A para esta síntesis.

## 9. Qué se midió y evidencia cruda

La prueba HTTP ya fue ejecutada y publicada en el turno anterior. No presento lectura de un recibo como nueva ejecución. Archivo crudo íntegro con igualdad byte a byte comprobada previamente:

[Resultados PostgreSQL16](https://github.com/gatehot59-star/custos-legis-tarija/blob/c35fb90472492fee65280ad69b38b4b95cbb076d/docs/auditorias/2026-09-16-18-http-pg16/resultados.json)

Campos verbatim de ese resultado:

```json
"server_version_num": 160015
"http_exit": 0
"passed": 24
"failed": 0
"negative_exit": 1
"api_stopped": true
"pg_stop": 0
"pg_status": 3
"candidate_changed_files": []
```

Candidato `24e2490442e872498b61a8534dbfe714922fdf3e`; verificador SHA256 `516b5f4757ccc2eade0cee4a7f5875075f6dd281d12168bb111b8459f0e14939`. SHA256 de salida `ddf08b997e2b0ae607840a9f1d59dcffdd907a69cb02735b5d50e23fd740c475`.

Salida literal relevante de lecturas de este turno:

```text
HEAD corpus-legal-tarija 4259ba81df9b32aefc2c09a3aa595bb0b1c13b38
CONTEXT_PATHS []
PR corpus-legal-tarija 1 open False False 2360f27d43fdc9a1e2a74a3f6465698918df2ad1
LAST_FILES ['infra/2026-09-16-rotacion-gitea.md']
FEEDBACK_MENTIONS sistema/api/esquema.sql []
FEEDBACK_MENTIONS sistema/web/index.html []
```

El único match en servidor.py fue la sugerencia de usar la ruta de búsqueda en línea362, no un envío de feedback. Consulta usada para esa inspección: `re.search("feedback|sugerenc|reportar|incidencia", l, re.I)` sobre las líneas de esos tres archivos obtenidos de raw.githubusercontent.com. Limitación explícita: puede omitir implementaciones con otros nombres.

Custos main leído `c35fb90472492fee65280ad69b38b4b95cbb076d`. Contexto dice literalmente `**De este repo:** cero código, cero base, cero agente, cero cliente.` y su última actualización es fundación10-sep. Se contrasta con la ejecución16-sep, no se acepta como estado actual.

Una petición pública posterior para PRs de Custos alcanzó `HTTP Error 403: rate limit exceeded`. No se convirtió en conclusión sobre esos PRs. Lectura del inventario enlazado de mudh-mobile dio404: no hice afirmaciones de capacidad o imposibilidad a partir de ese enlace.

## 10. Fuentes examinadas

- [Reevaluación desde fuentes del corpus](https://github.com/gatehot59-star/corpus-legal-tarija/blob/4259ba81df9b32aefc2c09a3aa595bb0b1c13b38/mediciones/2026-09-16-ventaja-del-corpus-revaluada-desde-fuentes.md).
- [Separación de productos, documento histórico](https://github.com/gatehot59-star/corpus-legal-tarija/blob/4259ba81df9b32aefc2c09a3aa595bb0b1c13b38/SUITE-Y-CONSUMIDORES.md).
- [Cobertura con corrección de denominadores y fechas](https://github.com/gatehot59-star/corpus-legal-tarija/blob/4259ba81df9b32aefc2c09a3aa595bb0b1c13b38/COBERTURA.md).
- [Rotación Gitea16-sep con controles y pendientes](https://github.com/gatehot59-star/corpus-legal-tarija/blob/4259ba81df9b32aefc2c09a3aa595bb0b1c13b38/infra/2026-09-16-rotacion-gitea.md).
- [Sistema corpus, README histórico](https://github.com/gatehot59-star/corpus-legal-tarija/blob/4259ba81df9b32aefc2c09a3aa595bb0b1c13b38/sistema/README.md).
- [PR1 corpus](https://github.com/gatehot59-star/corpus-legal-tarija/pull/1).
- [Contexto Custos fundacional, desactualizado](https://github.com/gatehot59-star/custos-legis-tarija/blob/c35fb90472492fee65280ad69b38b4b95cbb076d/docs/agents/CONTEXTO-CUSTOS-LEGIS.md).
- [Informe HTTP PG16](https://app.clickup.com/90171457413/docs/2kza6fw5-12357).

## 11. Archivos generados

`docs/agents/respuestas/2026-09-16-19-corpus-primero-piloto-universitario.md` y [Doc público](https://app.clickup.com/90171457413/docs/2kza6fw5-12377), Space > Doc. No se modificó el contexto vivo: esta respuesta documenta una recomendación pendiente, no cambia el estado operativo.

## 12. NO MEDIDO

Servicio productivo del corpus hoy, comparación completa desplegado/main/PR, colección actual completa, anonimización integral, fidelidad jurídica completa, feedback en ramas o despliegue, demanda, instituciones disponibles, usuarios reales, métricas del piloto, costos y voluntad de pago. No se inventó un porcentaje de avance. No hubo nuevo test de Custos ni se implementó el feedback.
