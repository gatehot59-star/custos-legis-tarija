# ADR-002: vertical MVP trazable antes de agentes autónomos

**Fecha:** 2026-09-26  
**Estado:** aceptado para el sprint MVP  
**Rama:** `titan/mvp-vertical-20260926`

## Contexto

El repositorio ya tiene piezas ejecutables para autenticación multi-bufete, compuerta de privacidad, cliente del corpus, cálculo de plazos, revisión humana y RLS. No tiene todavía un flujo único que una documento, búsqueda citada, plazo, revisión y exportación. El corpus HTTP público está cerrado y la vigencia de muchas normas está `NO_MEDIDO`; una respuesta plausible sin evidencia es un riesgo jurídico, no una mejora.

## Decisión

Cerrar primero un flujo vertical pequeño, con cuatro roles lógicos representados como etapas versionadas, no como agentes autónomos:

1. `extractor`: registra caso y documento sin reescribir el original.
2. `investigador`: consulta el corpus y clasifica citas permitidas, candidatas no leídas y precedentes derogados.
3. `redactor`: genera un borrador determinista a partir de evidencia disponible, nunca una afirmación sin cita.
4. `verificador`: bloquea la aprobación si falta fuente, fragmento, hash, vigencia o validación numérica.

La exportación DOCX solo se habilita para el hash exacto de un borrador aprobado por un usuario con matrícula. Toda transición deja un evento JSONL auditable. El motor de búsqueda se mantiene por puerto, así BM25, vectorial y grafo se pueden comparar sin cambiar el flujo ni introducir Qdrant por moda.

## Alternativas rechazadas

- **Seis agentes autónomos y LangGraph ahora:** rechazado. El estado medido dice que el abogado todavía no usó el núcleo y que el repo no debe convertir una arquitectura histórica en código no validado.
- **Qdrant antes del benchmark:** rechazado. La búsqueda actual es léxica y el corpus declara ese límite; primero se miden 10 a 30 consultas.
- **Permitir citas con vigencia desconocida:** rechazado. `NO_MEDIDO` se conserva como candidato no leído y bloquea una salida presentada como definitiva.
- **Exportar desde cualquier borrador:** rechazado. El hash de contenido y el caso son parte de la aprobación HITL.

## Consecuencias

El primer producto es menos vistoso, pero se puede explicar, probar y auditar. La capa de integración añade un archivo JSONL por corrida, por lo que el piloto puede operar sin inventar una nueva infraestructura de cola. A 10x carga, el límite principal será el archivo de auditoría y el proveedor corpus; el puerto permite reemplazarlo por almacenamiento transaccional sin cambiar los contratos.

## Criterios de cierre

- Cada afirmación exportada tiene una cita verificable o queda fuera del borrador.
- `allowed_citations`, `unread_candidates` e `invalidated_precedents` son salidas explícitas.
- Un rechazo posterior revoca la aprobación anterior del mismo hash.
- El DOCX no existe si no hay aprobación coincidente.
- La suite local del vertical puede dar rojo ante una cita sin fuente, un cambio posterior al visto bueno y una exportación sin aprobación.

--- METODO TITAN ---
Accion delicada: NO
Modo aplicado:   TITAN FULL
Rubrica:         N/A hasta implementación y QA
N/A declarados:  QA de código, porque este archivo es un ADR
Review externo:  no pedido todavía
Instrumento:     no aplica a prosa; el contrato y tests serán el instrumento
