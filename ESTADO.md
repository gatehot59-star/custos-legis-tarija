# ESTADO REAL de Custos Legis Tarija

**Medido:** 2026-09-10 11:32 UTC · **Corrida de CI:** `tests #7` (commit `3275177`), **passing**

> **Este archivo existe porque el documento de diseño declaraba `FASE 1 ✅ ... FASE 5 ✅`
> sin una linea de codigo en el repo.** Aca va lo contrario: lo que corre, con su
> salida, y lo que no existe, dicho como no existe.
>
> **El testigo no soy yo.** El verde de abajo lo declara el badge del workflow en
> Actions, no mi maquina: https://github.com/gatehot59-star/custos-legis-tarija/actions/workflows/tests.yml

---

## §1 · LO QUE EXISTE Y CORRE (medido en CI, no en mi maquina)

| Pieza | Estado | Evidencia |
|---|---|---|
| **Plazos procesales POR MATERIA** | **VERDE, 71/71** | `test_plazos.py` en Actions |
| **Esquema PostgreSQL con RLS** | **VERDE**, 5 tablas con RLS **forzado** | `psql -f infra/init.sql`, `ON_ERROR_STOP=1` |
| **Aislamiento entre bufetes** | **VERDE, 16/16** | `test_rls.py` contra **PostgreSQL 16 real** |
| **Cliente del corpus** | **VERDE**, corrido en vivo el 10-sep 06:05 | 184 pasajes en **10,26 ms** |
| **5 falsadores de plazos** | **LOS 5 DAN ROJO** con su etiqueta exigida | `PLAZO-CORRIDO-90II`, `VACACION-NO-CONSUME`, `ARRANQUE-HABIL`, `HORA-PENAL`, `SIN-CALENDARIO-NO-MEDIDO` |
| **Falsador de la fuga D3** | **DA ROJO** cuando corresponde | `ETIQUETAS_ROJAS: FUGA-CKPT` |
| **Guard de la tabla de plazos** | activo | cuenta `confirmado=True` por **estructura**, no por grep |

**Total: 87 aserciones verdes (71 plazos + 16 RLS) y 6 falsadores que demuestran poder dar rojo.**

### Por que 5 falsadores y no uno

Un falsador solo prueba que el test detecta **lo que ese falsador rompe**. Cada
regla que la ley impone tiene el suyo, y el CI exige la **etiqueta** del rojo, no
cualquier rojo. Los cinco corren en el mismo paso, restauran el fuente y el paso
**verifica con `cmp` que `plazos.py` quedo identico** al original.

---

## §2 · EL D4 ESTABA MAL CERRADO, y lo medi con mi propio codigo

El `ESTADO.md` anterior declaraba el **D4 CERRADO**: "dias habiles con feriados
nacionales + Tarija". **Era un cierre incompleto y en la direccion peligrosa.**

Abri el **art. 90 de la Ley 439** en fuente oficial:

> **II.** [...] **Se exceptuan los plazos cuya duracion no exceda de quince dias,
> los cuales solo se computaran los dias habiles. En el computo de los plazos que
> excedan los quince dias se computaran los dias habiles y los inhabiles.**

La v1 contaba **habiles siempre**. `traslado_demanda` son **30 dias**. Corri la v1
contra el computo legal sobre las 48 notificaciones del 1, 8, 15 y 22 de cada mes
de 2026:

| Notificacion | v1 (habiles) | Ley (90.II corridos + 90.III) | Dias regalados |
|---|---|---|---|
| 2026-01-08 | 2026-02-24 | 2026-02-09 | **15** ← peor caso |
| 2026-12-15 | 2027-01-29 | 2027-01-14 | **15** |
| 2026-04-01 | 2026-05-18 | 2026-05-04 | **14** |
| 2026-01-01 | 2026-02-13 | 2026-02-02 | **11** |

**El error decia que el plazo vence DESPUES de lo que vence.** Y el art. 89.I dice
*"Los plazos procesales son perentorios"*: no hay recuperacion. Un abogado que le
crea al sistema presenta dos semanas tarde y pierde el derecho.

Es el mismo error de fondo que el `timedelta(days=)` que la v1 vino a arreglar:
**se aplico una sola regla a todos los plazos.** El arreglo cambio corridos por
habiles cuando la ley pide **las dos, segun el umbral de 15 dias**.

Los plazos de 3, 5 y 10 dias **ya estaban bien**, y los feriados moviles tambien
(Carnaval 16-17 feb, Viernes Santo 3 abr, Corpus 4 jun de 2026).

### Y dos huecos mas, medidos

1. **La vacacion judicial no existia en el modulo.** El art. 126.IV LOJ (Ley 810)
   dice que *"todo plazo [...] quedara suspendido"*. La v1 devolvia **15-dic** para
   10 dias habiles desde el 1-dic: una fecha **dentro del periodo suspendido**.
2. **El modulo era civil y no lo decia.** Devolvia un `date` pelado, asi que no
   podia representar el vencimiento a las **24:00** del art. 130 CPP ni las
   **medidas cautelares en dias corridos**.

---

