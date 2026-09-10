#!/usr/bin/env python3
"""Capa de datos de Custos Legis. Dos motores, y NO son equivalentes.

--------------------------------------------------------------------------------
POR QUE HAY DOS, Y POR QUE ESO ES PELIGROSO SI NO SE DECLARA
--------------------------------------------------------------------------------
  PostgresAlmacen  produccion. El aislamiento entre bufetes lo hace el
                   PLANIFICADOR de PostgreSQL via RLS (`infra/init.sql`).
  SqliteAlmacen    SOLO para probar el CABLEADO de la API de punta a punta.
                   **SQLite NO TIENE RLS.** El filtro por tenant lo hace Python.

**Un test de aislamiento contra SQLite daria VERDE y no probaria nada**, porque
estaria probando mi propio `WHERE tenant_id = ?` en vez de la politica del motor.
Ese es exactamente el defecto que este proyecto persigue: un guard que mira el
sujeto equivocado.

Asi que:
  - el aislamiento REAL se prueba en `test_rls.py` contra **PostgreSQL 16 real**
    en CI, con su falsador `FUGA-CKPT`;
  - `SqliteAlmacen` prueba que la API cablea bien (auth, rutas, compuerta, HITL);
  - y `SqliteAlmacen` **se niega a arrancar** sin `permitir_sin_rls=True`, y se
    niega IGUAL si `CUSTOS_ENTORNO=produccion` aunque le pasen el flag. Los dos
    caminos tienen su falsador.

NO MEDIDO: `PostgresAlmacen` no se ejecuto en este taller, porque `psycopg` no
esta instalado y no hay red para instalarlo. Su SQL es el mismo que ya corre
verde en `test_rls.py`, pero **esta clase en particular no fue ejecutada**. Va
declarado y no disimulado.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import uuid
from dataclasses import dataclass, field
from typing import Protocol


class SinTenant(RuntimeError):
    """Se intento tocar datos sin declarar el bufete. Nunca se degrada a 'todos'."""


class NoAutorizado(RuntimeError):
    pass


def hash_password(pw: str, sal: bytes | None = None) -> str:
    """PBKDF2-SHA256. Sin dependencias: `hashlib` alcanza y se puede auditar."""
    sal = sal or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), sal, 200_000)
    return f"pbkdf2_sha256$200000${sal.hex()}${dk.hex()}"


def verificar_password(pw: str, guardado: str) -> bool:
    try:
        algo, iters, sal_hex, dk_hex = guardado.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(sal_hex),
                                 int(iters))
        # compare_digest y no ==: el == corta en el primer byte distinto y filtra
        # informacion por tiempo.
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


@dataclass
class Usuario:
    id: str
    tenant_id: str
    email: str
    nombre: str
    rol: str
    matricula: str | None


class Almacen(Protocol):
    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None: ...
    def casos(self, tenant_id: str) -> list[dict]: ...
    def caso(self, tenant_id: str, case_id: str) -> dict | None: ...
    def crear_caso(self, tenant_id: str, datos: dict) -> dict: ...
    def registrar_aprobacion(self, tenant_id: str, ev: dict) -> dict: ...
    def aprobaciones(self, tenant_id: str, case_id: str | None = None) -> list[dict]: ...
    def registrar_uso(self, tenant_id: str | None, q_hash: str, n: int,
                      ms: int) -> None: ...
    def uso_total(self) -> int: ...


# ---------------------------------------------------------------------------
# SQLITE: solo para probar el cableado
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY, slug TEXT UNIQUE, nombre_bufete TEXT, ciudad TEXT);
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY, tenant_id TEXT, email TEXT, password_hash TEXT,
  nombre_completo TEXT, rol TEXT, matricula TEXT,
  UNIQUE(tenant_id, email));
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY, tenant_id TEXT, nro_expediente TEXT, juzgado TEXT,
  materia TEXT, sistema_origen TEXT, estado_procesal TEXT,
  fecha_ultimo_actuado TEXT, plazo_dias INTEGER, plazo_confirmado INTEGER);
CREATE TABLE IF NOT EXISTS aprobaciones (
  id TEXT PRIMARY KEY, tenant_id TEXT, case_id TEXT, matricula TEXT,
  usuario_id TEXT, tipo TEXT, sha256_entrada TEXT, decision TEXT,
  fundamento TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS uso_consultas (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, q_hash TEXT,
  n_resultados INTEGER, ms INTEGER, ts TEXT);
"""


