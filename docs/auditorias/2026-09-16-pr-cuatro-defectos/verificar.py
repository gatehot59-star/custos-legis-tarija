"""Arnes de verificacion del PR. Arranca el cluster aislado de brain-env, corre
las suites y guarda la salida cruda de cada una.

No es un instalador portable: usa el cluster que ya existe en el directorio de
la auditoria de integracion. Para repetir en otra maquina hay que preparar otro
cluster. Nunca contra produccion.

OJO CON UNA COSA: este arnes reaplica `infra/init.sql` en cada corrida, y ese
archivo trae `GRANT ... ON ALL TABLES`, asi que RESTAURA los privilegios amplios
de `custos_app`. La migracion `2026-09-16-cierra-el-borrado-de-un-bufete.sql` la
aplica `test_borrado_bufete.py`, que por eso puede medir el ANTES y el DESPUES
en la misma corrida. No es casualidad: es lo que hace que ese control positivo
siga siendo valido la segunda vez.

Uso:
    python verificar.py <ROOT>          # ROOT = dir con pgdata/ socket/ repo/
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                    else "/workspace/custos-integration-20260916-0314")
REPO = ROOT / "repo"
BACK = REPO / "backend"
PG = ROOT / "pgroot/usr/lib/postgresql/17/bin"
SOCK = ROOT / "socket"
DATA = ROOT / "pgdata"
ENV = dict(os.environ,
           LD_LIBRARY_PATH=str(ROOT / "pgroot/usr/lib/x86_64-linux-gnu"))
DSN_ADMIN = f"host={SOCK} dbname=postgres user=audit_admin"
DSN_APP = f"host={SOCK} dbname=postgres user=custos_app"
SUITES = ["test_api.py", "guard_esquema.py", "test_rls.py", "test_plazos.py",
          "test_anonimizador.py", "test_calendario.py",
          "test_regresiones_hitl.py", "test_borrado_bufete.py"]

out = {"arnes": "verificacion del PR de los cuatro defectos", "root": str(ROOT),
       "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "suites": []}
started = False
try:
    rc = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "-l",
                         str(ROOT / "postgres-verificar.log"), "-w", "start"],
                        env=ENV, capture_output=True, text=True, timeout=120)
    out["pg_start_rc"] = rc.returncode
    if rc.returncode:
        raise RuntimeError("pg start fallo: " + rc.stdout + rc.stderr)
    started = True
    import psycopg
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        out["postgres"] = c.execute("select version()").fetchone()[0]
        c.execute((REPO / "infra/init.sql").read_text(), prepare=False)
        out["app_role"] = c.execute(
            "select rolname, rolsuper, rolbypassrls from pg_roles"
            " where rolname='custos_app'").fetchone()
    ev = dict(ENV, DATABASE_URL=DSN_ADMIN, DATABASE_URL_APP=DSN_APP)
    for nombre in SUITES:
        destino = ROOT / ("verificar-" + nombre + ".log")
        with destino.open("w") as f:
            cp = subprocess.run([sys.executable, str(BACK / nombre)],
                                stdout=f, stderr=subprocess.STDOUT, env=ev,
                                cwd=str(BACK), timeout=300)
        texto = destino.read_text()
        out["suites"].append({"suite": nombre, "exit_code": cp.returncode,
                              "log": destino.name,
                              "tail": texto[-1800:]})
        print(f"{nombre:28s} exit={cp.returncode}")
finally:
    if started:
        s = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "-m", "fast",
                            "-w", "stop"], env=ENV, capture_output=True,
                           text=True)
        out["pg_stop_rc"] = s.returncode
        st = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "status"],
                            env=ENV, capture_output=True, text=True)
        out["pg_status_after_stop_rc"] = st.returncode
    out["git_diff_stat"] = subprocess.run(
        ["git", "diff", "--stat", "--", "backend", "infra"], cwd=str(REPO),
        capture_output=True, text=True).stdout.strip()
    out["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out["resumen"] = {
        "suites_verdes": sum(1 for s in out["suites"] if s["exit_code"] == 0),
        "suites_rojas": sum(1 for s in out["suites"] if s["exit_code"] != 0),
    }
    (ROOT / "verificar-resultados.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str))
    print(json.dumps(out["resumen"], indent=2))
