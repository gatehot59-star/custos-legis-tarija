#!/usr/bin/env python3
"""Tests de plazos. Incluye el CONTRA-TEST del bug que estamos evitando.

Un test que solo prueba mis aciertos no es un test. Aca hay tres clases:
  1. Casos correctos (el calculo habil funciona).
  2. CONTRA-TESTS: demuestran que el metodo INGENUO (timedelta) da mal, para que
     nadie "simplifique" esto en tres meses sin darse cuenta de lo que rompe.
  3. Casos adversos: feriados encadenados, plazo cero, fechas invertidas.

Correr: python3 test_plazos.py   (exit 0 verde, exit 1 rojo)
"""
import datetime as dt
import sys

import plazos as P

fallos: list[str] = []
verdes = 0


def chk(nombre, obtenido, esperado):
    global verdes
    if obtenido == esperado:
        verdes += 1
        print(f"  OK   {nombre}: {obtenido}")
    else:
        fallos.append(f"{nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")
        print(f"  ROJO {nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")


print("=== 1. Pascua (ancla de los feriados moviles) ===")
# Verificables contra cualquier calendario liturgico publicado.
chk("pascua 2026", P.pascua(2026), dt.date(2026, 4, 5))
chk("pascua 2025", P.pascua(2025), dt.date(2025, 4, 20))
chk("pascua 2024", P.pascua(2024), dt.date(2024, 3, 31))

print("\n=== 2. Feriados derivados ===")
f26 = P.feriados(2026)
# Viernes Santo 2026 = 3 de abril (Pascua 5-abr menos 2)
chk("viernes santo 2026", dt.date(2026, 4, 3) in f26, True)
chk("6 de agosto es feriado", dt.date(2026, 8, 6) in f26, True)
chk("La Tablada 15-abr en Tarija", dt.date(2026, 4, 15) in f26, True)
chk("La Tablada NO es feriado fuera de Tarija",
    dt.date(2026, 4, 15) in P.feriados(2026, tarija=False), False)

print("\n=== 3. Dias habiles ===")
# 2026-09-10 es jueves; 12 sabado; 13 domingo.
chk("jueves 10-sep es habil", P.es_habil(dt.date(2026, 9, 10)), True)
chk("sabado 12-sep NO es habil", P.es_habil(dt.date(2026, 9, 12)), False)
chk("domingo 13-sep NO es habil", P.es_habil(dt.date(2026, 9, 13)), False)

print("\n=== 4. EL CASO QUE IMPORTA: 3 dias habiles desde un jueves ===")
# Notificado jueves 10-sep-2026. Habiles: vie 11, lun 14, mar 15.
v = P.vencimiento(dt.date(2026, 9, 10), 3)
chk("vencimiento habil", v, dt.date(2026, 9, 15))
chk("y cae en dia habil", P.es_habil(v), True)

print("\n=== 5. CONTRA-TEST: el bug D4 que Fable cazo ===")
# Asi lo hacia el diseno original. Demuestra el dano, no lo esconde.
ingenuo = dt.date(2026, 9, 10) + dt.timedelta(days=3)
chk("timedelta(days=3) da domingo", ingenuo, dt.date(2026, 9, 13))
chk("...y ese dia NO es habil", P.es_habil(ingenuo), False)
chk("el metodo ingenuo ADELANTA el plazo 2 dias", (v - ingenuo).days, 2)
print("       ^ el sistema le habria dicho al abogado que vencia el domingo")

print("\n=== 6. Plazo que cruza un feriado nacional ===")
# Notificado lunes 3-ago-2026. Habiles: mar 4, mie 5, (jue 6 = INDEPENDENCIA),
# vie 7, lun 10, mar 11.
chk("5 habiles saltando el 6-ago",
    P.vencimiento(dt.date(2026, 8, 3), 5), dt.date(2026, 8, 11))

print("\n=== 7. Casos adversos ===")
chk("plazo 0 = mero tramite, sin vencimiento",
    P.vencimiento(dt.date(2026, 9, 10), 0), dt.date(2026, 9, 10))
chk("plazo negativo no explota",
    P.vencimiento(dt.date(2026, 9, 10), -5), dt.date(2026, 9, 10))
chk("cierre extraordinario del juzgado se respeta",
    P.vencimiento(dt.date(2026, 9, 10), 1, extra=[dt.date(2026, 9, 11)]),
    dt.date(2026, 9, 14))
chk("habiles_restantes invertido da negativo",
    P.habiles_restantes(dt.date(2026, 9, 15), dt.date(2026, 9, 10)) < 0, True)

print("\n=== 8. La tabla de plazos NO se presenta como cierta ===")
# Este es el test etico del modulo: mientras ningun abogado confirme la tabla,
# el sistema tiene que decir HIPOTESIS. Si alguien pone confirmado=True sin
# medicion, este test se lo cobra.
chk("auto interlocutorio = 3 dias", P.plazo_de("auto_interlocutorio")["dias"], 3)
chk("y esta marcado HIPOTESIS",
    P.plazo_de("auto_interlocutorio")["estado"], "HIPOTESIS")
chk("tipo inventado -> NO_MEDIDO, no un numero",
    P.plazo_de("recurso_que_no_existe")["estado"], "NO_MEDIDO")
chk("ningun plazo esta confirmado todavia",
    any(p["confirmado"] for p in P.PLAZOS.values()), False)

print("\n=== 9. Urgencia ===")
chk("2 dias = critico", P.urgencia(2), "critico")
chk("5 dias = alto", P.urgencia(5), "alto")
chk("vencido", P.urgencia(-1), "vencido")

print(f"\n{'='*60}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    sys.exit(1)
print("VERDE")
