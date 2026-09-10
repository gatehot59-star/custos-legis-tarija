#!/usr/bin/env python3
"""Tests de plazos POR MATERIA. Cada bug arreglado deja aca su contra-test.

Un test que solo prueba mis aciertos no es un test. Hay cuatro clases:
  1. Casos correctos.
  2. CONTRA-TESTS: demuestran el DANO del metodo viejo, con numero, para que
     nadie lo "simplifique" en tres meses sin ver lo que rompe.
  3. Casos adversos: feriados encadenados, arranque inhabil, plazo cero.
  4. Tests de HONESTIDAD: sin calendario judicial cargado el resultado tiene que
     ser NO_MEDIDO, y la tabla de plazos tiene que salir como HIPOTESIS.

LECCION DE ESTA SESION, y va arriba porque es la que mas vale:
las cuatro aserciones de la seccion 10 (vacacion judicial) PASABAN con la
suspension neutralizada a proposito. No por casualidad: la prorroga del art.
90.III las rescataba, porque el ultimo dia caia dentro de la vacacion y se
corria igual. Veredicto correcto por la razon equivocada, el mismo defecto P1
de la sesion pasada. La cura es mirar el COMPUTO dia por dia, no el resultado.
Mismo caso con el arranque del art. 90.I: en modo habiles no discrimina, porque
el sabado no cuenta de todos modos. Solo discrimina en CORRIDOS.

Correr: python3 test_plazos.py   (exit 0 verde, exit 1 rojo)
"""
import datetime as dt
import sys

import plazos as P
from plazos import Materia

fallos: list[str] = []
etiquetas: set[str] = set()
verdes = 0


def chk(nombre, obtenido, esperado, etiqueta=None):
    global verdes
    if obtenido == esperado:
        verdes += 1
        print(f"  OK   {nombre}: {obtenido}")
    else:
        fallos.append(f"{nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")
        if etiqueta:
            etiquetas.add(etiqueta)
        print(f"  ROJO [{etiqueta or '-'}] {nombre}: "
              f"obtuve {obtenido!r}, esperaba {esperado!r}")


# ---------------------------------------------------------------------------
# CALENDARIO DE PRUEBA. Los numeros de circular son FICTICIOS a proposito: la
# circular real de Tarija 2026 es NO MEDIDA y no se inventa en codigo de
# produccion. Estos tests prueban el MECANISMO de suspension, no el calendario.
# ---------------------------------------------------------------------------
def cal_prueba() -> P.CalendarioJudicial:
    c = P.CalendarioJudicial(departamento="Tarija")
    c.registrar(P.PeriodoSuspension(
        desde=dt.date(2026, 12, 9), hasta=dt.date(2027, 1, 2),
        departamento="Tarija", circular="CIRCULAR-DE-PRUEBA-NO-REAL",
        motivo="vacacion judicial"))
    c.declarar_cubierto(2026)
    c.declarar_cubierto(2027)
    return c


print("=== 1. Pascua y feriados derivados ===")
chk("pascua 2026", P.pascua(2026), dt.date(2026, 4, 5))
chk("pascua 2025", P.pascua(2025), dt.date(2025, 4, 20))
chk("pascua 2024", P.pascua(2024), dt.date(2024, 3, 31))
f26 = P.feriados(2026)
chk("viernes santo 2026 = 3-abr", dt.date(2026, 4, 3) in f26, True)
chk("carnaval 2026 = 16 y 17-feb",
    dt.date(2026, 2, 16) in f26 and dt.date(2026, 2, 17) in f26, True)
chk("corpus christi 2026 = 4-jun", dt.date(2026, 6, 4) in f26, True)
chk("6 de agosto es feriado", dt.date(2026, 8, 6) in f26, True)
chk("La Tablada 15-abr en Tarija", dt.date(2026, 4, 15) in f26, True)
chk("La Tablada NO aplica fuera de Tarija",
    dt.date(2026, 4, 15) in P.feriados(2026, tarija=False), False)

print("\n=== 2. Dias habiles ===")
chk("jueves 10-sep-2026 es habil", P.es_habil(dt.date(2026, 9, 10)), True)
chk("sabado 12-sep NO", P.es_habil(dt.date(2026, 9, 12)), False)
chk("domingo 13-sep NO", P.es_habil(dt.date(2026, 9, 13)), False)

