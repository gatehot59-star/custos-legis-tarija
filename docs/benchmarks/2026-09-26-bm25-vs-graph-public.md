# BM25 vs grafo con datos públicos

**Fecha:** 2026-09-26  
**Rama:** `titan/patrones-reales-20260926`  
**Instrumento:** `python3 benchmarks/bm25_vs_graph_public.py`  
**Resultado de ejecución:** `exit 0`

## Pregunta medida

Cuando el usuario parte de una cita numérica de una ley departamental, ¿recupera mejor una búsqueda léxica BM25 o la expansión determinista por relaciones explícitas del grafo?

No es una comparación de búsqueda temática sobre los 57.651 chunks. Es una prueba de recuperación de relaciones normativas, que es el único caso donde el grafo tiene una hipótesis falsable con los datos públicos disponibles.

## Datos públicos usados

Se usaron únicamente las relaciones publicadas en [EXP-VIG-001 del corpus legal de Tarija](https://github.com/gatehot59-star/corpus-legal-tarija/blob/main/mediciones/EXP-VIG-001-el-techo-de-la-vigencia-esta-medido-86-por-ciento-no-nombra-su-objeto.md):

- `07 -> 129 -> 500 -> 520`
- `432 -> 500 -> 520`
- `094 -> 517`

El gold de cada consulta es el cierre dirigido de hasta dos saltos. No se agregaron relaciones inferidas desde títulos ni cláusulas genéricas.

**Cobertura:** 4 documentos con cláusulas textuales, 5 consultas, 5 aristas explícitas. `k=2`, `max_hops=2`.

## Salida cruda verbatim

```text
{'dataset': {'documents': 4, 'queries': 5, 'edges': 5}, 'rows': [{'id': 'q-007', 'query': '7', 'relevant': ['LD-129', 'LD-500'], 'bm25': ['LD-129'], 'graph': ['LD-129', 'LD-500'], 'bm25_metrics': (1.0, 0.5, 1.0), 'graph_metrics': (1.0, 1.0, 1.0)}, {'id': 'q-129', 'query': '129', 'relevant': ['LD-500', 'LD-520'], 'bm25': ['LD-500'], 'graph': ['LD-500', 'LD-520'], 'bm25_metrics': (1.0, 0.5, 1.0), 'graph_metrics': (1.0, 1.0, 1.0)}, {'id': 'q-432', 'query': '432', 'relevant': ['LD-500', 'LD-520'], 'bm25': ['LD-500'], 'graph': ['LD-500', 'LD-520'], 'bm25_metrics': (1.0, 0.5, 1.0), 'graph_metrics': (1.0, 1.0, 1.0)}, {'id': 'q-500', 'query': '500', 'relevant': ['LD-520'], 'bm25': ['LD-520'], 'graph': ['LD-520'], 'bm25_metrics': (1.0, 1.0, 1.0), 'graph_metrics': (1.0, 1.0, 1.0)}, {'id': 'q-094', 'query': '94', 'relevant': ['LD-517'], 'bm25': ['LD-517'], 'graph': ['LD-517'], 'bm25_metrics': (1.0, 1.0, 1.0), 'graph_metrics': (1.0, 1.0, 1.0)}], 'summary': {'bm25': {'precision_at_2': 1.0, 'recall_at_2': 0.7, 'mrr_at_2': 1.0}, 'graph': {'precision_at_2': 1.0, 'recall_at_2': 1.0, 'mrr_at_2': 1.0}}}
```

## Veredicto

En este alcance, **el grafo gana en recall@2: 1.0 contra 0.7 de BM25**, un aumento absoluto de 0.3, porque recupera el segundo eslabón de las cadenas `07 -> 129 -> 500` y `129/432 -> 500 -> 520`. Ambos empatan en precision@2 y MRR@2: 1.0.

Esto demuestra una ventaja concreta del grafo para relaciones explícitas y transitivas. **No demuestra que el grafo mejore la búsqueda jurídica general.** Para temas, artículos, números de ley y frases conceptuales, el corpus solo tiene BM25 medido; el grafo queda `NO MEDIDO`.

## Límites que no se esconden

- El gold público es pequeño y derivado de un único informe de medición, no de una evaluación jurídica independiente.
- No se midió latencia comparable: el fixture tiene 4 documentos y no representa los 3.646 documentos/57.651 chunks del índice léxico.
- No se midió cobertura de relaciones sobre todo el corpus: el propio informe dice que 86% de las cláusulas abrogatorias son genéricas y no nombran el objeto.
- No se usó el SQLite privado ni se afirmó acceso al endpoint online.
- El resultado queda como `MEASURED` para recuperación de relaciones explícitas, y `NO MEDIDO` para calidad temática, corpus completo y validación por abogado.

--- METODO TITAN ---
Accion delicada: NO
Modo aplicado: TITAN FULL
Rubrica: pendiente de QA sobre instrumento y recibo
N/A declarados: latencia de producción y corpus completo, porque no corresponden a este fixture público
Review externo: pendiente
Instrumento: `python3 benchmarks/bm25_vs_graph_public.py`, exit 0; salida cruda preservada arriba