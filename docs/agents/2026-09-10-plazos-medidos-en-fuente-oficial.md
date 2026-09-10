# Plazos medidos en fuente oficial, y un defecto nuevo en `backend/plazos.py`

**Fecha:** 2026-09-10 · **Repo:** `gatehot59-star/custos-legis-tarija` · **Commit base leído:** `1c9f994`

**Instrumento:** (a) lectura del texto de cada norma en fuente oficial o repositorio que reproduce el texto ordenado (Lexivox, Gaceta Oficial, TSJ, UNODC/OAS); (b) **ejecución del propio `plazos.py`** contra el cómputo que ordena la ley, para todos los `noti` del 1, 8, 15 y 22 de cada mes de 2026.

**Tres estados:** CONFIRMADO (leí el texto), REFUTADO (el texto dice otra cosa), NO MEDIDO (no lo abrí).

---

## 1 · Lo que el header de `plazos.py` declaraba como hipótesis, ahora está CONFIRMADO por texto

El módulo dice: *"Los articulos del CPC (Ley 439) que el diseno cita NINGUN ABOGADO BOLIVIANO LOS CONFIRMO"*. Hay que separar dos cosas que el header mezcla:

- **La regla de cómputo**: ya no es hipótesis. Está en el texto.
- **La cantidad de días por tipo de acto** (arts. 252, 261, 365): **sigue NO MEDIDO**. No abrí esos artículos. La etiqueta `confirmado: False` de la tabla se queda como está y está bien puesta.

### Ley 439 art. 90, verbatim

> **II.** Los plazos transcurrirán en forma ininterrumpida, salvo disposición contraria. **Se exceptúan los plazos cuya duración no exceda de quince días, los cuales sólo se computarán los días hábiles. En el cómputo de los plazos que excedan los quince días se computarán los días hábiles y los inhábiles.**
>
> **III.** Los plazos vencen **el último momento hábil del horario de funcionamiento** de los juzgados y tribunales del día respectivo; sin embargo, si resultare que el último día corresponde a día inhábil, el plazo quedará prorrogado hasta el primer día hábil siguiente.

> **Art. 90.I.** Los plazos [...] comenzarán a correr **a partir del día siguiente hábil** al de la respectiva citación o notificación, salvo [...] plazos comunes, en cuyo caso correrán a partir del día hábil siguiente al de la **última** notificación.

Fuente: https://www.lexivox.org/norms/BO-L-N439.html

**El supuesto de dies a quo que el módulo declara (arranca el día hábil SIGUIENTE) es correcto y está en el art. 90.I.** Ese ya no es un supuesto, es la norma.

### Ley 1970 (CPP) art. 130, verbatim

> Los plazos determinados por días comenzarán a correr al día siguiente de practicada la notificación y **vencerán a las veinticuatro horas del último día hábil señalado**. Al efecto, **se computará sólo los días hábiles**, salvo que la ley disponga expresamente lo contrario **o que se refiera a medidas cautelares, caso en el cual se computarán días corridos**. [...] **Los plazos sólo se suspenderán durante las vacaciones judiciales.**

Fuente: https://www.lexivox.org/norms/BO-L-1970.html

---

## 2 · DEFECTO NUEVO, MEDIDO: `traslado_demanda` de 30 días está mal calculado

`PLAZOS["traslado_demanda"] = {"dias": 30, ...}` y `vencimiento()` cuenta **solo hábiles** para cualquier valor. Pero 30 > 15, así que el art. 90.II ordena contar **hábiles e inhábiles**.

Corrí el propio código contra el cómputo legal, 48 fechas de notificación de 2026:

| Notificación | `plazos.py` (hábiles) | Ley (90.II corridos + 90.III) | Días que el código regala |
|---|---|---|---|
| 2026-01-01 | 2026-02-13 | 2026-02-02 | **11** |
| 2026-01-08 | 2026-02-24 | 2026-02-09 | **15** ← peor caso 2026 |
| 2026-01-15 | 2026-03-03 | 2026-02-18 | **13** |
| 2026-04-01 | 2026-05-18 | 2026-05-04 | **14** |
| 2026-04-15 | 2026-05-28 | 2026-05-15 | **13** |
| 2026-12-01 | 2027-01-14 | 2026-12-31 | **14** |
| 2026-12-15 | 2027-01-29 | 2027-01-14 | **15** |