@dataclass
class SqliteAlmacen:
    """Almacen de PRUEBA. Sin RLS. Se niega a arrancar sin decirlo."""

    ruta: str = ":memory:"
    permitir_sin_rls: bool = False
    con: sqlite3.Connection = field(init=False)

    def __post_init__(self) -> None:
        if not self.permitir_sin_rls:
            raise RuntimeError(
                "SqliteAlmacen NO tiene RLS: el aislamiento entre bufetes seria "
                "un WHERE de Python, no una politica del motor. Si es una "
                "prueba, pasar permitir_sin_rls=True y decirlo por escrito.")
        if os.environ.get("CUSTOS_ENTORNO") == "produccion":
            raise RuntimeError(
                "SqliteAlmacen en CUSTOS_ENTORNO=produccion: rechazado. "
                "El aislamiento de un bufete no puede depender de un WHERE mio.")
        self.con = sqlite3.connect(self.ruta, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(_DDL)
        self.con.commit()

    # -- lectura -----------------------------------------------------------
    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None:
        r = self.con.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if not r:
            return None
        return (Usuario(id=r["id"], tenant_id=r["tenant_id"], email=r["email"],
                        nombre=r["nombre_completo"], rol=r["rol"],
                        matricula=r["matricula"]),
                r["password_hash"])

    def _guard(self, tenant_id: str | None) -> str:
        if not tenant_id:
            raise SinTenant("consulta sin tenant_id: se rechaza, no se amplia")
        return tenant_id

    def casos(self, tenant_id: str) -> list[dict]:
        t = self._guard(tenant_id)
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM cases WHERE tenant_id = ? ORDER BY nro_expediente",
            (t,))]

    def caso(self, tenant_id: str, case_id: str) -> dict | None:
        t = self._guard(tenant_id)
        r = self.con.execute(
            "SELECT * FROM cases WHERE tenant_id = ? AND id = ?",
            (t, case_id)).fetchone()
        return dict(r) if r else None

    def crear_caso(self, tenant_id: str, datos: dict) -> dict:
        t = self._guard(tenant_id)
        cid = str(uuid.uuid4())
        self.con.execute(
            "INSERT INTO cases (id, tenant_id, nro_expediente, juzgado, materia,"
            " sistema_origen, estado_procesal, fecha_ultimo_actuado, plazo_dias,"
            " plazo_confirmado) VALUES (?,?,?,?,?,?,?,?,?,0)",
            (cid, t, datos.get("nro_expediente"), datos.get("juzgado"),
             datos.get("materia"), datos.get("sistema_origen", "manual"),
             datos.get("estado_procesal", "activo"),
             datos.get("fecha_ultimo_actuado"), datos.get("plazo_dias")))
        self.con.commit()
        return self.caso(t, cid) or {}

    def registrar_aprobacion(self, tenant_id: str, ev: dict) -> dict:
        t = self._guard(tenant_id)
        aid = str(uuid.uuid4())
        self.con.execute(
            "INSERT INTO aprobaciones (id, tenant_id, case_id, matricula,"
            " usuario_id, tipo, sha256_entrada, decision, fundamento, ts)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (aid, t, ev.get("case_id"), ev["matricula"], ev["usuario_id"],
             ev["tipo"], ev["sha256_entrada"], ev["decision"],
             ev.get("fundamento"), ev["ts"]))
        self.con.commit()
        r = self.con.execute("SELECT * FROM aprobaciones WHERE id = ?",
                             (aid,)).fetchone()
        return dict(r)

    def aprobaciones(self, tenant_id: str, case_id: str | None = None
                     ) -> list[dict]:
        t = self._guard(tenant_id)
        if case_id:
            cur = self.con.execute(
                "SELECT * FROM aprobaciones WHERE tenant_id = ? AND case_id = ?"
                " ORDER BY ts DESC", (t, case_id))
        else:
            cur = self.con.execute(
                "SELECT * FROM aprobaciones WHERE tenant_id = ? ORDER BY ts DESC",
                (t,))
        return [dict(r) for r in cur]

    def registrar_uso(self, tenant_id: str | None, q_hash: str, n: int,
                      ms: int) -> None:
        # El T1 de Fable: "0 abogados" es un numero SIN SENSOR. Aca esta el
        # sensor. Se guarda q_hash, NO el texto: una busqueda juridica revela la
        # estrategia de un caso.
        import datetime as dt
        self.con.execute(
            "INSERT INTO uso_consultas (tenant_id, q_hash, n_resultados, ms, ts)"
            " VALUES (?,?,?,?,?)",
            (tenant_id, q_hash, n, ms,
             dt.datetime.now(dt.timezone.utc).isoformat()))
        self.con.commit()

    def uso_total(self) -> int:
        return self.con.execute("SELECT count(*) FROM uso_consultas").fetchone()[0]

    # -- siembra para pruebas ---------------------------------------------
    def sembrar_bufete(self, slug: str, nombre: str, email: str, pw: str,
                       rol: str = "socio", matricula: str | None = None) -> dict:
        tid, uid = str(uuid.uuid4()), str(uuid.uuid4())
        self.con.execute("INSERT INTO tenants VALUES (?,?,?,?)",
                         (tid, slug, nombre, "Tarija"))
        self.con.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
            (uid, tid, email.lower(), hash_password(pw), nombre + " (titular)",
             rol, matricula))
        self.con.commit()
        return {"tenant_id": tid, "user_id": uid}


