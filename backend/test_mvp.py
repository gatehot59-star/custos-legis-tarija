#!/usr/bin/env python3
"""Pruebas ejecutables del vertical MVP y sus patrones incorporados.

Ejecutar desde este directorio con `python3 test_mvp.py`. Cada falsador rompe
una condición distinta: una cita sin fuente, un plazo no confirmado, un cambio
posterior a la aprobación, una exportación sin aprobación o una cita apoyada en
memoria operativa.
"""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

import mvp
from patterns import (AnswerState, Claim, EvidenceItem, EvidenceLayer,
                      EvidenceRegistry, LegalGraph, draft_diff, workflow_pack)


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


class GraphFixtureProvider:
    """Fixture con relaciones explícitas para probar expansión por grafo."""

    def search(self, query: str, *, limit: int = 10) -> dict:
        return {"resultados": [
            {
                "uid": "art-90", "afirmacion": "Artículo 90 plazo civil",
                "pasaje": "diez días hábiles", "fuente_url": "https://f/90",
                "sha256": "9" * 64, "vigencia": "VIGENTE",
                "validacion_numerica": {"status": "validated"},
                "cites": ["precedente-90"],
            },
            {
                "uid": "precedente-90", "afirmacion": "precedente sobre plazo",
                "pasaje": "cómputo del plazo", "fuente_url": "https://f/p90",
                "sha256": "8" * 64, "vigencia": "VIGENTE",
                "validacion_numerica": {"status": "not_applicable"},
                "cites": ["norma-90"],
            },
            {
                "uid": "norma-90", "afirmacion": "norma relacionada",
                "pasaje": "regla aplicable", "fuente_url": "https://f/n90",
                "sha256": "7" * 64, "vigencia": "VIGENTE",
                "validacion_numerica": {"status": "not_applicable"},
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
check("answer contract marca evidencia parcial como limited", search.answer_state == "limited")
check("evidence_ids solo contiene autoridad legal", search.evidence_ids == ("ley-439",))

# La ruta feliz necesita un plazo explícitamente confirmado.
draft = service.draft(
    "tenant-a", "case-1", search,
    {"estado": "CONFIRMADO", "vencimiento": "2026-10-10",
     "fundamento": "fixture de cálculo validado"},
    "civil")
check("workflow pack civil queda versionado", draft.workflow.pack_id == "tarija-civil")
check("workflow tiene cuatro roles", draft.workflow.roles == (
    "extractor", "investigador", "redactor", "verificador"))
check("workflow conserva pasos como datos", "verificacion" in draft.workflow.steps)
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

# Judicex: la memoria operativa puede orientar, pero nunca citarse como ley.
registry = EvidenceRegistry()
registry.add_legal(EvidenceItem(
    "ley-1", EvidenceLayer.LEGAL, "Artículo 1", "https://f/1", "1" * 64))
registry.add_operational(EvidenceItem(
    "nota-1", EvidenceLayer.OPERATIONAL, "preferencia del abogado"))
grounded = registry.assess((Claim("c-1", "Artículo 1", ("ley-1",)),))
limited = registry.assess((Claim("c-1", "Artículo 1", ("ley-1", "nota-1")),))
abstain = registry.assess((Claim("c-2", "afirmación sin respaldo", ("nota-1",)),))
check("evidencia legal produce grounded", grounded.state is AnswerState.GROUNDED)
check("cita mezclada con memoria produce limited", limited.state is AnswerState.LIMITED)
check("memoria operativa sola produce abstain", abstain.state is AnswerState.ABSTAIN)

# LegalGraphRAG: recupera vecinos por relaciones, con hop y path visibles.
graph_service = mvp.MVPService.create(GraphFixtureProvider())
graph_search = graph_service.research(
    "tenant-a", "case-graph", "artículo 90", engine="graph")
check("graph retrieval conserva el motor", graph_search.engine == "graph")
check("graph retrieval expone contexto", "precedente-90" in graph_search.graph_context)
check("graph retrieval conserva citas válidas", len(graph_search.allowed_citations) >= 2)

# Mike: la propuesta se revisa como diff antes de reemplazar el borrador.
diff = draft_diff("línea uno\nlínea dos", "línea uno\nlínea corregida")
check("diff detecta cambios", diff["changed"] is True)
check("diff conserva hash antes/después", diff["before_sha256"] != diff["after_sha256"])
check("diff separa altas y bajas", diff["additions"] == 1 and diff["deletions"] == 1)

print(json.dumps({"checks": checks, "failures": failures}, ensure_ascii=False))
if failures:
    sys.exit(1)