**La dirección del error es la peligrosa.** El código dice que el plazo vence **después** de lo que realmente vence. Un abogado que le crea al sistema presenta hasta dos semanas tarde y el plazo es perentorio (art. 89.I: *"Los plazos procesales son perentorios"*). No hay recuperación.

Es el mismo defecto de fondo que el `timedelta(days=)` que este módulo vino a arreglar: **se aplicó una sola regla a todos los plazos.** El arreglo fue de `corridos` a `hábiles`, cuando la ley pide **las dos según el umbral de 15 días**.

### Lo que sí está bien, medido

Los plazos ≤ 15 días (3, 5, 10 días: interlocutorio, excepción, apelación, casación) **coinciden con la ley**. Verificado con notificación 2026-04-13 (lunes) y el feriado departamental de La Tablada el 15-abr en medio:

```
auto_interlocutorio       3d habiles desde 2026-04-13 -> 2026-04-17
contestacion_excepcion    5d habiles desde 2026-04-13 -> 2026-04-21
apelacion/casacion       10d habiles desde 2026-04-13 -> 2026-04-28
```

Y el generador de feriados móviles (Meeus/Butcher) da fechas correctas para 2026: Carnaval 16 y 17 de febrero, Viernes Santo 3 de abril, Corpus Christi 4 de junio.

**Nota sobre el 21 de junio de 2026: cae domingo.** No cambia nada porque el fin de semana ya es inhábil, pero es un recordatorio de que un feriado en fin de semana no agrega un día.

---

## 3 · DEFECTO MEDIDO: el módulo no conoce la vacación judicial

`es_habil()` solo excluye sábados, domingos, feriados nacionales, La Tablada y un set `extra` que hay que pasar a mano. **La vacación judicial no está.**

> **Ley 810, que modifica el art. 126 LOJ.** Vacación anual colectiva de **veinticinco (25) días calendario en el mes de diciembre** [...] **IV. Durante el período de vacaciones, todo plazo en la tramitación de los juicios quedará suspendido** y continuará automáticamente a la iniciación de sus labores, **debiendo establecerse con precisión el momento de suspensión y de reapertura**.

Fuente: https://www.lexivox.org/norms/BO-L-N810.xhtml

Medido con el código actual:

```
10 dias habiles desde 2026-12-01 -> el codigo dice 2026-12-15
```

Si la vacación arranca el 9 de diciembre, ese plazo **se suspende** y el vencimiento real cae en enero. El código entrega una fecha que cae dentro del período suspendido.

**Y el calendario judicial no es una constante anual:**

1. Las fuentes públicas de la vacación 2025-2026 **se contradicen**: unas dan 9-dic-2025 al 5-ene-2026, otras 9-dic-2025 al 2-ene-2026. Un dato de producción no puede salir de prensa: sale de la **circular del Tribunal Departamental**.
2. **Hay vacaciones extraordinarias.** En mayo de 2026 el TDJ de La Paz declaró una semana de vacación judicial por conflictos y bloqueos, descontada de la programada. Un calendario cargado una vez al año se desactualiza sin avisar.

**Diseño obligado:** tabla `calendario_judicial` versionada **por departamento**, con `fuente` (número de circular), `fecha_publicacion` y `vigencia`. Sin circular cargada para el período, el Vigilante devuelve **NO MEDIDO**, no un número. Eso es más honesto y más seguro que un feriado hardcodeado.

---

## 4 · DEFECTO DE CATEGORÍA: el módulo es civil y no lo dice

`vencimiento()` devuelve un `date` sin hora y sin parámetro de materia. La ley pide dos motores:

| Variable | Civil (Ley 439) | Penal (Ley 1970) |
|---|---|---|
| Plazo ≤ 15 días | Solo hábiles (90.II) | Solo hábiles (130) |
| Plazo > 15 días | Hábiles **e** inhábiles (90.II) | Solo hábiles salvo ley expresa (130) |
| Medidas cautelares | n/a | **Días corridos** (130) |
| Hora de vencimiento | Último momento hábil del horario judicial (90.III) | **24:00** del último día hábil (130) |
| Último día inhábil | Prórroga al primer hábil siguiente (90.III) | Vence el último día **hábil** señalado |
| Horas hábiles fuera del juzgado | 06:00 a 19:00 (art. 91.II) | idem |

Un `date` pelado no puede representar "vence a las 24:00" ni "vence cuando cierra el juzgado". La diferencia entre las dos es de horas y decide si un escrito entró.

