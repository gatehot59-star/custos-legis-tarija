# ESTADO REAL de Custos Legis Tarija

**Medido:** 2026-09-10 13:36 UTC · **Corrida de CI:** `tests #20` (commit `458bf54`), **passing**

> **Este archivo existe porque el documento de diseño declaraba `FASE 1 ✅ ... FASE 5 ✅`
> sin una linea de codigo en el repo.** Aca va lo contrario: lo que corre, con su
> salida, y lo que no existe, dicho como no existe.
>
> **El testigo no soy yo.** El verde lo declara Actions, no mi maquina:
> https://github.com/gatehot59-star/custos-legis-tarija/actions/workflows/tests.yml

---

## §0 · EL NUMERO QUE MAS IMPORTA HOY, y no es un verde

**La compuerta de privacidad deja publicable el 17,3 % del corpus. Retiene el 82,7 %.**

Medido con `impacto_compuerta.py` sobre la composicion que el propio corpus
publica en `/estado`:

| Fuente | Documentos | Clase | Decision |
|---|---|---|---|
| GENESIS (Autos Supremos del TSJ) | **5.030** | jurisprudencial | **RETENIDO** |
| Gaceta Tarija (normativa departamental) | 1.034 | normativo | PUBLICO |
| LexiVox (normativa nacional) | 15 | normativo | PUBLICO |
| **total** | **6.079** | | **17,3 % publicable** |

**Yo habia escrito, en el docstring de la compuerta, que el reparto "conserva el
valor del corpus (las normas, que son la MAYORIA y las que se citan)". Es falso.**
Las normas son 1 de cada 6 documentos.

**Que cambia y que no:**

- **NO cambia** el argumento tecnico. Un detector de nombres sigue siendo
  fail-open y sigue habiendo 4 de 4 fugas medidas (ver §2). La compuerta se
  sostiene.
- **SI cambia una decision de producto.** El flujo de `aprobado_por_matricula`
  NO es la excepcion para un caso raro: es **el camino de 5 de cada 6
  documentos**. Si aprobar documento por documento es incomodo, el producto es
  incomodo. Eso hay que diseñarlo sabiendo el numero, no descubrirlo con el
  primer abogado.
- **NO MEDIDO, y probablemente peor:** el reparto por **pasaje**. El corpus
  declara 78.930 pasajes y no publica su desglose por fuente. Un Auto Supremo es
  mas largo que una resolucion de la Asamblea, asi que por pasaje el porcentaje
  retenido es probablemente mayor. No lo afirmo: no lo tengo.

---

## §1 · LO QUE EXISTE Y CORRE (medido en CI, no en mi maquina)

| Pieza | Estado | Evidencia |
|---|---|---|
| **Compuerta de publicacion** | **VERDE, 53/53** | `test_anonimizador.py` |
| **Impacto de la compuerta** | **corre en CI** | `impacto_compuerta.py` |
| **Plazos procesales POR MATERIA** | **VERDE, 71/71** | `test_plazos.py` |
| **Calendario judicial por departamento** | **VERDE, 36/36** | `test_calendario.py` |
| **Esquema PostgreSQL con RLS** | **VERDE**, 5 tablas con RLS **forzado** | `psql -f infra/init.sql` |
| **Aislamiento entre bufetes** | **VERDE, 16/16** | `test_rls.py` contra **PostgreSQL 16 real** |
| **18 falsadores** | **LOS 18 DAN ROJO** con la etiqueta exigida | 9 plazos + 8 privacidad + 1 RLS |
| **7 guards** | activos | RLS forzado, tabla sin confirmar, fuente del calendario, reserva legal, ninguna fixture publicable |

**Total: 176 aserciones verdes (53 privacidad + 71 plazos + 36 calendario + 16 RLS)
y 18 falsadores que demuestran poder dar rojo.**

**Por que uno por mecanismo:** un falsador solo prueba que el test detecta **lo
que ese falsador rompe**. El CI exige la **etiqueta** del rojo, no cualquier rojo,
y al final verifica con `cmp` que los fuentes quedaron identicos.

