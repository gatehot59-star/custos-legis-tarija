# Sol: integración confirmada en main; el falsador no comprueba terminación de la suite

Fecha: 16-sep-2026, auditoría solicitada a las 14:24 ART. Sujeto: main `093e8a1502dd4ee5856aa4b1c06faeac5fa925b3`, cuyo padre es el merge `4a14f06eec28301cef175d74db7cb90a9f6dee3b`. Auditoría acotada de integración y regresión permanente. No se decide aquí el contrato jurídico de acciones sin caso: el mensaje de Nexus propone otro trabajo, distinto del pedido actual.

## Veredicto

**Brain incorporó las correcciones y la regresión a main.** Los dos PRs están mergeados, el commit combinado de main tiene cuatro checks exitosos y los siete tests del falsador pasan al ejecutarlos desde un archivo del commit. Ya no están pendientes de integración.

**Queda un falso positivo reproducible:** una suite que emite la aserción objetivo y después termina por RuntimeError es aceptada por FALSADOR 2. El exit es 1 tanto para una aserción fallida normal como para una excepción de Python. Contar un único ROJO no demuestra que la suite haya completado el resto de sus controles.

No afirmo que ese escenario haya sucedido en la corrida real de Actions ni que las correcciones del producto sean falsas. Es un defecto del instrumento de aceptación, demostrado con inyección acotada. No se aprueba despliegue ni se modificó código.

## Integración: resolución de una contradicción entre herramientas

El listado inicial de PRs devolvió state=closed y merged=false para ambos, contradiciendo el mensaje de Brain. No usé ese listado como veredicto final. La API REST directa de cada PR y el grafo git coinciden:

```text
PR 1 {'state': 'closed', 'merged': True, 'merged_at': '2026-09-16T17:09:15Z', 'merge_commit_sha': '4a14f06eec28301cef175d74db7cb90a9f6dee3b'}
PR 2 {'state': 'closed', 'merged': True, 'merged_at': '2026-09-16T17:07:23Z', 'merge_commit_sha': 'd349ee8fafc58179b4187547dba46de18637e54a'}
```

El merge d349ee8 tiene padres e2fe70b y 906146d. El merge 4a14f06 tiene padres c50035d y d349ee8. Es integración estructural, no inferida del texto de un commit.

El único archivo cambiado de 4a14f06 a 093e8a es `docs/auditorias/2026-09-16-09-mergeado-a-main-y-el-contrato-va-a-sol.md`. No hubo cambios de código posteriores entre esas dos revisiones.

## CI, por revisión exacta

Salida de la consulta pública de check-runs:

```text
CHECKS 4a14f06eec28301cef175d74db7cb90a9f6dee3b [('privacidad', 'completed', 'success'), ('rls', 'completed', 'success'), ('plazos', 'completed', 'success'), ('api-e2e', 'completed', 'success')]
CHECKS 093e8a1502dd4ee5856aa4b1c06faeac5fa925b3 []
```

No atribuyo checks propios a 093e8a. Los cuatro verdes pertenecen al merge y su código coincide con el head documental examinado.

## Mi arreglo anterior y la mejora de Brain

Mi versión exacta aceptaba una etiqueta objetivo aunque apareciera además un fallo de fixture. Brain agregó un contador de rojos y una regresión para ese caso; ese reparo a mi implementación es válido. También conservó una prueba del control positivo roto, que mi criterio exacto ya rechazaba, corrigiendo su atribución previa.

Ejecuté la suite actual desde `git archive 093e8a`, en directorio temporal. El clon del taller tiene modificaciones preexistentes en backend y un script: NO lo usé como árbol ejecutado, NO lo limpié y NO se atribuyen a esta auditoría.

Comando: `python3 backend/test_falsador_caso.py`, código de salida 0. Salida cruda:

```text
test_broken_positive_control_is_rejected (__main__.FalsadorCasoRegression.test_broken_positive_control_is_rejected)
Breaking the legitimate path is the opposite of a working sabotage. ... ok
test_contaminated_experiment_is_rejected (__main__.FalsadorCasoRegression.test_contaminated_experiment_is_rejected)
Target red plus a fixture red must NOT count as a clean detection. ... ok
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
Ran 7 tests in 2.108s

OK
```

## Nuevo borde: objetivo seguido de excepción

Usé el método `run_scenario` del propio test versionado, que ejecuta el bloque real FALSADOR 2, conserva imports y helper ok(), y sustituye solo la invocación final de la suite en una copia temporal. La inyección fue:

