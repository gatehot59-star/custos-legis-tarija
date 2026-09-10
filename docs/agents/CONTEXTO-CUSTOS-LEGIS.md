# CONTEXTO-CUSTOS-LEGIS · el contexto vivo del proyecto

**Creado:** 2026-09-10 · **Última actualización:** 2026-09-10 (fundación)

Esto se lee **antes** de trabajar en Custos Legis, y se actualiza en el mismo turno en que algo cambia.

---

## 1 · Qué es, y qué NO es

**CUSTOS LEGIS TARIJA** (*el que vela por la ley*): SaaS multi-inquilino para bufetes de Tarija. Vigila las notificaciones de los juzgados, calcula el plazo fatal, busca los fundamentos, valida que no se viole la CPE, arma la estrategia y redacta el memorial. **El abogado aprueba o rechaza; el sistema nunca presenta nada solo.**

**NO es** el corpus con una capa encima. El corpus es un producto independiente que sigue su propio camino (ver `README.md` §1).

---

## 2 · Decisiones tomadas

| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-09-10 | **`corpus-legal-tarija` es producto INDEPENDIENTE** y sigue mejorando por su cuenta | Decisión de Abraham. Si Custos Legis muere, el corpus sigue siendo vendible |
| 2026-09-10 | Custos Legis es la **segunda parte de la suite** y **consume** el corpus | Decisión de Abraham |
| 2026-09-10 | Se implementa en **Abacus.AI**, igual que el corpus | Decisión de Abraham |
| 2026-09-10 | Nace **público** | Actions gratis e ilimitado en público contra cuota en privado. Y el corpus ya es público: dos repos de la misma suite con visibilidad distinta obliga a recordar cuál es cuál |
| 2026-09-10 | El inventario de máquinas **no se copia, se linkea** | Copiarlo multiplica las copias a sincronizar |
| 2026-09-10 | **El humano aprueba siempre.** La compuerta va en la topología, no en el prompt | Un agente que presenta al juzgado sin firma es responsabilidad profesional del abogado |

---

## 3 · Estado medido

**De este repo:** cero código, cero base, cero agente, cero cliente.

**Del corpus que va a consumir** (medido 2026-09-09/10):

```
6.079 documentos · 78.930 pasajes · 102.620.935 caracteres
GENESIS 5.030 · Gaceta Tarija 1.034 · LexiVox 15
vigencia con estado medido: 13 de 527 leyes (2,47 %)
GET /buscar?q=asistencia+familiar -> 184 pasajes en 11,23 ms
```

**De la VM de Abacus:** x86_64, 2 núcleos, 6,3 GB de RAM libre, sin swap, 35 GB de disco, `/dev/kvm` usable (API 12), docker presente. `corpus-api` usa 24,8 MB.

**Del SIGC** (fuente primaria, `tsj.bo` 8-abr-2025 y `larazon.bo` 9-mar-2026): convenio firmado, **solo materia penal**, piloto en **Chuquisaca**, y el despliegue nacional era un **anteproyecto de Bs 160 millones** en marzo de 2026. Existe además **Éforo**, que ya interopera con SIREJ, Tritón JL, SEGIP y AGETIC.

---

## 4 · LOS CINCO HUECOS QUE EL DISEÑO NO CUBRE

El documento fuente es sólido en arquitectura. Estos huecos no son de arquitectura, y son los que pueden matar el producto.

### H1 · ¿Es legal que un agente redacte un memorial? ← **el que decide todo**

El sistema produce un escrito que se presenta a un juzgado bajo la **matrícula de un abogado**. En Bolivia eso toca el ejercicio de la abogacía y la responsabilidad profesional.

**NO MEDIDO:** qué dice la Ley del Ejercicio de la Abogacía y el código de ética del Colegio de Abogados de Tarija sobre delegar la redacción a un sistema automatizado, y quién responde si el memorial cita un artículo derogado y el cliente pierde el plazo.

**Es H1 y no H5 porque si la respuesta es mala, la arquitectura no importa.**

