#!/usr/bin/env python3
"""GUARD: toda tabla que la API escribe tiene que existir en el esquema.

POR QUE EXISTE, y es un defecto real de hoy:
`PostgresAlmacen.registrar_aprobacion()` escribia en `public.aprobaciones` y esa
tabla NO estaba en `infra/init.sql`. El gate de acciones externas habria
explotado en el primer INSERT contra Postgres, y en SQLite andaba perfecto
porque el almacen de prueba crea su propio DDL.

Este guard compara las dos cosas: las tablas que el codigo NOMBRA contra las
tablas que el esquema CREA. Cuenta estructura (nombres de tabla en sentencias
SQL), no palabras sueltas en un archivo.

Y revisa una segunda cosa que ya me morlio antes: **toda tabla con `tenant_id`
tiene que tener `FORCE ROW LEVEL SECURITY`.** `ENABLE` no alcanza: sin `FORCE`,
el DUENO de la tabla ignora las politicas, y el aislamiento se ve configurado y
no lo esta.

LIMITE DECLARADO: los nombres de tabla se leen con regex sobre `public.<algo>`.
Si manana alguien arma el nombre de tabla por concatenacion de strings, este
guard no lo ve. Cuenta lo que puede contar y no pretende mas.

Correr: python3 guard_esquema.py   (exit 0 verde, exit 1 rojo)
"""
from __future__ import annotations

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
INIT = RAIZ.parent / "infra" / "init.sql"

# Las tablas se leen del FUENTE, no de una lista escrita a mano: una lista a mano
# se desactualiza y el guard queda decorativo.
RE_TABLA_CODIGO = re.compile(r"\bpublic\.([a-z_][a-z0-9_]*)")
RE_TABLA_SQL = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.([a-z_][a-z0-9_]*)",
    re.I)
RE_RLS_FORZADO = re.compile(
    r"ALTER\s+TABLE\s+public\.([a-z_][a-z0-9_]*)\s+FORCE\s+ROW\s+LEVEL", re.I)

# Tablas sin RLS a proposito: `tenants` la administra el servicio y no tiene
# tenant_id propio, y `uso_consultas` acepta tenant NULL para el sensor.
SIN_RLS_A_PROPOSITO = frozenset({"tenants", "uso_consultas"})


def main() -> int:
    if not INIT.exists():
        print(f"ROJO: no encuentro {INIT}")
        return 1
    sql = INIT.read_text()
    creadas = set(RE_TABLA_SQL.findall(sql))
    forzadas = {m.lower() for m in RE_RLS_FORZADO.findall(sql)}

    nombradas: dict[str, set[str]] = {}
    for py in sorted(RAIZ.glob("*.py")):
        if py.name.startswith("test_") or py.name == "guard_esquema.py":
            continue
        for t in RE_TABLA_CODIGO.findall(py.read_text()):
            nombradas.setdefault(t, set()).add(py.name)

    print(f"tablas creadas en el esquema: {len(creadas)} -> {sorted(creadas)}")
    print(f"tablas nombradas en el codigo: {len(nombradas)} -> "
          f"{sorted(nombradas)}")
    print(f"tablas con RLS FORZADO: {len(forzadas)} -> {sorted(forzadas)}")

    rojos = []
    for t, archivos in sorted(nombradas.items()):
        if t not in creadas:
            rojos.append(f"public.{t} se usa en {sorted(archivos)} y NO existe "
                         "en infra/init.sql")

    for t in sorted(creadas):
        if t in SIN_RLS_A_PROPOSITO:
            continue
        marca = f"public.{t} ("
        bloque = sql[sql.index(marca):] if marca in sql else ""
        tiene_tenant = "tenant_id" in bloque[:2000]
        if tiene_tenant and t not in forzadas:
            rojos.append(f"public.{t} tiene tenant_id y NO tiene FORCE ROW LEVEL "
                         "SECURITY: sin FORCE el dueno ignora la politica")

    print()
    if rojos:
        print(f"ROJO: {len(rojos)} problema(s) de esquema")
        for r in rojos:
            print("  " + r)
        print("ETIQUETAS_ROJAS: ESQUEMA-INCOMPLETO")
        return 1
    print("VERDE: toda tabla que el codigo escribe existe en el esquema, y toda "
          "tabla con tenant_id tiene RLS forzado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
