# Sol: reparos corregidos en gran parte; falsador CASO aún demasiado amplio

16-sep-2026, revisión solicitada a las 12:29 ART. Sujeto exacto: PR #1, head `e2fe70b52b89544005eb44b55adb6c8b01196501`. Sigue abierto, draft y no mergeado. No se aprueba merge ni despliegue.

## Veredicto

**El avance de Brain es real.** El filtro explícito de caso está implementado y lo probé a nivel de función del producto; los falsadores de CI ya no aceptan cualquier error sin etiqueta; el instrumento de restauración deja de silenciar fallos y devuelve salida no cero cuando cuenta rojos. E6 detecta un sabotaje que no cambia el fuente.

**El reparo del CI está cerrado parcialmente, no por completo:** su segundo falsador exige solamente `ROJO CASO`, que también coincide con un fallo de creación del segundo expediente. Probé ese predicado con salida sintética. Eso no demuestra que la corrida verde real haya fallado por el motivo incorrecto; demuestra que su criterio todavía lo permite.

## 1. Caso omitido: corrección confirmada en el alcance probado

En `backend/api.py`, `_mismo_caso` compara None exclusivamente con None y los identificadores explícitos como cadenas. `exigir_aprobacion` incluye esa comparación además de tipo y hash.

Ejecuté la función del archivo extraído del SHA revisado en una carpeta temporal de brain-env, con un almacén sintético que devuelve las decisiones sin filtrarlas. No copié ni reescribí la función. No es una prueba de HTTP o RLS.

Salida cruda:

```jsonl
{"probe": "actual gate, synthetic store, not HTTP/RLS", "case": "same", "result": "AUTHORIZED"}
{"probe": "actual gate, synthetic store, not HTTP/RLS", "case": "other", "result": "BLOCKED"}
{"probe": "actual gate, synthetic store, not HTTP/RLS", "case": "omitted", "result": "BLOCKED"}
{"probe": "actual gate, synthetic store, not HTTP/RLS", "case": "none_to_none", "result": "AUTHORIZED"}
```

No equiparo el último resultado a un permiso de producto aprobado: el contrato de acciones sin expediente sigue sin decidir. La regresión versionada añade segundo caso, caso omitido y control positivo del caso original.

Sobre la objeción de Brain a mi revisión anterior: el defecto era omitir `case_id` y heredar una aprobación ligada a un expediente. El almacén ya filtraba un segundo ID explícito. Mi informe anterior describía ese mecanismo, pero el cierre en chat podía leerse como fuga arbitraria entre dos expedientes: queda acotado aquí. No corresponde inventar un segundo defecto para defender una formulación ambigua.

## 2. Falsadores del CI: uno preciso, el otro aún genérico

El primer falsador exige la línea de fallo D2 sobre revocación tras rechazo. Es una mejora concreta frente a aceptar cualquier exit no cero.

El segundo usa:

```bash
grep -q 'ROJO CASO' /tmp/f2.log
```

La misma suite emite ese prefijo para cuatro checks, incluido el control de que se creó el segundo expediente. Probé el grep exacto contra SOLO ese error ajeno a la herencia de aprobación:

```json
{"probe": "CI FALSADOR 2 label specificity", "synthetic_output": "  ROJO CASO el segundo expediente se creo (si no, no se puede medir): obtenido False, esperado True\n", "grep_returncode": 0, "wrong_case_check_accepted": true}
```

Con una salida no cero y esa línea, el criterio del falsador puede aprobar aunque no se haya demostrado el fallo de una acción sin caso. **REFUTADO: que el segundo filtro exija el check exacto esperado. NO MEDIDO: que ese falso positivo haya ocurrido en Actions.**

Corrección propuesta, no aplicada: exigir el identificador exclusivo del caso omitido, por ejemplo la etiqueta completa actual `ROJO CASO una accion SIN caso NO hereda la aprobacion del caso 1`, preferiblemente reemplazada por un identificador estructurado estable. Separar errores de fixtures de fallos de producto y exigir el código previsto, no solamente cualquier nonzero.

## 3. Revocación: código corregido y evidencia de recuperación

Leí el diff de `falsador_login_v2.py`: elimina suppress, guarda el error de revocación, lee pg_roles, suma un rojo si persiste bypass y añade `sys.exit(1)` cuando hay rojos sin excepción en vuelo. Las excepciones no manejadas conservan su traceback y salida no cero.

Leí los JSON reales del taller, sin volver a elevar permisos ni arrancar el cluster. La secuencia observada tiene CINCO archivos, no cuatro:

- 14:47:47: normal, 15/0, rol inicial y final sin bypass.
- 14:47:57: sabotaje, 7/2, parte sin bypass y termina con bypass; revocación FALLÓ explícitamente.
- 14:49:10: otro sabotaje, 6/3, parte con bypass heredado y termina igual.
- 14:49:12: normal de recuperación, 14/1, detecta bypass heredado y lo revoca.
- 14:49:41: normal final, 15/0, rol inicial y final sin bypass.

Todos esos JSON registran stop 0 y status posterior 3. Brain resumió el sabotaje de tres rojos; el archivo anterior de dos rojos explica de dónde vino el estado heredado de ese segundo sabotaje. No oculto ese paso al describir la cadena.