```python
ok('CASO una accion SIN caso NO hereda la aprobacion del caso 1', 200, 403)
raise RuntimeError("INJECTED crash after expected failure, before suite completion")
```

No hubo PostgreSQL ni llamadas HTTP. Se prueba el consumidor de resultados del workflow, no la causa real de un fallo de base. El paso muta y restaura la copia de api.py; el helper verifica restauración byte por byte.

Salida del paso real:

```text
sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 1
rojos que emitio la suite: 1 (se espera exactamente 1)
OK: sacar la igualdad de caso rompe exactamente ese check, y nada mas
```

`subprocess.returncode` del paso: **0**. Stderr del paso vacío porque el workflow redirige la salida de la suite a su log. La excepción fue inyectada después de la aserción objetivo; el RuntimeError produce exit 1 y no añade otra línea con prefijo `  ROJO `, de modo que satisface los tres requisitos actuales.

El test preexistente de salida anormal usa SystemExit(2). Eso no representa todas las terminaciones anormales: un RuntimeError también sale con 1. El test de traceback ajeno no emite antes el objetivo. Ninguno cubre esta combinación.

## Recomendación específica

No seguir ampliando grep por síntomas. Hacer que la suite emita al finalizar un resultado estructurado, escrito solo después de completar los controles y la limpieza, con identidad del escenario, número de checks ejecutados, lista exacta de fallos y estado de finalización. El falsador debe exigir finalización completa y únicamente el fallo objetivo; cualquier excepción debe invalidar el experimento aunque se haya visto antes la etiqueta correcta.

Agregar permanentemente target-then-RuntimeError y mantener el control de fallo objetivo con terminación completa. Revisar el mismo mecanismo en FALSADOR 1, que comparte la estrategia exit+conteo+etiqueta; en esta sesión solo se reprodujo FALSADOR 2. No afirmo que una simple marca textual sea una garantía criptográfica o protección ante suite hostil.

## Límites

Auditoría del cierre de PRs, CI estructurado, diff del test/workflow, siete escenarios y una inyección adicional. No auditoría exhaustiva del producto, no nueva ejecución de PostgreSQL16, no verificación de producción, corpus vivo, TLS, concurrencia ni toda la normativa. Brain reporta autorización humana para el merge; esta auditoría confirma el hecho técnico del merge, no reconstruye ese consentimiento desde su conversación.

No ejecuté la nueva decisión de producto que Brain dejó en Nexus como si fuera una instrucción directa del usuario en este turno. No envié mensajes en nombre del usuario ni modifiqué las correcciones.

## Método y evidencia

API pública de GitHub y grafo git para merge, check-runs por SHA, git archive para evitar el árbol sucio, unittest y bash del instrumento versionado en brain-env. Código y salida auxiliares conservados en `sol_audit_1724.py` y `sol_audit_1724.log` de la carpeta de pruebas. Las salidas decisivas se copian arriba verbatim.

Afirmación -> instrumento -> posibilidad de refutar -> resultado: merges reales -> API y dos padres git -> sí -> CONFIRMADO; siete regresiones pasan -> ejecución desde archive -> sí -> CONFIRMADO; falsador rechaza cualquier terminación anormal -> objetivo + RuntimeError en paso real -> sí -> REFUTADO en ese escenario.

Rúbrica del reporte: completitud13/15 (alcance acotado), arquitectura del razonamiento9/10 (identidad y límites), documentación9/10 (fuentes y salida), innovación5/5 (borde nuevo), proceso5/5 (contraste externo y archivo limpio). **41/45 = 91/100, 55 puntos N/A por tratarse de auditoría.** No es puntuación de preparación del producto ni aprobación de merge retroactiva.

Fuentes: [PR1](https://github.com/gatehot59-star/custos-legis-tarija/pull/1), [PR2](https://github.com/gatehot59-star/custos-legis-tarija/pull/2), [merge](https://github.com/gatehot59-star/custos-legis-tarija/commit/4a14f06eec28301cef175d74db7cb90a9f6dee3b), [workflow](https://github.com/gatehot59-star/custos-legis-tarija/blob/093e8a1502dd4ee5856aa4b1c06faeac5fa925b3/.github/workflows/api-e2e.yml), [test](https://github.com/gatehot59-star/custos-legis-tarija/blob/093e8a1502dd4ee5856aa4b1c06faeac5fa925b3/backend/test_falsador_caso.py).
