#!/usr/bin/env python3
"""Calendario judicial de Bolivia, POR DEPARTAMENTO y CON FUENTE. Solo stdlib.

POR QUE ESTE ARCHIVO EXISTE SEPARADO DE plazos.py:
`plazos.py` sabe COMO se suspende un plazo (art. 126.IV LOJ). Este archivo sabe
CUANDO, y ese "cuando" es un dato con fecha de caducidad que se re-mide, no una
constante que se recuerda. Mezclarlos invita a hardcodear diciembre.

--------------------------------------------------------------------------------
TRES COSAS MEDIDAS QUE OBLIGAN A ESTE DISENO
--------------------------------------------------------------------------------

1. LOS DEPARTAMENTOS NO COINCIDEN. En la misma gestion 2025:
     - Potosi ....... 8-dic-2025 a 1-ene-2026 (Acuerdo de Sala Plena 552/2025)
     - Santa Cruz ... 9-dic-2025 a 2-ene-2026 (TDJ Santa Cruz)
     - TSJ nacional . 9-dic-2025 a 5-ene-2026 (segun prensa citando al TSJ)
   Tres rangos distintos para el mismo anio. Un calendario nacional unico habria
   dado la fecha equivocada en dos de los tres casos.

2. LAS FECHAS CAMBIAN CADA ANIO Y NO SIGUEN PATRON. Tarija, medido:
     2018 ... 7-dic  a 31-dic
     2019 ... 3-dic  a 27-dic
     2023 ... 5-dic  a 29-dic
     2025 ... desde el 9-dic (fin no preciso en la fuente)
   Los 25 dias del art. 126 LOJ son fijos; el tramo NO.

3. HAY VACACIONES EXTRAORDINARIAS. En mayo de 2026 el TDJ de La Paz declaro una
   semana de vacacion judicial por conflictos y bloqueos, descontada de la
   programada. O sea: el calendario puede cambiar A MITAD DE ANIO y hacia atras.

--------------------------------------------------------------------------------
LA CIRCULAR DE TARIJA 2026 NO ES "NO MEDIDA": TODAVIA NO EXISTE
--------------------------------------------------------------------------------
Esto lo tenia mal planteado. Buscar la circular de la vacacion 2026 y no
encontrarla no es una falla de la busqueda: la vacacion se fija en Sala Plena
entre octubre y noviembre. La propia decana del TSJ lo dijo en julio de 2026:
la eleccion de autoridades seria "entre fines de octubre y los primeros dias de
noviembre, cuando se trate el tema de la vacacion judicial".

Hoy es septiembre de 2026. El dato NO PUEDE existir todavia.

Consecuencia de producto, y no es menor: **el Vigilante va a devolver NO_MEDIDO
para todo plazo que cruce diciembre de 2026, y eso es correcto, no un bug.** Y
cargar el calendario es una TAREA RECURRENTE con fecha conocida (octubre-noviembre
de cada anio), no un pendiente que se cierra una vez.

--------------------------------------------------------------------------------
NO MEDIDO, declarado
--------------------------------------------------------------------------------
  1. Gestiones 2020, 2021, 2022 y 2024 de Tarija: no las busque.
  2. El FIN exacto de la vacacion 2025 de Tarija. La fuente (presidente del TDJ,
     Esteban Ortiz, nov-2025) dice "desde el 9 de diciembre" y "retorno pleno en
     enero de 2026", sin fecha. Se registra el periodo para poder AVISAR, pero
     NO declara el anio cubierto: cualquier computo que lo toque sale NO_MEDIDO.
  3. Los numeros de Resolucion de Sala Plena de 2018 y 2019 de Tarija.
  4. Vacaciones extraordinarias de Tarija: ninguna medida. La de mayo-2026 es de
     La Paz y esta cargada como tal, no como si fuera nacional.
  5. Feriados departamentales de Tarija mas alla del 15 de abril (La Tablada).
"""
from __future__ import annotations

import datetime as _dt

from plazos import CalendarioJudicial, PeriodoSuspension

# ---------------------------------------------------------------------------
# PERIODOS MEDIDOS. Cada uno con su fuente citable.
# `cubre=False` = el dato esta INCOMPLETO y no autoriza a declarar el anio.
# ---------------------------------------------------------------------------

_D = _dt.date

TARIJA_COMPLETOS: tuple[tuple[PeriodoSuspension, int], ...] = (
    (PeriodoSuspension(
        desde=_D(2018, 12, 7), hasta=_D(2018, 12, 31), departamento="Tarija",
        circular="Resolucion de Sala Plena TDJ Tarija (numero NO MEDIDO) - "
                 "tarija-tdj.organojudicial.gob.bo/Paper/Detail/4360"), 2018),
    (PeriodoSuspension(
        desde=_D(2019, 12, 3), hasta=_D(2019, 12, 27), departamento="Tarija",
        circular="Sala Plena TDJ Tarija (numero NO MEDIDO) - "
                 "tarija-tdj.organojudicial.gob.bo/Paper/Detail/6061"), 2019),
    (PeriodoSuspension(
        desde=_D(2023, 12, 5), hasta=_D(2023, 12, 29), departamento="Tarija",
        circular="Resoluciones de Sala Plena TDJ Tarija 671/2023, 771/2023 y "
                 "804/2023 - tarija-tdj.organojudicial.gob.bo/Paper/Detail/10326"),
     2023),
)

