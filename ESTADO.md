# ESTADO REAL de Custos Legis Tarija

**Medido:** 2026-09-10 12:16 UTC · **Corrida de CI:** `tests #16` (commit `d789e83`), **passing**

> **Este archivo existe porque el documento de diseño declaraba `FASE 1 ✅ ... FASE 5 ✅`
> sin una linea de codigo en el repo.** Aca va lo contrario: lo que corre, con su
> salida, y lo que no existe, dicho como no existe.
>
> **El testigo no soy yo.** El verde lo declara Actions, no mi maquina:
> https://github.com/gatehot59-star/custos-legis-tarija/actions/workflows/tests.yml

---

## §1 · LO QUE EXISTE Y CORRE (medido en CI, no en mi maquina)

| Pieza | Estado | Evidencia |
|---|---|---|
| **Compuerta de publicacion** | **VERDE, 44/44** | `test_anonimizador.py` |
| **Plazos procesales POR MATERIA** | **VERDE, 71/71** | `test_plazos.py` |
| **Calendario judicial por departamento** | **VERDE, 36/36** | `test_calendario.py` |
| **Esquema PostgreSQL con RLS** | **VERDE**, 5 tablas con RLS **forzado** | `psql -f infra/init.sql` |
| **Aislamiento entre bufetes** | **VERDE, 16/16** | `test_rls.py` contra **PostgreSQL 16 real** |
| **Cliente del corpus** | **VERDE** el 10-sep 06:05 | 184 pasajes en **10,26 ms** |
| **16 falsadores** | **LOS 16 DAN ROJO** con la etiqueta exigida | ver §1.1 |
| **6 guards** | activos | RLS forzado, tabla sin confirmar, fuente del calendario, reserva legal, ninguna fixture publicable |

**Total: 167 aserciones verdes (44 privacidad + 71 plazos + 36 calendario + 16 RLS)
y 16 falsadores que demuestran poder dar rojo.**

### §1.1 · Los falsadores y que mecanismo prueba cada uno

| Falsador | Etiqueta | Rompe |
|---|---|---|
| reserva-legal-desactivada | `RESERVA-LEGAL` | la reserva de NNA, violencia y familia |
| extracto-sin-matricula | `CERO-FUGAS` | el HITL: publica texto de jurisprudencia sin aprobacion |
| senas-debiles-cuentan | `SENA-DEBIL` | una SCP que cita un articulo se publica como ley |
| seudonimo-con-iniciales | `SEUDONIMO-ESTABLE` | la no reidentificacion |
| ficha-devuelve-todo | `FICHA-LIMPIA` | la ficha publica filtra `texto_crudo` y `parte_actora` |
| autoridad-tratada-como-parte | `AUTORIDAD-INTACTA` | tapa al Magistrado Relator y mata la trazabilidad |
| umbral-15-desactivado | `PLAZO-CORRIDO-90II` | el art. 90.II: todo vuelve a habiles |
| vacacion-no-suspende | `VACACION-NO-CONSUME` | el art. 126.IV LOJ |
| arranque-sin-buscar-habil | `ARRANQUE-HABIL` | el art. 90.I (dia siguiente **habil**) |
| hora-penal-igual-a-civil | `HORA-PENAL` | las 24:00 del art. 130 CPP |
| confirmado-sin-calendario | `SIN-CALENDARIO-NO-MEDIDO` | fecha firme sin circular |
| incompleto-declara-cobertura | `REGISTRAR-NO-ES-CONFIRMAR` | registrar un dato incompleto como medido |
| calendario-ignora-departamento | `FILTRO-DEPARTAMENTO` | la separacion por departamento |
| materia-acepta-todo | `TERCER-REGIMEN` | el rechazo de materias no modeladas |
| no-distingue-no-emitido | `NO-EMITIDO` | "no emitido" vs "no medido" |
| rls-checkpoints-off | `FUGA-CKPT` | el aislamiento del D3 |

**Por que uno por mecanismo:** un falsador solo prueba que el test detecta **lo
que ese falsador rompe**. El CI exige la **etiqueta** del rojo, no cualquier rojo,
y al final verifica con `cmp` que los fuentes quedaron identicos.

---

## §2 · EL BLOQUEADOR #1: decidido con codigo, y NO arreglado

**Lo primero, para que nadie lea de mas:** la compuerta vive en ESTE repo. La
fuga medida vive en **`corpus-legal-tarija`**, que es **otro producto**, y su
endpoint **no respondio** cuando lo consulte hoy. Lo que hay es **la pieza y la
decision de arquitectura**, no el corte del corpus real. Mientras nadie cablee
esto en el buscador, el problema sigue vivo del otro lado.

