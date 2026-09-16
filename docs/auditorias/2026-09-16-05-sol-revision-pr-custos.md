# Sol: Brain pasó del diagnóstico a un PR con correcciones

Revisión acotada del 16-sep-2026, solicitada a las 08:15 ART. Sujeto: PR #1 de Custos, head 50ffc399843f01a5dbf05375872d8f19cfca7383. No es aprobación de merge ni auditoría completa del diff.

## Veredicto

**Ahora sí hay cambios de producto en la rama y un CI exitoso contra PostgreSQL 16.** No corresponde repetir que Brain solo diagnosticó. El PR sigue draft, abierto y no mergeado: las correcciones no están incorporadas a main por este PR.

[PR #1](https://github.com/gatehot59-star/custos-legis-tarija/pull/1) · [Check api-e2e del head revisado](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35088777828/job/104769838589).

## Qué contrasté en fuentes

- `backend/almacen.py`: login requiere bufete, resuelve tenant y consulta users por `_en_tenant`, sin introducir BYPASSRLS como arreglo.
- `backend/api.py`: selecciona la última decisión aplicable por timestamp e id; sobrescribe log_request, log_message y log_error para no reformatear la requestline completa.
- `backend/plazos.py`: el arranque al día calendario siguiente queda restringido a penal corrido, preservando el arranque hábil civil. El borde penal de vencimiento inhábil devuelve NO_MEDIDO. Leí el diff; no certifiqué de nuevo su conclusión jurídica sobre vigencia del artículo.
- `backend/test_regresiones_hitl.py`: obtiene tokens con POST /sesion, mismo email en dos bufetes; usa PostgresAlmacen y HTTP real. No inyecta sesiones para el recorrido e2e. El corpus es un doble declarado.
- `.github/workflows/api-e2e.yml`: PostgreSQL postgres:16, control de rol, suites API/esquema/RLS, regresiones y mutación del orden de decisiones. Consulté el check estructurado del head: completed/success, 11:09:12 a 11:09:50 UTC. Esto prueba el resultado de ese job, no corrección universal.
- `falsador_login_v2.py`: añade revocación en finally y una excepción inyectada tras elevar. El finally exterior suprime errores al revocar/consultar rol: todavía no debe interpretarse como garantía absoluta de restauración en cualquier fallo.
- `infra/2026-09-16-cierra-el-borrado-de-un-bufete.sql`: revoca INSERT/UPDATE/DELETE del rol app sobre tenants, conserva SELECT y cambia la FK de aprobaciones a RESTRICT. La migración existe en el PR; no es un cambio de producción acreditado aquí.

## Dos huecos que impiden dar aprobación completa

### Caso omitido amplía la selección de aprobaciones

El encargo pedía identidad exacta tenant/caso/tipo/hash. `PostgresAlmacen.aprobaciones(tenant_id, case_id)` y su equivalente SQLite filtran por caso solo si el argumento es truthy; con None devuelven todas las aprobaciones del tenant. `exigir_aprobacion()` filtra tipo/hash pero no vuelve a exigir igualdad de case_id. Así, una petición sin caso puede heredar una aprobación asociada a un caso concreto. La regresión leída no prueba omitir el caso ni usar otro caso dentro del mismo bufete.

**Hallazgo estático, reproducción HTTP nueva NO MEDIDA.** No afirmo envío de escritos: el endpoint sigue AUTORIZADA_PERO_NO_EJECUTADA. Falta contrato explícito de acciones sin caso y prueba que discrimine ese alcance.

### El falsador del CI acepta cualquier fallo

El workflow reintroduce el orden antiguo y considera éxito del falsador cualquier salida no cero de test_regresiones_hitl.py. No exige una etiqueta estable de fallo D2 ni distingue error de infraestructura, traceback o defecto distinto. Un verde previo y el assert del reemplazo ayudan, pero no demuestran que el rojo posterior sea por la revocación.

**Debilidad confirmada leyendo el workflow; no afirmo que el job observado haya fallado por otra causa.** Exigir código esperado y aserción/etiqueta concreta, no cualquier exit distinto de cero.

## Infraestructura adicional reportada por Brain

Nexus contiene un reporte de Brain que afirma autorización adicional a las 07:51 ART y cierre del bind de Gitea en la VM, con controles de red. No re-medí la VM ni verifiqué esa autorización en esta revisión de Custos: es un trabajo reportado, no confirmado por mí. No confundirlo con un despliegue del PR Custos.

## Qué no hice

No ejecuté otra suite, no modifiqué producto, no cambié permisos, no mergeé ni desplegué. No revisé las 14 modificaciones completas del PR ni toda la normativa citada. No validé corpus vivo, proxy/TLS, producción, concurrencia o arranque systemd. El CI actual cubre el recorrido acotado con corpus doble.

## Método y cierre

Leí respuestas de Nexus al encargo 205, PR y check runs, API, almacén, regresiones, migración y workflow al SHA fijado; usé git en brain-env para leer el diff de plazos y el bloque final del falsador. El código/CI y no los mensajes son el soporte de las conclusiones técnicas.

Rúbrica de revisión acotada: completitud 18/25 (diff parcial y sin reproducción de los bordes nuevos), razonamiento 23/25 (alcances separados), documentación 22/25 (SHA y fuentes), proceso 21/25 (lectura real y cierre documental). **84/100, parcial: no aprobación de merge.** No usar el número como puntuación de calidad del producto.

## Referencias de código

Todas en la revisión 50ffc399843f01a5dbf05375872d8f19cfca7383:

- https://github.com/gatehot59-star/custos-legis-tarija/blob/50ffc399843f01a5dbf05375872d8f19cfca7383/backend/api.py
- https://github.com/gatehot59-star/custos-legis-tarija/blob/50ffc399843f01a5dbf05375872d8f19cfca7383/backend/almacen.py
- https://github.com/gatehot59-star/custos-legis-tarija/blob/50ffc399843f01a5dbf05375872d8f19cfca7383/backend/test_regresiones_hitl.py
- https://github.com/gatehot59-star/custos-legis-tarija/blob/50ffc399843f01a5dbf05375872d8f19cfca7383/.github/workflows/api-e2e.yml
- https://github.com/gatehot59-star/custos-legis-tarija/blob/50ffc399843f01a5dbf05375872d8f19cfca7383/infra/2026-09-16-cierra-el-borrado-de-un-bufete.sql
