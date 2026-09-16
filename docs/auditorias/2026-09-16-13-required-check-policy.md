# Checks obligatorios independientes de la suite ejecutable

Pedido de Abraham, 16-sep-2026 17:21 ART. [PR #4](https://github.com/gatehot59-star/custos-legis-tarija/pull/4) apilado sobre PR #3, rama titan/tester-required-check-policy. Base 9eaece7849fd4451b228de7e37d3f8858b67edce; código 2f7893a5027835d5eed5c51f2c0e2990f195718a. Sin merge, despliegue ni modificación de ramas ajenas.

## Garantía nueva y límite exacto

**Borrar o vaciar checks en la suite no reduce los requisitos.** El runner y el validador leen `backend/required_checks.json`, un archivo versionado separado, no el AST de la suite ni la lista autodeclarada por un recibo.

El contrato inicial fija 45 identidades: 12 de plazos, 32 de integración HTTP/PostgreSQL y 1 de cierre. Se tomó una fotografía inicial del fuente auditado durante esta implementación y se incluyó explícitamente en el diff para revisión. No existe generación del contrato al ejecutar la suite o el CI. Cambiarlo requiere editarlo deliberadamente, no solo editar tests.

**Independencia de datos no es independencia de permisos:** alguien que puede modificar el repo y sus tests también puede proponer cambiar esta política. No configuré protecciones de rama, CODEOWNERS, firmas ni un supervisor externo. Repetir las 45 etiquetas sin ejecutar fases o fabricar un JSON completo no queda resuelto aquí. No se debe interpretar cleanup_returned como evidencia externa de limpieza: conserva la limitación de PR3 ya auditada.

## Implementación

- `backend/required_checks.json`: versión, revisión de origen, regla explícita de cambios y listas por fase.
- `backend/suite_receipt.py`: elimina descubrimiento por AST, exige las tres fases, listas no vacías, ids válidos y globalmente únicos. Añade `policy_sha256` al recibo; el validador lo contrasta con la política que él carga, además del manifiesto completo.
- `backend/test_falsador_caso.py`: añade tres métodos de regresión, manteniendo los 15 subescenarios anteriores. El workflow de PR3 ya ejecuta este archivo bajo backend/**: no fue necesario cambiarlo.

Comando:

```bash
python3 backend/test_falsador_caso.py
```

## Rojo contra el runner anterior

La MISMA prueba reduce una copia de la suite a una aserción y dos fases vacías. Con el runner del PR3, devuelve 0 en lugar del 2 requerido. No es un error de imports o nombres de test.

Salida cruda de brain-env:

```text
OLD_EXIT 1
test_suite_reduction_cannot_reduce_required_checks (__main__.RequiredPolicyRegression.test_suite_reduction_cannot_reduce_required_checks) ... FAIL

======================================================================
FAIL: test_suite_reduction_cannot_reduce_required_checks (__main__.RequiredPolicyRegression.test_suite_reduction_cannot_reduce_required_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/custos-required-contract-20260916/backend/test_falsador_caso.py", line 110, in test_suite_reduction_cannot_reduce_required_checks
    self.assertEqual(run.returncode, 2, run.stderr)
AssertionError: 0 != 2 : 

----------------------------------------------------------------------
Ran 1 test in 0.118s

FAILED (failures=1)
```

El runner corregido conserva 45 requisitos, devuelve 2 y no marca completo el recibo. La prueba además altera manualmente ese recibo para decir completed=true con lista reducida; el validador lo rechaza por checks faltantes. Políticas ausentes, malformadas, con una fase vacía o con check duplicado también se rechazan.

## Verde desde los archivos publicados

Extraje `2f7893a` con git archive a un directorio nuevo del taller. Ejecuté los archivos de ese commit, no el árbol local con modificaciones de otro trabajo.

```text
complete_target: step_exit=0, expected_accept=True
target_then_crash: step_exit=2, expected_accept=False
cleanup_crash: step_exit=2, expected_accept=False
partial_return: step_exit=2, expected_accept=False
fixture_only: step_exit=2, expected_accept=False
contaminated: step_exit=2, expected_accept=False
positive_broken: step_exit=2, expected_accept=False
traceback: step_exit=2, expected_accept=False
no_failure: step_exit=2, expected_accept=False
abnormal_exit: step_exit=2, expected_accept=False
missing: step_exit=2, expected_accept=False
stale: step_exit=2, expected_accept=False
malformed: step_exit=2, expected_accept=False
duplicate: step_exit=2, expected_accept=False
skipped: step_exit=2, expected_accept=False

test_receipt_contract (__main__.CompletionRegression.test_receipt_contract)
Fifteen outcomes discriminate completion from matching log output. ... ok
test_invalid_policy_fails_closed (__main__.RequiredPolicyRegression.test_invalid_policy_fails_closed) ... ok
test_policy_has_reviewed_phase_inventory (__main__.RequiredPolicyRegression.test_policy_has_reviewed_phase_inventory) ... ok
test_suite_reduction_cannot_reduce_required_checks (__main__.RequiredPolicyRegression.test_suite_reduction_cannot_reduce_required_checks) ... ok

----------------------------------------------------------------------
Ran 4 tests in 7.457s

OK
```

4 métodos unittest, uno incluye los 15 subescenarios. No se suman como 19 pruebas de producto. La prueba positiva usa resultados sintéticos: acredita el consumidor del recibo, no ejecución jurídica/SQL de esos checks. El CI conserva su integración PostgreSQL16 real.

## Compatibilidad

Recibos anteriores sin policy_sha256 dejan de ser válidos; se mantienen como evidencia histórica, no se reescriben. Un cambio explícito de política invalida recibos de otra política por hash. Nuevos checks en la suite requieren un cambio explícito del contrato; no se aceptan silenciosamente.

La versión de política es un entero positivo, no un mecanismo de autorización. El hash identifica bytes, no autenticidad. Las identidades siguen siendo etiquetas literales: no se añadió un registro de IDs con autoridad externa.

## Método y alcance

TITAN FULL por cambio del contrato del verificador de CI. Implementación autorizada, no auditoría independiente de código propio. Lectura del PR actual, rama separada, runner y validador ejecutados en subprocess, regresión roja con versión anterior y repetición verde desde Git. No se tocó producción ni se abrió PostgreSQL local nuevo en este turno.

Dos intentos de transporte de un script auxiliar fallaron antes de ejecutarlo; se descartaron y se transfirió en partes completas. No se contaron como tests ni evidencia del defecto.

Revisión automática solicitada en PR4; el silencio no aprueba. Completitud14/15 (política/consumidores/regresión), ejecutabilidad15/15 (rojo/verde y archive), seguridad13/15 (alcance no adversarial explícito), documentación9/10, proceso4/5 (revisión externa pendiente): 55/60 = **92/100**, N/A40 para configuración/instrumento acotados. No aprobación de PR3 completo ni de producto.
