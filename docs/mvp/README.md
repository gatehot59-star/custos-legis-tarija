# Vertical MVP trazable

Esta entrega cierra el primer flujo técnico de Custos Legis sin crear agentes autónomos:

`documento -> búsqueda citada -> plazo -> borrador -> verificación -> aprobación humana -> DOCX`

## Componentes

- `backend/mvp_contract.py`: contratos de cita, documento, workflow, borrador y auditoría.
- `backend/mvp.py`: orquestador de cuatro roles lógicos: extractor, investigador, redactor y verificador.
- `backend/benchmark_busqueda.py`: protocolo común para comparar BM25, vectorial y grafo sin convertir un motor ausente en resultado cero.
- `backend/test_mvp.py`: 13 aserciones de contrato, HITL, hash y DOCX.
- `backend/test_benchmark_busqueda.py`: control de `MEASURED` frente a `NO_MEDIDO`.
- `docs/adr/2026-09-26-01-vertical-mvp-trazable.md`: decisión de arquitectura.

## Ejecución

Desde `backend/`:

```sh
python3 -m py_compile mvp_contract.py mvp.py benchmark_busqueda.py test_mvp.py test_benchmark_busqueda.py
python3 test_mvp.py
python3 test_benchmark_busqueda.py
```

La integración con el backend existente se realiza por puertos: el proveedor debe implementar `search(query, limit=...)`. Para una corrida real se usa el cliente autenticado del corpus, no se lee su SQLite ni se reabre su endpoint público cerrado.

## Reglas de seguridad del flujo

- `NO_MEDIDO` no se convierte en `VIGENTE`.
- Una cita necesita UID, fuente HTTP, fragmento, hash de fuente, vigencia y validación numérica o `not_applicable` explícito.
- Los candidatos no leídos y precedentes invalidados salen en campos separados: `unread_candidates` e `invalidated_precedents`.
- Un borrador se aprueba solo con rol `socio` o `asociado`, matrícula y verificación positiva.
- El DOCX exige aprobación vigente del hash exacto; un cambio posterior bloquea la exportación.
- Cada etapa escribe un evento JSONL si se construye el servicio con `audit_path`.

## Límite real de esta entrega

El flujo técnico está implementado y probado con fixtures. No se declara todavía un benchmark real contra 10-30 consultas del corpus porque el proveedor del corpus está cerrado y no hay un abogado que haya ejecutado el piloto. Vectorial y grafo quedan `NO_MEDIDO`, no `0`.
