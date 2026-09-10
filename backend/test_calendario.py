#!/usr/bin/env python3
"""Tests del calendario judicial y del limite de materias.

Lo que se prueba aca NO es que las fechas sean correctas (eso lo dice la fuente
citada en cada periodo), sino que el modulo:
  1. no invente cobertura donde no la tiene,
  2. trate a cada departamento por separado, porque MEDIDO no coinciden,
  3. distinga "dato no emitido todavia" de "dato que no busque",
  4. reproduzca el mecanismo de pausa y reanudacion que el TSJ aplica,
  5. y RECHACE las materias que no modela en vez de calcularlas como civiles.

Correr: python3 test_calendario.py   (exit 0 verde, exit 1 rojo)
"""
import datetime as dt
import sys

import calendario_judicial as C
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


print("=== 1. Cobertura: solo los anios que tienen fuente ===")
cal = C.calendario("Tarija")
chk("Tarija cubre 2018, 2019 y 2023", sorted(cal.cobertura), [2018, 2019, 2023],
    "COBERTURA-SOLO-MEDIDA")
chk("2024 NO esta cubierto (no lo busque)", cal.cubre(2024), False,
    "COBERTURA-SOLO-MEDIDA")
chk("2026 NO esta cubierto (no fue emitido)", cal.cubre(2026), False,
    "COBERTURA-SOLO-MEDIDA")
chk("hay 4 periodos cargados y uno es incompleto", len(cal.periodos), 4)
chk("el periodo 2025 esta cargado PERO no da cobertura",
    cal.suspendido(dt.date(2025, 12, 15)) is not None and not cal.cubre(2025),
    True, "REGISTRAR-NO-ES-CONFIRMAR")

print("\n=== 2. Los departamentos NO coinciden: es la prueba del diseno ===")
# Mismo anio 2025, tres rangos distintos, cada uno con su fuente.
pot = C.calendario("Potosi")
scz = C.calendario("Santa Cruz")
chk("en Potosi el 8-dic-2025 esta suspendido",
    pot.suspendido(dt.date(2025, 12, 8)) is not None, True, "POR-DEPARTAMENTO")
chk("en Santa Cruz el 8-dic-2025 NO",
    scz.suspendido(dt.date(2025, 12, 8)) is None, True, "POR-DEPARTAMENTO")
chk("en Potosi el 2-ene-2026 ya NO esta suspendido",
    pot.suspendido(dt.date(2026, 1, 2)) is None, True, "POR-DEPARTAMENTO")
chk("en Santa Cruz el 2-ene-2026 SI",
    scz.suspendido(dt.date(2026, 1, 2)) is not None, True, "POR-DEPARTAMENTO")
lp = C.calendario("La Paz")
chk("La Paz tiene la vacacion EXTRAORDINARIA de mayo-2026",
    lp.suspendido(dt.date(2026, 5, 27)) is not None, True, "EXTRAORDINARIA")
chk("y Tarija no la tiene (no es nacional)",
    cal.suspendido(dt.date(2026, 5, 27)) is None, True, "EXTRAORDINARIA")

# ATENCION: las seis aserciones de arriba NO probaban el filtro por
# departamento. `calendario(dep)` ya carga solo los periodos de ese dep, asi que
# borrar el filtro de `suspendido()` no cambiaba nada y el falsador daba verde.
# Otra vez el veredicto correcto por la razon equivocada. Para discriminar hace
# falta UN calendario con periodos MEZCLADOS.
mixto = P.CalendarioJudicial(departamento="Tarija")
for p, anio in C.TARIJA_COMPLETOS:
    mixto.registrar(p)
for p, anio in C.OTROS_DEPARTAMENTOS:
    mixto.registrar(p)
chk("un calendario de Tarija con periodos de otros deps ignora los ajenos",
    mixto.suspendido(dt.date(2026, 5, 27)), None, "FILTRO-DEPARTAMENTO")
chk("y el de Potosi tampoco se le pega",
    mixto.suspendido(dt.date(2025, 12, 8)), None, "FILTRO-DEPARTAMENTO")
chk("pero SI reconoce los propios",
    mixto.suspendido(dt.date(2023, 12, 20)) is not None, True,
    "FILTRO-DEPARTAMENTO")
mixto.departamento = "La Paz"
chk("y cambiando el departamento cambia lo que ve",
    mixto.suspendido(dt.date(2026, 5, 27)) is not None, True,
    "FILTRO-DEPARTAMENTO")

print("\n=== 3. Cada periodo cita su fuente. Sin fuente no entra ===")
chk("todos los periodos de Tarija citan fuente",
    all(len(p.circular) > 20 for p in cal.periodos), True, "FUENTE-OBLIGATORIA")
chk("el periodo 2025 dice que su fin NO fue medido",
    any("NO MEDIDO" in p.circular for p in C.TARIJA_INCOMPLETOS), True,
    "FUENTE-OBLIGATORIA")

