# Recibo de verificación HTTP del vertical MVP

**Rama:** `titan/mvp-http-routes-20260926`  
**Fecha:** 2026-09-26

## Comandos

```sh
python3 -m py_compile backend/api.py backend/mvp_http.py backend/mvp_server.py backend/test_mvp_http.py
python3 backend/test_mvp_http.py
```

## Salida cruda

```text
127.0.0.1 POST /sesion 200
127.0.0.1 POST /sesion 200
127.0.0.1 POST /casos 201
127.0.0.1 POST /mvp/investigaciones 401
127.0.0.1 POST /mvp/documentos 201
127.0.0.1 POST /mvp/investigaciones 201
127.0.0.1 POST /mvp/borradores 201
127.0.0.1 POST /mvp/borradores/{draft_id}/verificar 200
127.0.0.1 POST /mvp/borradores/{draft_id}/decision 201
127.0.0.1 POST /mvp/borradores/{draft_id}/exportar 200
127.0.0.1 POST /mvp/borradores/{draft_id}/verificar 404
VERDE HTTP MVP: rutas existentes + sesión, caso, documento, investigación, borrador, HITL y DOCX
```

**Exit code:** `0`.

La prueba demuestra autenticación compartida, creación del caso por la ruta existente, rechazo sin sesión, carga de documento, investigación, borrador, verificación, aprobación humana, exportación DOCX y aislamiento de borrador entre bufetes.

## Límite declarado

La integración se entrega como `mvp_server.py`, un wrapper compatible que conserva `api.py` sin duplicar su autenticación. El comando histórico `python3 backend/api.py` sigue sirviendo solo las rutas originales; el arranque del MVP es `python3 backend/mvp_server.py`. La persistencia del estado del vertical sigue siendo de piloto: memoria para índices y decisiones, JSONL opcional para auditoría.

--- METODO TITAN ---
Accion delicada: NO
Modo aplicado: TITAN FULL
Rubrica: N/A para recibo
N/A declarados: PostgreSQL/RLS y corpus real no fueron necesarios para este test de cableado
Review externo: no pedido
Instrumento: Python 3, comandos arriba, exit 0, salida cruda incluida
