#!/usr/bin/env python3
"""Tests de la compuerta de publicacion.

LO QUE ESTOS TESTS PRUEBAN, y lo que NO:

  SI prueban que la compuerta es fail-closed: que retiene ante la duda, que la
  reserva legal gana sobre todo, y que un fallo del detector NO se convierte en
  una fuga.

  NO prueban que el detector tenga buen recall. **No lo tiene, y esta medido**:
  la seccion 5 corre cuatro textos adversarios y el detector no ve ninguno de
  los cuatro nombres. Ese es el resultado que justifica la arquitectura, asi que
  esta escrito como asercion y no como comentario: si alguien "mejora" el
  detector, el numero cambia y el test lo canta.

Correr: python3 test_anonimizador.py   (exit 0 verde, exit 1 rojo)
"""
import sys

import anonimizador as A
import fixtures_reales as F
from anonimizador import Clase, Decision

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


MATRICULA = "MJ-DE-PRUEBA-12345"

print("=== 1. RESERVA LEGAL: gana sobre todo, ni anonimizada ===")
# Los tres fixtures sinteticos son NNA, familia y violencia.
for texto, materia, proc, sint, esperados in F.FIXTURES:
    if not sint:
        continue
    v = A.evaluar(texto, materia)
    chk(f"reserva: {proc[11:40]}", v.decision, Decision.RESERVA_LEGAL,
        "RESERVA-LEGAL")
    # Y con matricula aprobada TAMBIEN se retiene: no hay firma que lo habilite.
    v2 = A.evaluar(texto, materia, aprobado_por_matricula=MATRICULA)
    chk("   ...y la matricula NO la habilita", v2.decision,
        Decision.RESERVA_LEGAL, "RESERVA-LEGAL")
    chk("   ...y no entrega texto", v2.texto_publicable, None, "RESERVA-LEGAL")

print("\n=== 2. La capa publica NO muestra texto de jurisprudencia ===")
jur = ("VISTOS: el recurso de apelacion interpuesto por Maria Elena Choque "
       "Villca contra Juan Carlos Mamani Quispe sobre cumplimiento de "
       "contrato, y el Auto de Vista 12/2020 de la Sala Civil Segunda.")
v = A.evaluar(jur, "civil")
chk("jurisprudencia sin aprobacion -> RETENIDO", v.decision, Decision.RETENIDO,
    "NO-TEXTO-LIBRE")
chk("y no entrega texto", v.texto_publicable, None, "NO-TEXTO-LIBRE")
chk("el motivo cita la Ley 387",
    any("387" in m for m in v.motivos), True, "NO-TEXTO-LIBRE")

print("\n=== 3. Con matricula, seudonimiza partes y NO toca autoridades ===")
jur2 = jur[:-1] + ", Magistrado Relator Dr. Carlos Alberto Eguez Anez."
v = A.evaluar(jur2, "civil", aprobado_por_matricula=MATRICULA)
chk("aprobado -> PUBLICO", v.decision, Decision.PUBLICO)
pub = v.texto_publicable or ""
chk("la parte actora desaparecio", "Choque Villca" in pub, False, "SEUDONIMIZA")
chk("la parte demandada desaparecio", "Mamani Quispe" in pub, False,
    "SEUDONIMIZA")
chk("el MAGISTRADO sigue nombrado", "Carlos Alberto Eguez Anez" in pub, True,
    "AUTORIDAD-INTACTA")
chk("hay dos etiquetas de parte", pub.count("[PARTE-"), 2, "SEUDONIMIZA")
chk("el seudonimo no pega palabras", "] contra [" in pub, True, "SEUDONIMIZA")
chk("y el motivo dice quien aprobo",
    any(MATRICULA in m for m in v.motivos), True, "HITL-MATRICULA")

print("\n=== 4. El seudonimo es ESTABLE y no reidentifica ===")
chk("mismo nombre, misma etiqueta",
    A.seudonimo("Juan Carlos Mamani Quispe"),
    A.seudonimo("JUAN CARLOS MAMANI QUISPE"), "SEUDONIMO-ESTABLE")
chk("nombres distintos, etiquetas distintas",
    A.seudonimo("Juan Perez") == A.seudonimo("Maria Perez"), False,
    "SEUDONIMO-ESTABLE")
chk("la etiqueta NO contiene las iniciales (reidentifican en un juzgado chico)",
    "JCMQ" in A.seudonimo("Juan Carlos Mamani Quispe"), False,
    "SEUDONIMO-ESTABLE")
chk("con otra sal, otra etiqueta",
    A.seudonimo("Juan Perez") == A.seudonimo("Juan Perez", sal="otra"), False,
    "SEUDONIMO-ESTABLE")

print("\n=== 5. EL DETECTOR FALLA, Y ESTA MEDIDO ===")
# Estos cuatro esquivan el detector: pide 2 tokens capitalizados seguidos.
ADVERSARIOS = (
    ("Se declara PROBADA la demanda ordinaria interpuesta contra Mamani, "
     "conforme al Auto de Vista 12/2020 de la Sala Civil Segunda.",
     "Mamani", "un solo apellido"),
    ("VISTOS: el recurso de apelacion planteado por juan carlos quispe contra "
     "la Sentencia 45/2019 del Juzgado Publico Civil 3ro.",
     "quispe", "nombre en minusculas (OCR malo)"),
    ("Auto de Vista. El demandante, sr. R. Villca T., interpone recurso contra "
     "la resolucion de fs. 120.",
     "Villca", "nombre abreviado con iniciales"),
    ("SENTENCIA. Se condena al acusado GUTIERREZ a la pena de tres anos.",
     "GUTIERREZ", "apellido solo en mayuscula"),
)
no_vistos = 0
for texto, nombre, por_que in ADVERSARIOS:
    partes = [c for c in A.candidatos(texto) if c.rol == "parte"]
    visto = any(nombre.lower() in c.texto.lower() for c in partes)
    if not visto:
        no_vistos += 1
    print(f"       [{por_que}] detectado: {visto}")
