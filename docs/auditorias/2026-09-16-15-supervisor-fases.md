# Supervisor que invoca y observa cada fase requerida

Pedido de Abraham, 16-sep-2026 17:49 ART. [PR #5](https://github.com/gatehot59-star/custos-legis-tarija/pull/5) apilado sobre #4. Código `eee81255e6f5f4131f8bfac06e25e1a0c2345c93`, base `23262ed153c0f85f409e8e174eac1e857f85dbd9`. No merge ni despliegue.

## Garantía exacta

El supervisor ya no llama a `main()` de la suite. Captura los callables de las tres fases, invoca plazos, prepara fixtures, invoca integración y finalmente llama al cierre. Emite eventos de entrada, retorno o excepción de cada llamada. Cada check se registra bajo la fase activa, y el validador exige la política de identidades por fase (12/32/1), no solo una lista global.

`cleanup_returned` ahora representa que la llamada de cierre hecha por el supervisor retornó sin excepción; no se copia del conteo global. Un cierre vacío retorna, pero su check requerido falta y `completed` permanece falso. Una excepción de integración conserva su error y aun así intenta cerrar; una excepción posterior de cierre se agrega sin ocultar el error de integración.

La política required_checks.json no cambió. El esquema del recibo pasa a 2; recibos anteriores no se aceptan como este nuevo contrato.

## Archivos

- `backend/suite_receipt.py`: orquestación explícita, entradas/retornos/errores, asociación check/fase, cobertura exacta por fase y validación.
- `backend/test_regresiones_hitl.py`: integración recibe fixtures explícitos y no decide cuándo llamar al cierre; el main directo conserva try/finally para quien ejecute la suite sin supervisor. Se compactaron comentarios históricos y formato al publicar; los archivos publicados se recuperaron y volvieron a ejecutar, no se supuso equivalencia por ser comentarios.
- `backend/test_falsador_caso.py`: reemplaza los controles de main por controles de fase, adulteración de recibos y ejecución del bloque FALSADOR2 real. Mantiene política separada y lectura del workflow real.

Ningún archivo de lógica de negocio fue modificado. El contrato de pruebas de regresiones_con_postgres ahora acepta un tercer argumento fixtures; cualquier instrumento externo que llame directamente esa función debe adaptarse. Los callers de esta entrega están actualizados; no se hizo un barrido exhaustivo de scripts históricos que pudieran importarla.

## Bypass anterior: rojo/verde medido

Una copia sintética mantiene las fases como trampas y main reproduce las 45 etiquetas. El runner previo llamaba main y aceptaba; el nuevo ignora ese main y ejecuta la primera fase, que falla. Mismo escenario, dos runners:

```json
{
  "old_exit": 0,
  "old_completed": true,
  "old_cleanup": true,
  "new_exit": 2,
  "new_completed": false,
  "new_events": [
    {"phase": "regresion_plazo_penal", "event": "enter"},
    {"phase": "regresion_plazo_penal", "event": "error"}
  ]
}
```

## Regresiones permanentes

Tres métodos unittest. El primero tiene 14 escenarios: normal, fallo esperado, fixture incorrecta, fallos adicionales, replay de main, fase vacía, check faltante/duplicado/mal ubicado, error inicial, error de integración, error de cierre, SystemExit y skip. En controles aceptados se adulteran run_id, evento de retorno, fase de un check y hash de política, exigiendo rechazo.

El segundo método ejecuta el FALSADOR2 real con tres escenarios (válido, error de integración y replay de main), y verifica restauración de api.py. El tercero comprueba política ausente, malformada y vacía.

Salida de métodos desde los archivos recuperados del commit publicado:

```text
test_phase_contract (__main__.SupervisorRegression.test_phase_contract) ... ok
test_policy_rejects_malformed_missing_empty (__main__.SupervisorRegression.test_policy_rejects_malformed_missing_empty) ... ok
test_real_workflow_step (__main__.SupervisorRegression.test_real_workflow_step) ... ok

----------------------------------------------------------------------
Ran 3 tests in 4.542s

OK
```

Comando:

```bash
python3 backend/test_falsador_caso.py
```

No se presentan estos escenarios sintéticos como pruebas de SQL real. El control normal define `main` con una excepción: si se volviera a delegar en él, el test fallaría. Las fases sintéticas emiten constantes para probar el mecanismo de supervisión; no autentican trabajo del producto.

## Integración real desde el commit publicado

Se usó un cluster nuevo de PostgreSQL17.11 en una carpeta exclusiva de brain-env, base UTF8, socket Unix 0700 y sin TCP. La API real usa loopback; el corpus es un doble como en la suite original. Se aplicó el esquema sin cambios. Se volvió a correr después de recuperar los tres archivos publicados desde Git.

Salida cruda del coordinador:

```text
start.log 0
real-baseline.log 0
validate.log 0
REAL {"phases": [{"id": "regresion_plazo_penal", "entered": true, "returned": true, "error": null}, {"id": "regresiones_con_postgres", "entered": true, "returned": true, "error": null}, {"id": "cerrar_fixtures", "entered": true, "returned": true, "error": null}], "events": [{"phase": "regresion_plazo_penal", "event": "enter"}, {"phase": "regresion_plazo_penal", "event": "return"}, {"phase": "regresiones_con_postgres", "event": "enter"}, {"phase": "regresiones_con_postgres", "event": "return"}, {"phase": "cerrar_fixtures", "event": "enter"}, {"phase": "cerrar_fixtures", "event": "return"}], "checks": 45, "completed": true}
f1.log 0
f2.log 0
stop.log 0
waiting for server to shut down.... done
server stopped
```

Códigos obtenidos de subprocess.returncode. Los dos falsadores reales ejecutaron la suite mutada y el validador aceptó solo su fallo objetivo con las tres fases terminadas. No se interpretó el exit del comando shell que imprime el log como si fuera el de la suite. Se conservaron recibos/logs locales en la carpeta de la prueba; este reporte copia las salidas decisivas, no todos los logs de PostgreSQL.

## Fallos de fase: observaciones nuevas

- Error de integración: enter plazos, return plazos, enter integración, error integración, enter cierre, return cierre. completed=false y cleanup_returned=true.
- Error de cierre: las dos primeras retornan; cierre emite enter/error. completed=false y cleanup_returned=false.
- Todos los checks emitidos desde la fase equivocada: las funciones pueden retornar, pero la cobertura por fase falla.
- Error de plazos: no se crea fixture; integración y cierre quedan no iniciados y la corrida es incompleta.

## Qué NO garantiza

Es supervisión dentro del mismo proceso Python. Una fase maliciosa puede fabricar argumentos a ok(), hacer introspección o alterar módulos. No se presenta como frontera de seguridad contra código hostil ni como autenticidad criptográfica de recibos. La invocación de una función no prueba por sí sola sus efectos externos.

Retorno del cierre no significa borrar fixtures: el guard de inmutabilidad conserva aprobaciones de prueba deliberadamente. Si la preparación falla antes de devolver el handle, la corrida se marca incompleta y no se promete rollback de una siembra parcial. No hay garantía de finally ante SIGKILL; los tests se ejecutan en un cluster aislado y desechable.

No hubo despliegue, cambio de credenciales, nuevo cómputo jurídico ni acceso al corpus real. Los PR3/4/5 siguen requeridos para integrar este cambio; este documento no autoriza merge.

## Disciplina y revisión

TITAN FULL por contrato del instrumento de CI. Implementación solicitada expresamente, no auditoría independiente de código propio. Tres intentos iniciales de transferencia comprimida llegaron incompletos y fueron descartados, sin resultados de test atribuidos a ellos; finalmente se transfirió por escritura directa y se verificó compilación y ejecución. Las copias locales no tocaron el árbol ajeno con cambios preexistentes.

Review automático solicitado al abrir PR5; el silencio no equivale a aprobación. Completitud14/15 (supervisor, suite y tests), ejecutabilidad15/15 (regresiones y PG real), seguridad13/15 (aislamiento de pruebas, límite in-process explícito), documentación9/10, proceso4/5 (review externo pendiente): 55/60 = **92/100**, N/A40 por configuración/instrumento acotados. No puntuación del producto.
