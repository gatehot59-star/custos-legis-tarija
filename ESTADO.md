# ESTADO REAL de Custos Legis Tarija

**Medido:** 2026-09-10 06:05 UTC · **Corrida de CI:** `34443503074`, **success**

> **Este archivo existe porque el documento de diseño declaraba `FASE 1 ✅ ... FASE 5 ✅`
> sin una linea de codigo en el repo.** Aca va lo contrario: lo que corre, con su
> salida, y lo que no existe, dicho como no existe.

---

## §1 · LO QUE EXISTE Y CORRE (medido en CI, no en mi maquina)

| Pieza | Estado | Evidencia |
|---|---|---|
| **Plazos habiles bolivianos** | **VERDE, 27/27** | `test_plazos.py` en Actions |
| **Esquema PostgreSQL con RLS** | **VERDE**, 5 tablas con RLS **forzado** | `psql -f infra/init.sql`, `ON_ERROR_STOP=1` |
| **Aislamiento entre bufetes** | **VERDE, 16/16** | `test_rls.py` contra **PostgreSQL 16 real** |
| **Cliente del corpus** | **VERDE**, corrido en vivo | 184 pasajes en **10,26 ms** |
| **Falsador de plazos** | **DIO ROJO cuando corresponde** | sabotaje detectado con el rojo esperado |
| **Falsador de la fuga D3** | **DIO ROJO cuando corresponde** | `ETIQUETAS_ROJAS: FUGA-CKPT` |

**Total: 43 aserciones verdes y 2 falsadores que demuestran poder dar rojo.**

### El falsador del D3, verbatim, porque es el que importa

Con el RLS de `cl_checkpoints` deshabilitado a proposito:

```
ROJO FUGA-CKPT B NO ve el memorial secreto de A: obtuve True, esperaba False
ROJO FUGA-CKPT consulta dirigida al checkpoint de A da vacio: obtuve 1, esperaba 0
ETIQUETAS_ROJAS: FUGA-CKPT
```

Y con el RLS restaurado, **verde otra vez**. O sea: el test **prueba la fuga que dice probar**, no otra cosa.

---

## §2 · LOS 9 DEFECTOS DE FABLE: cuales estan cerrados

| # | Defecto del diseño | Estado |
|---|---|---|
| **D1** | `_limpiar_texto_legal` reescribia el crudo | **CERRADO**: `texto_crudo` y `texto_normalizado` separados, con **trigger** que rechaza modificar el crudo. Verificado por test |
| **D2** | `estado_vigencia="vigente"` hardcodeado | **CERRADO**: tres estados (`VIGENTE`/`DEROGADA`/`NO_MEDIDO`) y **advertencia obligatoria**. Medido: 3 de 3 resultados salen con "vigencia no verificada" |
| **D3** | fuga cross-tenant por el checkpointer | **CERRADO**: `cl_checkpoints` con `tenant_id`, RLS forzado y trigger de convencion. **Con falsador que lo demuestra** |
| **D4** | plazos en dias calendario | **CERRADO**: dias habiles con feriados nacionales + Tarija. Contra-test incluido: `timedelta(days=3)` desde un jueves cae **domingo** |
| **D5** | Constitucionalista audita una estrategia que no existe | **PENDIENTE**: no hay grafo todavia. Anotado |
| **D6** | `Depends(lambda...)` con generador sin consumir | **NO APLICA AUN**: no hay FastAPI |
| **D7** | `InMemoryStore` se pierde al reiniciar | **CERRADO por diseño**: la memoria va en `cl_checkpoints`, en Postgres |
| **D8** | modelos hardcodeados detras del gateway | **PENDIENTE** |
| **D9** | SIREJ→SIGC sin fuente verificable | **CERRADO**: medido en fuente primaria, y **dimensionado**: solo penal, piloto en Chuquisaca, Bs 160 M como anteproyecto en mar-2026. El campo `sistema_origen` acepta `sirej`/`sigc`/`eforo`/`manual` |