chk("el detector NO ve 4 de 4 nombres adversarios", no_vistos, 4,
    "DETECTOR-FALLA")
print("       ^ este numero es el que justifica que el detector NO sea el control")

# Y LO QUE IMPORTA: que ese fallo no se convierta en fuga.
fugas = 0
for texto, nombre, por_que in ADVERSARIOS:
    v = A.evaluar(texto, "civil")
    if v.publicable and v.texto_publicable and nombre in v.texto_publicable:
        fugas += 1
chk("y aun asi, CERO fugas en la capa publica", fugas, 0, "CERO-FUGAS")

print("\n=== 6. Normativo: publico, porque no tiene partes por naturaleza ===")
ley = ("LEY N 439 DE 19 DE NOVIEMBRE DE 2013. Por cuanto, la Asamblea "
       "Legislativa Plurinacional, ha sancionado la siguiente Ley: DECRETA: "
       "ARTICULO 90. (COMIENZO, TRANSCURSO Y VENCIMIENTO).")
v = A.evaluar(ley)
chk("una ley se publica sin compuerta", v.decision, Decision.PUBLICO,
    "NORMATIVO-PUBLICO")
chk("y con su texto completo", v.texto_publicable == ley, True,
    "NORMATIVO-PUBLICO")
chk("clasificada como normativo", v.clase, Clase.NORMATIVO, "NORMATIVO-PUBLICO")

print("\n=== 7. Citar un articulo NO convierte un fallo en una ley ===")
# ESTE ES UN DEFECTO QUE MEDI EN MI PROPIA v1: tenia `ARTICULO \d+` y `CODIGO`
# como senas normativas, y clasifico un fragmento de la SCP 0693/2023-S4 como
# NORMATIVO. Como los normativos se publican sin compuerta, esa Sentencia
# Constitucional habria salido a la capa publica.
scp = F.FIXTURES[2][0]
clase, motivos = A.clasificar(scp)
chk("la SCP NO se clasifica como normativa", clase == Clase.NORMATIVO, False,
    "SENA-DEBIL")
chk("queda DESCONOCIDO y por lo tanto retenido", clase, Clase.DESCONOCIDO,
    "SENA-DEBIL")
chk("y el motivo explica que la sena era debil",
    any("DEBILES" in m for m in motivos), True, "SENA-DEBIL")
chk("el veredicto la retiene", A.evaluar(scp, "penal").decision,
    Decision.RETENIDO, "SENA-DEBIL")

print("\n=== 8. Al corpus se le CREE el tipo, no se adivina ===")
chk("tipo declarado 'Ley' -> normativo",
    A.clasificar(scp, tipo_declarado="Ley")[0], Clase.NORMATIVO,
    "TIPO-DECLARADO")
chk("tipo declarado 'Sentencia Constitucional' -> jurisprudencial",
    A.clasificar(scp, tipo_declarado="Sentencia Constitucional")[0],
    Clase.JURISPRUDENCIAL, "TIPO-DECLARADO")
chk("tipo declarado raro -> DESCONOCIDO, no se adivina",
    A.clasificar(scp, tipo_declarado="cosa rara")[0], Clase.DESCONOCIDO,
    "TIPO-DECLARADO")

print("\n=== 9. Personas JURIDICAS no son personas naturales (art. 21.2 CPE) ===")
emp = F.FIXTURES[1][0]
roles = {c.rol for c in A.candidatos(emp)}
chk("la sociedad y la editorial salen como juridica", roles, {"juridica"},
    "PERSONA-JURIDICA")
chk("ninguna como parte",
    any(c.rol == "parte" for c in A.candidatos(emp)), False, "PERSONA-JURIDICA")

print("\n=== 10. La ficha publica no filtra texto ===")
ficha = A.ficha_publica({
    "uid": "as-589-2021", "tipo_norma": "Auto Supremo", "numero": "589/2021",
    "fecha": "2021-09-20", "organo": "TSJ", "fuente_url": "https://ej.bo/x",
    "sha256": "ab12", "vigencia": "NO_MEDIDO",
    "texto_crudo": "NOMBRE QUE NO DEBE SALIR",
    "parte_actora": "Maria Choque"})
chk("la ficha no trae texto_crudo", "texto_crudo" in ficha, False, "FICHA-LIMPIA")
chk("ni parte_actora", "parte_actora" in ficha, False, "FICHA-LIMPIA")
chk("el nombre no aparece en ningun valor",
    any("Choque" in str(v) for v in ficha.values()), False, "FICHA-LIMPIA")
chk("pero si la cadena de custodia",
    bool(ficha["fuente_url"]) and bool(ficha["sha256"]), True)
chk("y dice por que no hay texto", "no publicado" in ficha["nota"], True)

print("\n=== 11. Los 6 fixtures REALES: ninguno se publica por accidente ===")
reales = [f for f in F.FIXTURES if not f[3]]
publicados = [proc for texto, materia, proc, sint, esp in reales
              if A.evaluar(texto, materia).publicable]
chk("ninguno de los 6 reales sale a la capa publica", publicados, [],
    "FAIL-CLOSED")
chk("y son 6", len(reales), 6)

print(f"\n{'='*62}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    if etiquetas:
        print("ETIQUETAS_ROJAS: " + " ".join(sorted(etiquetas)))
    sys.exit(1)
print("VERDE")
