# ESTADO REAL de Custos Legis Tarija

**Medido:** 2026-09-10 11:45 UTC · **Corrida de CI:** `tests #11` (commit `b0bd857`), **passing**

> **Este archivo existe porque el documento de diseño declaraba `FASE 1 ✅ ... FASE 5 ✅`
> sin una linea de codigo en el repo.** Aca va lo contrario: lo que corre, con su
> salida, y lo que no existe, dicho como no existe.
>
> **El testigo no soy yo.** El verde de abajo lo declara Actions, no mi maquina:
> https://github.com/gatehot59-star/custos-legis-tarija/actions/workflows/tests.yml

---

## §1 · LO QUE EXISTE Y CORRE (medido en CI, no en mi maquina)

| Pieza | Estado | Evidencia |
|---|---|---|
| **Plazos procesales POR MATERIA** | **VERDE, 71/71** | `test_plazos.py` |
| **Calendario judicial por departamento** | **VERDE, 36/36** | `test_calendario.py` |
| **Esquema PostgreSQL con RLS** | **VERDE**, 5 tablas con RLS **forzado** | `psql -f infra/init.sql`, `ON_ERROR_STOP=1` |
| **Aislamiento entre bufetes** | **VERDE, 16/16** | `test_rls.py` contra **PostgreSQL 16 real** |
| **Cliente del corpus** | **VERDE**, corrido en vivo el 10-sep 06:05 | 184 pasajes en **10,26 ms** |
| **10 falsadores** | **LOS 10 DAN ROJO** con la etiqueta exigida | ver §1.1 |
| **4 guards** | activos | RLS forzado, tabla de plazos sin confirmar, fuente obligatoria en el calendario |

**Total: 123 aserciones verdes (71 plazos + 36 calendario + 16 RLS) y 10 falsadores
que demuestran poder dar rojo.**

### §1.1 · Los 10 falsadores y que mecanismo prueba cada uno

| Falsador | Etiqueta exigida | Rompe |
|---|---|---|
| umbral-15-desactivado | `PLAZO-CORRIDO-90II` | el art. 90.II: todo vuelve a habiles |
| vacacion-no-suspende | `VACACION-NO-CONSUME` | el art. 126.IV LOJ |
| arranque-sin-buscar-habil | `ARRANQUE-HABIL` | el art. 90.I (dia siguiente **habil**) |
| hora-penal-igual-a-civil | `HORA-PENAL` | las 24:00 del art. 130 CPP |
| confirmado-sin-calendario | `SIN-CALENDARIO-NO-MEDIDO` | la honestidad: fecha firme sin circular |
| incompleto-declara-cobertura | `REGISTRAR-NO-ES-CONFIRMAR` | registrar un dato incompleto como si estuviera medido |
| calendario-ignora-departamento | `FILTRO-DEPARTAMENTO` | la separacion por departamento |
| materia-acepta-todo | `TERCER-REGIMEN` | el rechazo de materias no modeladas |
| no-distingue-no-emitido | `NO-EMITIDO` | la diferencia entre "no emitido" y "no medido" |
| rls-checkpoints-off | `FUGA-CKPT` | el aislamiento del D3 |

**Por que 10 y no uno:** un falsador solo prueba que el test detecta **lo que ese
falsador rompe**. El CI exige la **etiqueta** del rojo, no cualquier rojo, y al
final verifica con `cmp` que los fuentes quedaron identicos.

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
*"Los plazos procesales son perentorios"*: no hay recuperacion.

Es el mismo error de fondo que el `timedelta(days=)` que la v1 vino a arreglar:
**se aplico una sola regla a todos los plazos.** Los plazos de 3, 5 y 10 dias **ya
estaban bien**, y los feriados moviles tambien (Carnaval 16-17 feb, Viernes Santo
3 abr, Corpus 4 jun de 2026).

### El motor hoy, por materia

