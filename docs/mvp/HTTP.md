# Integración HTTP del vertical MVP

El archivo `backend/mvp_server.py` reutiliza el servidor y el handler de `backend/api.py`. Las rutas existentes (`/salud`, `/sesion`, `/casos`, `/buscar`, `/plazo`, `/aprobar`, `/acciones/externa` y `/uso`) siguen pasando por el código original. El wrapper solo intercepta `/mvp/*` después de validar la misma sesión.

## Rutas nuevas

- `POST /mvp/documentos`: recibe `case_id`, `filename`, `media_type` opcional y `contenido_base64`.
- `POST /mvp/investigaciones`: recibe `case_id`, `query`, `limit` opcional y `engine` opcional.
- `POST /mvp/borradores`: recibe `case_id`, `search_id`, `materia`, `deadline` y `jurisdiction` opcional.
- `POST /mvp/borradores/{draft_id}/verificar`: recibe `case_id`.
- `POST /mvp/borradores/{draft_id}/decision`: recibe `case_id`, `decision` y `fundamento` opcional.
- `POST /mvp/borradores/{draft_id}/exportar`: recibe `case_id` y devuelve el DOCX como base64.

Todas requieren `Authorization: Bearer <sesión>`. El adaptador comprueba que el caso, investigación y borrador pertenecen al tenant de la sesión. Los documentos tienen un límite de 10 MiB.

## Arranque

Para un piloto con PostgreSQL:

```sh
DATABASE_URL_APP='...' python3 backend/mvp_server.py
```

Para pruebas, se puede importar `servir_con_mvp(app, host, puerto)` e inyectar el mismo `App` y el mismo cliente de corpus que usa la API.

La auditoría del vertical es JSONL si se define `CUSTOS_MVP_AUDIT_PATH`; de lo contrario queda en memoria de proceso, igual que la sesión del backend existente. Esto no se presenta como persistencia de producción.