print("\n=== 3. CIVIL, plazo <= 15 dias: solo habiles (art. 90.II) ===")
cal = cal_prueba()
c = P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.CIVIL, calendario=cal)
chk("3 habiles desde jueves 10-sep", c.vencimiento.date(), dt.date(2026, 9, 15))
chk("modo es habiles", c.modo, "habiles")
chk("estado CONFIRMADO con calendario", c.estado, P.CONFIRMADO)
chk("cae en dia habil", P.es_habil(c.vencimiento.date()), True)
chk("10 habiles cruzando La Tablada (noti lun 13-abr)",
    P.computo_detallado(dt.date(2026, 4, 13), 10, Materia.CIVIL,
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 4, 28))
chk("5 habiles saltando el 6-ago (noti lun 3-ago)",
    P.computo_detallado(dt.date(2026, 8, 3), 5, Materia.CIVIL,
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 8, 11))

print("\n=== 4. EL BUG QUE ENCONTRE HOY: civil > 15 dias va CORRIDO ===")
# Art. 90.II: "En el computo de los plazos que excedan los quince dias se
# computaran los dias habiles y los inhabiles". traslado_demanda son 30.
c30 = P.computo_detallado(dt.date(2026, 1, 8), 30, Materia.CIVIL, calendario=cal)
chk("30 dias desde 2026-01-08 vence 2026-02-09", c30.vencimiento.date(),
    dt.date(2026, 2, 9), "PLAZO-CORRIDO-90II")
chk("y el modo es corridos", c30.modo, "corridos", "PLAZO-CORRIDO-90II")
chk("el fundamento cita el 90.II", "90.II" in c30.fundamento, True)
chk("hubo prorroga: el dia 30 caia sabado 7-feb",
    any("PRORROGA" in d["marca"] for d in c30.detalle), True)

print("\n=== 5. CONTRA-TEST del bug de la v1 de este modulo ===")
# La v1 contaba SOLO habiles para cualquier plazo. Reproduzco esa ruta y mido
# el dano. Si alguien vuelve a unificar las dos reglas, este test se lo cobra.
def v1_solo_habiles(noti, dias):
    cur, n = noti, 0
    while True:
        cur += dt.timedelta(days=1)
        if P.es_habil(cur):
            n += 1
            if n == dias:
                return cur

viejo = v1_solo_habiles(dt.date(2026, 1, 8), 30)
chk("la v1 daba 2026-02-24", viejo, dt.date(2026, 2, 24), "PLAZO-CORRIDO-90II")
chk("o sea 15 dias DE MAS", (viejo - c30.vencimiento.date()).days, 15,
    "PLAZO-CORRIDO-90II")
print("       ^ y en la direccion peligrosa: le decia al abogado que tenia")
print("         hasta el 24-feb un plazo PERENTORIO que vencio el 9-feb")

print("\n=== 6. CONTRA-TEST del D4 original (timedelta) ===")
ingenuo = dt.date(2026, 9, 10) + dt.timedelta(days=3)
chk("timedelta(days=3) desde jueves da domingo", ingenuo, dt.date(2026, 9, 13))
chk("...y ese dia NO es habil", P.es_habil(ingenuo), False)
chk("adelantaba el plazo 2 dias", (dt.date(2026, 9, 15) - ingenuo).days, 2)

print("\n=== 7. El umbral de 15 dias es un borde, y se prueba en el borde ===")
c15 = P.computo_detallado(dt.date(2026, 3, 2), 15, Materia.CIVIL, calendario=cal)
c16 = P.computo_detallado(dt.date(2026, 3, 2), 16, Materia.CIVIL, calendario=cal)
chk("15 dias -> habiles", c15.modo, "habiles", "UMBRAL-15")
chk("16 dias -> corridos", c16.modo, "corridos", "UMBRAL-15")
chk("y el plazo MAS LARGO vence ANTES (no es un error, es el 90.II)",
    c16.vencimiento < c15.vencimiento, True, "UMBRAL-15")
print(f"       15d -> {c15.vencimiento.date()} | 16d -> {c16.vencimiento.date()}")

print("\n=== 8. PENAL: art. 130 CPP ===")
cp = P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.PENAL, calendario=cal)
chk("3 dias penales son habiles", cp.modo, "habiles")
chk("vence a las 24:00 (23:59:59)", cp.vencimiento.time(), dt.time(23, 59, 59),
    "HORA-PENAL")
cc = P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.PENAL,
                         medida_cautelar=True, calendario=cal)
chk("medida cautelar va en CORRIDOS", cc.modo, "corridos", "CAUTELAR-CORRIDA")
chk("y vence antes que la no cautelar", cc.vencimiento < cp.vencimiento, True,
    "CAUTELAR-CORRIDA")
