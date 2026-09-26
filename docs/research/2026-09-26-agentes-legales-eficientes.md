# Investigación: agentes legales comparables y arquitectura eficiente para Custos Legis

Fecha: 2026-09-26 ART  
Sujeto interno: `gatehot59-star/custos-legis-tarija`, `main` en `60d6705d5c8b66952e7748d8b95f376cc3697db5`.  
Método: TITAN FULL, lectura viva de GitHub del repo propio y de repositorios externos, contraste con papers y separación explícita entre código verificable, claims autorreportados y propuestas.  
Acción: investigación y documentación únicamente. No se modificó `main`, no se desplegó, no se conectaron proveedores y no se copiaron archivos externos.

## Veredicto ejecutivo

**No conviene copiar un “agente legal” entero.** La mayoría son demos con LangChain/LangGraph y un prompt grande; Custos necesita algo más sobrio: intake de causa, aislamiento por bufete, corpus público/privado separado, plazos deterministas, citas verificadas y abogado aprobando antes de actuar.

La mejor arquitectura para Custos es una **cascada local y auditable**:

1. Reglas y retrieval deterministas primero.
2. Modelo pequeño local para clasificar, extraer y elegir herramientas.
3. Motor simbólico para plazos, fechas, importes, condiciones y procedimientos compilables.
4. Modelo mayor solo para conflictos, excepciones, hechos ambiguos o investigación multi-hop.
5. Auditoría de citas por afirmación antes de revelar el resultado.
6. Presupuesto duro de tokens, herramientas, reintentos y tiempo.
7. Revisión humana obligatoria para estrategia, memoriales, envío externo y resultados de alto riesgo.

El patrón más valioso no es “más agentes”: es **menos contexto, menos herramientas visibles y más verificaciones fuera del LLM**.

## Punto de partida real de Custos

El propio README y `ESTADO.md` dicen que el repositorio está en fase de fundación: no hay FastAPI productivo, grafo de agentes, frontend, Qdrant, facturación, despliegue ni cliente. Sí hay trabajo técnico verificable en privacidad, RLS, plazos y calendario: 176 aserciones verdes y 18 falsadores declarados por CI, pero la compuerta todavía no está cableada al buscador del Corpus.

El corpus es producto independiente y Custos lo consume. El corpus tiene 6.079 documentos, pero el estado interno de Custos advierte que 5.030 Autos Supremos quedan retenidos por privacidad y que solo el 17,3% de los documentos queda publicable según esa compuerta. Por eso Custos no puede diseñarse como “chat sobre todo el Corpus”: necesita política de acceso por bufete, materia, fuente y documento.

