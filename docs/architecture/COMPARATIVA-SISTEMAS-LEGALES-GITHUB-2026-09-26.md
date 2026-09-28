# Custos Legis frente a sistemas legales open source

**Fecha:** 2026-09-26  
**Alcance:** contraste arquitectónico a partir de los README y documentos públicos de repositorios GitHub; no se ejecutaron esos sistemas ni se auditó su seguridad interna. La comparación sirve para decidir qué incorporar, no para declarar que otro proyecto está listo para producción.

## Veredicto en criollo

Custos Legis hoy no es un sistema de seis agentes. Es un **núcleo de seguridad y reglas**, con API HTTP, persistencia multi-tenant, compuerta de privacidad, cálculo de plazos y aprobación humana. Tiene **cero agentes implementados y cero agentes corriendo**.

El diseño futuro menciona seis agentes, pero el repositorio actual no contiene el grafo ni sus nombres. Por eso la afirmación correcta es: **seis previstos en el diseño, ninguno construido**. La parte más valiosa de Custos hoy no es la inteligencia generativa: es impedir que una fecha dudosa, un texto sensible o un escrito no aprobado salga como si fuera confiable.

## Estado actual de Custos Legis

### Sí existe y está verificado

- API HTTP con `ThreadingHTTPServer` stdlib, por defecto en loopback.
- Login por bufete, sesiones de 8 horas y PBKDF2-SHA256.
- PostgreSQL con `FORCE ROW LEVEL SECURITY` para usuarios, expedientes, documentos, checkpoints, corridas y aprobaciones.
- Expedientes y documentos privados; `texto_crudo` inmutable a nivel de trigger.
- Cliente HTTP del corpus independiente, con cadena de custodia, hash, fuente y tres estados de vigencia: `VIGENTE`, `DEROGADA`, `NO_MEDIDO`.
- Compuerta de privacidad fail-closed: jurisprudencia sin texto libre en la capa pública, reserva legal retenida y extractos solo con matrícula.
- Motor de plazos civil/penal con detalle día por día, advertencias y estado explícito.
- Gate HITL: aprobación por rol y matrícula, caso, tipo y SHA-256 exacto; el rechazo posterior revoca la aprobación anterior.
- Sensor de uso que guarda hash de consulta, no la consulta jurídica.
- 176 aserciones verdes y 18 falsadores según el estado medido del repositorio.

### No existe todavía

- Grafo LangGraph y seis agentes.
- Frontend o UI usable.
- FastAPI formal.
- Scraper judicial, Qdrant, Redis, Celery y facturación.
- Integración con SIREJ, SIGC, firma digital o envío al juzgado.
- Uso por un abogado real. Esto sigue en cero.

## Qué hace cada sistema comparable