### H2 · La vigencia: el sistema puede citar una ley abrogada

Medido en el corpus: **el 86 % de las abrogaciones no nombra a su objeto** ("se abrogan todas las disposiciones contrarias"). La vigencia automática al 100 % **no existe con esa fuente**, y hoy hay **13 de 527 leyes** con estado.

El diseño asume un campo `estado_vigencia: "vigente"` como filtro de búsqueda. **Ese filtro hoy descartaría el 97,5 % del corpus, o peor: dejaría pasar como vigente lo que nadie midió.**

**Es el defecto más peligroso del producto**, porque un memorial que cita una norma abrogada es un memorial perdido y el abogado no lo va a notar.

### H3 · Legalidad del scraping judicial

El diseño propone Playwright con *"retardos aleatorios y rotación de cabeceras para mimetizar tráfico humano y evitar la suspensión de la IP"*.

Eso es, textualmente, **evadir una medida de control de un sistema del Estado**. Para el corpus resolví la publicidad con norma (CPCo arts. 15 y 19), pero eso cubre **leer resoluciones publicadas**, no **automatizar consultas de expedientes de terceros**.

**NO MEDIDO:** si el SIREJ publica términos de uso, y si consultar el expediente de un cliente con su poder cambia el análisis. **Hipótesis no medida:** existiría una vía legítima por Ciudadanía Digital (que Éforo ya usa) en vez de scraping.

### H4 · Ningún abogado usó nada de esta suite

El corpus lleva desde el 3-sep en producción con **cero abogados** usándolo. Custos Legis es **mucho más complejo** y arranca con el mismo cero.

El diseño especifica plazos procesales (3 días para apelar un auto interlocutorio, Art. 252 CPC) **sin que un abogado boliviano los haya confirmado**. Si esa tabla está mal, el sistema calcula mal el plazo fatal, que es su promesa central.

### H5 · El costo por caso no está estimado

El flujo son **6 nodos LLM**, varios con Claude Sonnet y 2.000-4.000 tokens de salida, y un ciclo que puede repetirse hasta 2 veces por rechazo del abogado. **NO MEDIDO:** cuánto cuesta procesar UNA notificación, y si eso deja margen sobre lo que un bufete de Tarija paga.

El diseño ya trae la tabla `agent_runs` con `costo_usd`. Es lo correcto: **el instrumento existe antes del producto.**

---

## 5 · Cementerio de hipótesis

| # | Hipótesis | Cómo murió |
|---|---|---|
| H-001 | "El MVP actual es un prototipo conversacional en AbacusAI al que le falta el corpus de la Gaceta de Tarija" (auditoría del documento fuente) | **FALSA, medida.** Ese enlace es el corpus: 184 pasajes en 11,23 ms con FTS5, y las Leyes Departamentales aparecen en las facetas. La auditoría concluyó sobre un sujeto que no midió |
| H-002 | "El reemplazo del SIREJ por el SIGC es la alerta más urgente" | **PARCIAL.** El convenio existe (8-abr-2025) pero es **solo penal**, piloto en Chuquisaca, y en marzo-2026 el despliegue nacional seguía siendo un anteproyecto de Bs 160 M. Para civil y familiar en Tarija, el SIREJ sigue |

---

## 6 · Lo que sigue, y el orden importa

1. **H1 y H3**: las dos preguntas legales. Son de lectura, no de código, y pueden invalidar el producto.
2. **Medir el contrato del corpus como proveedor**: ¿su API alcanza para el Agente Investigador o hace falta la capa vectorial? El `/estado` ya declara que la búsqueda es literal.
3. **Un abogado real**, con el corpus que ya existe, antes de escribir el primer agente.
4. Recién después: PostgreSQL + RLS con el test negativo cross-tenant, que es la única prueba del diseño que **no puede fallar en silencio**.

**Lo que NO voy a hacer:** empezar por el código del grafo porque es la parte divertida. En el corpus ya me costó 33 commits sin mover el producto.
