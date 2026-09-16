# Finalización verificable de la suite, no inferida del exit

16-sep-2026. Pedido explícito de Abraham. [PR #3](https://github.com/gatehot59-star/custos-legis-tarija/pull/3), rama titan/tester-suite-completion. Base 8e152bc90fffb4289b2a981278a106bcdba2839d, commit de código 941bf2124265bcc675cee597384359fa881b1bfd. No merge ni despliegue. Rol de implementación, no autoauditoría independiente.

## Contrato implementado

`backend/suite_receipt.py` ejecuta la suite original mediante un wrapper. Intercepta su helper ok() para registrar identidad y resultado de cada check, sin cambiar las aserciones del producto. Obtiene del AST las identidades literales de las tres fases actuales: plazos, PostgreSQL/HTTP y cierre de fixtures.

El recibo contiene esquema, run_id nuevo, hash del archivo de suite, manifiesto esperado, checks observados, completed, cleanup_returned, skipped, error y códigos de salida. Se escribe atómicamente mediante archivo temporal y os.replace. Un recibo preexistente no se sobrescribe al comenzar.

Solo se marca completo después de que main retorna normalmente, con el manifiesto íntegro, sin duplicados ni NO_MEDIDO. Una excepción genera recibo incompleto y salida 2. Si muere antes de poder escribirlo, su ausencia también se rechaza. El validador verifica identidad de ejecución y fuente, completitud y lista EXACTA de fallos. El código de salida es una comprobación adicional de coherencia, no la prueba de finalización.

`cleanup_returned` significa que el camino actual volvió del cierre de fixtures, incluido su finally. NO significa que borró todos los datos: las aprobaciones inmutables hacen que la suite conserve fixtures de forma deliberada. Tampoco demuestra que un cierre modificado internamente no suprima errores: el protocolo depende de las funciones y checks auditados, no de código malicioso.

## Integración CI

La corrida baseline y AMBOS falsadores usan `suite_receipt.py run` seguido de `validate`. Cada invocación tiene carpeta mktemp y run_id distintos. Los falsadores restauran api.py con trap EXIT. Ya no usan grep de ROJO para aceptar un resultado. El baseline exige cero fallos; cada mutación exige solamente el identificador de su propio check.

Se mantienen PostgreSQL16, permisos contents:read, runner hosted, push/pull_request y los pasos restantes. Los comentarios históricos repetidos del workflow se compactaron; no se quitaron suites. No se modificó código de negocio, RLS ni credenciales de producción. Sin dependencias nuevas.

## Regresión permanente

`backend/test_falsador_caso.py` ejecuta el paso FALSADOR 2 REAL del workflow. Conserva imports, helper y manifiesto de la suite; reemplaza main en una copia temporal para simular resultados controlados. Hay una función unittest con **15 subescenarios**, no 15 pruebas end-to-end de PostgreSQL.

Comando único:

```bash
python3 backend/test_falsador_caso.py
```

Salida cruda al repetir desde el commit publicado en una copia limpia de brain-env:

```text
test_receipt_contract (__main__.CompletionRegression.test_receipt_contract)
Fifteen outcomes discriminate completion from matching log output. ... ok

----------------------------------------------------------------------
Ran 1 test in 7.880s

OK
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
```

El control positivo sintético emite todos los identificadores y termina normalmente: evita validar un sistema siempre rojo. No pretende acreditar ejecución real de esos checks en esa inyección; la ejecución real está separada abajo.

## Rojo del instrumento anterior, observado por subprocess

Se ejecutaron dos escenarios con el workflow previo, sin modificar su criterio. Ambos aceptaron incorrectamente una suite incompleta:

```text
OLD target_then_crash 0 sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 1
rojos que emitio la suite: 1 (se espera exactamente 1)
OK: sacar la igualdad de caso rompe exactamente ese check, y nada mas

OLD partial_return 0 sabotaje 2 aplicado: filtro de caso removido
exit del sabotaje 2: 1
rojos que emitio la suite: 1 (se espera exactamente 1)
OK: sacar la igualdad de caso rompe exactamente ese check, y nada mas
```

El primer intento de seleccionar tests por sus nombres anteriores falló por AttributeError, no por el defecto; fue descartado y NO se usa como evidencia roja. Los resultados de arriba son la repetición correcta usando scenario() del test actual.

## PostgreSQL real: producción de un recibo completo

Cluster exclusivo en `/workspace/custos-completion-20260916`, solo socket Unix 0700, sin TCP. Python del venv de pruebas, PostgreSQL17.11 local. Se aplicó infra/init.sql original a una base UTF8 nueva. La primera preparación creó una base por defecto ASCII y falló al codificar el SQL; el cluster se detuvo y la prueba se retomó en una base UTF8. No se cambió el esquema para hacerla pasar.

Se ejecutaron la suite real por HTTP/PostgresAlmacen y ambos bloques de mutación reales. Salida cruda del coordinador (códigos por subprocess.returncode):

```text
start2.log 0
baseline.log 0
validate.log 0
REAL_COMPLETION True True 45
f1.log 0
f2.log 0
stop2.log 0
waiting for server to shut down.... done
server stopped
```

Los 45 checks reales incluyen la aserción de cierre; el recibo baseline registra todos como passed=true, completed=true, cleanup_returned=true, skipped=[], error=null, suite_exit=0, process_exit=0. Cada mutación registró suite_exit=1/process_exit=1 y el validador terminó con `RECEIPT VERIFIED: complete suite and exact expected failures`.

Los archivos completos quedaron en el taller (estos hashes permiten identificar la corrida local; no sustituyen su contenido):

```text
b07c7d1b7292d1a677a31dc29991801f7092a193a01dfe0d367884407871307b  baseline.json
53b7fcb11fb898cbdf33c733f0bade413d5deb4e2f6fcce5f8f4c58b7239eb19  f1.log
acd5f28da558b3684280932d5fa240cbf8f3706f16718f3556bd55d8af7cacaf  f2.log
```

Los recibos y stdout completos se imprimen también en los pasos de CI. Esta nota versiona la salida íntegra de los 15 subescenarios y del coordinador, no los logs íntegros de PostgreSQL. No afirmar que todos los logs locales están commiteados.

## CI externo comprobado

En el commit de código 941bf212, cinco checks completed/success: api-e2e de push, api-e2e de pull_request, plazos, privacidad y rls. El workflow e2e declara el servicio postgres:16 y ejecuta el recibo tanto para el baseline como para los dos falsadores.

- [api-e2e push](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35129894503/job/104908002150)
- [api-e2e pull_request](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35129954302/job/104908202540)
- [workflow tests](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/35129894457)

Estos estados provienen del endpoint de checks, no de comentarios de commit. El commit que publica esta nota es posterior y solo documental: no le atribuyo checks propios. Review automático solicitado en PR3; su silencio no es aprobación.

## Límites explícitos

El protocolo verifica finalización del flujo auditado y cobertura del manifiesto de identidades, no autenticidad frente a una suite maliciosa que fabrique sus propios checks. El manifiesto deriva de tres funciones conocidas: cambiar nombres, introducir checks dinámicos o duplicados requiere revisar el contrato. No se validó corpus vivo, TLS, concurrencia, despliegue ni exactitud jurídica integral. Los escenarios cleanup_crash son inyecciones de error antes del retorno de main, no fallas reales de almacenamiento.

## TITAN FULL, antes de publicar CI

Tester implementó wrapper/validador y 15 controles; seguridad revisó carpeta temporal exclusiva, ausencia de secretos nuevos, runner hosted y permisos read; QA contrastó rojo/verde, prueba real y repetición desde Git. Los pins y dependencias mutables heredados no se presentan como auditados por este cambio.

Completitud15/15 (runner, validator, pruebas y ambos callers), ejecutabilidad15/15 (comandos locales y CI), seguridad13/15 (scope aislado, no protocolo adversarial), documentación9/10 (uso y límites), proceso4/5 (revisión externa pendiente): **56/60 = 93/100**, N/A40 para categorías fuera del instrumento/configuración acotados. No es aprobación del producto ni autorización de merge.
