#!/usr/bin/env python3
"""GUARD: toda tabla que la API escribe tiene que existir en el esquema.

Compara las tablas nombradas por el código contra `infra/*.sql`, incluyendo
migraciones versionadas, y exige FORCE ROW LEVEL SECURITY donde corresponde.
"""
from __future__ import annotations

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
INFRA = RAIZ.parent / "infra"
RE_TABLA_CODIGO = re.compile(r"\bpublic\.([a-z_][a-z0-9_]*)")
RE_TABLA_SQL = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.([a-z_][a-z0-9_]*)",
    re.I)
RE_RLS_FORZADO = re.compile(
    r"ALTER\s+TABLE\s+public\.([a-z_][a-z0-9_]*)\s+FORCE\s+ROW\s+LEVEL",
    re.I)

# Tablas sin RLS a propósito: `tenants` la administra el servicio y no tiene
# tenant_id propio, y `uso_consultas` acepta tenant NULL para el sensor.
SIN_RLS_A_PROPOSITO = frozenset({"tenants", "uso_consultas"})


def main() -> int:
    """Verifica código y todas las fuentes SQL versionadas del esquema."""
    fuentes = sorted(INFRA.glob("*.sql"))
    if not fuentes:
        print(f"ROJO: no encuentro fuentes SQL en {INFRA}")
        return 1
    sql = "\n".join(path.read_text() for path in fuentes)
    creadas = set(RE_TABLA_SQL.findall(sql))
    forzadas = {m.lower() for m in RE_RLS_FORZADO.findall(sql)}

    nombradas: dict[str, set[str]] = {}
    for py in sorted(RAIZ.glob("*.py")):
        if py.name.startswith("test_") or py.name == "guard_esquema.py":
            continue
        for t in RE_TABLA_CODIGO.findall(py.read_text()):
            nombradas.setdefault(t, set()).add(py.name)

    print(f"fuentes SQL inspeccionadas: {[p.name for p in fuentes]}")
    print(f"tablas creadas en el esquema: {len(creadas)} -> {sorted(creadas)}")
    print(f"tablas nombradas en el código: {len(nombradas)} -> "
          f"{sorted(nombradas)}")
    print(f"tablas con RLS FORZADO: {len(forzadas)} -> {sorted(forzadas)}")

    rojos = []
    for t, archivos in sorted(nombradas.items()):
        if t not in creadas:
            rojos.append(f"public.{t} se usa en {sorted(archivos)} y NO existe "
                         "en las fuentes SQL")

    for t in sorted(creadas):
        if t in SIN_RLS_A_PROPOSITO:
            continue
        marca = f"public.{t} ("
        bloque = sql[sql.index(marca):] if marca in sql else ""
        tiene_tenant = "tenant_id" in bloque[:2000]
        if tiene_tenant and t not in forzadas:
            rojos.append(f"public.{t} tiene tenant_id y NO tiene FORCE ROW LEVEL "
                         "SECURITY: sin FORCE el dueño ignora la política")

    print()
    if rojos:
        print(f"ROJO: {len(rojos)} problema(s) de esquema")
        for r in rojos:
            print("  " + r)
        print("ETIQUETAS_ROJAS: ESQUEMA-INCOMPLETO")
        return 1
    print("VERDE: toda tabla que el código escribe existe en las fuentes SQL, y "
          "toda tabla con tenant_id tiene RLS forzado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