print("\n=== 4. 'No emitido' NO es lo mismo que 'no medido' ===")
hoy = dt.date(2026, 9, 10)
chk("2026 en septiembre: TODAVIA NO EXISTE",
    "NO EXISTE" in C.por_que_falta(2026, hoy=hoy), True, "NO-EMITIDO")
chk("2027: no se fija hasta oct-nov de 2027",
    "todavia no se fija" in C.por_que_falta(2027, hoy=hoy), True, "NO-EMITIDO")
chk("2024: deberia existir y no la medi",
    "NO fue medida" in C.por_que_falta(2024, hoy=hoy), True, "NO-EMITIDO")
# En noviembre ya deberia existir, asi que el mensaje cambia.
chk("el mismo 2026 en noviembre ya es un pendiente mio",
    "NO fue medida" in C.por_que_falta(2026, hoy=dt.date(2026, 11, 20)), True,
    "NO-EMITIDO")

print("\n=== 5. Pausa y reanudacion, como lo hace el TSJ ===")
# Notificado 1-dic-2023, 10 dias habiles. Vacacion Tarija 5 al 29 de diciembre.
# Habiles antes de la vacacion: solo el lunes 4. Los 9 restantes van despues.
# Es el mismo mecanismo del AS 589/2021: dias transcurridos hasta la vacacion,
# reinicio del computo al retorno, y prorroga si el ultimo cae inhabil.
c = P.computo_detallado(dt.date(2023, 12, 1), 10, Materia.CIVIL, calendario=cal)
chk("el vencimiento cae en enero de 2024", c.vencimiento.date(),
    dt.date(2024, 1, 12), "PAUSA-Y-REANUDA")
contados_antes = [d for d in c.detalle
                  if d["cuenta"] and d["fecha"] < dt.date(2023, 12, 5)]
chk("solo 1 dia contado antes de la vacacion", len(contados_antes), 1,
    "PAUSA-Y-REANUDA")
chk("ese dia es el lunes 4-dic", contados_antes[0]["fecha"],
    dt.date(2023, 12, 4), "PAUSA-Y-REANUDA")
chk("ningun dia de la vacacion se conto",
    [d for d in c.detalle if d["cuenta"] and cal.suspendido(d["fecha"])], [],
    "PAUSA-Y-REANUDA")
chk("y el estado es NO_MEDIDO porque el plazo se derrama a 2024 sin circular",
    c.estado, P.NO_MEDIDO, "COBERTURA-DERRAME")
print("       ^ el plazo cruza a 2024 y 2024 no esta medido: el modulo lo dice")
print("         en vez de fingir que la fecha es firme")

print("\n=== 6. EL TERCER REGIMEN: materias que el modulo NO modela ===")
# AS 589/2021 (Sala Contenciosa Administrativa Segunda del TSJ): el plazo se
# computa "desde el dia y hora de la diligencia hasta la misma hora del dia de
# vencimiento", art. 264 de la Ley 1340. No es habiles ni corridos.
ok, motivo = P.materia_modelada("contencioso_administrativo")
chk("contencioso administrativo NO esta modelado", ok, False, "TERCER-REGIMEN")
chk("y el motivo cita el momento a momento",
    "MOMENTO A MOMENTO" in (motivo or ""), True, "TERCER-REGIMEN")
chk("civil si esta modelado", P.materia_modelada("civil")[0], True)
chk("penal si esta modelado", P.materia_modelada("PENAL")[0], True)
ok2, motivo2 = P.materia_modelada("marciano")
chk("una materia desconocida tampoco se calcula", ok2, False, "TERCER-REGIMEN")
chk("y avisa que no esta ni modelada ni declarada",
    "NI declarada" in (motivo2 or ""), True, "TERCER-REGIMEN")
chk("familia, laboral y constitucional estan declaradas como no modeladas",
    all(not P.materia_modelada(m)[0]
        for m in ("familia", "laboral", "constitucional")), True,
    "TERCER-REGIMEN")
# El enum sigue siendo la barrera dura.
try:
    P.computo_detallado(dt.date(2026, 9, 10), 10, "contencioso_administrativo")
    chk("pasarla como string deberia explotar", "no exploto", "TypeError",
        "TERCER-REGIMEN")
except TypeError:
    verdes += 1
    print("  OK   pasarla como string explota (TypeError)")

print("\n=== 7. Reporte de cobertura, para el humano ===")
rep = C.cobertura("Tarija")
chk("el reporte lista los anios cubiertos", rep["anios_cubiertos"],
    [2018, 2019, 2023])
chk("y marca los periodos incompletos", len(rep["periodos_incompletos"]) > 0,
    True)

print(f"\n{'='*62}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    if etiquetas:
        print("ETIQUETAS_ROJAS: " + " ".join(sorted(etiquetas)))
    sys.exit(1)
print("VERDE")