---

## §2 · EL BLOQUEADOR #1: decidido con codigo, y NO arreglado

**Lo primero, para que nadie lea de mas:** la compuerta vive en ESTE repo. El
buscador con la fuga vive en **`corpus-legal-tarija`**, que es **otro producto**.
Lo que hay es **la pieza y la decision de arquitectura**, no el corte. Mientras
nadie cablee esto en el buscador, el codigo de aca no protege nada de alla.

### Por que el corpus no responde: la respuesta estaba commiteada

El `ESTADO.md` anterior tenia como NO MEDIDO *"por que el endpoint del corpus no
respondio"*. **No era un misterio: el acceso publico lo cerre YO a las 06:29 UTC
de hoy**, por orden de Abraham, y quedo en
`corpus-legal-tarija/CIERRE-PUBLICO-2026-09-10.md` con 12 rutas dando 503 y
control positivo por SSH de que la VM seguia viva. Ver §7/P8.

### Lo que se midio y cambio el diseño

El primer instinto era un **anonimizador**: detectar nombres y taparlos. Lo
escribi, y despues lo corri contra cuatro textos adversarios:

| Texto | Nombre | Detectado |
|---|---|---|
| "interpuesta contra Mamani" | Mamani | **NO** (un solo apellido) |
| "planteado por juan carlos quispe" | quispe | **NO** (minusculas, OCR malo) |
| "El demandante, sr. R. Villca T." | Villca | **NO** (abreviado) |
| "Se condena al acusado GUTIERREZ" | GUTIERREZ | **NO** (mayuscula suelta) |

**Cuatro de cuatro.** Con el detector como control, los cuatro nombres se habrian
**publicado**: el gate no tenia nada que retener.

**Un detector de nombres es FAIL-OPEN.** Asi que el control **no es el detector**:

1. **La capa publica NO muestra texto libre de jurisprudencia.** Metadatos, cita,
   hash y enlace oficial. Superficie de fuga **cero por construccion**.
2. **Las normas SI se publican enteras**, porque no tienen partes por naturaleza.
   (Y son el 17,3 %: ver §0.)
3. **Reserva legal** (NNA, violencia, familia, 17 disparadores en el texto): no se
   publica **ni anonimizada**. Ni con matricula.
4. **El extracto seudonimizado** requiere **aprobacion de un abogado con
   matricula**, documento por documento (Ley 387 art. 6).

### La categoria importa, y aca se paga caro (E-01)

- **"Magistrado Relator: Dr. Carlos Alberto Eguez Anez"** es un acto publico de
  una autoridad en ejercicio. **Taparlo destruye la trazabilidad de la cita**, y
  hay un falsador dedicado a que nadie lo tape.
- **"la denuncia presentada por Maria Elena Choque Villca"** es una parte.
- **"Editorial Amanecer S.A."** es una persona **juridica**: el art. 21.2 CPE
  habla de "las bolivianas y los bolivianos".

### El defecto que medi en mi propia v1 de la compuerta

Tenia `ARTICULO \d+` y `CODIGO` como señas **normativas**. Con eso clasifico un
fragmento de la **SCP 0693/2023-S4** como NORMATIVO, y los normativos se publican
sin compuerta: **esa Sentencia Constitucional habria salido a la capa publica por
citar el art. 130 del CPP.** Ahora hay señas **fuertes** y **debiles**.

Y una regla que sale de ahi: **si el corpus DECLARA el tipo, se le cree al
corpus.** Adivinar por texto lo que un metadato ya dice es reemplazar un dato por
una heuristica.

---

## §3 · EL MOTOR DE PLAZOS: el D4 estaba mal cerrado

El art. 90.II de la Ley 439 pide **dos** reglas:

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
89.I declara **perentorio**.

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
declaradas como no modeladas**.

---

## §4 · EL CALENDARIO JUDICIAL

