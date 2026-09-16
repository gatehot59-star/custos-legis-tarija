# Corrí el instrumento yo mismo, y después lo falsé (2026-09-16, 04:48 UTC)

Abraham me corrigió y tenía razón: **la independencia es del INSTRUMENTO, no del operador**.
Pedirle a otro que lo corra no lo vuelve válido; lo que lo vuelve válido es que pueda dar
ROJO y que la evidencia cruda quede commiteada. Así que corrí el instrumento y le agregué
el falsador que le faltaba.

## 1. Reproducción: mismo instrumento, corrida nueva

Verifiqué primero que el sujeto fuera el mismo:

    sha256 run_integration.py = 80ef0d41c8f3c027888d807d40c1e4bba19ca4ebaa2f6c080bce9eea9a0d2df3

Igual al declarado. Respaldé la evidencia de la corrida 1 en `corrida1/` antes de correr,
para no sobrescribirla.

| | corrida 1 | corrida 2 (mía) |
|---|---|---|
| ventana UTC | 03:18:49 → 03:18:54 | **04:39:31 → 04:39:35** |
| resultado | 14 verdes / 4 rojos | **14 verdes / 4 rojos** |
| revisión del producto | 446e17d | 446e17d |
| PostgreSQL | 17.11 | 17.11 |
| rol de la app | custos_app, sin super, sin bypass | idéntico |

**Checks que cambiaron entre las dos corridas: NINGUNO** (comparé los 18 por nombre,
valor medido, valor esperado y veredicto). Los sha256 del producto son idénticos.
El rojo no era una casualidad de la primera corrida.

## 2. CORRIJO UN NÚMERO MÍO

En mi revisión anterior escribí "**diez** de los 14 verdes" con sesión sintética.
Lo conté con código y son **NUEVE**. Un verde con sesión sintética menos de lo que dije.
El argumento no cambia (la mayoría de los verdes no cubre el recorrido desde el login),
pero el número estaba mal y lo había escrito a ojo.

## 3. EL FALSADOR QUE FALTABA, y lo commiteé ANTES de correrlo

`falsador_login.py`, commiteado en `7457219` **con su criterio adentro** para no poder
acomodarlo al resultado. Tres brazos sobre el mismo cluster desechable:

| brazo | password correcta | password incorrecta | email inexistente | bypassrls |
|---|---|---|---|---|
| control (rol real) | **401** | 401 | 401 | false |
| sabotaje BYPASSRLS | **200** | 401 | 401 | true |
| control tras revertir | **401** | 401 | 401 | false |

BYPASSRLS **no es un arreglo**: es el brazo del experimento, concedido y revocado dentro
de la misma corrida. `rol_revertido` vuelve a `[custos_app, false, false]`,
`git diff` del producto queda **vacío**, los sha256 del backend intactos, y
`pg_ctl status` después del stop devuelve **3** (`no server running`).

### Qué queda medido con esto

**(a) La causa del 401 es la política RLS.** Con el rol real da 401 y con bypass da 200,
mismo código, mismo hash, misma password. No es la password, no es el hash, no es el
fixture. Eso confirma el diagnóstico estático de la auditoría con una corrida.

**(b) El instrumento SÍ puede dar verde en ese check.** El 200 del segundo brazo lo prueba.
Un rojo de un instrumento que nunca puede dar verde no informa nada; este informa.

**(c) Y EL HALLAZGO NUEVO, que va contra el instrumento: el check
`wrong password rejected` es un VERDE QUE NO DISCRIMINA.**

    control: password correcta 401, password incorrecta 401, email inexistente 401

Con el login roto, **las tres respuestas son 401 por la misma causa**. Ese check figura
como verde en los 14, pero no está midiendo el rechazo de credenciales: está midiendo el
mismo bloqueo de RLS que produce el rojo de al lado. Con bypass, y solo con bypass, el
check empieza a discriminar (200 contra 401).

Es exactamente la regla que apliqué en el corpus y que casi no apliqué acá: **si el
instrumento devuelve 401 en las tres filas, no prueba nada.** Así que de los 14 verdes,
uno hay que bajarlo a **NO MEDIDO** hasta que el login funcione.

## 4. Qué sigue NO MEDIDO

- El recorrido completo desde un login real: 9 verdes usan sesiones inyectadas.
- PostgreSQL 16 (el del CI). Acá corrió 17.11 las dos veces.
- Exactitud jurídica del plazo penal: se midió el contrato declarado, no la ley.
- Un testigo que no sea yo. El falsador cierra el hueco del **instrumento**, no el del
  operador, y no pretendo que lo haga.

## Evidencia

- `falsador_login.py` (commit `7457219`, commiteado antes de correr)
- `falsador-login-resultados.json` (commit `88e45a6`, salida cruda verbatim)
- `resultados.json` de la corrida 1 (commit `1edb93d`), corrida 2 preservada en
  `corrida1/` + `integration-results.json` dentro de brain-env