| Variable | Civil (Ley 439) | Penal (Ley 1970) |
|---|---|---|
| Inicio | dia siguiente **habil** (90.I) | dia siguiente (130) |
| Plazo ≤ 15 dias | solo habiles (90.II) | solo habiles (130) |
| Plazo > 15 dias | habiles **e** inhabiles (90.II) | solo habiles salvo ley expresa |
| Medidas cautelares | n/a | **dias corridos** (130) |
| Hora de vencimiento | cierre del juzgado (90.III), **hora NO MEDIDA** | **24:00** (130) |
| Ultimo dia inhabil | prorroga al primer habil (90.III) | vence el ultimo dia **habil** |
| Vacacion judicial | **suspende** (126.IV LOJ) | **suspende** (130 + 126 LOJ) |

---

## §3 · EL CALENDARIO JUDICIAL: tres mediciones que cambian el diseño

1. **Los departamentos NO coinciden.** Gestion 2025: Potosi **8-dic a 1-ene**
   (Acuerdo de Sala Plena 552/2025), Santa Cruz **9-dic a 2-ene**, y el TSJ
   nacional **hasta el 5-ene** segun prensa. **Tres rangos, mismo anio.** Un
   calendario nacional unico habria fallado en dos de los tres casos.
2. **Las fechas no siguen patron.** Tarija medido: 2018 del 7 al 31-dic, 2019 del
   3 al 27-dic, 2023 del 5 al 29-dic. Los 25 dias del art. 126 son fijos; el
   tramo no.
3. **Hay vacaciones extraordinarias.** Mayo de 2026, TDJ La Paz, una semana por
   conflictos y bloqueos, descontada de la programada. El calendario puede
   cambiar a mitad de anio.

### El pendiente del 2026 estaba MAL PLANTEADO, y esto es lo mas util del turno

En el `ESTADO.md` anterior escribi que faltaba "conseguir la circular del TDJ
Tarija" y que era "una llamada de telefono, no un sprint". **Es falso.**

La vacacion de cada gestion se fija en Sala Plena **entre octubre y noviembre**.
Lo dijo la decana del TSJ en julio de 2026: la eleccion de autoridades seria
*"entre fines de octubre y los primeros dias de noviembre, cuando se trate el tema
de la vacacion judicial"*. **Hoy es septiembre. El dato no puede existir.**

No es un dato que no medi: es un dato que **el Organo Judicial no emitio todavia**.
Son dos pendientes distintos y uno de los dos no es mio. `por_que_falta(anio)`
devuelve el motivo correcto segun la fecha, y el falsador `NO-EMITIDO` lo prueba.

**Consecuencia:** el Vigilante va a devolver `NO_MEDIDO` para todo plazo que cruce
diciembre de 2026, **y eso es correcto**. Cargar el calendario es una **tarea
recurrente con fecha conocida** (octubre-noviembre de cada anio), no un pendiente
que se cierra una vez.

---

## §4 · UN TERCER REGIMEN QUE NO MODELO (hallazgo del AS 589/2021)

Buscando corroboracion del art. 90.II encontre el **Auto Supremo 589/2021** (Sala
Contenciosa Administrativa Segunda del TSJ). Confirma el mecanismo de pausa y
reanudacion de la vacacion judicial, tal como quedo implementado: *"habiendo
transcurrido 6 dias hasta esa fecha; posteriormente el computo se reinicio [...] a
la conclusion de la vacacion judicial, quedando 4 dias"*.

**Pero tambien me mostro que hay un regimen que este modulo no cubre.** El mismo
fallo dice que el plazo *"se computa desde el dia y hora de la diligencia hasta la
misma hora del dia de vencimiento"* (art. 264 de la Ley 1340) y que **corre de
momento a momento**. Eso no es habiles ni corridos: es una tercera regla.

Un contencioso administrativo clasificado como CIVIL **no explota**: devuelve una
fecha creible y equivocada, que es la peor clase de resultado. `MATERIAS_NO_MODELADAS`
declara las **siete** que no se computar, cada una con su motivo, y el enum sigue
siendo la barrera dura.

Y una tentacion que rechace: el mismo AS dice que *"el art. 261 del CPC establece
el plazo de diez dias para interponer el recurso de apelacion"*, lo que corrobora
una entrada de mi tabla. **No lo tomo como confirmacion**: el fallo mezcla el CPC
abrogado con la Ley 439 y resuelve un contencioso administrativo. **Una
corroboracion ambigua no es una medicion.** La tabla sigue en `HIPOTESIS`.

