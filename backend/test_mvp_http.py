#!/usr/bin/env python3
"""Prueba HTTP real del vertical conectado a api.py."""
from __future__ import annotations

import base64
import json
import threading
import urllib.error
import urllib.request

import almacen as AL
import api as API


class CorpusDoble:
    """Proveedor de fixture con el contrato que consume el vertical."""

    def buscar(self, query: str, limit: int = 10) -> dict:
        """Devuelve una fuente vigente con validación numérica."""
        return {"total_pasajes": 1, "resultados": [{
            "uid": "ley-439", "afirmacion": "El plazo es de 10 días.",
            "pasaje": "Artículo 90: el plazo es de 10 días.",
            "fuente_url": "https://fuente.example/ley-439",
            "sha256": "a" * 64, "vigencia": "VIGENTE",
            "validacion_numerica": {"status": "validated", "expected": "10",
                                    "observed": "10", "method": "fixture"},
        }]}


def request(port: int, method: str, path: str, body: dict | None = None,
            token: str | None = None) -> tuple[int, dict]:
    """Hace una petición JSON contra el servidor real del test."""
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
store.sembrar_bufete("b", "Estudio B", "b@example.test", "clave-b",
                    rol="socio", matricula="MAT-B")
app = API.App(almacen=store, corpus=CorpusDoble())
server = API.servir(app, "127.0.0.1", 0)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]

status, data = request(port, "POST", "/sesion",
                       {"email": "a@example.test", "password": "clave-a"})
assert status == 200
token_a = data["token"]
status, data_b = request(port, "POST", "/sesion",
                         {"email": "b@example.test", "password": "clave-b"})
assert status == 200
token_b = data_b["token"]

status, data = request(port, "POST", "/casos",
                       {"nro_expediente": "MVP-1/2026", "juzgado": "Juzgado 1", "materia": "civil"}, token_a)
assert status == 201
case_id = data["id"]

status, _ = request(port, "POST", "/mvp/investigaciones",
                    {"case_id": case_id, "query": "artículo 90"})
assert status == 401

encoded = base64.b64encode(b"notificacion de prueba").decode()
status, data = request(port, "POST", "/mvp/documentos",
                       {"case_id": case_id, "filename": "notificacion.pdf",
                        "contenido_base64": encoded}, token_a)
assert status == 201
assert len(data["documento"]["sha256"]) == 64

status, data = request(port, "POST", "/mvp/investigaciones",
                       {"case_id": case_id, "query": "artículo 90", "limit": 5}, token_a)
assert status == 201
search_id = data["search_id"]
assert len(data["investigacion"]["allowed_citations"]) == 1

status, data = request(port, "POST", "/mvp/borradores",
                       {"case_id": case_id, "search_id": search_id,
                        "materia": "civil", "deadline": {"estado": "CONFIRMADO"}}, token_a)
assert status == 201
draft_id = data["borrador"]["draft_id"]

status, data = request(port, "POST", f"/mvp/borradores/{draft_id}/verificar",
                       {"case_id": case_id}, token_a)
assert status == 200 and data["verificacion"]["ok"] is True

status, data = request(port, "POST", f"/mvp/borradores/{draft_id}/decision",
                       {"case_id": case_id, "decision": "aprobado",
                        "fundamento": "revisado"}, token_a)
assert status == 201

status, data = request(port, "POST", f"/mvp/borradores/{draft_id}/exportar",
                       {"case_id": case_id}, token_a)
assert status == 200
assert data["media_type"].endswith("wordprocessingml.document")
assert len(base64.b64decode(data["content_base64"])) > 100

status, _ = request(port, "POST", f"/mvp/borradores/{draft_id}/verificar",
                    {"case_id": case_id}, token_b)
assert status == 404

server.shutdown()
print("VERDE HTTP MVP: sesión, caso, documento, investigación, borrador, HITL y DOCX")
