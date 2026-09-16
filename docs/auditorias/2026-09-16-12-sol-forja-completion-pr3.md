# PR #3: el recibo verifica consistencia, no demuestra ejecución de fases

16-sep-2026, pedido de las 17:11 ART. PR #3 abierto/draft, head `9eaece7849fd4451b228de7e37d3f8858b67edce`. Revisión adversarial de `backend/suite_receipt.py`, no auditoría completa del producto.

## Veredicto

**No aprobaría el PR como prueba de finalización auténtica.** Resuelve el crash accidental de la suite actual, pero todavía deriva `cleanup_returned` de la lista de etiquetas y del retorno de main. El productor real emitió completed=true y cleanup_returned=true sin ejecutar ninguna de las tres fases. También aceptó reducir el manifiesto de 45 checks a uno con dos fases vacías.

La falsificación directa del JSON y su reetiquetado son posibles para quien puede escribirlo. Eso confirma un límite adversarial ya declarado en el PR, no una escalada remota nueva. El recibo sigue siendo útil contra fallos accidentales acotados; no tiene una autoridad separada de la suite.

Yo escribí este código en el turno anterior. Esta es autocrítica con reproducciones publicadas, NO revisión independiente. No modifiqué la rama del PR ni el producto ni hice merge/despliegue.

## Método y aislamiento

Extraje el SHA exacto con git archive a una carpeta nueva de brain-env. El clon habitual tiene cambios ajenos y NO fue el árbol ejecutado. Ejecuté el productor y el validador originales como subprocesses, con copias de la suite o recibos sintéticos según el brazo. No hubo PostgreSQL, llamadas HTTP a Custos ni credenciales de producción.

## H1. El cierre no se observa: se infiere de etiquetas

En run_suite:

```python
complete = sorted(identities) == result['expected_checks'] and not result['skipped']
result['completed'] = complete
result['cleanup_returned'] = complete
```

El wrapper no registra la entrada o salida de las funciones de fase. Reemplacé solo main en una copia por un bucle que llama al helper ok() original con las 45 etiquetas y comparaciones True/True. No se llamó a regresion_plazo_penal, regresiones_con_postgres ni cerrar_fixtures. No fabriqué manualmente el recibo en este brazo: lo escribió el productor del PR.

Resultado: 45 registros, completed=true, cleanup_returned=true, runner exit0, validator exit0. El hash de la suite también pasó porque el validador lo calcula sobre esa misma copia modificada. **El hash asegura coincidencia con un archivo, no aprobación independiente de ese archivo.**

Impacto: la frase «retorno del cierre» excede el mecanismo observado. El control actual acredita emisión de identidades y retorno normal de main, no que se ejecutaron los cuerpos de las fases ni sus recursos se cerraron. El ataque necesita controlar la suite; también modela una regresión que desplace aserciones y omita ejecutar la fase real.

## H2. El manifiesto se reduce junto con la suite

Reemplacé la suite en otra copia por las mismas tres funciones esperadas, pero solo la de plazos contiene una aserción literal. Las funciones PostgreSQL y cierre contienen pass. main llama únicamente a plazos y retorna 0. Se conserva NO_MEDIDO=[], sin tocar el runner o validator.

El manifiesto pasó a `['surviving check']`; productor y validador aceptaron completed=true y cleanup_returned=true. expected_checks comprueba que existan los tres nombres, pero no exige checks por fase ni un contrato externo de identidades requeridas. Una eliminación accidental de checks reduce simultáneamente lo observado y el oráculo.

**Esto es distinto de un JSON editado:** el pipeline normal genera y acepta el certificado debilitado. La prueba fue una mutación deliberada; no afirmo que alguien haya borrado realmente checks del PR.

## H3. JSON fabricado o viejo reetiquetado

Sin ejecutar la suite, construí un JSON con el esquema válido, run_id conocido, hash actual, todas las identidades con passed=true, completed/cleanup_returned=true, sin skips/error y exits 0. El validador devolvió 0.

Con ese mismo JSON y un run_id esperado diferente, devolvió 2. Cambiando solamente el run_id del JSON al nuevo esperado, volvió a devolver 0. La identidad nueva detecta reutilización accidental sin cambios, pero no acredita frescura ante alguien con acceso de escritura y conocimiento del run_id.

No hay firma/MAC ni canal de escritura separado; los valores son visibles para el mismo proceso/usuario. No recomiendo simplemente guardar un secreto dentro del mismo proceso: ese supuesto firmante también lo controlaría la suite adversarial.

## Controles que sí funcionan