---

## §5 · LOS 9 DEFECTOS DE FABLE

| # | Defecto | Estado |
|---|---|---|
| **D1** | `_limpiar_texto_legal` reescribia el crudo | **CERRADO** con trigger que rechaza modificar el crudo |
| **D2** | `estado_vigencia="vigente"` hardcodeado | **CERRADO**: tres estados y advertencia obligatoria |
| **D3** | fuga cross-tenant por el checkpointer | **CERRADO** con RLS forzado, trigger y falsador |
| **D4** | plazos en dias calendario | **CERRADO DE VERDAD RECIEN AHORA** (ver §2) |
| **D5** | Constitucionalista audita una estrategia que no existe | **PENDIENTE**: no hay grafo |
| **D6** | `Depends(lambda...)` sin consumir el generador | **NO APLICA AUN**: no hay FastAPI |
| **D7** | `InMemoryStore` se pierde al reiniciar | **CERRADO por diseño**: memoria en Postgres |
| **D8** | modelos hardcodeados detras del gateway | **PENDIENTE** |
| **D9** | SIREJ→SIGC sin fuente verificable | **CERRADO**: solo penal, piloto en Chuquisaca |

**6 de 9 cerrados con codigo y test. 3 pendientes, declarados.**

---

## §6 · LO QUE NO EXISTE, y no voy a llamarlo fase verde

| Capa | Estado |
|---|---|
| FastAPI / endpoints | **NO EXISTE** |
| Los 6 agentes / grafo LangGraph | **NO EXISTE** |
| Frontend Next.js | **NO EXISTE** |
| Scraper judicial | **NO EXISTE** (legalidad **acotada**, ver §8) |
| Qdrant / busqueda vectorial | **NO EXISTE, y a proposito**: el ADR-001 dice medir antes si el lexico alcanza |
| Facturacion | **NO EXISTE** |
| Desplegado en Abacus | **NO** |
| Calendario de Tarija 2024 y 2026 | **2024 no medido; 2026 NO EMITIDO todavia** |
| **Un abogado que lo haya usado** | **CERO** |

---

## §7 · LOS DEFECTOS PROPIOS DE ESTA SESION

Cuatro, y **tres son sobre mis propios instrumentos**.

### P3 · Mis tests de vacacion judicial pasaban con la suspension APAGADA

Cuatro aserciones, corridas con la suspension neutralizada a proposito: **65
verdes, 0 rojos**. No detectaron nada. La causa no es azar: **la prorroga del art.
90.III las rescataba**, porque el ultimo dia caia dentro de la vacacion y se corria
igual. El resultado correcto, el mecanismo roto.

**Cura:** mirar el **computo**, no el resultado. Las nuevas verifican que ningun dia
suspendido aparezca con `cuenta=True` en el detalle, y que la marca cite la
circular. Ahi si el falsador da rojo.

### P4 · Mis tests "por departamento" tampoco discriminaban

Seis aserciones sobre la separacion por departamento daban **verde con el filtro
borrado**. Motivo: `calendario(dep)` ya carga solo los periodos de ese
departamento, asi que el test probaba el **cargador**, no el **filtro**. Para
discriminar hace falta un calendario **mezclado**. Con eso el falsador da rojo con
`FILTRO-DEPARTAMENTO`.

**Tres veces en dos sesiones** un control acierta el veredicto por la razon
equivocada (el sabotaje del RLS, la vacacion, el departamento). El patron es
siempre el mismo: **la asercion mira el resultado y no el mecanismo.** Esta anotado
en la cabecera del workflow.

### P5 · El falsador del CI habria dado rojo por el grep, no por el sabotaje

El workflow viejo exigia el texto literal `ROJO vencimiento habil`, y la v2 renombro
ese caso. El paso habria fallado **por el grep**. **Un guard que depende de un texto
libre es fragil por diseño.** Reemplazado por etiquetas estables.

### P6 · Commitear archivo por archivo dejo dos corridas ROJAS en `main`

**Verificado en la lista de fallos de Actions, no supuesto:** **#5** y **#6** en rojo.