Fuente interna: [README de Custos](https://github.com/gatehot59-star/custos-legis-tarija/blob/main/README.md) y [estado medido](https://github.com/gatehot59-star/custos-legis-tarija/blob/main/ESTADO.md).

## Los candidatos que realmente vale la pena estudiar

### 1. Lawgent: mejor referencia integral

[Repositorio Lawgent](https://github.com/WenzhuoXu/lawgent) presenta el modelo más cercano a un producto serio: planner por complejidad, subagentes con contextos separados, packs por jurisdicción, conectores/MCP, RAG híbrido, memoria tipada, ejecuciones durables, ledger de tokens/coste y una capa separada de verificación de citas.

Lo que hay que tomar:

- Jurisdicción como filtro real del runtime, no como una frase del prompt.
- Skills versionadas por tarea: triage, revisión contractual, litigación, compliance, cite-check y drafting.
- `extract → validate → round-trip → support-check → repair/abstain` para las citas.
- “Pinpoint unavailable” antes que inventar artículo/página.
- Ledger por turno: modelo, tokens, herramientas, latencia y coste.
- Memoria tipada de proyecto: hechos, decisiones, tareas, riesgos, fuentes y preguntas abiertas.
- Run durable con artefactos, pausa y reanudación.

Lo que no hay que copiar sin reducción: Qdrant + embeddings grandes + múltiples conectores + frontend completo. Es demasiado para la VM actual de Custos y no resuelve primero el producto central.

### 2. Case Closed: mejor referencia de operación de causa

[Arquitectura backend de Case Closed](https://github.com/jasonpereira518/caseclosed/blob/main/BACKEND_ARCHITECTURE.md) modela `workspace → matter → documents → jobs → messages`, separa documentos privados de corpus jurídico compartido, crea trabajos asíncronos idempotentes y obliga a citar únicamente IDs presentes en el paquete de recuperación.

Lo que hay que tomar:

- `matter_id` y `workspace_id` en cada documento, chunk, job y mensaje.
- `client_message_id` para que reintentos del navegador no dupliquen trabajos.
- Respuesta 202 con job durable y estados `queued/running/succeeded/failed/cancelled`.
- Router separado para actualización de causa, pregunta grounded e investigación jurídica.
- Filtro de autorización antes de recuperar texto, no después.
- Si no queda una cita válida, devolver insuficiencia de evidencia, no una respuesta elegante.

Lo que no hay que copiar: dependencia completa de Clerk, Firestore, Cloud Tasks, Document AI, Vertex y Vector Search. Primero hay que demostrar el flujo con componentes mínimos y medibles.

### 3. L-MARS: mejor referencia de fidelidad de citas

[L-MARS](https://github.com/boqiny/L-MARS) separa Query, Search, Judge y Summary Agent. Su `VerifyAgent` divide la respuesta en afirmaciones atómicas y clasifica cada una como `supported`, `partially_supported`, `unsupported`, `citation_unreachable`, `no_citation` o `verifier_error`. `Faith-Search` re-busca una fuente o descarta la cita rota.

El README reporta, en su benchmark, que el loop de juez eleva strict citation F1 de 0,13 a 0,25, baja la ausencia de citas de 34% a 13% y reduce las citas inalcanzables por debajo de 1% con Faith-Search. Es evidencia del proyecto, no una garantía para Bolivia.

Esto debe entrar en Custos como contrato de salida:

```json
{
  "claim_id": "c-001",
  "text": "...",
  "source_id": "sha256:page:paragraph",
  "pinpoint": "articulo/pagina/parrafo",
  "valid_at": "fecha",
  "verification": "supported|partial|unsupported",
  "review_required": false
}
```

La separación crítica es: **la fuente existe** no significa **la fuente respalda la afirmación**.

### 4. PAKTON: mejor referencia para contratos largos

[PAKTON](https://github.com/petrosrapto/PAKTON) separa Archivist, Interrogator y Researcher, con RAG y evaluación de ContractNLI, LegalBenchRAG, GEVAL, preferencia humana y acuerdo estadístico. El proyecto es Apache-2.0 y advierte que el código publicado todavía no coincide por completo con la versión desplegada.

Lo que hay que tomar para Custos:

- Rol especializado de conservación/organización del documento.
- Pregunta jurídica separada de recuperación.
- Evaluar completitud y explicabilidad, no solo exactitud.
- Tener conjunto humano y juez automático, con acuerdo estadístico.

No usar PAKTON como fundamento de producción: es principalmente investigación de revisión contractual.

### 5. LegalAgentBench: benchmark, no producto

[LegalAgentBench](https://github.com/CSHaitao/LegalAgentBench) aporta 17 corpus, 37 herramientas, 300 tareas y `process rate` para medir pasos intermedios, no solamente la respuesta final. Es derecho chino, así que no se puede trasladar el dataset sin adaptación, pero sí el método.

Custos necesita su propio benchmark con:

- intake y conflicto;
- selección de jurisdicción;
- búsqueda de norma primaria;
- plazo por materia;
- vigencia temporal;
- contraste de jurisprudencia;
- redacción de memorial;
- abstención por fuente insuficiente;
- filtración de documentos privados;
- selección de herramienta y trayectoria.

## Qué hacer con los agentes de pocos recursos

### A. SLM/router primero

La línea más sensata es destilar tareas estrechas a un modelo local pequeño: clasificar materia, detectar jurisdicción, extraer artículos/fechas/partes, seleccionar herramienta, decidir si falta evidencia y producir JSON validado. No debe resolver solo una estrategia ni afirmar vigencia.

El trabajo [Ace-Attorney](https://github.com/disi-unibo-nlp/ace-attorney) muestra el patrón de profesor LLM → ejemplos sintéticos → estudiante SLM y un paradigma de recuperación selectiva. La cifra de “aproximadamente 1200% menos CO2” debe tratarse como claim del paper hasta replicar unidades y tablas; no convertirla en “12x más barato”.

### B. Compilar lo que no necesita creatividad

[Amortized Intelligence / DACL](https://aclanthology.org/2026.acl-industry.102.pdf) propone usar el LLM una vez para compilar cláusulas a un grafo tipado y ejecutar después con un motor determinista. Reporta 9,9x menos tokens y 26,8 s frente a aproximadamente 164 s en uno de sus escenarios.

Para Custos es ideal en:

- plazos procesales;
- vencimientos y prórrogas;
- multas e importes;
- requisitos acumulativos;
- secuencias de trámite;
- elegibilidad y condiciones.

El grafo debe tener hash de norma, artículo, vigencia, fuente y tests de contraejemplo. El problema residual es la extracción de hechos: un motor perfecto con hechos erróneos sigue dando una respuesta errónea.

### C. Cascada con escalamiento condicionado

[SATER](https://aclanthology.org/2025.emnlp-main.531.pdf) y [Vertical Routing](https://aclanthology.org/2026.tacl-1.104.pdf) respaldan no usar el modelo grande en todas las etapas. La idea aplicable es dividir:

1. jurisdicción;
2. recuperación;
3. extracción;
4. issue spotting;
5. excepciones;
6. aplicación de hechos;
7. validación de citas;
8. redacción.

El modelo grande solo entra en conflictos, novedad, excepciones y hechos ambiguos. Antes de escalar se comprueba cobertura de evidencia, no solo la autoconfianza del SLM.

### D. Herramientas visibles por categoría

[TinyAgent](https://github.com/SqueezeAILab/TinyAgent) y el patrón ToolRAG muestran que exponer todos los schemas de herramientas desperdicia tokens y empeora la selección. Custos debería recuperar primero una categoría y presentar solo 2 a 5 herramientas relevantes: `plazos`, `corpus`, `expediente`, `citas`, `redaccion`, `revision_humana`.

### E. Memoria direccionable, no resumen destructivo

Lawgent y trabajos como [ARC](https://arxiv.org/abs/2607.25066) apuntan a la misma solución: archivo append-only con evidencia verbatim, vista activa compacta y punteros recuperables. Nunca resumir destruyendo una cita, una excepción, una decisión humana o una condición de vigencia.

### F. Ruta rápida y DeepSearch separado

[MARVEL](https://github.com/Nikhil-Mukund/marvel) usa fast path para preguntas simples y DeepSearch para investigación compleja. La ruta profunda mejora cobertura, pero su latencia publicada es órdenes de magnitud mayor. En Custos debe activarse solo por conflicto, falta de cobertura, múltiples jurisdicciones o hechos distribuidos, y mostrar el coste/tiempo antes de ejecutarse si el usuario lo permite.

## Diseño objetivo para Custos

```text
INTAKE DETERMINISTA
  → tenant / matter / rol / jurisdicción / fecha de hechos / riesgo

ROUTER SLM LOCAL
  → tipo de tarea / herramientas permitidas / fast-path o escalamiento

FAST PATH
  → filtros de acceso
  → BM25 + búsqueda exacta
  → regla compilada o extracción
  → claim estructurado

ESCALAMIENTO
  → conflicto de fuentes / excepción / novedad / multi-hop
  → modelo mayor, con paquete mínimo de evidencia

GROUNDING
  → cada claim tiene source_id + pinpoint + vigencia
  → existencia + round-trip + soporte
  → reparar una vez o abstenerse

HUMAN GATE
  → estrategia, memorial, envío, conclusión de alto riesgo

AUDIT LOG
  → hashes, modelo, prompt versionado, herramientas, tokens, latencia,
    citas, decisiones y versión del Corpus
```

## Qué NO hacer

- No iniciar con seis agentes conversando entre sí.
- No exponer todo el Corpus y todo el expediente al prompt.
- No usar un modelo pequeño para decidir solo sobre prisión, violencia, familia, plazos perentorios o estrategia.
- No llamar “verificado” a un JSON que solo pasó validación sintáctica.
- No copiar código de un repo sin revisar licencia; Lawgent es MIT y PAKTON Apache-2.0, pero otros candidatos no quedaron con licencia confirmada.
- No montar PostgreSQL + Redis + Qdrant + workers en la VM compartida de 2 cores sin medir costo y degradación.
- No cargar un stack cloud pesado antes de demostrar un caso de uso con 10 casos representativos.

## Roadmap de ingeniería inversa clean-room

### Fase 0: benchmark y contrato, antes de agentes

Construir 10 a 20 casos bolivianos ficticios y públicos, separados del ajuste, con expected sources, artículos, fechas, permisos y decisión humana. Medir baseline manual y Corpus actual. Métricas: recall de fuente primaria, citas soportadas, vigencia, abstención, tokens, latencia y error severo.

### Fase 1: núcleo barato y determinista

Implementar solo contratos, no el grafo completo:

- `Matter`, `Document`, `SourceEvidence`, `Claim`, `Job`, `ReviewGate`;
- retrieval por BM25/FTS y filtros de tenant/jurisdicción;
- cálculo de plazos fuera del LLM;
- `client_message_id` idempotente;
- presupuesto externo de tokens/herramientas;
- log append-only con hashes.

### Fase 2: router y grounding

Agregar SLM local para clasificación/extracción/tool routing. Después, implementar auditoría por claim inspirada en L-MARS. Si no hay fuente primaria o la cita no soporta la proposición: `INSUFICIENTE`, no improvisación.

### Fase 3: motor compilado

Compilar plazos y reglas calculables a IR tipado versionado. Revisar cada regla y agregar falsadores. Esto es donde Custos puede ser más eficiente que una SaaS que quema tokens por repetir razonamiento.

### Fase 4: modelo grande solo donde paga

Añadir escalamiento para conflictos, excepciones y multi-hop. El modelo grande recibe solo evidencia mínima, no todo el expediente. Mantener un único intento de reparación por defecto.

### Fase 5: interfaz y operación

Jobs asíncronos idempotentes, estados observables, matter/workspace, uploads, exportación y revisión humana. Luego medir despliegue separado de la VM del Corpus.

## Scorecard TITAN

- Completitud de investigación: 14/15. Se revisó repo propio, candidatos principales, papers y patrones de eficiencia; no se hizo auditoría línea por línea de cada candidato.
- Ejecutabilidad: 12/15. Los repos reales fueron leídos por GitHub, pero no se clonaron ni ejecutaron en este turno.
- Seguridad: 14/15. Se priorizan aislamiento, citas, abstención, budgets, licencias y límites; no se ejecutó SAST de terceros.
- Testing: 12/15. Se propone benchmark propio y falsadores; no se ejecutó suite externa.
- Arquitectura: 10/10. La cascada y los contratos separan determinismo, SLM, modelo grande y humano.
- DevOps: N/A para este informe de investigación.
- Documentación: 10/10. Candidatos, enlaces, límites y roadmap durable.
- Innovación: 5/5. El diferencial recomendado es el motor compilado + cascada + grounding por claim.
- Proceso QA: 5/5. Claims de terceros separados de evidencia verificada y se conserva la limitación de no ejecutar repos externos.

Total aplicable: **82/90 = 91,1/100**. N/A: 10 puntos de DevOps porque no se hizo una entrega de infraestructura.

--- METODO TITAN ---
Accion delicada: NO; investigación y documentación, sin código de producto ni despliegue.
Modo aplicado: TITAN FULL.
Rúbrica: 82/90 -> 91,1/100.
N/A declarados: 10 puntos de DevOps; no se entregó infraestructura.
Review externo: dos investigadores independientes consultados; sus resultados se contrastaron con README y árboles de GitHub. No equivale a aprobación de producto.
Instrumento: GitHub MCP sobre repos vivos, búsqueda web y lectura de papers; evidencia citada en este archivo; no se ejecutaron repos externos.
Artefactos: este informe + Doc público de ClickUp.