### Lo que se midio y cambio el diseño

El primer instinto era un **anonimizador**: detectar nombres y taparlos. Lo
escribi, y despues lo corri contra cuatro textos adversarios:

| Texto | Nombre | Detectado |
|---|---|---|
| "interpuesta contra Mamani" | Mamani | **NO** (un solo apellido) |
| "planteado por juan carlos quispe" | quispe | **NO** (minusculas, OCR malo) |
| "El demandante, sr. R. Villca T." | Villca | **NO** (abreviado) |
| "Se condena al acusado GUTIERREZ" | GUTIERREZ | **NO** (mayuscula suelta) |

**Cuatro de cuatro.** Y con el detector como control, los cuatro nombres se
habrian **publicado**: el gate no tenia nada que retener.

**Un detector de nombres es FAIL-OPEN**: borra lo que reconoce y deja lo que no.
En una causa de NNA una sola omision es la violacion que el producto vino a
evitar. Asi que el control **no es el detector**:

1. **La capa publica NO muestra texto libre de jurisprudencia.** Metadatos, cita,
   hash y enlace oficial. Con eso la superficie de fuga es **cero por
   construccion**, y no depende de que un regex entienda apellidos bolivianos.
2. **Las normas SI se publican enteras**, porque **no tienen partes por
   naturaleza**. Ahi esta la mayor parte del valor del corpus: las leyes y los
   codigos son lo que un abogado cita.
3. **Reserva legal** (NNA, violencia, familia, y 17 disparadores en el texto):
   no se publica **ni anonimizada**. Ni con matricula.
4. **El extracto seudonimizado existe**, pero requiere **aprobacion de un abogado
   con matricula**, documento por documento (Ley 387 art. 6). La responsabilidad
   de que no quede un nombre suelto es de quien aprueba, no del detector.

### La categoria importa, y aca se paga caro (E-01)

No todo nombre propio en una resolucion es un dato a proteger:

- **"Magistrado Relator: Dr. Carlos Alberto Eguez Anez"** es un acto publico de
  una autoridad en ejercicio. **Taparlo destruye la trazabilidad de la cita**, y
  hay un falsador dedicado a que nadie lo tape.
- **"la denuncia presentada por Maria Elena Choque Villca"** es una parte.
- **"Editorial Amanecer S.A."** es una persona **juridica**: el art. 21.2 CPE
  habla de "las bolivianas y los bolivianos".

Un anonimizador que trata a los tres igual arruina el producto en un caso y no
protege nada en el otro.

### El defecto que medi en mi propia v1 de la compuerta

Tenia `ARTICULO \d+` y `CODIGO` como señas **normativas**. Con eso clasifico un
fragmento de la **SCP 0693/2023-S4** como NORMATIVO, y los normativos se publican
sin compuerta: **esa Sentencia Constitucional habria salido a la capa publica por
citar el art. 130 del CPP.** La jurisprudencia cita articulos todo el tiempo.
Ahora hay señas **fuertes** (que establecen la clase) y **debiles** (que no
establecen nada), y un falsador que lo cuida.

Y una regla que sale de ahi: **si el corpus DECLARA el tipo del documento, se le
cree al corpus.** Adivinar por texto lo que un metadato ya dice es reemplazar un
dato por una heuristica.

---

## §3 · EL MOTOR DE PLAZOS: el D4 estaba mal cerrado

El `ESTADO.md` anterior declaraba el **D4 CERRADO**. Era un cierre incompleto y en
la direccion peligrosa. El art. 90.II de la Ley 439 pide **dos** reglas:

> **II.** [...] **Se exceptúan los plazos cuya duracion no exceda de quince dias,
> los cuales solo se computaran los dias habiles. En el computo de los plazos que
> excedan los quince dias se computaran los dias habiles y los inhabiles.**

La v1 contaba **habiles siempre**. `traslado_demanda` son **30 dias**:

| Notificacion | v1 (habiles) | Ley (90.II + 90.III) | Dias regalados |
|---|---|---|---|
| 2026-01-08 | 2026-02-24 | 2026-02-09 | **15** ← peor caso |
| 2026-12-15 | 2027-01-29 | 2027-01-14 | **15** |
| 2026-04-01 | 2026-05-18 | 2026-05-04 | **14** |

**Decia que el plazo vence DESPUES de lo que vence**, sobre un plazo que el art.
89.I declara **perentorio**. Los plazos de 3, 5 y 10 dias ya estaban bien.

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

Y un **tercer regimen que NO modelo**: el AS 589/2021 computa un contencioso
administrativo **de momento a momento** (art. 264 Ley 1340). Clasificado como
CIVIL no explota: devuelve una fecha creible y equivocada. Hay **siete materias
declaradas como no modeladas**, cada una con su motivo.

