# Revisión del estado real de Custos Legis

Fecha: 2026-09-29 ART  
Sujeto principal: `main` en `b37fce3d968b6b40f42e2b5c81de669bf333a950`.  
Fuentes: GitHub vivo, checks individuales de PR #18 y PR #19, y Docs de estado del 28/29-sep.

## Veredicto

Custos Legis avanzó de un repo fundacional a un **MVP vertical determinista persistente**. Ya hay HTTP, flujo documento → investigación → borrador → verificación → aprobación humana → DOCX, PostgreSQL/RLS, auditoría y CI verde del merge principal.

Pero todavía no es una plataforma de agentes, no está desplegado ni validado con abogado real. La descripción honesta hoy es: **MVP técnico integrable, no producto piloto validado**.

## Lo que está en main

El merge de PR #16 dejó en `main`:

- `backend/mvp.py`, `mvp_contract.py`, `mvp_http.py`, `mvp_server.py` y `mvp_persistence.py`.
- Cuatro roles lógicos en un servicio Python: extractor, investigador, redactor y verificador.
- Rutas `/mvp/documentos`, `/mvp/investigaciones`, `/mvp/borradores`, verificación, decisión y exportación.
- PostgreSQL persistente con cinco tablas verticales, RLS forzado, hashes, transacciones atómicas y decisiones/auditoría inmutables.
- Retrieval BM25 y grafo dirigido acotado; el grafo no es Qdrant ni una base persistente.
- Motor de plazos separado, con estados `CONFIRMADO`, `HIPOTESIS` y `NO_MEDIDO`.
- CI principal y checks del merge final declarados 9/9 verdes.

## Lo que está probado ahora

PR #18, que todavía no está mergeado, tiene 9 check runs exitosos actuales: `mvp-persistence`, `api-e2e`, `mvp-http`, `privacidad`, `plazos` y `rls`, con duplicación por disparadores. PR #19 también tiene 10/10 checks exitosos, pero es un experimento de caída/reinicio basado en la rama de PR #18 y no forma parte de `main`.

Esto prueba software en CI. No prueba Corpus live, despliegue, usuarios, abogado, carga real ni operación del taller.

## Lo que no existe todavía

- Agentes autónomos ejecutándose: **0**.
- LLM conectado: **0**.
- OCR o almacenamiento del binario original dentro del vertical: fuera de alcance actual.
- Integración viva contra el contrato real de API key del Corpus: **NO MEDIDA**.
- Abogado real usando un expediente autorizado: **NO MEDIDO**.
- Despliegue operativo de Custos: **NO MEDIDO**.
- Runtime de `brain-env`: el 29-sep el contenedor registrado no estaba corriendo, así que CPU, RAM, tests locales y Git desde el taller siguen **NO MEDIDOS**.

## Bloqueadores reales

1. **El PR #18 contiene avances importantes, pero sigue abierto.** Allí viven el puente HTTP autenticado al Corpus y `/mvp/plazos`; no deben atribuirse a `main`.
2. **La documentación de `main` está atrasada.** `ESTADO.md` y `CONTEXTO-CUSTOS-LEGIS.md` todavía dicen “cero código/cero base/cero agente”, contradiciendo el merge `b37fce3`.
3. **La interfaz sigue siendo API, no una experiencia de bufete.** Falta cliente autenticado y uso observacional de un abogado.
4. **El documento privado no queda almacenado como binario:** hoy se registra metadata y hash. Es una decisión de alcance, pero limita la utilidad del expediente.
5. **El Corpus live y la API key siguen sin recibo contra producción.** El adaptador está preparado, no acreditado.
6. **Plazos:** el motor existe, pero el vertical aún recibe un `deadline` confirmado; todavía no extrae notificación → regla → calendario automáticamente.
7. **La compuerta de privacidad está en Custos, no cableada dentro del Corpus.** El riesgo de publicación del Corpus sigue siendo una frontera externa.

## Orden correcto desde hoy

1. Actualizar `ESTADO.md` y `CONTEXTO-CUSTOS-LEGIS.md` para que `main` no mienta.
2. Decidir y ejecutar el merge de PR #18 solo después de revisar su contrato live del Corpus.
3. Probar el adaptador contra un Corpus staging autenticado, no contra el servicio productivo sin autorización.
4. Hacer benchmark real de 10 a 30 consultas y dos casos de plazo, con evidencia cruda.
5. Probarlo con un abogado y un expediente autorizado.
6. Recién después agregar almacenamiento binario, UI y SLM/router. No construir seis agentes todavía.

## Scorecard

- Producto real implementado: 14/15.
- Ejecutabilidad reproducible: 12/15, CI verde pero taller no disponible.
- Seguridad/aislamiento: 14/15, RLS y falsadores verdes; Corpus live no medido.
- Testing: 14/15, checks actuales verdes; falta caso real y carga.
- Arquitectura: 9/10, frontera Corpus/Custos limpia; API/UI todavía mínima.
- Documentación: 6/10, deriva grave entre `main` y `ESTADO.md`.
- Proceso QA: 9/10, checks individuales consultados; no hay validación externa del uso jurídico.

Total: **78/90 = 86,7/100**. No alcanza para declarar producto piloto verde.

--- METODO TITAN ---
Accion delicada: NO; revisión y documentación.
Modo aplicado: TITAN FULL.
Rúbrica: 78/90 -> 86,7/100.
N/A declarados: despliegue productivo y validación jurídica externa no ejecutados.
Review externo: no equivale a aprobación; PRs abiertos tratados como no integrados.
Instrumento: GitHub live, checks individuales PR18/PR19 y Docs de estado 28/29-sep.