print(f"       penal habil -> {cp.vencimiento} | cautelar -> {cc.vencimiento}")

print("\n=== 9. La hora de vencimiento DIFIERE por materia ===")
civ = P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.CIVIL, calendario=cal)
chk("misma fecha en civil y penal", civ.vencimiento.date(),
    cp.vencimiento.date())
chk("pero NO la misma hora", civ.vencimiento == cp.vencimiento, False,
    "HORA-POR-MATERIA")
chk("civil avisa que la hora de cierre es NO MEDIDA",
    any("NO MEDIDA" in a for a in civ.advertencias), True)

print("\n=== 10. VACACION JUDICIAL: suspende, no consume (art. 126.IV LOJ) ===")
# Notificado 1-dic-2026, 10 dias habiles, con vacacion del 9-dic al 2-ene.
cv = P.computo_detallado(dt.date(2026, 12, 1), 10, Materia.CIVIL, calendario=cal)
chk("el vencimiento cae DESPUES de la vacacion",
    cv.vencimiento.date() > dt.date(2027, 1, 2), True, "VACACION-SUSPENDE")
chk("y no cae dentro del periodo suspendido",
    cal.suspendido(cv.vencimiento.date()) is None, True, "VACACION-SUSPENDE")
sin_vac = P.computo_detallado(dt.date(2026, 12, 1), 10, Materia.CIVIL)
chk("sin calendario habria dicho 15-dic, dentro de la vacacion",
    sin_vac.vencimiento.date(), dt.date(2026, 12, 15), "VACACION-SUSPENDE")
chk("...y ese dia esta suspendido",
    cal.suspendido(dt.date(2026, 12, 15)) is not None, True)
print(f"       con calendario -> {cv.vencimiento.date()} | "
      f"sin calendario -> {sin_vac.vencimiento.date()}")
# Corridos tambien se pausan, no se consumen.
cvc = P.computo_detallado(dt.date(2026, 12, 1), 30, Materia.CIVIL, calendario=cal)
chk("un plazo corrido tambien se PAUSA en la vacacion",
    cvc.vencimiento.date() > dt.date(2027, 1, 2), True, "VACACION-SUSPENDE")

# ATENCION. Las cuatro aserciones de arriba PASABAN con la suspension
# neutralizada, y no por casualidad: la prorroga del art. 90.III las rescataba,
# porque el ultimo dia caia dentro de la vacacion y se corria igual. Verdicto
# correcto por la razon equivocada, el mismo defecto P1 de la sesion pasada.
# Estas si discriminan, porque miran el COMPUTO, no el resultado.
contados_en_vacacion = [d for d in cv.detalle
                        if d["cuenta"] and cal.suspendido(d["fecha"])]
chk("NINGUN dia suspendido se cuenta como plazo", contados_en_vacacion, [],
    "VACACION-NO-CONSUME")
marcados = [d for d in cv.detalle if d["marca"].startswith("suspendido")]
chk("y el detalle los marca como suspendidos", len(marcados) > 0, True,
    "VACACION-NO-CONSUME")
chk("citando la circular que lo dispone",
    all("CIRCULAR-DE-PRUEBA-NO-REAL" in d["marca"] for d in marcados), True,
    "VACACION-NO-CONSUME")
corridos_en_vacacion = [d for d in cvc.detalle
                        if d["cuenta"] and cal.suspendido(d["fecha"])]
chk("tampoco en computo corrido", corridos_en_vacacion, [],
    "VACACION-NO-CONSUME")

print("\n=== 11. HONESTIDAD: sin calendario no hay fecha confiable ===")
chk("sin calendario el estado es NO_MEDIDO", sin_vac.estado, P.NO_MEDIDO,
    "SIN-CALENDARIO-NO-MEDIDO")
chk("y no es confiable", sin_vac.confiable, False, "SIN-CALENDARIO-NO-MEDIDO")
chk("vencimiento() devuelve None, no una fecha muda",
    P.vencimiento(dt.date(2026, 12, 1), 10, Materia.CIVIL), None,
    "SIN-CALENDARIO-NO-MEDIDO")
chk("pero con calendario si devuelve fecha",
    P.vencimiento(dt.date(2026, 12, 1), 10, Materia.CIVIL,
                  calendario=cal) is not None, True)
chk("avisa que el art. 126 LOJ no fue contemplado",
    any("126 LOJ" in a for a in sin_vac.advertencias), True)
falta = P.computo_detallado(dt.date(2028, 3, 1), 10, Materia.CIVIL,
                            calendario=cal)