## §3 · LOS 9 DEFECTOS DE FABLE: cuales estan cerrados

| # | Defecto del diseño | Estado |
|---|---|---|
| **D1** | `_limpiar_texto_legal` reescribia el crudo | **CERRADO**: `texto_crudo` y `texto_normalizado` separados, con **trigger** que rechaza modificar el crudo |
| **D2** | `estado_vigencia="vigente"` hardcodeado | **CERRADO**: tres estados (`VIGENTE`/`DEROGADA`/`NO_MEDIDO`) y **advertencia obligatoria** |
| **D3** | fuga cross-tenant por el checkpointer | **CERRADO**: `cl_checkpoints` con `tenant_id`, RLS forzado y trigger. **Con falsador que lo demuestra** |
| **D4** | plazos en dias calendario | **CERRADO DE VERDAD RECIEN AHORA** (ver §2). El cierre anterior era parcial y peligroso |
| **D5** | Constitucionalista audita una estrategia que no existe | **PENDIENTE**: no hay grafo todavia |
| **D6** | `Depends(lambda...)` con generador sin consumir | **NO APLICA AUN**: no hay FastAPI |
| **D7** | `InMemoryStore` se pierde al reiniciar | **CERRADO por diseño**: la memoria va en `cl_checkpoints`, en Postgres |
| **D8** | modelos hardcodeados detras del gateway | **PENDIENTE** |
| **D9** | SIREJ→SIGC sin fuente verificable | **CERRADO**: solo penal, piloto en Chuquisaca, Bs 160 M como anteproyecto en mar-2026 |

**6 de 9 cerrados con codigo y test. 3 pendientes, declarados.**

---

## §4 · LO QUE NO EXISTE, y no voy a llamarlo fase verde

| Capa | Estado |
|---|---|
| FastAPI / endpoints | **NO EXISTE** |
| Los 6 agentes / grafo LangGraph | **NO EXISTE** |
| Frontend Next.js | **NO EXISTE** |
| Scraper judicial | **NO EXISTE** (y su legalidad ahora **acotada**, ver §6) |
| Qdrant / busqueda vectorial | **NO EXISTE, y a proposito**: el ADR-001 dice medir antes si el lexico alcanza |
| Facturacion | **NO EXISTE** |
| Desplegado en Abacus | **NO** |
| **El calendario judicial de Tarija** | **VACIO**. La estructura existe y el modulo devuelve `NO_MEDIDO` sin ella. Falta la circular del TDJ |
| **Un abogado que lo haya usado** | **CERO** |

---

## §5 · LOS DEFECTOS PROPIOS DE ESTA SESION

Tres, y los dos primeros son sobre mis propios instrumentos.

### P3 · MIS TESTS DE VACACION JUDICIAL PASABAN CON LA SUSPENSION APAGADA

Escribi cuatro aserciones para la vacacion judicial, las corri con la suspension
neutralizada a proposito, y **dieron 65 verdes y 0 rojos**. No detectaron nada.

La causa no es azar: **la prorroga del art. 90.III las rescataba.** El ultimo dia
caia dentro de la vacacion, `es_habil()` lo veia inhabil por otro motivo, y el
vencimiento se corria igual. El resultado era correcto y el mecanismo estaba roto.

**Es el mismo defecto P1 de la sesion pasada, en otro archivo.** La primera vez fue
un sabotaje que dijo "fuga detectada" sin detectar ninguna. La cura es la misma:
**mirar el COMPUTO, no el resultado.** Las aserciones nuevas verifican que ningun
dia suspendido aparezca con `cuenta=True` en el detalle dia por dia, y que la
marca cite la circular. Con eso el falsador da rojo con `VACACION-NO-CONSUME`.

Segundo caso identico en la misma sesion: el test del **arranque habil** (art. 90.I)
**no discriminaba en modo habiles**, porque el sabado no cuenta de todos modos.
Solo discrimina en **corridos**, donde el sabado si consumiria un dia. El test se
movio ahi.

### P4 · EL FALSADOR DEL CI HABRIA DADO ROJO POR EL GREP, NO POR EL SABOTAJE

El workflow viejo exigia el texto literal `ROJO vencimiento habil`. La v2 de los
tests renombro ese caso, asi que el paso habria fallado **por el grep** y no por el
sabotaje: el veredicto correcto por la razon equivocada, ahora en sentido inverso.
**Un guard que depende de un texto libre es fragil por diseño.** Se reemplazo por
etiquetas estables que el test emite a proposito.

### P5 · COMMITEAR ARCHIVO POR ARCHIVO DEJO DOS CORRIDAS ROJAS EN `main`

**Verificado en la lista de fallos de Actions, no supuesto:** las corridas **#5** y
**#6** estan en rojo.

- **#5** (`bac0004`): subi `plazos.py` v2 con los tests **viejos**, que llamaban
  `vencimiento(fecha, 3)` sin materia. El `TypeError` que agregue a proposito hizo
  su trabajo, contra mi propio commit.
- **#6** (`5de4788`): subi los tests nuevos con el workflow **viejo**, o sea el
  grep del P4.