---

## §4 · EL CALENDARIO JUDICIAL: tres mediciones que cambian el diseño

1. **Los departamentos NO coinciden.** Gestion 2025: Potosi **8-dic a 1-ene**
   (Acuerdo de Sala Plena 552/2025), Santa Cruz **9-dic a 2-ene**, TSJ nacional
   **hasta el 5-ene**. Tres rangos, mismo año.
2. **Las fechas no siguen patron.** Tarija: 2018 del 7 al 31-dic, 2019 del 3 al
   27-dic, 2023 del 5 al 29-dic.
3. **Hay vacaciones extraordinarias.** Mayo 2026, TDJ La Paz, una semana por
   conflictos y bloqueos.

### El pendiente del 2026 estaba MAL PLANTEADO

Escribi que faltaba "conseguir la circular del TDJ Tarija" y que era "una llamada
de telefono". **Es falso.** La vacacion se fija en Sala Plena **entre octubre y
noviembre**; lo dijo la decana del TSJ en julio de 2026. **Hoy es septiembre: el
dato no puede existir.**

No es un dato que no medi: es un dato que **el Organo Judicial no emitio
todavia**. `por_que_falta(anio)` devuelve el motivo correcto segun la fecha, y el
falsador `NO-EMITIDO` lo prueba. Cargar el calendario es una **tarea recurrente
con fecha conocida**, no un pendiente que se cierra una vez.

---

## §5 · LOS 9 DEFECTOS DE FABLE

| # | Defecto | Estado |
|---|---|---|
| **D1** | `_limpiar_texto_legal` reescribia el crudo | **CERRADO** con trigger |
| **D2** | `estado_vigencia="vigente"` hardcodeado | **CERRADO**: tres estados y advertencia |
| **D3** | fuga cross-tenant por el checkpointer | **CERRADO** con RLS forzado y falsador |
| **D4** | plazos en dias calendario | **CERRADO DE VERDAD** recien ahora (ver §3) |
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
| **La compuerta CABLEADA en el corpus** | **NO**. El modulo existe aca; el buscador vive en `corpus-legal-tarija` |
| FastAPI / endpoints | **NO EXISTE** |
| Los 6 agentes / grafo LangGraph | **NO EXISTE** |
| Frontend Next.js | **NO EXISTE** |
| Scraper judicial | **NO EXISTE** (legalidad acotada, ver §8) |
| Qdrant / busqueda vectorial | **NO EXISTE, a proposito**: medir antes si el lexico alcanza |
| Facturacion | **NO EXISTE** |
| Desplegado en Abacus | **NO** |
| Calendario de Tarija 2024 y 2026 | **2024 no medido; 2026 NO EMITIDO todavia** |
| **Un abogado que lo haya usado** | **CERO** |

---

## §7 · LOS DEFECTOS PROPIOS, acumulados

### P3 · Mis tests de vacacion judicial pasaban con la suspension APAGADA

65 verdes, 0 rojos, cero deteccion. **La prorroga del art. 90.III los rescataba.**
Resultado correcto, mecanismo roto.

### P4 · Mis tests "por departamento" tampoco discriminaban

Verdes con el filtro **borrado**: `calendario(dep)` ya carga solo los periodos de
ese departamento, asi que el test probaba el **cargador**, no el **filtro**.

### P5 · El falsador del CI habria dado rojo por el grep

Exigia el texto literal `ROJO vencimiento habil` y la v2 renombro ese caso. **Un
guard que depende de un texto libre es fragil por diseño.**

### P6 · Commitear archivo por archivo dejo dos corridas ROJAS en `main`

**#5** y **#6**, verificado en la lista de fallos de Actions.

### P7 · Mi propio falsador tenia un SyntaxError, y el arnes lo canto

La corrida **#15** fallo. El sabotaje 6 de privacidad borraba un bloque con un
triple-quote que terminaba en comilla y escapaba `\\s` donde el fuente tiene
`\s`: **el script no aplico nada**. El paso fallo con *"el test PASO con la
compuerta saboteada"*.

**Lo anoto como acierto del arnes y no solo como error mio.** Un sabotaje que no
sabotea tiene que dar **rojo**, no verde, y esta vez el arnes hizo justo eso: es
el E1 de ayer aplicado. La leccion de diseño: **sabotear con el replace mas corto
posible.** Un bloque multilinea con comillas anidadas es un instrumento fragil.

**Cinco veces en dos sesiones** un control se equivoco por mirar el resultado y no
el mecanismo. Es el patron que mas dinero cuesta de este repo, y esta anotado en
la cabecera del workflow.