---

## 5 · Qué cambia en el código

1. `vencimiento(notificacion, dias, materia)` con el **umbral de 15 días** y las dos rutas del art. 90.II. Test que compare las dos rutas en el mismo caso.
2. **Contra-test obligatorio**: `traslado_demanda` desde 2026-01-08 debe dar **2026-02-09**, no 2026-02-24. Si el test pasa con el código actual, el test no discrimina.
3. `materia` explícita (`civil` | `penal`) y `medida_cautelar: bool`. Devolver `datetime`, no `date`.
4. `calendario_judicial` versionado por departamento y circular. Sin circular, `NO_MEDIDO`.
5. El cálculo **siempre muestra el cómputo día por día** con la marca de cada día (hábil, inhábil, feriado, vacación) para que el abogado lo verifique en segundos. Un número solo no es verificable.
6. Actualizar el header del módulo: la **regla de cómputo** está confirmada por texto; lo que sigue siendo hipótesis es la **cantidad de días por tipo de acto**.

---

## 6 · Dos correcciones a afirmaciones MÍAS del turno anterior

### 6.1 · REFUTADO: la Ley 1322 no excluye los textos oficiales

Afirmé que la Ley 1322 **excluye de protección los textos oficiales** (leyes, decretos, resoluciones judiciales) y concluí que se podía mostrar y vender el texto íntegro *"sin pedir permiso de nadie"*. Fui a buscar el artículo y **no existe**. Lo que dice el texto:

> **Art. 4.** Esta Ley protege exclusivamente la forma literaria, plástica o sonora [...] **No son objetos de protección las ideas** contenidas en las obras literarias y artísticas, o el contenido ideológico o técnico de las obras científicas.

> **Art. 8.** Únicamente la persona natural puede ser autor; sin embargo, **el Estado, las entidades de derecho público** [...] **pueden ejercer los derechos de autor como titulares derivados**.

Eso excluye **ideas**, no **textos oficiales**, y el art. 8 va en la dirección contraria a lo que afirmé. Tampoco encontré la excepción en la Decisión 351 de la CAN al alcance de esta medición: lo que aparece en las legislaciones andinas es la difusión **por prensa y con fines informativos** de discursos y alocuciones pronunciadas en actuaciones judiciales, que no es reproducir la resolución completa en un producto pago.

**Estado real: NO MEDIDO, no verde.** No está probado que esté prohibido, y la publicidad procesal (CPE art. 178) juega a favor. Pero mi conclusión operativa citaba un artículo que no dice lo que yo quería que dijera, que es exactamente el defecto que le marqué al documento fuente.

**Mientras no haya opinión legal:** corpus público con metadatos, cita, extracto anonimizado, hash y **enlace a fuente oficial**. Texto íntegro detrás de login. El índice, la compilación y el buscador sí son producto propio.

Fuente: https://www.lexivox.org/norms/BO-L-1322.html

### 6.2 · REFUTADO: la prescripción son 3 o 5 años, y el artículo citado era el equivocado

> **CC art. 1507.** Los derechos patrimoniales se extinguen por la prescripción **en el plazo de cinco años**, a menos que la ley disponga otra cosa.
>
> **CC art. 1508.** **Prescribe a los tres años** el derecho al resarcimiento del daño que causa un hecho ilícito o generador de responsabilidad, contados desde que el hecho se verificó.

El documento fuente decía *"10 años según el Código Civil, art. 1508"*. Ni el plazo ni el artículo: el 1508 son **tres** años y es justamente el que aplica al daño por hecho ilícito, o sea el escenario de un error de plazo. **Conservar evidencia 10 años sigue siendo prudente, pero se justifica por prudencia, no citando el 1508.**

Fuente: https://www.oas.org/dil/esp/codigo_civil_bolivia.pdf

---

## 7 · Otras dos verificaciones que cambian el diseño

### 7.1 · CONFIRMADO: el límite penal del acceso automatizado es el CP 363 ter, no la Ley 164

> **CP art. 363 ter.** El que **sin estar autorizado** se apodere, acceda, utilice, modifique, suprima o inutilice, datos almacenados en una computadora o en cualquier soporte informático, **ocasionando perjuicio al titular de la información** [...]

Dos elementos **acumulativos**: falta de autorización **y** perjuicio al titular. La consulta pública por NUREJ, sin login y sin eludir autenticación, no encaja en el tipo. El uso de credenciales ajenas, sí. **La Ley 164 no tipifica scraping.**

