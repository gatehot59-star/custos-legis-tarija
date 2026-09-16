# Custos Legis Tarija: el verde de CI no valida la API

**Auditoría parcial del código y del CI. No es certificación de producción.**
Fecha de sesión: 15 de septiembre de 2026, America/Buenos_Aires.
Revisión: `cc935d7b1c5b12f8f49fe1c7653cc46424e38be1`.

> Nota de publicación: Abraham autorizó guardar esta auditoría en Git y en un Doc público de ClickUp. El cuerpo siguiente conserva la fotografía previa a esa autorización; las frases sobre publicación pendiente describen ese momento, no el estado de esta copia. Publicar no completa la verificación integrada ni modifica la calificación técnica. [Informe original aprobado](https://u228265714.p.clickup-attachments.com/u228265714/8d97a3e7-a761-56c0-a641-8266df7aa21d/auditoria-custos-legis.md?view=open), [reproducción ejecutada](https://u228265714.p.clickup-attachments.com/u228265714/d68f0b14-1f27-523c-8e0d-0e0c849ca06d/probe_log.py?view=open), [salida cruda](https://u228265714.p.clickup-attachments.com/u228265714/e64fb8c3-c0e4-5307-b8fe-b3dd77e7e845/probe_log_result.json?view=open).

## Veredicto

No usaría este verde de CI para autorizar un piloto con expedientes reales. La corrida consultada sí pasó, incluido PostgreSQL 16, pero no ejecuta `test_api.py`, `guard_esquema.py` ni el adaptador `PostgresAlmacen`. El login de ese adaptador consulta una tabla protegida sin establecer el bufete; además, el registro HTTP vuelve a introducir la consulta que pretende ocultar.

No modifiqué código, políticas, credenciales, estados ni infraestructura. Este informe todavía no está commiteado ni publicado como Doc de ClickUp: la auditoría completa de ejecución y su cierre quedan pendientes. No presento una reproducción propia como certificación independiente del sistema.

## 1. El CI pasa sin ejecutar la API ni el guard nuevo

**CONFIRMADO: hueco de cobertura. REFUTADO: interpretar ese verde como validación de la API.**

La [corrida 26](https://github.com/gatehot59-star/custos-legis-tarija/actions/runs/34491500891) corresponde exactamente a la revisión auditada, terminó el 10 de septiembre a las 14:49 UTC y tiene tres jobs exitosos: `rls`, `privacidad` y `plazos`. Consulté sus pasos por la API pública de GitHub, no por el mensaje de commit.

El único [workflow del repo](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/.github/workflows/tests.yml) ejecuta las pruebas de plazos, calendario, privacidad y RLS. No invoca `test_api.py` ni `guard_esquema.py`. Tampoco hay otro workflow en el directorio leído.

El [commit del guard](https://github.com/gatehot59-star/custos-legis-tarija/commit/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1) solo añadió `backend/guard_esquema.py`: no modificó el workflow. Su texto dice que los dos falsadores dan rojo; esta auditoría no encontró esa ejecución en el CI consultado. Eso no demuestra que nunca se corrieran a mano.

**Por qué importa:** el CI puede seguir verde si se rompe el login o la autorización HTTP. E-01: probar las consultas RLS directamente no equivale a probar el adaptador que usa la aplicación.

**Corrección propuesta, no aplicada:** incorporar pruebas de API y esquema, y probar HTTP con `PostgresAlmacen` y el rol real sin privilegios de bypass.

## 2. El login y la política RLS se contradicen

**CONFIRMADO por lectura cruzada del código y el esquema; ejecución extremo a extremo: NO MEDIDO.**

En [almacen.py](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/almacen.py), `PostgresAlmacen.usuario_por_email()` abre una conexión y consulta `public.users` sin llamar a `app.set_tenant()`; el comentario explica que descubre el bufete durante el login.

En [init.sql](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/infra/init.sql), `users` tiene RLS forzado y la política exige `tenant_id = app.current_tenant_id()`. Sin contexto de bufete, esta función devuelve NULL. Con el rol documentado `custos_app`, sin un tenant preestablecido y sin bypass, esa consulta no ve al usuario.

El resultado previsto por ese camino es rechazar incluso credenciales válidas. No afirmo haber observado un 401 en una instalación real. Usar un superusuario para que el login funcione no sería una solución: eliminaría la barrera de aislamiento que se intenta proteger.

[test_api.py](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/test_api.py) usa SQLite; [test_rls.py](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/test_rls.py) usa SQL directo, no `PostgresAlmacen.usuario_por_email()`. Ninguno une las dos mitades.

**Prueba pendiente:** sembrar un usuario sintético en PostgreSQL aislado, arrancar la API con el rol de aplicación y comprobar login válido, inválido y aislamiento. El esquema admite el mismo email en distintos bufetes, por lo que también debe probarse cómo se selecciona el bufete sin ambigüedad.

## 3. El registro HTTP incluye la consulta completa

**REFUTADO el comentario «NO se loguea la query string», por inspección y reproducción aislada. Producción: NO MEDIDO.**

En [api.py, `log_message`](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/api.py), el primer fragmento imprime solo la ruta, pero el segundo agrega `fmt % args`. El registro de respuesta de `BaseHTTPRequestHandler` recibe ahí la línea HTTP original, incluida la consulta.

Copié ese método en un servidor mínimo, sin cambiar su lógica, e hice una solicitud HTTP local con un dato sintético. **No ejecuté la API completa ni accedí a datos de abogados.**

Salida cruda del instrumento auxiliar, Python 3.12.13:

```json
{
  "instrumento": "reproduccion aislada de log_message con BaseHTTPRequestHandler real",
  "maquina": "sandbox auxiliar, NO brain-env ni produccion",
  "python": "3.12.13",
  "http_status": 200,
  "stdout_verbatim": "127.0.0.1 GET /buscar \"GET /buscar?q=CANARIO_AUDITORIA_793 HTTP/1.1\" 200 -\n",
  "consulta_en_log": true
}
```

El HTTP 200 controla que sí hubo solicitud; la presencia del canario demuestra el mecanismo observado. El programa de reproducción y su salida acompañan este informe. W-01: los escribí y ejecuté yo; son evidencia reproducible auxiliar, no un testigo independiente ni una medición del despliegue.

Guardar `q_hash` en la base no impide esta exposición en stdout. **Qué faltó medir:** privacidad del texto en los registros HTTP, no solamente en la respuesta y en la tabla del sensor.

## 4. Un rechazo posterior no invalida una aprobación anterior

**CONFIRMADO como comportamiento del código leído; prueba HTTP del escenario: NO MEDIDO.**

[init.sql](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/infra/init.sql) indica que para cambiar de decisión se debe registrar un evento nuevo. Los almacenamientos devuelven aprobaciones en orden descendente de fecha.

Pero [`exigir_aprobacion()`](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/api.py) recorre todos los eventos buscando cualquiera con `decision == 'aprobado'`, mismo tipo, hash y matrícula. Si el primero es un rechazo posterior, lo salta y puede aceptar la aprobación vieja.

La prueba existente verifica un contenido que solo fue rechazado; no la secuencia aprobar, rechazar el mismo contenido y volver a pedir autorización.

**Alcance del riesgo:** el propio endpoint devuelve `AUTORIZADA_PERO_NO_EJECUTADA`; no encontré un envío real a juzgados. El defecto está en la autorización, no es evidencia de que se haya presentado un escrito.

## 5. El comienzo del plazo penal cautelar hereda la regla civil

**CONFIRMADA la contradicción con el contrato declarado; validación jurídica y reproducción del motor completo: NO MEDIDO.**

[plazos.py](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/plazos.py) distingue civil y penal y ofrece cautelares penales en días corridos. Sin embargo, la búsqueda de `inicio` exige `marca == 'habil'` para todas las materias. No tiene una rama que permita comenzar el cómputo penal corrido al día siguiente inhábil.

Para una notificación el viernes 11 de septiembre de 2026 y tres días, sin suspensiones ni feriados adicionales, el recorrido del código comienza el lunes 14 y llega al miércoles 16. El contrato de contar desde el día siguiente en corridos comenzaría el sábado 12 y llegaría al lunes 14. Esta comparación es de lógica y contrato: no estoy resolviendo aquí el plazo legal de una causa concreta.

[test_plazos.py](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/backend/test_plazos.py) prueba la cautelar desde un jueves, cuyo día siguiente ya es hábil. Los casos de arranque en viernes son civiles. Por eso ese borde penal no queda discriminado por los casos leídos.

**No extrapolar:** no afirmo haber validado toda la legislación, la tabla de cantidades por acto ni el calendario real de Tarija.

## 6. Los documentos de estado quedaron atrás del código

**REFUTADOS como descripción actual; no como fotografía histórica del momento de redacción.**

El [contexto vivo](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/docs/agents/CONTEXTO-CUSTOS-LEGIS.md) todavía dice «cero código, cero base». [ESTADO.md](https://github.com/gatehot59-star/custos-legis-tarija/blob/cc935d7b1c5b12f8f49fe1c7653cc46424e38be1/ESTADO.md) dice que no existen endpoints y pone el sensor de uso como trabajo siguiente. La misma revisión ya contiene API, esquema y registro de consultas.

La precisión importa: que FastAPI no exista sigue siendo cierto, porque la implementación usa stdlib. Lo falso como estado actual es agrupar esa ausencia con «endpoints: NO EXISTE».

El Doc inicial de 43 aserciones es anterior a la expansión del código. No marqué ese número histórico como falso por el solo hecho de que el repo haya cambiado.

## Qué sí se sostiene

El CI consultado es un registro estructurado de ejecución real en runners `ubuntu-24.04`, no un eco del mensaje de commit. El job RLS inicializó PostgreSQL, aplicó el esquema, ejecutó aislamiento, desactivó RLS de checkpoints para el falsador y volvió a ejecutar con la política restaurada; todos esos pasos figuran exitosos.

Esto respalda la ejecución de esa suite en ese commit, no toda la aplicación. No descargué el texto completo de logs, así que no presento un nuevo recuento independiente de cada aserción.

## Límites, independencia y cierre pendiente

- El taller `brain-env`, consultado por el servicio `build`, falló antes de ejecutar el comando: `OCI runtime exec failed ... no space left on device`. Eso mide el fallo de esa llamada, no la capacidad de todas las máquinas ni la causa del consumo de disco. No borré archivos.
- El navegador del gateway falló porque su página/contexto estaba cerrado. La lectura pública alternativa sí recuperó los runs y jobs de Actions.
- Leí el inventario de máquinas desde Git y el método compartido de MUDH. Ese método declara alcance MUDH/AURA/SIAO: no lo usé para inventar permisos específicos de Custos ni juzgar sus commits como infracciones automáticas.
- Consulté el pizarrón por su servicio SQLite. La búsqueda de Custos devolvió un mensaje que lo confundía con KAMPE IR; no lo tomé como fuente de identidad ni trasladé esa auditoría al repo CORREAI.
- No corrí PostgreSQL nuevo, la API completa ni el corpus real. No medí clientes activos, despliegue, costo, vigencia jurídica ni pérdida de datos.
- No audité exhaustivamente cada archivo o commit. No había PRs abiertos en la respuesta consultada; `docs/` no contenía directorio de auditorías.
- Soy Brain en función de auditor en esta sesión, no una identidad independiente por cambiar de rol. Los estados de Actions son evidencia externa; mi reproducción local sigue siendo propia.
- No ejecuté pruebas pagas ni disparé workflows. No escribí mensajes en el buzón, no creé issues y no publiqué aún el informe en Git ni en un Doc.

### Bloque de método y autoevaluación

Afirmación -> instrumento -> ¿podía refutarla? -> resultado:

- CI exitoso en la revisión exacta -> API pública de runs/jobs -> sí -> CONFIRMADO.
- El CI valida API y guard nuevo -> listado de workflows, código YAML y pasos ejecutados -> sí -> REFUTADO.
- La consulta no aparece en el log -> código y reproducción HTTP aislada -> sí, para ese método -> REFUTADO en ese alcance; producción NO MEDIDO.
- Login operativo con PostgreSQL real -> faltó ejecutar API + adaptador + rol restringido -> no se ejecutó el instrumento necesario -> NO MEDIDO, con conflicto estático documentado.
- Corrección legal integral de plazos -> suite existente y lectura de código no bastan -> NO MEDIDO.

Rúbrica explícita para esta auditoría parcial, no para el producto: completitud 12/25 (faltan pruebas integradas y despliegue), razonamiento 23/25 (fuentes cruzadas y límites por afirmación), documentación 21/25 (fuentes y reproducción incluidas, publicación canónica pendiente), proceso 14/25 (lectura de contexto y fuentes reales, sin testigo independiente de la reproducción ni cierre en Git/Doc/pizarrón). **70/100: por debajo de 90; no se declara auditoría completa ni aprobación.** Es autoevaluación, no medición externa de calidad.

## Recomendación

Primero probar y resolver el login con PostgreSQL restringido y eliminar el texto de las consultas del log; después incorporar la API al CI y cubrir revocación de aprobación y arranque penal cautelar. No cambiar privilegios de la base para hacer pasar el login. Mantener esta auditoría como parcial hasta reproducir esos caminos con el producto real en un entorno aislado.

La próxima escritura propuesta es solo documental: este informe en `docs/auditorias/2026-09-15-01-custos-api-ci-auditoria-parcial.md` y un Doc público en ClickUp. Ninguna corrección de producto está autorizada por este informe.
