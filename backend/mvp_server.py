#!/usr/bin/env python3
"""Servidor integrado de Custos Legis y puente del piloto."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any

import api as API
from almacen import PostgresAlmacen
from mvp import MVPError
from mvp_http import MVPHTTPError, MVPHTTPState

App = API.App
MAX_JSON_BODY_BYTES = 14 * 1024 * 1024


class ConfiguredCorpusHTTP:
    """Cliente HTTP autenticado, sin conocer la base interna del Corpus.

    El nombre del header y el esquema son configurables porque el contrato
    autenticado del Corpus todavía no está publicado. Sin API key, producción
    conserva el cliente cerrado existente y no inventa una credencial.
    """

    def __init__(self, base: str, api_key: str, header: str = "Authorization",
                 scheme: str = "Bearer") -> None:
        if not base or not api_key or not header:
            raise ValueError("base, api_key y header son obligatorios")
        self.base = base.rstrip("/")
        self.api_key = api_key
        self.header = header
        self.scheme = scheme

    def buscar(self, q: str, limit: int = 10, offset: int = 0) -> dict[str, Any]:
        """Consulta /buscar con credencial, límite y offset explícitos."""
        url = self.base + "/buscar?" + urllib.parse.urlencode({
            "q": q, "limit": limit, "offset": offset,
        })
        request = urllib.request.Request(url, headers={
            "User-Agent": f"custos-legis/{API.VERSION}",
            "Accept": "application/json",
            self.header: f"{self.scheme} {self.api_key}" if self.scheme else self.api_key,
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise API.CorpusCerrado(f"/buscar devolvió HTTP {response.status}")
                payload = json.loads(response.read().decode("utf-8"))
        except API.CorpusCerrado:
            raise
        except urllib.error.HTTPError as exc:
            if exc.code == 503:
                raise API.CorpusCerrado(
                    "el Corpus rechazó la consulta autenticada (503)") from exc
            raise API.CorpusCerrado(
                f"/buscar rechazó la consulta (HTTP {exc.code})") from exc
        except Exception as exc:  # noqa: BLE001
            raise API.CorpusCerrado(
                f"no se pudo consultar el Corpus autenticado: {type(exc).__name__}: {exc}") from exc
        if not isinstance(payload, dict):
            raise API.CorpusCerrado("/buscar no devolvió un objeto JSON")
        return payload


def corpus_configurado() -> object:
    """Selecciona cliente autenticado solo cuando existe una API key explícita."""
    key = os.environ.get("CORPUS_API_KEY", "").strip()
    if not key:
        return API.CorpusHTTP()
    return ConfiguredCorpusHTTP(
        base=os.environ.get("CORPUS_BASE", "https://150448fcc6.abacusai.cloud"),
        api_key=key,
        header=os.environ.get("CORPUS_API_KEY_HEADER", "Authorization"),
        scheme=os.environ.get("CORPUS_API_KEY_SCHEME", "Bearer"),
    )


def construir_handler_mvp(app: App):
    """Extiende el handler existente con MVP y cálculo visible de plazos."""
    base_handler = API.construir_handler(app)

    class Handler(base_handler):
        """Handler que añade `/mvp/*` y delega lo demás a `api.py`."""

        def _despachar(self, metodo: str, ruta: str, params: dict):
            if ruta == "/mvp/plazos" and metodo == "POST":
                try:
                    sesion = self._sesion()
                    longitud = int(self.headers.get("Content-Length") or 0)
                    if longitud > MAX_JSON_BODY_BYTES:
                        raise MVPHTTPError(413, "el cuerpo JSON supera el límite de 14 MiB")
                    cuerpo = self._cuerpo()
                    if not isinstance(cuerpo, dict):
                        raise MVPHTTPError(400, "el cuerpo JSON debe ser un objeto")
                    case_id = cuerpo.get("case_id")
                    if not isinstance(case_id, str) or not case_id.strip():
                        raise MVPHTTPError(400, "case_id es obligatorio")
                    if app.almacen.caso(sesion.usuario.tenant_id, case_id) is None:
                        raise MVPHTTPError(404, "caso inexistente en este bufete")
                    calculo = {key: value for key, value in cuerpo.items()
                               if key != "case_id"}
                    return 200, app.plazo(sesion, calculo)
                except MVPHTTPError as error:
                    return error.status, {"error": str(error)}
                except API.CorpusCerrado as error:
                    return 503, {"error": str(error), "corpus": "cerrado"}
                except MVPError as error:
                    return 422, {"error": str(error)}
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
    app = App(almacen=almacen, corpus=corpus_configurado())
    host = os.environ.get("CUSTOS_HOST", "127.0.0.1")
    puerto = int(os.environ.get("CUSTOS_PUERTO", "8090"))
    server = servir_con_mvp(app, host, puerto)
    print(f"custos-legis MVP en http://{host}:{puerto}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