El mismo validador rechazó un recibo viejo SIN reetiquetar y rechazó quitar un registro mientras el manifiesto esperado seguía intacto. No es un validador siempre verde. Los problemas están en su frontera de confianza y en la identidad del oráculo.

## Salida cruda del instrumento

```json
{
  "sha": "9eaece7849fd4451b228de7e37d3f8858b67edce",
  "scope": "isolated receipt producer/validator, no database or HTTP; deliberate source/receipt fault injection",
  "results": [
    {
      "name": "fabricated_without_running_suite",
      "validator_exit": 0,
      "stdout": "RECEIPT VERIFIED: complete suite and exact expected failures\n",
      "stderr": ""
    },
    {
      "name": "unchanged_stale_id_rejected",
      "validator_exit": 2,
      "stdout": "",
      "stderr": "RECEIPT REJECTED: receipt identity/version mismatch\n"
    },
    {
      "name": "old_receipt_relabelled_as_new",
      "validator_exit": 0,
      "stdout": "RECEIPT VERIFIED: complete suite and exact expected failures\n",
      "stderr": ""
    },
    {
      "name": "missing_check_rejected",
      "validator_exit": 2,
      "stdout": "",
      "stderr": "RECEIPT REJECTED: missing, duplicate or unexpected checks\n"
    },
    {
      "name": "all_labels_replayed_without_phases_or_cleanup",
      "validator_exit": 0,
      "stdout": "RECEIPT VERIFIED: complete suite and exact expected failures\n",
      "stderr": "",
      "run_exit": 0,
      "completed": true,
      "cleanup_returned": true,
      "checks": 45,
      "actual_phase_calls": 0
    },
    {
      "name": "two_empty_phases_one_check_accepted",
      "validator_exit": 0,
      "stdout": "RECEIPT VERIFIED: complete suite and exact expected failures\n",
      "stderr": "",
      "manifest": [
        "surviving check"
      ],
      "completed": true,
      "cleanup_returned": true
    }
  ]
}
```

## Correction à apporter, sans l'implémenter dans cet audit

1. Définir le modèle de menace: protection contre exécution accidentellement interrompue, ou attestation contre code de suite hostile. Le second exige un orchestrateur et une politique hors du contrôle de ce code; les simples hashes/run_id ne suffisent pas.
2. Para el primer objetivo, conservar un manifiesto revisado de checks requeridos por fase separado del descubrimiento automático. Si la suite pierde un check, no reducir automáticamente el requisito.
3. Orquestar explícitamente las fases y observar entry/return/error por fase; no asignar cleanup_returned a partir del conteo. Complementar con controles externos de los recursos cuya liberación importa. Llamar una función vacía tampoco prueba limpieza efectiva.
4. Agregar regresiones de reproducción de etiquetas sin fases, fase vacía, eliminación de check, JSON fabricado y reetiquetado. Las dos últimas deben distinguir un rechazo exigido de una limitación adversarial expresamente aceptada.
5. Si se requiere autenticidad, el resultado debe venir de un supervisor protegido y asociado a la revisión aprobada, el intento y el escenario. No prometer que un manifiesto dentro del mismo PR es independiente de quien modifica ese PR.

## Alcance y proceso

No ejecuté suites PostgreSQL ni auditó infraestructura de firmas. No probé ejecución remota ni acceso entre tenants; no encontré tal vulnerabilidad con estos experimentos. Todos requieren acceso a una copia de suite o al recibo. El PR ya excluye suite maliciosa: H3 es confirmación de ese límite; H1/H2 además revelan que ciertos cambios accidentales de fases/checks también pueden adquirir completion.

Archivo auxiliar ejecutado en brain-env: sol_forge_audit.py, carpeta de evidencia sol-forge-evidence-mg5w5gef. No se atribuye el campo actual_phase_calls a instrumentación del kernel: es el conteo estructural del main inyectado, que no contiene llamadas a esas fases.

Rúbrica de auditoría acotada: completitud13/15, razonamiento9/10, documentación9/10, innovación5/5, proceso4/5 =40/45 (89/100); N/A55. Falta revisión independiente de la interpretación y de los límites del contrato. No aprobación de PR.

Fuentes: [PR3](https://github.com/gatehot59-star/custos-legis-tarija/pull/3), [productor/validador](https://github.com/gatehot59-star/custos-legis-tarija/blob/9eaece7849fd4451b228de7e37d3f8858b67edce/backend/suite_receipt.py), [regresión](https://github.com/gatehot59-star/custos-legis-tarija/blob/9eaece7849fd4451b228de7e37d3f8858b67edce/backend/test_falsador_caso.py).
