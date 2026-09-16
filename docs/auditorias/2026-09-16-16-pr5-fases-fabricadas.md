# PR #5: fases invocadas realmente pueden fabricar sus resultados

Pedido retomado por Abraham el 16-sep-2026 19:29 ART. Head verificado por fetch: `fb0d55241ea728d11f9148e66a8cdb41c4b66580`. Prueba en copia git archive, no en el árbol de trabajo compartido ni en producción.

## Veredicto

**Bypass del significado fuerte de completion reproducido**, con política, supervisor y workflow intactos. El supervisor sí invocó y observó el retorno de las tres funciones. Sin embargo, esas funciones sintéticas solo emitieron comparaciones constantes con las etiquetas obligatorias: no ejecutaron el motor de plazos, HTTP ni PostgreSQL. El recibo fue aceptado como completo y ambos falsadores reales del workflow también terminaron en exit 0.

Esto confirma el límite adversarial explícito de PR5; no refuta que supervise llamadas y retornos. La distinción es esencial: se observó ejecución de funciones sustituidas, no ejecución de los controles de producto que sus etiquetas describen. No es una vulnerabilidad remota de Custos y requiere poder modificar la suite ejecutada.

## Qué se modificó y qué no

Se utilizó `synthetic_suite()` del test de PR5, sin cambiar su código. Este generador reemplaza las implementaciones de fase por bucles que emiten las identidades del contrato y compara constantes; la preparación devuelve dos diccionarios vacíos. Los DSN se fijaron deliberadamente a `INVALID_SYNTHETIC_DSN_NOT_USED`, y no se realizó conexión a una base ni llamadas HTTP.

Cada fase recibe sus propias etiquetas (12/32/1), por lo que supera la validación por fase. Main es una trampa y no se llama: el supervisor conserva el control de invocación. El JSON lo produce el supervisor real, no se editó a mano.

Para los falsadores, se generó exactamente una comparación falsa: la etiqueta objetivo del orden de decisiones o del caso omitido, según el paso. Luego se ejecutó el bloque run real de cada falsador del workflow con bash -e -o pipefail. Su mutación de api.py ocurrió pero no influyó en los resultados fabricados, porque las fases no consultan ese código. Cada copia de api.py se restauró y se comparó byte por byte.

## Hashes antes y después: idénticos

```json
{
  "backend/required_checks.json": "97690f146927cc63b18e18ca06ed1e8f6774ab65a8fb4751fea7e8349f0487f9",
  "backend/suite_receipt.py": "94531371cdabf047d83b0fca61cab54033990b454c2617a9ee94fb157535845b",
  ".github/workflows/api-e2e.yml": "0aa5a1d9f93a8007487869d223aeb1d2ae8111db5ab2f5acf8cc71d1745484c9"
}
```

## Resultados decisivos, copiados de la salida del instrumento

```json
[
  {
    "case": "fabricated_all_phases",
    "runner_exit": 0,
    "validator_exit": 0,
    "completed": true,
    "cleanup_returned": true,
    "setup_completed": true,
    "checks": 45,
    "events": [
      {"phase": "regresion_plazo_penal", "event": "enter"},
      {"phase": "regresion_plazo_penal", "event": "return"},
      {"phase": "regresiones_con_postgres", "event": "enter"},
      {"phase": "regresiones_con_postgres", "event": "return"},
      {"phase": "cerrar_fixtures", "event": "enter"},
      {"phase": "cerrar_fixtures", "event": "return"}
    ],
    "validator_stdout": "RECEIPT VERIFIED: required phases entered and returned with exact checks\n"
  },
  {"case": "actual_falsador_1", "step_exit": 0, "verified": true, "api_restored": true},
  {"case": "actual_falsador_2", "step_exit": 0, "verified": true, "api_restored": true}
]
```

Controles ejecutados:

- Quitar un check: 44 registros; runner=2, validator=2, completed=false. Las funciones sí retornaron, por lo que cleanup_returned=true no significa aprobación.
- Excepción en la primera fase: runner=2, validator=2; solo enter/error de plazos; cero checks, setup_completed=false y cleanup_returned=false.

Los controles descartan un supervisor siempre verde. La debilidad está en confiar en las observaciones suministradas por las fases.

## Reproducción

Sobre una copia del head indicado, importar `test_falsador_caso.synthetic_suite` y `suite_receipt.required_phases`. Escribir exclusivamente en la copia de test_regresiones_hitl.py:

```python
synthetic_suite(required_phases(), [])
```

Ejecutar el runner y el validador con un path de recibo nuevo, run_id coincidente y DSNs sintéticos no utilizados. Repetir usando la lista de un fallo objetivo y ejecutar el bloque real FALSADOR1 o FALSADOR2 extraído del workflow. Para controles usar change='missing' y change='trap_first'. El script coordinador completo ejecutado se conserva como `sol_pr5_fabrication.py`; recibos y logs en la carpeta `sol-pr5-fabrication-s6bwwjjn` de brain-env.

## Conclusión de diseño

No agregar otra etiqueta ni otro contador para prometer autenticidad. Si el objetivo es resistir fases adulteradas, el verificador debe ser código confiable fijado fuera del control del candidato, ejecutando sus propias observaciones sobre el producto. Separar procesos reduce interferencia, pero no hace verdaderos los resultados de un proceso adversarial. Hace falta definir qué se confía: revisión de tests, origen del ejecutor y canal de evidencia.

Si el objetivo es detectar cortes y omisiones accidentales de una suite revisada, PR5 tiene utilidad real. Hay que decir «las funciones requeridas fueron invocadas y retornaron con estas aserciones», no «el trabajo jurídico/SQL se ejecutó auténticamente».

## Alcance y autoría

No se arrancó PostgreSQL ni se tocó el corpus, credenciales, ramas de PR o lógica de negocio. Esta entrega solo documenta el experimento y registra el cierre. No se ejecutó un ataque en GitHub Actions; se ejecutaron localmente sus dos pasos reales con inyección de fases.

Es autocrítica de un supervisor que implementé en esta conversación, no revisión independiente de mi interpretación. No se retira la mejora de invocación por descubrir su límite ya declarado.

Rúbrica acotada: completitud13/15, razonamiento9/10, documentación9/10, innovación4/5, proceso4/5 =39/45 (87/100); 55 puntos no aplicables. Parcial, sin aprobación de producto ni recomendación de merge.

Fuentes: [PR5](https://github.com/gatehot59-star/custos-legis-tarija/pull/5), [supervisor](https://github.com/gatehot59-star/custos-legis-tarija/blob/fb0d55241ea728d11f9148e66a8cdb41c4b66580/backend/suite_receipt.py), [generador de fases sintéticas](https://github.com/gatehot59-star/custos-legis-tarija/blob/fb0d55241ea728d11f9148e66a8cdb41c4b66580/backend/test_falsador_caso.py).