**6 de 9 cerrados con codigo y test. 3 pendientes, declarados.**

---

## §3 · LO QUE NO EXISTE, y no voy a llamarlo fase verde

| Capa | Estado |
|---|---|
| FastAPI / endpoints | **NO EXISTE** |
| Los 6 agentes / grafo LangGraph | **NO EXISTE** |
| Frontend Next.js | **NO EXISTE** |
| Scraper judicial | **NO EXISTE** (y su legalidad **NO MEDIDA**) |
| Qdrant / busqueda vectorial | **NO EXISTE, y a proposito**: el ADR-001 dice medir antes si el lexico alcanza |
| Facturacion | **NO EXISTE** |
| Desplegado en Abacus | **NO** |
| **Un abogado que lo haya usado** | **CERO** |

---

## §4 · LOS DEFECTOS PROPIOS DE ESTA SESION

Dos, y el primero es el que mas vale:

### P1 · Mi propio falsador dio el veredicto correcto por la razon equivocada

La v1 del sabotaje de CI imprimio **"OK: la fuga de checkpoints fue detectada"** y **no habia detectado ninguna fuga**. El test fallaba porque sembraba bufetes nuevos en cada corrida sin limpiar, y mi contra-test de conteo ("el superusuario ve 2 casos") se rompia al ver 4.

**Un control que acierta el veredicto por la razon equivocada no es un control.** Arreglado con dos cosas: el test limpia lo suyo y cuenta **solo sus filas**, y cada rojo lleva una **etiqueta estable** que el CI exige (`FUGA-CKPT`).

Y de paso mordio el clasico: `grep 'ROJO ' archivo` sin match sale con codigo **1**, y con `bash -e` eso mato el paso. **Un grep vacio no es un error del sistema.**

### P2 · El bytecode cacheado sobrevivio al sabotaje

Restaure `plazos.py`, el **md5 coincidia con el original**, y el test seguia dando rojo. Causa: el `__pycache__/plazos.cpython-312.pyc` **saboteado** seguia ahi. Un cache es un instrumento contaminado, y el md5 del fuente no lo detecta. El workflow ahora borra `__pycache__` antes y despues.

---

## §5 · LO QUE BLOQUEA, y no es tecnico

1. **PRIVACIDAD DEL CORPUS.** Medido hoy: `q=Mamani` en el buscador **publico sin login** devuelve **1.232 pasajes**, y el primero nombra a las dos partes de una causa de **violacion de un menor**. Custos Legis va a manejar datos **mas** sensibles. **Decision de Abraham, sin resolver.**
2. **¿Es legal que un agente redacte un memorial?** Se presenta bajo la matricula de un abogado. **NO MEDIDO.**
3. **Legalidad del scraping judicial.** El diseño propone rotar cabeceras "para mimetizar trafico humano". Eso es evadir un control del Estado. **NO MEDIDO**, e hay hipotesis de via legitima por Ciudadania Digital.
4. **La tabla de plazos no la confirmo ningun abogado.** El codigo lo declara: cada entrada sale como `HIPOTESIS`, nunca como cierta.
5. **Colision de nombres:** "Custos Legis" ya era el log HMAC de KAMPE IR. Renombrar hoy cuesta un `git mv`.

---

## §6 · Lo proximo, en orden

1. **Decidir la privacidad del corpus.** Bloquea todo lo demas.
2. **T1 de Fable: sensor de uso.** La tabla `uso_consultas` ya esta en el esquema, con `q_hash` en vez del texto (decision declarada: una busqueda juridica revela la estrategia de un caso).
3. **Un abogado**, con el corpus que ya existe.
4. **Medir si el lexico alcanza** antes de meter Qdrant en una VM de 2 nucleos.
5. Recién despues: FastAPI y el grafo.

**No empiezo por el grafo porque es la parte divertida.** En el corpus eso costo 33 commits sin mover el producto.
