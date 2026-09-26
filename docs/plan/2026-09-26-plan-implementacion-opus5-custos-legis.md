# Plan ejecutable para Opus 5: Custos Legis consume Corpus Tarija

Fecha: 2026-09-26 ART  
Repositorio objetivo: `gatehot59-star/custos-legis-tarija`  
Repositorio de conocimiento jurídico público: `gatehot59-star/corpus-legal-tarija`  
Regla de frontera: Custos consume Corpus por contrato HTTP; Corpus sigue siendo producto independiente.

## 0. Orden recibida

Implementar un vertical MVP trazable de Custos Legis para un bufete: crear una causa, cargar documentos, consultar el Corpus, producir resultados con citas verificables, calcular plazos con reglas deterministas, pedir revisión humana y exportar un recibo auditable.

**No implementar todavía:** seis agentes autónomos, scraping judicial, facturación, despliegue público, Qdrant, memoria vectorial de expedientes, envío automático de memoriales o una promesa de “predicción de resultado”.

El objetivo es que el producto exista y pueda probarse con diez casos, no construir una plataforma enorme que solo conversa consigo misma.

## 1. Reglas operativas para Opus 5

1. Leer antes de editar: `README.md`, `ESTADO.md`, `PENDIENTES.md`, `docs/`, PRs abiertos y ramas existentes.
2. No confiar en que la documentación coincide con el árbol: registrar el SHA exacto elegido como base.
3. No trabajar sobre `main`; crear una rama `titan/...` desde el SHA vigente.
4. No copiar código de repos externos. Extraer patrones clean-room y respetar licencias.
5. No enviar documentos del bufete al Corpus público ni a logs, CI o artefactos.
6. Ningún agente puede saltar tenant, caso, grupo, colección o revisión humana.
7. El LLM no calcula plazos, importes ni permisos: esos resultados salen de código determinista.
8. Una cita con formato correcto no es una cita verificada. Debe existir, devolver texto y respaldar la afirmación.
9. Ante fuente insuficiente, conflicto o vigencia no medida: `INSUFICIENTE` o `REVISIÓN_HUMANA`, nunca completar por memoria.
10. Cada cambio debe tener tests que puedan fallar, evidencia cruda y un cierre commiteado.

## 2. Arquitectura mínima

```text
HTTP/API
  -> autenticación + tenant + autorización de matter
  -> Job idempotente por client_message_id
  -> Router determinista
       |-- pregunta sobre documentos privados
       |-- búsqueda jurídica en Corpus
       |-- cálculo de plazo/regla
       |-- redacción pendiente de revisión
  -> retrieval mínimo autorizado
  -> ClaimSet estructurado
  -> validación de citas y vigencia
  -> ReviewGate
  -> respuesta/exportación + AuditReceipt
```

### Componentes obligatorios

- `Matter`: bufete, cliente, jurisdicción, materia, estado y nivel de riesgo.
- `Document`: original, hash, MIME, tamaño, extracción, versión y retención.
- `SourceEvidence`: `source_id`, colección, UID, versión, fuente, pinpoint, quote y fecha de consulta.
- `Claim`: afirmación atómica, evidencia, estado `supported/partial/unsupported`, vigencia y revisión requerida.
- `Job`: estado durable, etapa, progreso, error sanitizado, reintentos y `client_message_id` único.
- `ReviewGate`: quién revisa, qué debe revisar, decisión, fecha y evidencia de decisión.
- `AuditReceipt`: hash de entrada, versión del Corpus, modelo, prompt versionado, herramientas, tokens, latencia, citas y resultado.

## 3. Fases y entregables

### Fase 0: inventario y base reproducible

**Entregables:** `docs/agents/BASELINE-...md`, SHA base, árbol real, matriz de ramas/PRs, entorno de ejecución, contrato de configuración y plan de rollback.

**Criterios:** se puede clonar la rama limpia, instalar dependencias fijadas, ejecutar una prueba mínima y saber qué es código real, rama experimental o solo documentación.

**No avanzar** si el SHA base o la frontera Corpus/Custos quedan ambiguos.

### Fase 1: contrato del vertical MVP

Crear contratos tipados de entrada/salida antes de la implementación:

- `POST /matters`
- `POST /matters/{id}/documents`
- `POST /matters/{id}/jobs` con `client_message_id`
- `GET /jobs/{id}`
- `GET /matters/{id}/evidence`
- `POST /reviews/{id}/decision`
- `GET /audit/{run_id}`

Cada respuesta debe declarar `status`, `version`, `warnings`, `citations` y `review_required`. Los errores no deben revelar existencia de otro tenant, documento o usuario.

**Fixtures:** diez casos jurídicos ficticios/anónimos, separados del ajuste, con fuentes esperadas, artículos, fechas, permiso esperado y resultado humano.

### Fase 2: persistencia y aislamiento

Implementar primero tenant, matter, documentos, jobs y auditoría. RLS o equivalente debe aplicarse en cada lectura y escritura. Los documentos privados y el Corpus compartido deben tener rutas/identidades separadas.

**Falsadores mínimos:** tenant A no lee B; usuario sin asignación no lee matter; reintento no duplica job; documento retirado deja de recuperarse; job cancelado no publica salida tardía.

### Fase 3: adaptador estable de Corpus

Consumir exclusivamente el contrato HTTP del Corpus. El adaptador debe:

- timeout explícito;
- reintentos limitados solo para fallos transitorios;
- respuesta vacía diferenciada de error;
- versión/SHA del Corpus en cada resultado;
- `source_id`, UID, versión, URL y pinpoint preservados;
- no inventar resultados;
- cachear solo por versión y consulta autorizada;
- devolver `SOURCE_UNAVAILABLE` o `INSUFFICIENT_EVIDENCE` cuando corresponda.