Fuente: https://sherloc.unodc.org/cld/en/legislation/bol/codigo_penal/libro_segundo/articulos_363bis_ter/articulos_363bis_ter.html

### 7.2 · CONFIRMADO: el HITL se ancla en la Ley 387, no en un Colegio

> **Ley 387 art. 6.** Para ejercer la abogacía [...] se requiere: 1. Título profesional. **2. Registro y matriculación en el Ministerio de Justicia.**
>
> **Art. 32.II.** La responsabilidad por infracciones a la ética **no exime de la responsabilidad penal, civil o administrativa**.

La afiliación a un Colegio figura entre los **derechos** del abogado (art. 8), no entre los requisitos. El régimen de ética y los Tribunales de Ética están dentro de la Ley 387 y su reglamento (DS 1760, modificado por DS 4690). **El evento `aprobado_por_matricula` firma con el número del Registro Público de la Abogacía del Ministerio de Justicia.**

Fuente: http://www.gacetaoficialdebolivia.gob.bo/normas/descargarPdf/142494

---

## 8 · NO MEDIDO, declarado

1. **Arts. 252, 261 y 365 de la Ley 439.** Son los que fundan la tabla `PLAZOS`. No los abrí. La tabla sigue en `confirmado: False` con razón.
2. **Ley 1173 y el buzón electrónico de notificaciones penales.** Lo afirmé en el turno anterior sin verificarlo. Hasta abrir el texto, el modelo penal se queda en el art. 130 puro.
3. **Circular de vacaciones judiciales 2026 del TDJ Tarija.** Es el primer registro del calendario judicial y sin él el Vigilante no arranca.
4. **Feriados departamentales de Tarija con fuente normativa**, más allá del 15 de abril.
5. **Cobertura del corpus propio:** falta correr `buscar?q="quince días"` contra `corpus-legal-tarija` y confirmar que el art. 90.II está indexado. Si la norma que decide el producto no está en el corpus, el corpus tiene un hueco en el centro.
6. **Términos de uso del portal del Órgano Judicial y del SIREJ.**

---

## 9 · Estado del proyecto de ley de IA (era hipótesis, ahora tiene fecha)

- **PL 178/2024-2025** "Promoción, Gestión y Uso de la Inteligencia Artificial": aprobado por la **Cámara de Senadores el 22-oct-2025** y remitido a Diputados. 31 artículos.
- Reportes de 2026 lo siguen ubicando **en Diputados, en análisis**, sin plazo. **No hay ley de IA promulgada.**
- Las fuentes **se contradicen sobre la autoridad**: unas dicen que crea la **ARIA**, otras que la autoridad competente es **AGETIC**. No lo resuelvo sin el texto del proyecto.
- Además aparecen un **PL 310/2025-2026** reportado en marzo de 2026 y un **PL CD-558-24 archivado el 17-jun-2025**. No es un único proyecto lineal.

**Consecuencia:** no se escribe "Custos Legis deberá registrarse ante AGETIC" como obligación vigente. Se escribe: *no hay obligación de registro vigente a la fecha de esta medición*, y el diseño debe poder absorber un régimen de sistemas de alto riesgo (auditoría, trazabilidad, supervisión humana) sin rehacerse. La trazabilidad ya diseñada cubre eso.

---

## 10 · Qué quedó cerrado y qué sigue siendo pregunta para el abogado

**Cerrado por texto, ya no necesita opinión:** cómputo de plazos por materia, umbral de 15 días, hora de vencimiento, dies a quo, suspensión por vacaciones, ancla de la responsabilidad profesional, y el límite penal del acceso automatizado.

**Abierto y bloqueante:**

1. Redistribución del texto íntegro de resoluciones y gacetas en un producto pago (sin artículo que lo autorice ni que lo prohíba: es opinión profesional).
2. Qué datos anonimizar, en qué materias, con qué base normativa (reserva en NNA y violencia).
3. Qué consentimiento y contrato hacen falta para tratar datos del bufete y enviarlos a un proveedor de IA, sin ley de protección de datos vigente.
4. Qué autorización específica exige almacenar credenciales del bufete.
5. Qué debe decir el sistema, textualmente, cuando un plazo o una cita no está verificado.

**El único de los cinco que frena el MVP es ninguno. Lo que frena el MVP es el defecto de la sección 2, y está en el código, no en la ley.**