chk("anio sin circular -> NO_MEDIDO", falta.estado, P.NO_MEDIDO,
    "COBERTURA-CALENDARIO")

print("\n=== 12. La materia es obligatoria, no hay default silencioso ===")
try:
    P.computo_detallado(dt.date(2026, 9, 10), 3, "civil")  # type: ignore[arg-type]
    chk("un string como materia deberia explotar", "no exploto", "TypeError",
        "MATERIA-OBLIGATORIA")
except TypeError:
    verdes += 1
    print("  OK   un string como materia explota (TypeError)")

print("\n=== 13. Casos adversos ===")
chk("plazo 0 = mero tramite",
    P.computo_detallado(dt.date(2026, 9, 10), 0, Materia.CIVIL,
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 9, 10))
chk("plazo negativo no explota",
    P.computo_detallado(dt.date(2026, 9, 10), -5, Materia.CIVIL,
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 9, 10))
# Notificado VIERNES: el sabado no es el dia 1 (art. 90.I, "dia siguiente HABIL")
cvi = P.computo_detallado(dt.date(2026, 9, 11), 1, Materia.CIVIL, calendario=cal)
chk("noti viernes, 1 dia habil -> lunes", cvi.vencimiento.date(),
    dt.date(2026, 9, 14), "ARRANQUE-HABIL")
chk("el detalle muestra los dias previos al arranque",
    any("antes del arranque" in d["marca"] for d in cvi.detalle), True)
# En habiles el arranque no cambia el resultado (el sabado no cuenta igual), asi
# que la unica prueba que discrimina el art. 90.I es en CORRIDOS: ahi el sabado
# SI consumiria un dia si el plazo arrancara antes del primer habil.
cvi16 = P.computo_detallado(dt.date(2026, 9, 11), 16, Materia.CIVIL,
                            calendario=cal)
chk("noti viernes, 16 dias CORRIDOS arrancan el lunes -> 29-sep",
    cvi16.vencimiento.date(), dt.date(2026, 9, 29), "ARRANQUE-HABIL")
chk("el dia 1 es lunes 14, no el sabado 12",
    [d["fecha"] for d in cvi16.detalle if d["n"] == 1], [dt.date(2026, 9, 14)],
    "ARRANQUE-HABIL")
chk("cierre extraordinario del juzgado se respeta",
    P.computo_detallado(dt.date(2026, 9, 10), 1, Materia.CIVIL,
                        extra=[dt.date(2026, 9, 11)],
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 9, 14))
chk("plazo comun: se computa desde la ULTIMA notificacion",
    P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.CIVIL,
                        plazo_comun_ultima_notificacion=dt.date(2026, 9, 14),
                        calendario=cal).vencimiento.date(),
    dt.date(2026, 9, 17))
chk("habiles_restantes invertido da negativo",
    P.habiles_restantes(dt.date(2026, 9, 15), dt.date(2026, 9, 10)) < 0, True)

print("\n=== 14. La TABLA sigue siendo hipotesis (la REGLA ya no) ===")
chk("auto interlocutorio = 3 dias", P.plazo_de("auto_interlocutorio")["dias"], 3)
chk("marcado HIPOTESIS", P.plazo_de("auto_interlocutorio")["estado"],
    P.HIPOTESIS, "TABLA-HIPOTESIS")
chk("tipo inventado -> NO_MEDIDO", P.plazo_de("recurso_que_no_existe")["estado"],
    P.NO_MEDIDO)
chk("ningun plazo confirmado todavia",
    any(p["confirmado"] for p in P.PLAZOS.values()), False, "TABLA-HIPOTESIS")
chk("cada plazo declara su materia",
    all(isinstance(p["materia"], Materia) for p in P.PLAZOS.values()), True)
chk("traslado_demanda avisa que excede 15 dias",
    "EXCEDE" in P.PLAZOS["traslado_demanda"]["fundamento"], True)

print("\n=== 15. El computo se muestra dia por dia (verificable a mano) ===")
txt = c30.como_texto()
chk("el texto trae el fundamento", "90.II" in txt, True)
chk("trae la advertencia de calendario", "ADVERTENCIA" in txt, True)
chk("trae 30 dias contados", txt.count("[30/30]"), 1)
print("\n" + P.computo_detallado(dt.date(2026, 9, 10), 3, Materia.CIVIL,
                                 calendario=cal).como_texto())

print(f"\n{'='*62}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    if etiquetas:
        print("ETIQUETAS_ROJAS: " + " ".join(sorted(etiquetas)))
    sys.exit(1)
print("VERDE")
