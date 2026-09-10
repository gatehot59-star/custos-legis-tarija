# ADR-001 · La frontera entre el corpus y Custos Legis

**Fecha:** 2026-09-10 · **Estado:** aceptada · **Decide:** Abraham

## Contexto

Abraham declaró que **`corpus-legal-tarija` es un producto independiente que debe seguir mejorando**, y que Custos Legis es la **segunda parte de la suite que se vale de él**.

Sin una frontera escrita, el riesgo concreto es que Custos Legis empiece a pedirle al corpus cosas que lo convierten en su módulo interno: multi-tenancy, datos confidenciales de bufetes, campos que solo Custos Legis usa. **Ahí el corpus deja de ser vendible por sí mismo**, que es exactamente lo que Abraham quiere evitar.

## Decisión

**El corpus se consume por su contrato HTTP público y nada más.** Custos Legis es **un cliente**, no un dueño.

### Lo que Custos Legis SÍ puede pedirle al corpus

Son mejoras que **le sirven a cualquier consumidor**, no solo a Custos Legis, y por eso son legítimas:

| # | Pedido | Por qué le sirve también al corpus solo |
|---|---|---|
| 1 | **Vigencia usable** (hoy 13 de 527) | cualquiera que cite una ley necesita saber si vive |
| 2 | **Títulos reales** (hoy 432 de 1.034 son basura) | un resultado sin nombre no se le muestra a nadie |
| 3 | **`materia` poblada** (hoy vacía al 100 %) | es un filtro básico de cualquier buscador |
| 4 | **Jerarquía normativa explícita** (nacional / departamental / municipal) | es un metadato del documento, no una necesidad de Custos Legis |
| 5 | **Corpus municipal de Tarija** (hoy inexistente) | amplía la cobertura del producto base |

### Lo que Custos Legis NO puede pedirle

| # | NO se le pide | Dónde va |
|---|---|---|
| 1 | **Multi-tenancy / RLS** | en Custos Legis. El corpus sirve datos **públicos**: no tiene inquilinos |
| 2 | **Guardar documentos confidenciales de bufetes** | en Custos Legis, cifrado y aislado. Meter un expediente privado en un repo público sería un incidente |
| 3 | **Estado procesal, plazos, casos, facturación** | en Custos Legis. Nada de eso es normativa |

**La regla de decisión, para no discutirla caso por caso:**

> ¿Le sirve a alguien que **solo** usa el corpus? → va al corpus.
> ¿Solo le sirve a un bufete con expedientes activos? → va a Custos Legis.

## El contrato que ya existe, medido

El corpus **ya expone** lo que un agente necesita, y eso no hay que construirlo:

```
GET /buscar?q=...&limit=&offset=   -> pasajes con cita, fuente_url, sha256
GET /texto?uid=&nro=               -> texto continuo del documento
GET /estado                        -> conteos y limites declarados
GET /openapi.json                  -> contrato formal
GET /agente/manifiesto             -> descubrimiento para agentes
GET /api/v1/procedencias/{uid}     -> de donde sale cada documento
```

Y `/buscar` devuelve **facetas por materia, tipo y año** más el conteo total, medido en **11,23 ms** para 184 pasajes.

**El corpus también ya declara sus límites**, que es la parte que un consumidor honesto tiene que respetar:

- la búsqueda es **literal**: no hay expansión semántica
- las facetas cuentan sobre **una muestra de 400 pasajes**, no sobre el total
- el desplazamiento **corta en 10.000 pasajes**

## Consecuencia incómoda, y va escrita

**El "Agente Investigador" del diseño asume búsqueda vectorial sobre Qdrant. El corpus hoy es léxico.**

Y no es obvio que vectorial sea mejor acá: para *"Art. 252 CPC"*, *"AS/0122/2026"* o *"Ley 439"*, **BM25 le gana a la similitud semántica**, que puede traer un fallo parecido en vez del que lleva ese número. La búsqueda semántica contesta *"casos como este"*, que es **otra pregunta**.

**Decisión: no se asume. Se mide.** El falsador es barato: tomar 10 consultas reales de un abogado y comparar léxico contra vectorial. Si el léxico alcanza, **Qdrant no entra al stack** y se ahorra un servicio entero en una VM de 2 núcleos.

**NO MEDIDO:** las 10 consultas reales. Requieren un abogado, que es el hueco H4.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Custos Legis lee la base SQLite del corpus directo | acopla los dos productos por su esquema interno: un cambio del corpus rompe Custos Legis en silencio |
| Copiar el corpus dentro de Custos Legis | dos copias que divergen. Ya vi ese patrón con el inventario de máquinas |
| Fusionar los dos repos | contradice la decisión de Abraham y mata la venta independiente del corpus |

## Criterio de éxito de esta ADR

Se cumple si dentro de tres meses **el corpus sigue arrancando y sirviendo sin que Custos Legis exista**. Si para entonces el corpus necesita a Custos Legis para funcionar, esta frontera se rompió y hay que decirlo.