No medí de nuevo los exit codes de esas ejecuciones ni comparé cada JSON con el SHA del instrumento: son evidencia de taller ajena leída y contrastada con el mecanismo versionado. No certifico restauración frente a SIGKILL ni ante imposibilidad de contactar la base. El head que modifica este instrumento no tiene una corrida CI propia.

## 4. E6 y los CUATRO jobs: comprobados sin mezclar revisiones

La API pública de checks devuelve **cero checks para e2fe70b**, no cuatro verdes. No es evidencia de fallo: ese commit cambió el instrumento bajo docs y no los paths que disparan los workflows. Leí el historial de runs y los jobs de ambos workflows:

- [api-e2e, run 35108224166](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35108224166): SUCCESS en `30da4fc6821a5b7b575c6fcecdb7bdf05bbd3b2c`. Incluye regresiones de login real, control del rol, migración, ambos falsadores y verificación de árbol sin cambios.
- [tests, run 35109369304](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35109369304): privacidad, plazos y rls, los tres SUCCESS en `89569d4533c202d4e8c8c66faa68ee599afc477f`. El paso de nueve falsadores de plazos y el de ocho de privacidad también figuran exitosos.

Comparaciones git obtenidas contra el head:

```text
30da4fc -> e2fe70b:
.github/workflows/tests.yml
docs/auditorias/2026-09-16-pr-cuatro-defectos/falsador_login_v2.py

89569d4 -> e2fe70b:
docs/auditorias/2026-09-16-pr-cuatro-defectos/falsador_login_v2.py
```

Por tanto el producto y workflow api-e2e conservan los bytes de su corrida exitosa, y tests.yml conserva los de la suya. **Cuatro jobs exitosos sobre sus revisiones pertinentes, no cuatro checks nuevos sobre el head.** El instrumento bajo docs queda fuera de esa evidencia de CI.

E6 incorpora comparación de fuentes después del sabotaje y antes del test, más restauración cuando falla el script de sabotaje de plazos. Los patrones del arranque civil y del estado coinciden con el código reindentado. Lo comprobé leyendo el diff; la ejecución del paso completo la respalda Actions, no una nueva corrida propia.

## 5. Mi omisión anterior: aceptada con precisión temporal

La revisión de las 08:15 solo consultó api-e2e. En el SHA 50ffc399 había un único check y era success, pero el último workflow tests de la rama, en el padre d4dc7c5, tenía plazos FAILURE. Debí revisar también esa evidencia de rama en vez de dejar el resto sin examinar.

Consulta estructurada:

```text
PREVIOUS_TESTS [('privacidad', 'success', 'd4dc7c549a605fe0c6904438b146494ffa5ac112'), ('plazos', 'failure', 'd4dc7c549a605fe0c6904438b146494ffa5ac112'), ('rls', 'success', 'd4dc7c549a605fe0c6904438b146494ffa5ac112')]
```

No aprobé el PR entonces, pero eso no elimina la omisión. Mi afirmación de success de api-e2e era cierta; una lectura de «CI completo verde» habría sido falsa. Ahora la evidencia de ambos workflows sí está consultada.

## Qué sigue pendiente

Precisar el segundo falsador y sus fixtures; decidir qué significa aprobar una acción sin expediente; corpus vivo, proxy/TLS, concurrencia, arranque como servicio, retención/exportación de evidencia y exactitud jurídica integral. No convertí la ausencia de modificación del art. 130 en dos leyes en una prueba exhaustiva de vigencia.

No realicé auditoría exhaustiva de las 16 modificaciones del PR. No mergeé, desplegué, cambié políticas ni ejecuté sabotaje de permisos. La prueba propia fue de función con almacén sintético y del filtro de texto del CI; no una repetición completa del producto con PostgreSQL.

## Fuentes y método

Código y diffs por git en brain-env; Nexus para descubrir afirmaciones; API pública de GitHub para runs/jobs; JSON de restauración en el taller. Comparación de paths entre revisiones antes de trasladar el alcance de un verde. Los dos programas auxiliares ejecutados quedan en el taller como sol_read_ci.py y sol_probe_1530.py; sus salidas completas en los logs homónimos. Las salidas decisivas se conservan arriba verbatim. No presentar esta corrida propia como una certificación independiente de todo el producto.

- [PR](https://github.com/gatehot59-star/custos-legis-tarija/pull/1)
- [API auditada](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/backend/api.py)
- [Regresiones](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/backend/test_regresiones_hitl.py)
- [Workflow e2e](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/.github/workflows/api-e2e.yml)
- [Workflow tests/E6](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/.github/workflows/tests.yml)
- [Instrumento de revocación](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/docs/auditorias/2026-09-16-pr-cuatro-defectos/falsador_login_v2.py)

Rúbrica de revisión acotada: completitud 21/25 (ambos workflows; sin diff íntegro), razonamiento 23/25 (SHA, causalidad y alcance separados), documentación 22/25 (fuentes y salidas), proceso 21/25 (lectura real, prueba propia acotada y cierre). **87/100: parcial, sin aprobación de merge.** Es autoevaluación del trabajo de revisión, no puntuación del producto.
