#!/usr/bin/env python3
"""Plazos procesales bolivianos en dias HABILES. Cero dependencias.

POR QUE ESTE ARCHIVO EXISTE Y VA PRIMERO:
El diseno original calculaba el vencimiento con `timedelta(days=plazo)` mientras
el prompt del agente decia "dias habiles". Fable lo cazo como D4 y tiene razon:
es el peor bug posible de este producto, porque el sistema le diria a un abogado
que tiene hasta el viernes cuando el plazo vence el miercoles, o al reves, y el
abogado le cree al sistema.

El error no es cosmetico: un plazo de 3 dias habiles que arranca un jueves vence
el martes siguiente (5 dias corridos). `timedelta(days=3)` daria el domingo, que
ni es habil ni existe como fecha de presentacion.

QUE ES NO MEDIDO ACA, y va declarado arriba porque importa:
  1. LA TABLA DE PLAZOS. Los articulos del CPC (Ley 439) que el diseno cita
     NINGUN ABOGADO BOLIVIANO LOS CONFIRMO. Estan como HIPOTESIS y el codigo
     lo dice en cada entrada. Si esta tabla esta mal, el producto miente.
  2. Los feriados departamentales de Tarija distintos de los nacionales.
  3. Si el computo arranca el mismo dia de la notificacion o el siguiente
     (dies a quo). Aca se asume el SIGUIENTE, que es lo habitual, y se declara.
"""
from __future__ import annotations

import datetime as _dt
from typing import Iterable

# ---------------------------------------------------------------------------
# FERIADOS NACIONALES DE BOLIVIA
# Fijos: (mes, dia). Los moviles (Carnaval, Viernes Santo, Corpus Christi)
# dependen de Pascua y se calculan con Butcher/Meeus, no se hardcodean por anio.
# ---------------------------------------------------------------------------
FERIADOS_FIJOS: tuple[tuple[int, int, str], ...] = (
    (1, 1, "Anio Nuevo"),
    (1, 22, "Estado Plurinacional"),
    (5, 1, "Dia del Trabajo"),
    (6, 21, "Anio Nuevo Aymara"),
    (8, 6, "Independencia"),
    (11, 2, "Todos los Santos"),
    (12, 25, "Navidad"),
)

# Feriado DEPARTAMENTAL de Tarija: 15 de abril (Batalla de La Tablada).
# Va aparte porque un juzgado de Tarija no trabaja y uno de La Paz si.
FERIADOS_TARIJA: tuple[tuple[int, int, str], ...] = ((4, 15, "La Tablada (Tarija)"),)


