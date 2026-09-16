# Regresión permanente del falso positivo de FALSADOR 2

Pedido explícito de Abraham, 16-sep-2026. Cambios de prueba/CI autorizados; no se modifica la lógica de producto. [PR #2](https://github.com/gatehot59-star/custos-legis-tarija/pull/2) apilado sobre la rama del PR #1. Base e2fe70b52b89544005eb44b55adb6c8b01196501; código publicado d838fe8976db7b07d94e976e13586d1fc79925a8. Sin merge ni despliegue.

## Archivos y ejecución

`backend/test_falsador_caso.py`: cinco tests unittest que extraen el bloque FALSADOR 2 del workflow REAL. Copian backend a un directorio temporal, mantienen el helper real ok() de test_regresiones_hitl.py y sustituyen únicamente su invocación final por un resultado controlado. Ejecutan el bloque con bash -e -o pipefail y verifican que api.py se restaure. No requieren PostgreSQL ni red.

`.github/workflows/api-e2e.yml`: ejecuta esta regresión antes de instalar dependencias; agrega pull_request con los mismos filtros de paths, conserva push y contents:read. No pull_request_target, no runner self-hosted ni secretos nuevos. FALSADOR 2 exige exit 1 y texto específico con observado 200/esperado403, no el prefijo amplio ROJO CASO. El resto de e2e con PostgreSQL16 continúa.

Comando local:

```bash
python3 backend/test_falsador_caso.py
```

## Evidencia cruda: workflow anterior

Ejecutado en brain-env, con la suite nueva y workflow original de e2fe70b. Código de salida vuelto a medir por subprocess.returncode: 1. El shell exterior que luego imprime el log no se usa como testigo del exit de la suite.

```text
test_expected_assertion_with_exit_one_is_accepted (__main__.FalsadorCasoRegression.test_expected_assertion_with_exit_one_is_accepted)
Positive control: never replace the falsifier by always-fail. ... ok
test_expected_label_with_abnormal_exit_is_rejected (__main__.FalsadorCasoRegression.test_expected_label_with_abnormal_exit_is_rejected)
A label cannot excuse an abnormal suite termination. ... FAIL
test_fixture_failure_is_not_a_detected_regression (__main__.FalsadorCasoRegression.test_fixture_failure_is_not_a_detected_regression)
Historical false positive: setup assertion alone must reject. ... FAIL
test_successful_suite_is_rejected (__main__.FalsadorCasoRegression.test_successful_suite_is_rejected)
If the sabotaged suite passes, the falsifier must fail. ... ok
test_unrelated_traceback_is_rejected (__main__.FalsadorCasoRegression.test_unrelated_traceback_is_rejected)
An import/setup-style crash cannot validate the mutation. ... ok

======================================================================
FAIL: test_expected_label_with_abnormal_exit_is_rejected (__main__.FalsadorCasoRegression.test_expected_label_with_abnormal_exit_is_rejected)
A label cannot excuse an abnormal suite termination.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/custos-permanent-falsifier-20260916/backend/test_falsador_caso.py", line 113, in test_expected_label_with_abnormal_exit_is_rejected
    self.assertNotEqual(result.returncode, 0, result.stdout)
AssertionError: 0 == 0 : sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 2
OK: sacar la igualdad de caso rompe exactamente los checks del caso


======================================================================
FAIL: test_fixture_failure_is_not_a_detected_regression (__main__.FalsadorCasoRegression.test_fixture_failure_is_not_a_detected_regression)
Historical false positive: setup assertion alone must reject.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/custos-permanent-falsifier-20260916/backend/test_falsador_caso.py", line 93, in test_fixture_failure_is_not_a_detected_regression
    self.assertNotEqual(result.returncode, 0, result.stdout)
AssertionError: 0 == 0 : sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 1
OK: sacar la igualdad de caso rompe exactamente los checks del caso


----------------------------------------------------------------------
Ran 5 tests in 1.479s

FAILED (failures=2)
```

## Evidencia cruda: archivos recuperados del commit d838fe8

Tras publicar se recuperaron test y workflow desde Git y se volvió a ejecutar en brain-env. Resultado:

```text
test_expected_assertion_with_exit_one_is_accepted (__main__.FalsadorCasoRegression.test_expected_assertion_with_exit_one_is_accepted)
Positive control: never replace the falsifier by always-fail. ... ok
test_expected_label_with_abnormal_exit_is_rejected (__main__.FalsadorCasoRegression.test_expected_label_with_abnormal_exit_is_rejected)
A label cannot excuse an abnormal suite termination. ... ok
test_fixture_failure_is_not_a_detected_regression (__main__.FalsadorCasoRegression.test_fixture_failure_is_not_a_detected_regression)
Historical false positive: setup assertion alone must reject. ... ok
test_successful_suite_is_rejected (__main__.FalsadorCasoRegression.test_successful_suite_is_rejected)
If the sabotaged suite passes, the falsifier must fail. ... ok
test_unrelated_traceback_is_rejected (__main__.FalsadorCasoRegression.test_unrelated_traceback_is_rejected)
An import/setup-style crash cannot validate the mutation. ... ok

----------------------------------------------------------------------
Ran 5 tests in 1.484s

OK
```

Código de salida 0. Además se alternó workflow corregido -> viejo -> corregido en la copia local: la misma suite regresó al rojo con el criterio anterior.

## Alcance y seguridad

Prueba de inyección de fallos del consumidor de resultados del CI, no un nuevo benchmark de HTTP/RLS. Conserva un control positivo para que reemplazar el paso por uno siempre rojo falle también. Dependencia explícita de bash; ausencia o deriva de formato de workflow falla, no omite el test. Los directorios temporales son propios; no se toca /tmp/f2.log compartido. No usa credenciales de la base para esta suite. El workflow completo todavía utiliza PostgreSQL efímero como antes.

No es un parser genérico de workflows: extrae el bloque inline conocido y rechaza expresiones GitHub no soportadas. Etiquetas renombradas requieren actualizar el contrato. No pretende detectar todas las combinaciones de fallo posterior a una etiqueta válida. Pins mutables del workflow existente no fueron renovados; no se agregaron paquetes nuevos.

## Revisión y rúbrica

TITAN FULL por cambio de CI. Tester implementa y ejecuta; seguridad acotada comprueba temporales, ausencia de secretos nuevos, contents:read y runner hosted; QA revisa archivos y rojo/verde. Cambié a rol de implementación por pedido expreso: no presento mi propio cambio como auditoría independiente. Review automático solicitado en PR #2, sin aprobación inferida del silencio.

Rúbrica aplicable a configuración/instrumento: completitud15/15 (ambos archivos completos y conectados), ejecutabilidad15/15 (comando único, rojo y verde medidos), seguridad13/15 (aislamiento y permisos; pins heredados fuera de esta corrección), documentación9/10 (contrato, uso y límites), proceso4/5 (evidencia real; revisión externa pendiente). 56/60 = **93/100**; 40 puntos N/A de categorías no pertinentes al cambio acotado. No es aprobación de producto, merge ni despliegue. El estado de CI se consulta por SHA, no se presume por esta rúbrica.
