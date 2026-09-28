#!/usr/bin/env python3
"""Falsador del header autenticado del cliente Corpus configurable."""
from __future__ import annotations

import io
import json
import urllib.request

import mvp_server as SERVER


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"resultados": [], "total_pasajes": 0}).encode()


captured = {}
original = urllib.request.urlopen


def fake_urlopen(request, timeout=0):
    captured["url"] = request.full_url
    captured["authorization"] = request.get_header("Authorization")
    captured["user_agent"] = request.get_header("User-agent")
    captured["timeout"] = timeout
    return Response()


urllib.request.urlopen = fake_urlopen
try:
    client = SERVER.ConfiguredCorpusHTTP(
        "https://corpus.example", "secret-test-key")
    result = client.buscar("artículo 90", limit=7, offset=100)
finally:
    urllib.request.urlopen = original

assert result["total_pasajes"] == 0
assert "q=art%C3%ADculo+90" in captured["url"]
assert "limit=7" in captured["url"] and "offset=100" in captured["url"]
assert captured["authorization"] == "Bearer secret-test-key"
assert captured["timeout"] == 30
print("VERDE Corpus auth: API key en header, offset explícito y timeout")