# Dato INCOMPLETO: el inicio esta en fuente, el fin no.
TARIJA_INCOMPLETOS: tuple[PeriodoSuspension, ...] = (
    PeriodoSuspension(
        desde=_D(2025, 12, 9), hasta=_D(2026, 1, 2), departamento="Tarija",
        circular="FIN NO MEDIDO. Inicio anunciado por el presidente del TDJ "
                 "Tarija (Esteban Ortiz, nov-2025); el fin '2026-01-02' es un "
                 "SUPUESTO tomado de otro departamento, NO de la circular de "
                 "Tarija - lavozdetarija.com/2025/11/21/",
        motivo="vacacion judicial (fin no confirmado)"),
)

# Otros departamentos, medidos. Estan aca porque son la PRUEBA de que el
# calendario tiene que ser por departamento: mismo anio, tres rangos.
OTROS_DEPARTAMENTOS: tuple[tuple[PeriodoSuspension, int], ...] = (
    (PeriodoSuspension(
        desde=_D(2025, 12, 8), hasta=_D(2026, 1, 1), departamento="Potosi",
        circular="Acuerdo de Sala Plena TDJ Potosi 552/2025 - "
                 "radiokollasuyo.bo/2025/10/29/"), 2025),
    (PeriodoSuspension(
        desde=_D(2025, 12, 9), hasta=_D(2026, 1, 2), departamento="Santa Cruz",
        circular="TDJ Santa Cruz, presidente Aldo Quezada (dic-2025) - "
                 "notibol.com/noticia/bo/6938c1e95267f"), 2025),
    (PeriodoSuspension(
        desde=_D(2026, 5, 25), hasta=_D(2026, 5, 31), departamento="La Paz",
        circular="Sala Plena extraordinaria TDJ La Paz, 24-may-2026 - "
                 "fmlapaz.bo/tribunal-de-la-paz-adelanta-vacacion-judicial/",
        motivo="vacacion judicial EXTRAORDINARIA (conflictos y bloqueos), "
               "descontada de la programada"),
     2026),
)

# El anio en que la vacacion de cada gestion se fija en Sala Plena. Antes de
# esto, el dato no existe y no hay busqueda que lo encuentre.
MES_EN_QUE_SE_FIJA = (10, 11)  # octubre-noviembre


def calendario(departamento: str = "Tarija") -> CalendarioJudicial:
    """Calendario con lo MEDIDO para ese departamento. Nada inventado."""
    cal = CalendarioJudicial(departamento=departamento)
    if departamento == "Tarija":
        for p, anio in TARIJA_COMPLETOS:
            cal.registrar(p)
            cal.declarar_cubierto(anio)
        for p in TARIJA_INCOMPLETOS:
            cal.registrar(p, cubre=False)
    for p, anio in OTROS_DEPARTAMENTOS:
        if p.departamento == departamento:
            cal.registrar(p)
            cal.declarar_cubierto(anio)
    return cal


def por_que_falta(anio: int, *, hoy: _dt.date | None = None) -> str:
    """Explica POR QUE no hay dato, que no es lo mismo que no haberlo buscado."""
    hoy = hoy or _dt.date.today()
    if anio > hoy.year:
        return (f"la vacacion de {anio} todavia no se fija: se decide en Sala "
                f"Plena en octubre-noviembre de {anio}")
    if anio == hoy.year and hoy.month < MES_EN_QUE_SE_FIJA[0]:
        return (f"la vacacion de {anio} TODAVIA NO EXISTE: se fija en Sala Plena "
                f"en octubre-noviembre, y hoy es {hoy:%Y-%m-%d}. No es un dato "
                f"que falte buscar, es un dato que no fue emitido")
    return (f"la circular de {anio} deberia existir y NO fue medida: "
            f"buscarla en el portal del TDJ")


def cobertura(departamento: str = "Tarija") -> dict:
    """Que anios se pueden calcular y que anios no, con el motivo."""
    cal = calendario(departamento)
    return {
        "departamento": departamento,
        "anios_cubiertos": sorted(cal.cobertura),
        "periodos_cargados": len(cal.periodos),
        "periodos_incompletos": [p.circular.split(".")[0]
                                 for p in cal.periodos
                                 if "NO MEDIDO" in p.circular],
    }


if __name__ == "__main__":
    import json
    import plazos as P

    hoy = _dt.date.today()
    for dep in ("Tarija", "Potosi", "Santa Cruz", "La Paz"):
        print(f"{dep:12s} {json.dumps(cobertura(dep), ensure_ascii=False)}")

    print(f"\nhoy: {hoy:%Y-%m-%d}")
    for anio in (2024, hoy.year, hoy.year + 1):
        print(f"  {anio}: {por_que_falta(anio, hoy=hoy)}")

    cal = calendario("Tarija")
    print("\n--- plazo de 10 dias notificado el 1-dic-2023 (anio CUBIERTO) ---")
    print(P.computo_detallado(_D(2023, 12, 1), 10, P.Materia.CIVIL,
                              calendario=cal).como_texto())
    print("\n--- el mismo plazo en dic-2026 (anio SIN circular emitida) ---")
    c = P.computo_detallado(_D(2026, 12, 1), 10, P.Materia.CIVIL, calendario=cal)
    print(f"estado: {c.estado} | confiable: {c.confiable}")
    for a in c.advertencias:
        print(f"  ADVERTENCIA: {a}")
    print(f"  motivo real: {por_que_falta(2026, hoy=hoy)}")