Probar fuente no disponible, 401/403, 404, 429, 503, JSON inválido, versión inesperada y resultado contradictorio.

### Fase 4: fast path de bajo consumo

Sin LLM en la primera respuesta cuando alcanza:

1. clasificar materia/jurisdicción con reglas;
2. buscar por BM25/FTS y filtros;
3. extraer pasajes y metadatos;
4. calcular plazo con el motor existente;
5. construir `ClaimSet` con citas;
6. validar existencia y round-trip.

Agregar un SLM local solo para clasificación/extracción JSON/tool routing. No permitirle decidir vigencia, autoridad, privacidad o resultado jurídico final.

**Presupuesto inicial externo:** máximo 8 llamadas LLM, 12 herramientas, 2 reintentos, una escalada y tiempo límite configurable. Si se excede, detener y dejar recibo.

### Fase 5: grounding y auditoría por afirmación

Implementar el patrón L-MARS/Lawgent sin copiar código:

- dividir respuesta en claims atómicos;
- validar que cada cita exista;
- hacer round-trip del quote contra el pasaje;
- comprobar que la cita respalde la proposición;
- marcar `partial` si solo respalda una parte;
- eliminar o corregir una cita fallida una sola vez;
- si sigue fallando, abstenerse;
- mostrar al abogado qué fue verificado y qué no.

### Fase 6: reglas compilables y plazos

Encapsular plazos, feriados, suspensión, materia y excepciones en una representación versionada. Cada regla debe tener fuente, artículo, vigencia, fixture positivo y falsador negativo.

El LLM solo extrae hechos candidatos: fecha de notificación, materia y acto. El motor determinista decide el vencimiento. Si falta un dato crítico, no calcula.

### Fase 7: revisión humana y redacción

La redacción de memorial, estrategia, recomendación, envío o conclusión de alto riesgo debe crear `ReviewGate` y quedar bloqueada hasta decisión humana.

La salida debe separar:

- hechos recibidos;
- normas/citas verificadas;
- inferencias del sistema;
- incertidumbres;
- propuesta editable;
- decisión del abogado.

Nunca usar “probabilidad de ganar” como producto MVP.

### Fase 8: prueba punta a punta

Correr diez casos separados del ajuste:

- cinco preguntas de Corpus;
- dos cálculos de plazo;
- una contradicción entre fuentes;
- una consulta sin evidencia suficiente;
- una redacción que exige revisión.

Medir: recall de fuente primaria, claims soportados, citas correctas, vigencia, abstención, fugas cross-tenant, tokens, latencia p50/p95, reintentos y errores severos.

### Fase 9: operación y entrega

Solo después de la suite verde:

- Docker no-root;
- CI reproducible;
- health/readiness;
- logs sin PII ni texto jurídico completo;
- backup y restore probado;
- runbook de Corpus caído, job atascado, fuente retirada y revocación de usuario;
- staging separado de la VM del Corpus, salvo medición explícita que pruebe que no degrada.

## 4. Gates de aceptación

No declarar MVP verde hasta cumplir todos:

- aislamiento de dos tenants y dos usuarios;
- 10/10 casos ejecutados con evidencia cruda;
- 0 citas `unsupported` presentadas como soportadas;
- 0 acceso a documento no autorizado;
- 0 cálculo de plazo delegado al LLM;
- jobs idempotentes y reanudables;
- salida `INSUFICIENTE` reproducible;
- revisión humana obligatoria en alto riesgo;
- versión del Corpus, modelo y prompt registrados;
- presupuesto de tokens medido por caso;
- CI ejecuta falsadores positivos y negativos;
- restore a destino nuevo probado;
- no hay secretos, PII ni expedientes en Git/CI/artifacts.

## 5. Orden de prioridad

1. Contrato + fixtures + baseline.
2. Tenant/matter/document/job/audit.
3. Adaptador Corpus estable.
4. Fast path determinista y citas.
5. Plazos fuera del LLM.
6. ReviewGate y redacción.
7. SLM/router local.
8. Escalamiento al modelo grande.
9. Benchmark de diez casos.
10. Deploy separado y documentación.

Este orden prioriza que Custos exista sobre la maquinaria de agentes. Si una tarea no acerca al vertical a completar una causa de punta a punta, queda fuera del primer incremento.

## 6. Reglas de ingeniería inversa

Estudiar Lawgent, Case Closed, L-MARS, PAKTON, LegalAgentBench, DACL y MARVEL como patrones. No copiar cuerpos de código, prompts, datasets ni assets sin revisar licencia y atribución. Reimplementar contratos y tests propios en Custos.

## 7. Entrega exigida a Opus 5

Opus debe entregar en su rama:

- código completo, no pseudocódigo;
- migraciones y configuración;
- fixtures y banco de falsadores;
- tests unitarios, integración, seguridad y E2E;
- workflow CI;
- README de arranque;
- `docs/agents/evidencia/*.json` con salida cruda;
- `docs/agents/respuestas/*.md` con veredicto separado;
- PR con SHA, límites y deuda técnica;
- no merge, deploy ni credenciales reales sin autorización humana.

## Cierre TITAN

Modo: TITAN FULL.  
Acción delicada: no, plan/documentación.  
Criterio rector: implementar Custos Legis, que consume Corpus Tarija; no convertir Corpus en módulo de Custos ni mezclar expedientes privados con el corpus público.  
Resultado esperado: un vertical MVP trazable, barato y verificable antes de construir la plataforma completa.
