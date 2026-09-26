#!/usr/bin/env python3
"""Pruebas ejecutables del vertical MVP.

Ejecutar desde este directorio con `python3 test_mvp.py`. Cada falsador rompe
una condición distinta: una cita sin fuente, un plazo no confirmado, un cambio
posterior a la aprobación y una exportación sin aprobación.
"""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

import mvp


class FixtureProvider:
    """Proveedor controlado: representa el contrato del corpus sin red."""

    def search(self, query: str, *, limit: int = 10) -> dict:
        return {"resultados": [
            {
                "uid": "ley-439",
                "afirmacion": "El plazo confirmado es de 10 días hábiles.",
                "pasaje": "Artículo 90: el plazo de 10 días se computa así.",
                "fuente_url": "https://fuente.example/ley-439",
                "sha256": "a" * 64,
                "vigencia": "VIGENTE",
                "validacion_numerica": {
                    "status": "validated", "expected": "10",
                    "observed": "10", "method": "fixture legal revisado"
                },
            },
            {
                "uid": "candidato-sin-vigencia",
                "pasaje": "Texto con artículo 99.",
                "fuente_url": "https://fuente.example/sin-vigencia",
                "sha256": "b" * 64,
                "vigencia": "NO_MEDIDO",
            },
            {
                "uid": "precedente-derogado",
                "pasaje": "Texto derogado.",
                "fuente_url": "https://fuente.example/derogado",
                "sha256": "c" * 64,
                "vigencia": "DEROGADA",
            },
        ][:limit]}


checks = 0
failures: list[str] = []


def check(name: str, condition: bool) -> None:
    global checks
    checks += 1
    if condition:
        print(f"OK   {name}")
    else:
        failures.append(name)
        print(f"ROJO {name}")


service = mvp.MVPService.create(FixtureProvider())
doc = service.ingest_document("tenant-a", "case-1", "notificacion.pdf",
                              b"contenido anonimo del fixture")
check("documento conserva hash", len(doc.sha256) == 64)
search = service.research("tenant-a", "case-1", "plazo artículo 90")
check("una cita pasa a allowed_citations", len(search.allowed_citations) == 1)
check("candidato sin vigencia queda unread", len(search.unread_candidates) == 1)
check("precedente derogado queda invalidado", len(search.invalidated_precedents) == 1)

# La ruta feliz necesita un plazo explícitamente confirmado.
draft = service.draft(
    "tenant-a", "case-1", search,
    {"estado": "CONFIRMADO", "vencimiento": "2026-10-10",
     "fundamento": "fixture de cálculo validado"},
    "civil")
check("workflow tiene cuatro roles", draft.workflow.roles == (
    "extractor", "investigador", "redactor", "verificador"))
check("verificador acepta el borrador", service.verify(draft.draft_id)["ok"])

with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / "salida.docx"
    try:
        service.export_docx("tenant-a", "case-1", draft.draft_id, target)
        check("exportación sin aprobación bloquea", False)
    except mvp.ApprovalRequired:
        check("exportación sin aprobación bloquea", True)

    approved = service.decide("tenant-a", "case-1", draft.draft_id,
                              "user-1", "socio", "MAT-1", "aprobado",
                              "revisado por abogado")
    check("aprobación registra hash exacto", approved["content_sha256"] == draft.content_sha256)
    service.export_docx("tenant-a", "case-1", draft.draft_id, target)
    check("DOCX se crea tras aprobación", target.exists())
    with zipfile.ZipFile(target) as archive:
        check("DOCX contiene document.xml", "word/document.xml" in archive.namelist())
        check("DOCX contiene la cita", "fuente.example" in archive.read("word/document.xml").decode())

# Falsador: un cambio posterior al borrador no puede exportarse con la aprobación vieja.
service.drafts[draft.draft_id] = mvp.Draft(
    draft_id=draft.draft_id, case_id=draft.case_id,
    content=draft.content + " CAMBIO POSTERIOR", content_sha256=mvp.sha256_text(
        draft.content + " CAMBIO POSTERIOR"), workflow=draft.workflow,
    search=draft.search, deadline=draft.deadline, warnings=draft.warnings)
try:
    service.export_docx("tenant-a", "case-1", draft.draft_id, "/tmp/no-debe-existir.docx")
    check("cambio posterior rompe hash", False)
except mvp.ApprovalRequired:
    check("cambio posterior rompe hash", True)

# Falsador: una cita sin fuente no entra aunque tenga fragmento y vigencia.
bad = mvp.citation_from_result({
    "uid": "sin-fuente", "pasaje": "Afirmación 10", "vigencia": "VIGENTE",
    "sha256": "d" * 64,
})
check("cita sin fuente no es exportable", not bad.exportable)

print(json.dumps({"checks": checks, "failures": failures}, ensure_ascii=False))
if failures:
    sys.exit(1)