| Sistema | Lo mejor que aporta | Qué no copiar sin más |
|---|---|---|
| [Judicex](https://github.com/JustVugg/judicex) | Separa memoria jurídica citable de memoria operativa; versiona fuentes oficiales; contrato de respuesta `grounded/limited/abstain/chat`; verifica citas y números; funciona local y sin LLM | Es alpha, local-first y sin multiusuario/RLS endurecido. Su SQLite sirve para privacidad local, no resuelve el SaaS multi-bufete de Custos |
| [Mike](https://github.com/open-legal-products/mike) | Producto completo: Next.js, Express, Supabase/Postgres, almacenamiento de objetos, biblioteca documental, workflows reutilizables, revisión tabular, Word add-in, conectores MCP y telemetría con lista blanca | Es una plataforma mucho más pesada. Sus conectores de escritura quedan desactivados si no hay confirmación humana; esa advertencia confirma que el gate HITL no puede ser un detalle de prompt |
| [Mike Workflows](https://github.com/open-legal-products/mike-workflows) | Workflows como datos versionados y portables, con packs, metadata y validación automática | No meter instrucciones gigantes dentro del código ni atar los workflows a un solo modelo/harness |
| [Taiwan Legal RAG](https://github.com/aa0101181514/tw-legal-rag) | Divide retrieval de generación; `allowed_citations`; marca candidatos no leídos; añade `case_history`; distingue búsqueda semántica, léxica y por número; incluye citation check y reglas explícitas de verificación | Su check es a nivel de bundle y no demuestra que la interpretación sea correcta. Además el corpus y el modelo están en un servicio externo, no bajo control del bufete |
| [AI Legal Agent](https://github.com/Paparusi/legal-ai-agent) | Muchas operaciones útiles de documento: leer, editar, comparar, revisar por lotes, historial, memoria de empresa, costos por proveedor, multi-LLM y administración multi-tenant | Su autonomía de edición y crawling es demasiado amplia para Custos antes de tener permisos, versionado, auditoría y aprobación por operación. Más features no equivale a más seguridad |
| [AI Regulatory Compliance Assistant](https://github.com/Ramseygithub/ai-legal-compliance-assistant) | Pipeline claro de ingestión, embeddings, grafo de entidades, RAG y análisis de cumplimiento | JSON/archivos locales y dependencias de proveedor; no es una arquitectura de expedientes privados ni de responsabilidad profesional |
| [LegalGraphRAG](https://github.com/XMUDeepLIT/LegalGraphRAG) | Enseña a medir retrieval/razonamiento con corpus, configuración reproducible y métricas de cargo, artículo y pena; usa grafo y varios modelos | Es un framework experimental de predicción penal, no un producto de bufete. No copiar el grafo antes de tener consultas reales y un benchmark de Tarija |
| [LawGlance](https://github.com/lawglance/lawglance) | Prototipo accesible de asistente legal RAG con Django, Chroma y CrewAI | Es justamente el riesgo que hay que evitar: chat RAG genérico no alcanza para vigencia, cadena de custodia, tenant ni responsabilidad del escrito |

## Innovaciones reales de Custos

### Lo que está muy bien

1. **Privacidad fail-closed por arquitectura.** No confía en detectar todos los nombres. Como el detector falló en 4 de 4 textos adversarios, la capa pública no expone texto libre jurisprudencial. Es una decisión bastante mejor que “anonimizar y rezar”.
2. **Aprobación sobre contenido exacto.** La matrícula no aprueba “una acción”; aprueba el SHA-256 de un contenido, para que el sistema no ejecute un borrador distinto. La última decisión manda.
3. **`NO_MEDIDO` como estado operativo.** En plazos y vigencia no rellena huecos con una fecha o un “vigente” inventado. Eso es raro y muy valioso en legal tech.
4. **RLS aplicado al estado sensible del futuro agente.** No protege solo `cases`: también cubre checkpoints, donde quedarían memoriales, documentos y estrategia. Es el sitio correcto para mirar.
5. **Frontera corpus/Custos.** Evita convertir un corpus público vendible en una base interna de un bufete.
6. **Sensor de uso sin guardar la estrategia jurídica.** Mide adopción con `q_hash`, no almacenando consultas en claro.

### Lo que todavía es una promesa, no una innovación usable

- Los seis agentes no existen.
- La UI no existe.
- La fecha calculada no es automáticamente una verdad jurídica: varias tablas de días por acto siguen sin confirmar.
- La compuerta vive en Custos, pero el corpus independiente todavía debe exponer el contrato autenticado que Custos consumirá.

## Contras y riesgos, sin maquillaje

- **Producto no usable por un abogado:** sin UI, sin piloto y sin caso real.
- **Cobertura estrecha:** el motor calcula solo civil y penal; familia, laboral, constitucional y otras materias devuelven `NO_MEDIDO`.
- **La compuerta retiene 82,7% del corpus medido:** solo 17,3% queda publicable como normativa. Si la aprobación documento por documento es incómoda, no es un borde: es el flujo principal.
- **Vigencia incompleta:** la ausencia de estado es frecuente en el corpus. El producto debe hacer visible esa limitación, no esconderla.
- **Operación aún frágil:** sesiones en memoria, sin rate limiting/TLS en este proceso, sin costo por caso medido y sin integración judicial.
- **Arquitectura prevista demasiado grande para el hardware medido:** Postgres + Redis + Qdrant + Celery + agentes en la VM de 2 núcleos del corpus es mala idea. La VM separada es la opción sensata.
- **Riesgo de sobreconstrucción:** el grafo de seis agentes puede repetir el error del corpus: mucha maquinaria, cero abogados usando el núcleo.

## Qué tomar, en orden

### P0: tomar ya de Judicex y Taiwan Legal RAG

- Contrato de respuesta estructurado por afirmación: cada afirmación lleva `claim`, fuente, fragmento, estado de vigencia y validación numérica.
- Estados explícitos `grounded`, `limited`, `abstain`, `chat`; si no hay soporte suficiente, no se redacta.
- Lista blanca `allowed_citations`, candidatos no leídos fuera de autoridad y `case_history` para no citar una decisión anulada como vigente.
- Verificación de números jurídicos: días, porcentajes, artículos y fechas no pasan solo porque el modelo los escribió.

### P1: tomar de Mike y Mike Workflows

- Workflows versionados como datos, no seis agentes rígidos en código.
- Packs por materia y jurisdicción, con schema y validación CI.
- Conectores separados, permisos por conexión y toda escritura externa en modo propuesta hasta que el abogado apruebe el contenido exacto.
- Observabilidad por lista blanca, excluyendo nombres de archivos, texto, queries, headers y credenciales.

### P2: tomar de LegalGraphRAG y compliance assistant, pero con freno

- Benchmark propio con 10 a 30 consultas reales de abogados de Tarija.
- Grafo jurídico solo para relaciones que mejoren una tarea medida: artículo, norma modificadora, derogación, precedente, órgano y materia.
- Comparar léxico/BM25 contra vectorial y graph retrieval. Para “Art. 252 CPC” la búsqueda exacta debe ganar; para “casos como este” puede ganar la semántica.
- Métricas separadas: recall de fuente, precisión de cita, vigencia, exactitud numérica, tiempo y costo.

### P3: tomar funcionalidad de AI Legal Agent después del piloto

- Comparación documental, historial de cambios, revisión por lotes y exportación DOCX.
- No permitir edición autónoma de un documento presentado: primero genera propuesta, luego diff, luego aprobación por hash, luego exporta.

## Arquitectura recomendada para la siguiente versión

No construir seis agentes todavía. Construir un **workflow verificable con tres roles lógicos**:

1. **Extractor determinista:** carga expediente, OCR, hechos, fechas, partes y documentos; no concluye derecho.
2. **Investigador con evidencia:** consulta el corpus, arma bundle de fuentes y `allowed_citations`, verifica vigencia y estado de lectura.
3. **Redactor controlado:** produce borrador con claims trazables, lista de faltantes y estado `grounded/limited/abstain`; nunca presenta nada.

Después agregar un cuarto rol de **verificador independiente** para números, citas, vigencia y contradicciones. El abogado sigue siendo la aprobación final. El grafo multiagente recién se justifica cuando el benchmark demuestra que separar roles supera a un flujo único más barato.

## Decisión recomendada

**Custos tiene una base de seguridad mejor que la mayoría de los demos legales, pero hoy tiene menos producto que ellos.** No hay que copiarles el “chat con veinte herramientas”. Hay que tomar de Judicex la disciplina de evidencia, de Taiwan Legal RAG la defensa de citas y de Mike el empaquetado de workflows; después convertir el núcleo actual en una experiencia mínima de plazos y búsqueda para un abogado real.

La próxima entrega correcta no es un sexto agente. Es: un abogado, un expediente, una consulta, un plazo visible, un borrador con citas y un rechazo que bloquee la salida.