---

## §8 · LO QUE BLOQUEA, y que se descarto de la lista

**Cerrado por texto** (ver `docs/agents/2026-09-10-plazos-medidos-en-fuente-oficial.md`):

| Antes bloqueaba | Ahora |
|---|---|
| "La tabla de plazos no la confirmo ningun abogado" | **La REGLA de computo si esta confirmada** (art. 90 Ley 439, art. 130 CPP). Sigue en hipotesis la **cantidad de dias por acto** (arts. 252, 261, 365 no abiertos) |
| "¿Es legal que un agente redacte un memorial?" | **Ninguna norma lo prohibe.** El ancla es la **Ley 387** (art. 6, art. 32.II), **no un Colegio**: la afiliacion es un derecho, no un requisito |
| "Legalidad del scraping judicial" | **Acotada.** La Ley 164 **no tipifica** scraping. El limite es el **CP art. 363 ter**, con dos elementos **acumulativos**: sin autorizacion **y** perjuicio al titular |
| "Privacidad del corpus" | **Decidida en diseño y con codigo** (ver §2). **NO cerrada**: falta cablearla en el corpus, que es otro repo |

**SIGUE BLOQUEANDO:**

1. **CABLEAR LA COMPUERTA EN EL CORPUS.** Es lo unico que separa la decision del
   arreglo. Y antes hay que ver por que el endpoint no respondio.
2. **REDISTRIBUCION DEL TEXTO INTEGRO en un producto pago.** Corrijo una
   afirmacion mia: dije que la **Ley 1322 excluye los textos oficiales** y que por
   eso se podia vender el corpus "sin pedir permiso de nadie". **Fui a buscar ese
   articulo y no existe.** El art. 4 excluye **ideas**; el art. 8 dice que el
   Estado **puede ejercer derechos de autor como titular derivado**. Vuelve a
   **NO MEDIDO**, y es pregunta para el abogado.
3. **Tratamiento de datos del bufete y envio a un proveedor de IA.**
4. **Almacenamiento de credenciales del bufete.**
5. **Colision de nombres:** "Custos Legis" ya era el log HMAC de KAMPE IR.

---

## §9 · NO MEDIDO, declarado

1. **RECALL DE LA COMPUERTA CONTRA EL CORPUS REAL.** Todo lo medido es contra **9
   fixtures** (6 reales, 3 sinteticos). Es un **piso, no un veredicto**. Y peor:
   **escribi el detector Y elegi los fixtures** (W-01). La medicion que vale es
   contra el corpus, con un tercero eligiendo la muestra.
2. **Arts. 252, 261 y 365 de la Ley 439**: fundan la tabla `PLAZOS`.
3. **Art. 264 de la Ley 1340**: el regimen "de momento a momento" esta
   **identificado, no medido**. Lo se por el AS 589/2021, no por su texto.
4. **Arts. de la Ley 548 (NNA) y 348 (violencia)** que fundan la reserva: **no los
   lei**. La reserva esta puesta por prudencia, no por texto medido.
5. **Calendario de Tarija 2020-2022 y 2024**; **fin exacto de la vacacion 2025**
   (cargado con `cubre=False`: avisa pero no autoriza a calcular).
6. **Por que el endpoint del corpus no respondio** el 10-sep.
7. **Ley 1173 y el buzon electronico penal.**
8. **Hora de cierre de los juzgados de Tarija** (el modulo usa 18:00 como supuesto
   declarado y lo avisa en cada calculo).
9. **Terminos de uso del portal del Organo Judicial y del SIREJ.**

---

## §10 · Lo proximo, en orden

1. **Ver por que el corpus no responde**, y correr la compuerta contra sus 6.079
   documentos. Ese numero (cuantos quedan publicos, cuantos retenidos) es el que
   convierte la decision en arreglo. Y es el que puede refutar todo lo de §2.
2. **Cablear la compuerta en el buscador del corpus.** Hasta entonces la fuga
   sigue viva.
3. **Confirmar la tabla de plazos** con los arts. 252, 261 y 365 en la mano.
4. **Leer los arts. de la Ley 548 y 348** para que la reserva legal tenga texto y
   no prudencia.
5. **T1: sensor de uso.** La tabla `uso_consultas` ya esta, con `q_hash` en vez del
   texto (una busqueda juridica revela la estrategia de un caso).
6. **Un abogado**, con el corpus que ya existe.
7. **Medir si el lexico alcanza** antes de meter Qdrant en una VM de 2 nucleos.
8. Recien despues: FastAPI y el grafo.

**No empiezo por el grafo porque es la parte divertida.** En el corpus eso costo 33
commits sin mover el producto.