- **#5** (`bac0004`): `plazos.py` v2 con los tests **viejos**, que llamaban
  `vencimiento(fecha, 3)` sin materia. El `TypeError` que agregue a proposito hizo
  su trabajo, contra mi propio commit.
- **#6** (`5de4788`): tests nuevos con el workflow **viejo**, o sea el P5.

En la segunda tanda de commits (#8 a #11) ordene los archivos para que cada paso
quedara verde, y los cuatro pasaron. **El sintoma que anoto es otro:** un historial
verde con dos huecos se lee despues como "siempre estuvo verde".

---

## §8 · LO QUE BLOQUEA, y que se descarto de la lista

**Se cerraron por texto** (ver `docs/agents/2026-09-10-plazos-medidos-en-fuente-oficial.md`):

| Antes bloqueaba | Ahora |
|---|---|
| "La tabla de plazos no la confirmo ningun abogado" | **La REGLA de computo si esta confirmada** (art. 90 Ley 439, art. 130 CPP). Lo que sigue en hipotesis es la **cantidad de dias por acto** (arts. 252, 261, 365 no abiertos). Eran dos cosas y estaban mezcladas |
| "¿Es legal que un agente redacte un memorial?" | **Ninguna norma lo prohibe.** El ancla es la **Ley 387** (art. 6 registro y matricula en el Ministerio de Justicia; art. 32.II la responsabilidad no se exime), **no un Colegio**: la afiliacion es un derecho, no un requisito |
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
3. **Tratamiento de datos del bufete y envio a un proveedor de IA.**
4. **Almacenamiento de credenciales del bufete** para consultar expedientes.
5. **Colision de nombres:** "Custos Legis" ya era el log HMAC de KAMPE IR.

---

## §9 · NO MEDIDO, declarado

1. **Arts. 252, 261 y 365 de la Ley 439**: fundan la tabla `PLAZOS`. No los abri.
2. **Art. 264 de la Ley 1340**: el regimen "de momento a momento" esta
   **identificado, no medido**. Lo se por el AS 589/2021, no por su texto.
3. **Calendario de Tarija 2020, 2021, 2022 y 2024**: no los busque.
4. **Fin exacto de la vacacion 2025 de Tarija**: la fuente da el inicio y no el fin.
   Cargado con `cubre=False`, o sea que **avisa pero no autoriza a calcular**.
5. **Cobertura del corpus:** intente correr `q="quince dias"` contra el endpoint y
   **no respondio**. Consistente con el cierre por privacidad del §8.1, pero **no
   verificado**: si la norma que decide el producto no esta en el corpus, el corpus
   tiene un hueco en el centro.
6. **Ley 1173 y el buzon electronico penal.** Lo afirme sin leerlo.
7. **Hora de cierre de los juzgados de Tarija.** El art. 90.III dice "ultimo momento
   habil del horario de funcionamiento". El modulo usa 18:00 como **supuesto
   declarado** y lo avisa en cada calculo.
8. **Feriados departamentales de Tarija** mas alla del 15 de abril.
9. **Terminos de uso del portal del Organo Judicial y del SIREJ.**

---

## §10 · Lo proximo, en orden

1. **Decidir la privacidad del corpus.** Sigue bloqueando todo lo demas.
2. **Confirmar la tabla de plazos** con los arts. 252, 261 y 365 en la mano. Es lo
   unico que separa el motor de plazos de estar completo, y **ya no depende del
   calendario**: el calendario tiene fecha (octubre-noviembre) y el motor sabe
   decir NO_MEDIDO hasta entonces.
3. **Leer el art. 264 de la Ley 1340** si el producto va a tocar contencioso
   administrativo. Si no, dejarlo declarado y no modelarlo.
4. **T1: sensor de uso.** La tabla `uso_consultas` ya esta, con `q_hash` en vez del
   texto (una busqueda juridica revela la estrategia de un caso).
5. **Un abogado**, con el corpus que ya existe.
6. **Medir si el lexico alcanza** antes de meter Qdrant en una VM de 2 nucleos.
7. Recien despues: FastAPI y el grafo.

**No empiezo por el grafo porque es la parte divertida.** En el corpus eso costo 33
commits sin mover el producto.