1. **Los departamentos NO coinciden.** Gestion 2025: Potosi **8-dic a 1-ene**,
   Santa Cruz **9-dic a 2-ene**, TSJ nacional **hasta el 5-ene**. Tres rangos,
   mismo año.
2. **Las fechas no siguen patron.** Tarija: 2018 del 7 al 31-dic, 2019 del 3 al
   27-dic, 2023 del 5 al 29-dic.
3. **Hay vacaciones extraordinarias.** Mayo 2026, TDJ La Paz, una semana por
   conflictos y bloqueos.

### El pendiente del 2026 estaba MAL PLANTEADO

La vacacion se fija en Sala Plena **entre octubre y noviembre**; lo dijo la decana
del TSJ en julio de 2026. **Hoy es septiembre: el dato no puede existir.** No es
un dato que no medi: es un dato que **el Organo Judicial no emitio todavia**.

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

### P4 · Mis tests "por departamento" tampoco discriminaban

Verdes con el filtro **borrado**: el test probaba el **cargador**, no el **filtro**.

### P5 · El falsador del CI habria dado rojo por el grep

Exigia un texto literal que la v2 renombro. **Un guard que depende de un texto
libre es fragil por diseño.**

### P6 · Commitear archivo por archivo dejo dos corridas ROJAS en `main`

**#5** y **#6**, verificado en la lista de fallos de Actions.

### P7 · Mi propio falsador tenia un SyntaxError, y el arnes lo canto

La corrida **#15** fallo con *"el test PASO con la compuerta saboteada"*, que es
exactamente lo que tiene que decir. **Acierto del arnes**, no solo error mio.

### P8 · Declare NO MEDIDO algo que yo mismo habia commiteado seis horas antes

El `ESTADO.md` anterior listaba *"por que el endpoint del corpus no respondio"*
como NO MEDIDO. **La respuesta estaba en el repo de al lado, en un archivo que
escribi yo a las 06:33 UTC del mismo dia**, con las 12 rutas en 503 y el control
positivo por SSH.

Eso no es falta de informacion: **es haber dejado de buscar.** Y el costo real es
que un NO MEDIDO falso desvia el trabajo, igual que un defecto falso en un
informe de auditoria.

### P9 · Mi propio test no distinguia AFIRMAR de CITAR-PARA-REFUTAR

Al corregir el docstring escribi la asercion "la frase refutada NO puede estar en
el docstring". **Dio ROJO contra un docstring correcto**, porque el docstring
**cita** la frase para refutarla. Un `in` no distingue las dos cosas: es el mismo
defecto de **contar palabras en vez de estructura**. La version que quedo verifica
que la frase solo aparezca **despues** del encabezado de refutacion.

### P10 · Dos falsadores vivieron un rato solo en mi historial de shell

Los corri a mano, dieron rojo, y no los cablee. **Un control que nadie corre no es
un control, es una anecdota.** Ahora son los falsadores 7 y 8 del job de
privacidad.

**Siete veces en dos sesiones** un control se equivoco por mirar el resultado y no
el mecanismo, o por no existir donde se lo necesitaba. Es el patron mas caro de
este repo y esta anotado en la cabecera del workflow.

---

## §8 · LO QUE BLOQUEA, y que se descarto de la lista

**Cerrado por texto** (ver `docs/agents/2026-09-10-plazos-medidos-en-fuente-oficial.md`):

| Antes bloqueaba | Ahora |
|---|---|
| "La tabla de plazos no la confirmo ningun abogado" | **La REGLA de computo si esta confirmada** (art. 90 Ley 439, art. 130 CPP). Sigue en hipotesis la **cantidad de dias por acto** |
| "¿Es legal que un agente redacte un memorial?" | **Ninguna norma lo prohibe.** El ancla es la **Ley 387**, **no un Colegio** |
| "Legalidad del scraping judicial" | **Acotada.** El limite es el **CP art. 363 ter**, con dos elementos **acumulativos**: sin autorizacion **y** perjuicio al titular |
| "Privacidad del corpus" | **Decidida en diseño, con codigo y con su costo medido** (§0 y §2). **NO cerrada**: falta cablearla |

