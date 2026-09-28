#!/usr/bin/env python3
"""Falsadores de la ruta de plazos visible del vertical MVP."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import almacen as AL
import api as API
import mvp_server as SERVER


def request(port: int, method: str, path: str, body: object | None = None,
            token: str | None = None) -> tuple[int, dict]:
    raw = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 data=raw, method=method)
    if raw:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


store = AL.SqliteAlmacen(permitir_sin_rls=True)
store.sembrar_bufete("a", "Estudio A", "a@example.test", "clave-a",
                    rol="socio", matricula="MAT-A")
app = API.App(almacen=store)
server = SERVER.servir_con_mvp(app, "127.0.0.1", 0)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]

status, data = request(port, "POST", "/sesion",
                       {"email": "a@example.test", "password": "clave-a"})
assert status == 200
token = data["token"]
status, data = request(port, "POST", "/casos", {
    "nro_expediente": "PLAZO-MVP/2026", "juzgado": "Juzgado 1", "materia": "civil",
}, token=token)
assert status == 201
case_id = data["id"]

status, data = request(port, "POST", "/mvp/plazos", {
    "case_id": case_id, "notificacion": "2026-01-05", "dias": "3", "materia": "civil",
}, token=token)
assert status == 200
assert data["estado"] in {"CONFIRMADO", "NO_MEDIDO"}
assert data["computo"]
assert "fundamento" in data

status, data = request(port, "POST", "/mvp/plazos", {
    "case_id": case_id, "notificacion": "2026-01-05", "dias": "3",
    "materia": "familia",
}, token=token)
assert status == 200 and data["estado"] == "NO_MEDIDO"
assert data["vencimiento"] is None

status, _ = request(port, "POST", "/mvp/plazos", {
    "case_id": "caso-de-otro-tenant", "notificacion": "2026-01-05", "dias": "3",
    "materia": "civil",
}, token=token)
assert status == 404

server.shutdown()
print("VERDE MVP plazos: cálculo visible, detalle diario y NO_MEDIDO por materia")