def pascua(anio: int) -> _dt.date:
    """Domingo de Pascua por el algoritmo de Meeus/Jones/Butcher (gregoriano)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return _dt.date(anio, mes, dia + 1)


def feriados(anio: int, *, tarija: bool = True) -> dict[_dt.date, str]:
    """Todos los feriados no laborables de un anio, con su nombre."""
    out: dict[_dt.date, str] = {}
    for mes, dia, nombre in FERIADOS_FIJOS:
        out[_dt.date(anio, mes, dia)] = nombre
    if tarija:
        for mes, dia, nombre in FERIADOS_TARIJA:
            out[_dt.date(anio, mes, dia)] = nombre
    p = pascua(anio)
    # Moviles anclados a Pascua
    out[p - _dt.timedelta(days=48)] = "Carnaval (lunes)"
    out[p - _dt.timedelta(days=47)] = "Carnaval (martes)"
    out[p - _dt.timedelta(days=2)] = "Viernes Santo"
    out[p + _dt.timedelta(days=60)] = "Corpus Christi"
    return out


def es_habil(fecha: _dt.date, *, tarija: bool = True,
             extra: Iterable[_dt.date] = ()) -> bool:
    """Habil = no sabado, no domingo, no feriado. `extra` para cierres del juzgado."""
    if fecha.weekday() >= 5:            # 5=sab, 6=dom
        return False
    if fecha in feriados(fecha.year, tarija=tarija):
        return False
    return fecha not in set(extra)


def vencimiento(notificacion: _dt.date, dias_habiles: int, *,
                tarija: bool = True,
                extra: Iterable[_dt.date] = ()) -> _dt.date:
    """Fecha de vencimiento contando SOLO dias habiles.

    Supuesto DECLARADO (dies a quo): el computo arranca el dia habil SIGUIENTE
    a la notificacion, no el mismo dia. Es lo habitual, y si un abogado dice que
    en Tarija se cuenta distinto, se cambia aca y los tests lo detectan.

    dias_habiles == 0 -> mero tramite, no hay plazo: devuelve la notificacion.
    """
    if dias_habiles <= 0:
        return notificacion
    extra = set(extra)
    cursor = notificacion
    contados = 0
    # Tope de seguridad: 400 iteraciones cubre cualquier plazo real y evita
    # un bucle infinito si alguien pasa un set de feriados absurdo.
    for _ in range(400):
        cursor += _dt.timedelta(days=1)
        if es_habil(cursor, tarija=tarija, extra=extra):
            contados += 1
            if contados == dias_habiles:
                return cursor
    raise RuntimeError(
        "no se alcanzo el plazo en 400 dias: revisar el set de feriados")


def habiles_restantes(desde: _dt.date, hasta: _dt.date, *,
                      tarija: bool = True) -> int:
    """Dias habiles que quedan. Negativo si el plazo ya vencio."""
    if hasta < desde:
        return -habiles_restantes(hasta, desde, tarija=tarija)
    n = 0
    cursor = desde
    while cursor < hasta:
        cursor += _dt.timedelta(days=1)
        if es_habil(cursor, tarija=tarija):
            n += 1
    return n


# ---------------------------------------------------------------------------
# TABLA DE PLAZOS - **HIPOTESIS NO CONFIRMADA POR NINGUN ABOGADO**
#
# Cada entrada lleva `confirmado: False`. El sistema NO debe presentar un plazo
# como cierto mientras eso sea False: tiene que decir "plazo estimado, sin
# confirmar". Es la diferencia entre una herramienta y una trampa.
# ---------------------------------------------------------------------------
PLAZOS: dict[str, dict] = {
    "auto_interlocutorio": {
        "dias": 3, "fundamento": "Art. 252 CPC (Ley 439)", "confirmado": False},
    "auto_definitivo": {
        "dias": 10, "fundamento": "Art. 261 CPC (Ley 439)", "confirmado": False},
    "sentencia_apelacion": {
        "dias": 10, "fundamento": "apelacion de sentencia", "confirmado": False},
    "casacion": {
        "dias": 10, "fundamento": "recurso de casacion", "confirmado": False},
    "traslado_demanda": {
        "dias": 30, "fundamento": "Art. 365 CPC (Ley 439)", "confirmado": False},
    "contestacion_excepcion": {
        "dias": 5, "fundamento": "contestacion de excepcion", "confirmado": False},
    "decreto_mero_tramite": {
        "dias": 0, "fundamento": "sin plazo: mero tramite", "confirmado": False},
}


def plazo_de(tipo: str) -> dict:
    """Devuelve el plazo con su etiqueta de confirmacion. Nunca inventa."""
    if tipo not in PLAZOS:
        return {"dias": None, "fundamento": "tipo no reconocido",
                "confirmado": False, "estado": "NO_MEDIDO"}
    d = dict(PLAZOS[tipo])
    d["estado"] = "CONFIRMADO" if d["confirmado"] else "HIPOTESIS"
    return d


def urgencia(dias_restantes: int) -> str:
    if dias_restantes < 0:
        return "vencido"
    if dias_restantes <= 2:
        return "critico"
    if dias_restantes <= 5:
        return "alto"
    return "normal"
