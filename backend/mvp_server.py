#!/usr/bin/env python3
"""backend/mvp_server.py: servidor compatible con las rutas API y el vertical MVP.

Reutiliza el handler, autenticación, sesiones, almacén y corpus de `api.py`.
Solo intercepta rutas `/mvp/*`; todas las rutas existentes siguen pasando por
el handler original. Esto permite integrar el vertical sin duplicar la API ni
crear una segunda frontera de autenticación.
"""
from __future__ import annotations

import os
import sys
from http.server import ThreadingHTTPServer
from typing import Any

import api as API
from almacen import PostgresAlmacen
from mvp import MVPError
from mvp_http import MVPHTTPError, MVPHTTPState

App = API.App
MAX_JSON_BODY_BYTES = 14 * 1024 * 1024


def construir_handler_mvp(app: App):
    """Extiende el handler existente con las rutas autenticadas del MVP."""
    base_handler = API.construir_handler(app)

    class Handler(base_handler):
        """Handler que añade `/mvp/*` y delega lo demás a `api.py`."""

        def _despachar(self, metodo: str, ruta: str, params: dict):
            if ruta.startswith("/mvp/"):
                try:
                    sesion = self._sesion()
                    longitud = int(self.headers.get("Content-Length") or 0)
                    if longitud > MAX_JSON_BODY_BYTES:
                        raise MVPHTTPError(413, "el cuerpo JSON supera el límite de 14 MiB")
                    cuerpo = self._cuerpo() if metodo == "POST" else {}
                    if not isinstance(cuerpo, dict):
                        raise MVPHTTPError(400, "el cuerpo JSON debe ser un objeto")
                    return app.mvp_http.handle(
                        metodo, ruta, cuerpo, sesion, app.almacen)
                except MVPHTTPError as error:
                    return error.status, {"error": str(error)}
                except API.CorpusCerrado as error:
                    return 503, {"error": str(error), "corpus": "cerrado"}
                except MVPError as error:
                    return 422, {"error": str(error)}
            return super()._despachar(metodo, ruta, params)

    return Handler


def servir_con_mvp(app: App, host: str = "127.0.0.1",
                   puerto: int = 8090) -> ThreadingHTTPServer:
    """Sirve las rutas actuales y el vertical MVP bajo la misma sesión."""
    app.mvp_http = MVPHTTPState.create(app.corpus)
    return ThreadingHTTPServer((host, puerto), construir_handler_mvp(app))


def main() -> int:
    """Arranca el servidor de producción con PostgreSQL y devuelve su código."""
    dsn = os.environ.get("DATABASE_URL_APP")
    if not dsn:
        print("falta DATABASE_URL_APP: no se arranca con SQLite", file=sys.stderr)
        return 2
    almacen = PostgresAlmacen(dsn)
    try:
        almacen.uso_total()
    except Exception as error:  # noqa: BLE001
        print(f"NO SE PUDO CONECTAR A POSTGRES: {type(error).__name__}: {error}",
              file=sys.stderr)
        return 3
    app = App(almacen=almacen)
    host = os.environ.get("CUSTOS_HOST", "127.0.0.1")
    puerto = int(os.environ.get("CUSTOS_PUERTO", "8090"))
    server = servir_con_mvp(app, host, puerto)
    print(f"custos-legis MVP en http://{host}:{puerto}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
