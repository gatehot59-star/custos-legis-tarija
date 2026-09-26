# QA formal: vertical MVP conectado a HTTP

**Fecha:** 2026-09-26  
**PR:** [#8](https://github.com/gatehot59-star/custos-legis-tarija/pull/8)  
**Rama:** `titan/mvp-http-routes-20260926`  
**Commit auditado:** `9d5c4b2c7d7080513fbe914ae3318679cef22456`

## Alcance y método

Auditoría contra el repositorio y el diff real del PR, no contra el documento de cierre anterior. Se revisaron `backend/mvp_http.py`, `backend/mvp_server.py`, `backend/test_mvp_http.py`, `.github/workflows/mvp-http.yml`, `backend/mvp.py`, `backend/mvp_contract.py` y la API base. El primer workflow nuevo falló porque el test pasaba el token de la ruta `GET /casos` como cuerpo posicional; se corrigió a `token=token_a` en `backend/test_mvp_http.py` y se repitió el CI.

## Evidencia ejecutable

El commit final produjo estos check runs individuales, todos completados con `success`:

- [mvp-http](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242095337/job/108404411457): compila el vertical, ejecuta `test_mvp.py`, benchmark, `test_mvp_http.py` y `test_api.py`.
- [api-e2e](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242095335/job/108404411495): PostgreSQL 16 real, RLS, regresiones HITL y migración.
- [api-e2e](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242092781/job/108404404260): corrida equivalente del push, también verde.
- [plazos](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242092775/job/108404404407): calendario y falsadores de plazos, verde.
- [rls](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242092775/job/108404404340): RLS forzado y sabotaje de checkpoints, verde.
- [privacidad](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/36242092775/job/108404404241): compuerta y ocho falsadores, verde.

La primera corrida del workflow `mvp-http` quedó fallida y no se cuenta como verde: su evidencia sirvió para corregir el test. El estado final no se infiere del agregado: se leyó cada job individual.

## Hallazgos corregidos antes de aprobar

1. `backend/test_mvp_http.py`: el test de `GET /casos` enviaba el token como argumento `body`, por lo que el nuevo CI detectó un falso fallo. Se corrigió con argumento nombrado y se volvió a ejecutar.
2. `backend/mvp_http.py`: decisiones inválidas y exportaciones sin aprobación ya no caen como 500 opaco; se traducen a errores HTTP deterministas.
3. `backend/mvp_server.py`: cuerpos JSON que no son objetos reciben 400; cuerpos mayores a 14 MiB reciben 413; el corpus cerrado retorna 503; los errores de contrato MVP retornan 422.

## Controles revisados

- La sesión se valida por el handler existente antes de cada `/mvp/*`.
- Caso, búsqueda y borrador se atan al tenant; el borrador además exige coincidencia de caso.
- La exportación DOCX exige decisión aprobada sobre el hash exacto del borrador.
- La cita exportable exige URL HTTP(S), fragmento, hash, vigencia `VIGENTE` y validación numérica medida o no aplicable.
- El límite de documento es 10 MiB y el límite de cuerpo JSON es 14 MiB.
- La prueba HTTP cubre sesión, `/salud`, `/casos`, rechazo sin sesión, rechazo de JSON no objeto, documento, investigación, borrador, verificación, decisión inválida, HITL, DOCX con hash y aislamiento entre bufetes.

## Deuda técnica abierta

- El estado del vertical (`documents`, `searches`, `drafts`, `decisions`) vive en memoria de proceso; JSONL es opcional para auditoría. No se declara listo para varios workers.
- No se midió la búsqueda contra el corpus público real porque el corpus permanece cerrado; el fixture HTTP no reemplaza esa medición.
- No se ejecutó validación jurídica externa con un abogado dentro de este PR.

## Criterios N/A

**DevOps propio: N/A.** El PR agrega un wrapper HTTP y CI, pero no cambia Docker, systemd, infraestructura ni el despliegue. El CI sí queda cubierto por la verificación de entrega; no se usa N/A para ocultar la cobertura de tests.

## TITAN SCORECARD

| Criterio | Puntos | Evidencia |
|---|---:|---|
| Completitud | 14/15 | Cinco archivos del diff completos; revisión de archivos en el commit final. |
| Ejecutabilidad | 14/15 | `mvp-http`, `api-e2e`, `plazos`, `rls` y `privacidad` verdes; la primera corrida fallida fue corregida y repetida. |
| Seguridad | 12/15 | Sesión heredada, aislamiento tenant/caso, HITL por rol y hash, límites de entrada; deuda de persistencia/RLS del estado MVP. |
| Testing | 13/15 | Test HTTP real del handler, regresiones de núcleo y CI PostgreSQL 16; corpus real y abogado externo quedan fuera. |
| Arquitectura | 8/10 | Puerto de corpus y cuatro roles lógicos claros; estado en memoria y tipos `Any` limitan escala. |
| DevOps | N/A | No cambia despliegue propio; no entra en denominador. |
| Documentación | 9/10 | `docs/mvp/HTTP.md`, recibo HTTP y este QA describen arranque, rutas, límites y deudas. |
| Innovación | 4/5 | Citas fail-closed, validación numérica, HITL y cadena de custodia en DOCX. |
| Proceso QA | 5/5 | Evidencia por commit, check runs individuales y corrección guiada por un fallo real. |

**Resultado:** 79/80 aplicables = **98.75/100**, todos los criterios aplicables superan 8/10. **QA aprobado con deuda técnica explícita.** No implica merge automático ni declara producción: el PR sigue siendo un piloto y requiere decisión humana para integrarse.

--- METODO TITAN ---
Accion delicada: NO
Modo aplicado: TITAN FULL
Rubrica: 79/80 aplicables -> 98.75/100
N/A declarados: DevOps propio, PR sin cambio de despliegue
Review externo: sin hallazgos emitidos, no equivale a aprobación
Instrumento: GitHub Actions, check runs individuales del commit `9d5c4b2c7d7080513fbe914ae3318679cef22456`, todos `success`; evidencia cruda en GitHub