# ---------------------------------------------------------------------------
# POSTGRES: produccion. NO EJECUTADO en este taller (ver docstring del modulo).
# ---------------------------------------------------------------------------


@dataclass
class PostgresAlmacen:
    """Produccion. El aislamiento lo da RLS, no este codigo.

    CADA metodo abre transaccion y llama `app.set_tenant(%s)` ANTES de tocar
    datos. El `set_config(..., TRUE)` es local a la transaccion: sin eso el
    tenant se filtra al siguiente request que reuse la conexion del pool. Eso
    esta en `infra/init.sql` y probado en `test_rls.py`.
    """

    dsn: str

    def _con(self):
        import psycopg  # import local: el modulo se puede importar sin psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _en_tenant(self, tenant_id: str, sql: str, args: tuple = ()) -> list[dict]:
        if not tenant_id:
            raise SinTenant("consulta sin tenant_id: se rechaza, no se amplia")
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute("SELECT app.set_tenant(%s)", (tenant_id,))
                cur.execute(sql, args)
                if cur.description is None:
                    return []
                return list(cur.fetchall())

    def usuario_por_email(self, email: str) -> tuple[Usuario, str] | None:
        # Login: es la UNICA consulta sin tenant, porque el tenant se descubre
        # aca. Lee solo estas columnas y solo de usuarios activos.
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT id, tenant_id, email, password_hash, nombre_completo,"
                    " rol, matricula_cab FROM public.users"
                    " WHERE lower(email) = lower(%s) AND activo = TRUE", (email,))
                r = cur.fetchone()
        if not r:
            return None
        return (Usuario(id=str(r["id"]), tenant_id=str(r["tenant_id"]),
                        email=r["email"], nombre=r["nombre_completo"],
                        rol=r["rol"], matricula=r["matricula_cab"]),
                r["password_hash"])

    def casos(self, tenant_id: str) -> list[dict]:
        return self._en_tenant(tenant_id,
                               "SELECT * FROM public.cases ORDER BY nro_expediente")

    def caso(self, tenant_id: str, case_id: str) -> dict | None:
        r = self._en_tenant(tenant_id, "SELECT * FROM public.cases WHERE id = %s",
                            (case_id,))
        return r[0] if r else None

    def crear_caso(self, tenant_id: str, datos: dict) -> dict:
        r = self._en_tenant(
            tenant_id,
            "INSERT INTO public.cases (tenant_id, nro_expediente, juzgado,"
            " materia, sistema_origen, estado_procesal) VALUES"
            " (%s,%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, datos.get("nro_expediente"), datos.get("juzgado"),
             datos.get("materia"), datos.get("sistema_origen", "manual"),
             datos.get("estado_procesal", "activo")))
        return r[0] if r else {}

    def registrar_aprobacion(self, tenant_id: str, ev: dict) -> dict:
        r = self._en_tenant(
            tenant_id,
            "INSERT INTO public.aprobaciones (tenant_id, case_id, matricula,"
            " usuario_id, tipo, sha256_entrada, decision, fundamento)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, ev.get("case_id"), ev["matricula"], ev["usuario_id"],
             ev["tipo"], ev["sha256_entrada"], ev["decision"],
             ev.get("fundamento")))
        return r[0] if r else {}

    def aprobaciones(self, tenant_id: str, case_id: str | None = None
                     ) -> list[dict]:
        if case_id:
            return self._en_tenant(
                tenant_id, "SELECT * FROM public.aprobaciones WHERE case_id = %s"
                " ORDER BY creado_en DESC", (case_id,))
        return self._en_tenant(
            tenant_id, "SELECT * FROM public.aprobaciones ORDER BY creado_en DESC")

    def registrar_uso(self, tenant_id: str | None, q_hash: str, n: int,
                      ms: int) -> None:
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.uso_consultas (tenant_id, q_hash,"
                    " q_largo, n_resultados, ms) VALUES (%s,%s,%s,%s,%s)",
                    (tenant_id, q_hash, len(q_hash), n, ms))

    def uso_total(self) -> int:
        with self._con() as con:
            with con.cursor() as cur:
                cur.execute("SELECT count(*) AS n FROM public.uso_consultas")
                return cur.fetchone()["n"]