Ninguna rompio nada, pero **`main` estuvo roto dos commits**. La forma correcta es
un solo commit con los tres archivos, o una rama. Lo anoto porque el sintoma
(historial verde salvo dos huecos) es exactamente lo que despues se lee como
"siempre estuvo verde".

---

## §6 · LO QUE BLOQUEA, y que se descarto de la lista

**Se cerraron por texto** (medido 2026-09-10, ver `docs/agents/2026-09-10-plazos-medidos-en-fuente-oficial.md`):

| Antes bloqueaba | Ahora |
|---|---|
| "La tabla de plazos no la confirmo ningun abogado" | **La REGLA de computo si esta confirmada** (art. 90 Ley 439, art. 130 CPP). Lo que sigue en hipotesis es la **cantidad de dias por acto** (arts. 252, 261, 365 **no abiertos**). Eran dos cosas y estaban mezcladas |
| "¿Es legal que un agente redacte un memorial?" | **Ninguna norma lo prohibe.** El ancla es la **Ley 387** (registro y matricula en el Ministerio de Justicia, art. 6; responsabilidad que no se exime, art. 32.II), **no un Colegio**: la afiliacion es un derecho, no un requisito. El HITL firma con la matricula del Registro Publico |
| "Legalidad del scraping judicial" | **Acotada.** La Ley 164 **no tipifica** scraping. El limite penal real es el **CP art. 363 ter**, con **dos elementos acumulativos**: sin autorizacion **y** perjuicio al titular. Consulta publica por NUREJ sin eludir autenticacion no encaja; credenciales ajenas si |

**SIGUE BLOQUEANDO:**

1. **PRIVACIDAD DEL CORPUS.** Medido el 10-sep: `q=Mamani` en el buscador **publico
   sin login** devolvia **1.232 pasajes**, y el primero nombraba a las dos partes de
   una causa de **violacion de un menor**. **Decision de Abraham, sin resolver.**
2. **REDISTRIBUCION DEL TEXTO INTEGRO en un producto pago.** Y aca corrijo una
   afirmacion mia: dije que la **Ley 1322 excluye los textos oficiales** de
   proteccion y que por eso se podia vender el corpus "sin pedir permiso de nadie".
   **Fui a buscar ese articulo y no existe.** El art. 4 excluye **ideas**; el art. 8
   dice que el Estado **puede ejercer derechos de autor como titular derivado**.
   Vuelve a **NO MEDIDO**, y es pregunta para el abogado.
3. **Tratamiento de datos del bufete y envio a un proveedor de IA:** que
   consentimiento y que contrato, sin ley de proteccion de datos vigente.
4. **Almacenamiento de credenciales del bufete** para consultar expedientes.
5. **Colision de nombres:** "Custos Legis" ya era el log HMAC de KAMPE IR.
   Renombrar hoy cuesta un `git mv`.

---

## §7 · NO MEDIDO, declarado

1. **Arts. 252, 261 y 365 de la Ley 439**: fundan la tabla `PLAZOS`. No los abri.
2. **Circular de vacaciones judiciales 2026 del TDJ Tarija.** Sin ella el Vigilante
   devuelve `NO_MEDIDO`, que es lo correcto, pero no arranca.
3. **Cobertura del corpus:** intente correr `q="quince dias"` contra el endpoint del
   corpus para confirmar que el art. 90.II esta indexado y **el endpoint no
   respondio**. Consistente con el cierre por privacidad del punto §6.1, pero
   **no verificado**: si la norma que decide el producto no esta en el corpus, el
   corpus tiene un hueco en el centro.
4. **Ley 1173 y el buzon electronico penal.** Lo afirme sin leerlo. El computo penal
   se queda en el art. 130 puro.
5. **Hora de cierre de los juzgados de Tarija.** El art. 90.III dice "ultimo momento
   habil del horario de funcionamiento", no una hora. El modulo usa 18:00 como
   **supuesto declarado** y lo avisa en cada calculo.
6. **Feriados departamentales de Tarija** mas alla del 15 de abril.
7. **Terminos de uso del portal del Organo Judicial y del SIREJ.**

---

## §8 · Lo proximo, en orden

1. **Decidir la privacidad del corpus.** Sigue bloqueando todo lo demas.
2. **Conseguir la circular del TDJ Tarija** y cargar el calendario judicial. Es el
   unico dato que falta para que el motor de plazos pase de `NO_MEDIDO` a
   `CONFIRMADO`, y es una llamada de telefono, no un sprint.
3. **Confirmar la tabla de plazos** con los arts. 252, 261 y 365 en la mano.
4. **T1: sensor de uso.** La tabla `uso_consultas` ya esta, con `q_hash` en vez del
   texto (una busqueda juridica revela la estrategia de un caso).
5. **Un abogado**, con el corpus que ya existe.
6. **Medir si el lexico alcanza** antes de meter Qdrant en una VM de 2 nucleos.
7. Recien despues: FastAPI y el grafo.

**No empiezo por el grafo porque es la parte divertida.** En el corpus eso costo 33
commits sin mover el producto.
