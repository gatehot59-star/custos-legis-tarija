# Probado: FALSADOR 2 puede pasar por un fallo de preparación

16-sep-2026. Sujeto: paso FALSADOR 2 de `.github/workflows/api-e2e.yml`, revisión `e2fe70b52b89544005eb44b55adb6c8b01196501` del PR #1. Ejecución en brain-env por gateway build.run. No se alteró el producto del repo, no se ejecutó GitHub Actions ni se abrió PostgreSQL.

## Veredicto

**El paso terminó con exit 0 y anunció que detectó la regresión aunque la única aserción fallida fue la preparación del segundo expediente.** La aserción de una acción sin caso no fue ejecutada ni emitida. Esto prueba un falso positivo del mecanismo de aceptación del falsador bajo inyección controlada, no que una corrida histórica de Actions haya tenido ese falso positivo.

## Instrumento: qué se preservó y qué se inyectó

Extraje el bloque `run` de FALSADOR 2 directamente de Git. Se ejecutó bajo bash --noprofile --norc -e -o pipefail, con su mutación real de backend/api.py y su lógica de aceptación intactas. Solo se trasladaron las dos rutas temporales `/tmp/api.py.bak2` y `/tmp/f2.log` a directorios exclusivos para no sobrescribir archivos ajenos.

Cada escenario recibió una copia nueva del backend del SHA fijado. En `test_regresiones_hitl.py` se conservaron imports, funciones y el helper real `ok()`, reemplazando únicamente la invocación final de main por el fallo controlado de cada escenario. No se ejecutaron las funciones de integración ni se intentó crear realmente un expediente. Esta separación es deliberada: el objeto probado es el consumidor de resultados del test, no la causa de un error de base de datos.

Caso decisivo inyectado:

```python
ok('CASO el segundo expediente se creo (si no, no se puede medir)', False, True)
raise SystemExit(1)
```

La etiqueta pertenece a un check real existente. El programa no imprime directamente un mensaje inventado de éxito del workflow: el propio workflow decide y lo imprime.

SHA256 del bloque run extraído, antes de reubicar rutas: `61484e2a87a8d336443e586f9f5a4caecb2e26e6e013109c4527d80a0407a1ba`.

## Salida cruda decisiva

Suite, único mensaje:

```text
  ROJO CASO el segundo expediente se creo (si no, no se puede medir): obtenido False, esperado True
```

Paso del workflow:

```text
sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 1
OK: sacar la igualdad de caso rompe exactamente los checks del caso
```

`subprocess.returncode` del paso: **0**. Etiqueta específica de acción sin caso emitida: **false**. Archivo api.py restaurado idéntico al original: **true**.

## Controles que distinguen un falso positivo de un instrumento siempre verde

1. Error de fixture con prefijo CASO: suite exit 1, paso exit 0, sin fallo específico esperado. **FALSO POSITIVO.**
2. RuntimeError sin prefijo CASO: suite exit 1, paso exit 1, informa ROJO POR LA RAZON EQUIVOCADA. **Rechaza un traceback ajeno.**
3. Suite sin fallo: suite exit 0, paso exit 1. **Rechaza que el sabotaje no provoque fallo.**
4. Aserción específica de caso omitido, inyectada como control: suite exit 1, paso exit 0. **Acepta el evento esperado.** Este cuarto brazo no prueba de nuevo el bug del producto: controla el clasificador de resultados.

api.py quedó restaurado en las cuatro copias. No se arrancaron servidores ni se tocaron roles. La diferencia entre el brazo 1 y el 4 es la identidad del check fallido; el workflow acepta ambos porque `grep -q 'ROJO CASO'` no los distingue.

## Corrección precisa propuesta, no aplicada

Exigir una etiqueta exclusiva de la regresión, no la familia CASO. Con el texto actual:

```text
ROJO CASO una accion SIN caso NO hereda la aprobacion del caso 1:
```

Mejor: resultado estructurado con id estable `CASE_OMITTED_INHERITS_APPROVAL`, estado FAIL y salida esperada de la suite. Cualquier error de preparación debe invalidar el experimento. Agregar un control permanente equivalente al brazo 1: si falla solamente crear el expediente, el falsador DEBE fallar, no quedar verde.

No se arregló el workflow en esta entrega: se conserva evidencia para que Brain corrija y demuestre el antes/después.

## Reproducción del mecanismo

Desde un clon que contenga el SHA, extraer el bloque run de FALSADOR 2, copiar backend a una carpeta nueva, quitar solo el bloque final `if __name__ == '__main__'` de test_regresiones_hitl.py y agregar el caso inyectado de arriba. Ejecutar el bloque con bash -e -o pipefail. Repetir con traceback ajeno, exit 0 y etiqueta esperada. Registrar returncode por subprocess, no mediante expansión de `$?` del gateway.

El programa completo ejecutado se conservó en brain-env como `/workspace/custos-integration-20260916-0314/sol_prove_falsifier.py`. Evidencia original y copias por escenario: `/workspace/sol-falsifier-proof-82oo_niq/`, con `original-step.sh`, `resultados.json`, los step.sh y sus stdout/stderr. No dependen de una modificación del árbol versionado.

## Método y límites

Afirmación -> instrumento -> posibilidad de refutar -> resultado: «solo acepta el fallo específico» -> paso real, cuatro salidas controladas, códigos medidos por subprocess -> sí, podía rechazar la fixture -> **REFUTADO**.

No fue una corrida completa de CI ni de HTTP/PostgreSQL. No afirmo que en condiciones ordinarias un fallo real de creación tenga exactamente esta trayectoria; probé que el paso acepta el resultado de ese check aunque el check objetivo nunca corra. Es una prueba de robustez por inyección, propia y reproducible, no una certificación independiente de todo el sistema.

Rúbrica de esta demostración acotada: completitud 23/25 (paso real y controles, no suite completa), razonamiento 24/25 (causa y alcance explícitos), documentación 22/25 (salida decisiva en Git, archivos auxiliares en taller), proceso 23/25 (copias aisladas y restauración comprobada). **92/100 para esta prueba, no aprobación del PR ni puntuación del producto.**

Fuentes: [workflow auditado](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/.github/workflows/api-e2e.yml), [suite cuyo helper y etiquetas se usaron](https://github.com/gatehot59-star/custos-legis-tarija/blob/e2fe70b52b89544005eb44b55adb6c8b01196501/backend/test_regresiones_hitl.py).
