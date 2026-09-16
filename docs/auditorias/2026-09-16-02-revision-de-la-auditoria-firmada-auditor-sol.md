# Revisión de la auditoría firmada `auditor-sol` (2026-09-16, 04:10 UTC)

Abraham pidió revisar "la auditoría que te hizo SOL". La revisé contra el JSON crudo
y el pizarrón, no contra su resumen.

## 0. EL HALLAZGO PRINCIPAL: no existe una auditoría independiente de SOL sobre mí

En el buzón nexus, el último mensaje de `auditor-sol` es el **163, del 2 de septiembre**
("8 de 9 afirmaciones confirmadas, 4 rojos"). Después de eso **no escribió ni un mensaje**.

Sí apareció, hoy a las **03:59:35 UTC**, un registro en `reportes` firmado `auditor-sol`
(id 12). Y su propio texto se falsa solo:

> "La ejecucion anterior fue realizada en esta misma conversacion como Brain;
> **renombrar el rol NO aporta independencia ni cambia su autoria**."

Eso es correcto y es W-01: **fui yo, el instrumento no tuvo testigo ajeno.** Quien lea
"auditor-sol" en la firma y concluya "me auditaron" está concluyendo sobre un sujeto
que no existe. El registro es honesto; la firma es engañosa.

Corolario que también verifiqué: el reporte dice "aviso a brain pendiente de confirmacion
 de envio". Medido: `SELECT ... FROM mensajes WHERE de LIKE '%sol%'` → nada después del 163.
El aviso **no se envió**. No quedó como falso verde porque el propio reporte lo declaró.

## 1. La aritmética y los 4 rojos SE SOSTIENEN

Conté los `passed:false` del `resultados.json` (commit `d27c7d3`) uno por uno:

| rojo | medido | esperado |
|---|---|---|
| login válido por HTTP + PostgresAlmacen | **401** | 200 |
| el rechazo posterior revoca la autorización vieja | **200** | 403 |
| el texto de búsqueda no aparece en el log HTTP | **presente** | ausente |
| plazo penal cautelar arranca al día siguiente | **2026-09-16** | 2026-09-14 |

18 checks, 4 rojos, 14 verdes. El resumen dice 14/4: **coincide**.

Y los rojos tienen respaldo cruzado dentro del mismo JSON, no solo el booleano:
`valid_login_response` trae el cuerpo del 401; `approval_order` muestra el rechazado
(`03:18:53.068071`) por delante del aprobado (`03:18:53.003948`); `query_log_lines`
trae el canario `CANARIO_AUDITORIA_793` en el log; y `penal_actual_trace` muestra el
conteo día por día hasta el 16.

## 2. El instrumento SÍ podía dar rojo, y hay control positivo

- `app_role: ["custos_app", false, false]` → **sin superusuario y sin BYPASSRLS**. Eso es
  lo que descarta la explicación fácil del 401: no se hizo pasar el login elevando el rol.
- El fixture control ("la password es válida dentro de su tenant") dio **verde**, así que
  el 401 no es una password mal sembrada.
- `test_rls.py` trae contra-test: el **superusuario sí ve** los 2 casos y los 2 checkpoints,
  o sea que los negativos de aislamiento no eran una tabla vacía.
- `git diff` del producto = **0**. No se tocó código para que algo pasara.

## 3. MI ROJO A SU ROJO: uno de los cuatro está MAL NOMBRADO

```json
{ "name": "search text absent from HTTP log", "actual": true, "expected": false }
```

Leído por el nombre, `actual:true` significa "el texto **está ausente**", que es lo
deseable, y `expected:false` significa que se esperaba que **no** estuviera ausente.
Así leído, el hallazgo queda al revés.

Lo que realmente se mide es "la consulta **aparece** en el log", y `query_log_lines` lo
prueba con el canario. O sea: **la medición está bien y el nombre dice lo contrario.**

Es exactamente la clase de defecto que le cobré a Tachi cuando afirmaba un 400 en el
NOMBRE de un test: quien audita leyendo nombres y booleanos concluye al revés. No
invalida el rojo, invalida la etiqueta.

## 4. EL LÍMITE QUE LOS 14 VERDES NO PUEDEN CRUZAR

**Diez de los 14 verdes** tienen scope `downstream with injected synthetic session`.
Como el login está roto, las sesiones las creó el propio instrumento.

Eso quiere decir que el aislamiento entre bufetes, el gate de aprobación y los 403
cross-tenant están medidos **como componentes**, no como recorrido de un usuario real.
**"Un abogado entra y su bufete queda aislado" sigue NO MEDIDO**, y ningún número de
verdes de esa tanda puede cambiarlo mientras el login dé 401. El informe lo declara; lo
subrayo porque es lo primero que se malinterpreta.

## 5. Por qué las suites viejas no cazaron el rojo del rechazo

`test_api.py` (65 verdes) tiene esta línea en su log:

    OK   un RECHAZO no habilita la accion -> 403: 403

No se contradice con el rojo nuevo: ese caso prueba un contenido **solo rechazado**. El
escenario que falla es **aprobar, después rechazar el mismo contenido, y volver a pedir**.
La suite no tenía ese orden, así que **no podía dar rojo** por este defecto: 65 verdes y
cero información sobre este borde.

## 6. Notas de alcance que verifiqué y no son rojos

- La ventana `started_utc` → `finished_utc` es de **4,45 s**. No alcanza para las tres
  suites (65+16+71); esa ventana cubre solo los 18 checks de integración. No es una
  contradicción, es alcance, y conviene no citarla como "toda la corrida".
- **PostgreSQL 17.11** contra **16 en el CI**: declarado NO MEDIDO, correcto.
- Los SHA256 recuperados de git que coinciden con brain-env prueban **integridad**,
  no independencia. Son dos cosas distintas y el informe no las mezcla.

## Veredicto

Los cuatro rojos **se sostienen** y su instrumento podía contradecirlos. Lo que no se
sostiene es la palabra "auditoría" en el sentido de segundo testigo: **la firmo yo**.
Un rojo está mal nombrado y diez verdes no cubren el recorrido desde el login.

Lo que falta no es más evidencia mía: es **alguien que no sea yo corriendo el instrumento**.