**SIGUE BLOQUEANDO:**

1. **CABLEAR LA COMPUERTA EN EL CORPUS**, y decidir sabiendo que solo el 17,3 %
   queda abierto. Es la unica cosa que separa la decision del arreglo.
2. **REDISTRIBUCION DEL TEXTO INTEGRO en un producto pago.** Dije que la **Ley
   1322 excluye los textos oficiales** y **fui a buscar ese articulo y no
   existe**: el art. 4 excluye **ideas**; el art. 8 dice que el Estado **puede
   ejercer derechos de autor como titular derivado**. **NO MEDIDO**, pregunta para
   el abogado.
3. **Tratamiento de datos del bufete y envio a un proveedor de IA.**
4. **Almacenamiento de credenciales del bufete.**
5. **Colision de nombres:** "Custos Legis" ya era el log HMAC de KAMPE IR.

---

## §9 · NO MEDIDO, declarado

1. **RECALL DE LA COMPUERTA CONTRA EL TEXTO REAL.** Todo lo medido es contra **9
   fixtures** (6 reales, 3 sinteticos). El **impacto** si esta medido contra los
   6.079 documentos, pero por **fuente**, no abriendo cada documento. Y peor:
   **escribi el detector Y elegi los fixtures** (W-01).
2. **El reparto por PASAJE** (78.930 pasajes sin desglose por fuente).
3. **Que la asuncion fuente == clase se cumpla documento por documento.** Es el
   **punto unico de falla** del diseño: si GENESIS estuviera mal clasificado,
   5.030 Autos Supremos saldrian publicos con nombres. Hay contra-test.
4. **Cuantos de los 5.030 caen en RESERVA_LEGAL** (NNA, violencia).
5. **Arts. 252, 261 y 365 de la Ley 439**: fundan la tabla `PLAZOS`.
6. **Art. 264 de la Ley 1340**: el regimen "de momento a momento" esta
   **identificado, no medido**.
7. **Arts. de la Ley 548 (NNA) y 348 (violencia)** que fundan la reserva: **no los
   lei**. Prudencia, no texto.
8. **Calendario de Tarija 2020-2022 y 2024**; **fin exacto de la vacacion 2025**.
9. **Ley 1173 y el buzon electronico penal.**
10. **Hora de cierre de los juzgados de Tarija.**
11. **El bind en `0.0.0.0:8080` del backend del corpus.** El cierre de nginx NO lo
    tapa: desde internet no se llega (medido, 522), pero cualquier cosa dentro de
    la red de la VM le pega al backend directo. **El arreglo cuesta una linea** y
    es decision de Abraham, no mia.
12. **Si algo del corpus quedo cacheado o indexado afuera** antes del cierre.

---

## §10 · Lo proximo, en orden

1. **Decidir con el 17,3 % sobre la mesa.** Las opciones ya no son abstractas:
   (a) capa publica solo normativa y jurisprudencia detras de login, (b) aprobar
   por matricula en tandas, (c) reabrir todo aceptando el riesgo por escrito. La
   (a) es la que el codigo ya implementa.
2. **Arreglar el bind en `0.0.0.0`** si Abraham lo aprueba: una linea.
3. **Cablear la compuerta en el buscador del corpus.** Hasta entonces la fuga
   sigue viva del otro lado.
4. **Confirmar la tabla de plazos** con los arts. 252, 261 y 365 en la mano.
5. **Leer los arts. de la Ley 548 y 348** para que la reserva tenga texto.
6. **T1: sensor de uso.** La tabla `uso_consultas` ya esta, con `q_hash`.
7. **Un abogado**, con la normativa departamental, que es lo que SI se puede
   mostrar abierto hoy.
8. Recien despues: FastAPI y el grafo.

**No empiezo por el grafo porque es la parte divertida.** En el corpus eso costo 33
commits sin mover el producto.
