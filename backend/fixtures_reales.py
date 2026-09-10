#!/usr/bin/env python3
"""Fragmentos de texto judicial boliviano REAL, para medir el anonimizador.

POR QUE ESTE ARCHIVO EXISTE Y NO INVENTO LOS CASOS:
Si escribo yo el detector Y los casos de prueba, la medicion no es independiente
(W-01). No puedo eliminar ese problema, pero puedo reducirlo: estos fragmentos
NO los redacte yo. Son recortes de texto que aparece publicado en fuentes
judiciales y de prensa boliviana, con su procedencia al lado.

QUE SIGUE SIENDO DEBIL, declarado:
  - Son POCOS y elegidos por mi. Un corpus de 6.079 documentos tiene formas que
    aca no estan.
  - Los tres ultimos SI son sinteticos, y estan marcados `sintetico=True`:
    hacen falta porque no tengo a mano texto publico de causas de NNA o
    violencia, y justamente esas son las que no pueden filtrarse.
  - La medicion correcta es contra el corpus real. El endpoint no respondio
    cuando lo intente (2026-09-10), asi que esto es un piso, no un veredicto.
"""

# (texto, materia, procedencia, sintetico, nombres_de_parte_esperados)
FIXTURES: list[tuple[str, str, str, bool, tuple[str, ...]]] = [
    (
        "SALA CONTENCIOSA, CONTENCIOSA ADMINISTRATIVA, SOCIAL Y ADMINISTRATIVA "
        "SEGUNDA. Auto Supremo N 589/2021. Sucre, 20 de septiembre de 2021. "
        "Expediente: SC-CA.SAII-SCZ. 409/2021. Distrito: Santa Cruz. "
        "Magistrado Relator: Dr. Carlos Alberto Eguez Anez.",
        "administrativo",
        "AS 589/2021, encabezado citado en juristeca.com",
        False,
        (),  # no hay partes: solo el magistrado, que NO es dato a proteger
    ),
    (
        "En consecuencia, en el caso de analisis se establece que, la Sociedad "
        "Comunicaciones El Pais, sociedad absorbente de la Editorial Amanecer "
        "S.A., fue notificado con la Sentencia N 52 de 24 de octubre de 2009, "
        "el 12 de enero de 2010, momento desde el cual, el plazo para la "
        "presentacion del recurso de apelacion empezaba a correr.",
        "administrativo",
        "AS 589/2021, cuerpo citado en juristeca.com",
        False,
        (),  # personas juridicas: otra categoria, ver el modulo
    ),
    (
        "Sin embargo, dicha autoridad, realizando un computo equivoco de plazos "
        "procesales y apartado de lo dispuesto en el art. 130 del CPP que "
        "establece que para los plazos fijados en dias, se computaran solo los "
        "dias habiles, mediante Auto de 25 de abril de 2022 procedio a conminar "
        "al Ministerio Publico para que emita requerimiento conclusivo.",
        "penal",
        "SCP 0693/2023-S4, citada en juristeca.com",
        False,
        (),  # sin nombres: es el caso que prueba que no invento falsos positivos
    ),
    (
        "Considerando que fui citado con la accion ejecutiva en fecha 30 de "
        "junio de 2005, la prescripcion se ha producido pues han transcurrido "
        "cinco anos y diez dias en mi caso, computandose los plazos de dia a "
        "dia y no de momento a momento, al decir del art. 1488 del Codigo Civil.",
        "civil",
        "SC 0308/2010-R, memorial citado textual",
        False,
        (),
    ),
    (
        "El Presidente del Tribunal Departamental de Justicia de Tarija, Dr. "
        "Hermes Flores Eguez, informo en conferencia de prensa que, mediante "
        "Resolucion de Sala Plena se determino programar la Vacacion Anual "
        "Colectiva de 25 dias calendario a partir del viernes 07 de diciembre.",
        "administrativo",
        "TDJ Tarija, comunicado institucional",
        False,
        (),  # autoridad judicial nombrada en acto publico: NO es parte
    ),
    (
        "Auto de Vista 87/2007. La Sala Civil-Comercial Primera del Tribunal "
        "Departamental de Justicia de Oruro, emitio el Auto de Vista N 85/2016 "
        "de 30 de mayo, por el que CONFIRMA la Sentencia N 64/2015, senalando "
        "que la Empresa C.I.C.O. no demostro la comunicacion de la "
        "transferencia al acreedor A.L. o sus herederas.",
        "civil",
        "Auto 077/2018, citado en vlex (partes ya iniciadas en la fuente)",
        False,
        (),  # la fuente ya publica iniciales, no nombres
    ),
    # --- SINTETICOS, marcados. Hacen falta porque son los casos prohibidos. ---
    (
        "VISTOS: la denuncia presentada por Maria Elena Choque Villca contra "
        "Juan Carlos Mamani Quispe por el delito de violacion de infante, nina, "
        "nino o adolescente, en perjuicio de la menor de iniciales K.M.CH., "
        "domiciliada en calle Bolivar N 245, zona San Roque de Tarija.",
        "penal",
        "SINTETICO: causa penal con victima menor",
        True,
        ("Maria Elena Choque Villca", "Juan Carlos Mamani Quispe"),
    ),
    (
        "Se declara PROBADA la demanda de asistencia familiar interpuesta por "
        "Rosa Gutierrez Paco en representacion de sus hijos menores contra "
        "Pedro Nina Colque, debiendo el demandado pagar la suma de Bs 1.500.",
        "familiar",
        "SINTETICO: familia con menores",
        True,
        ("Rosa Gutierrez Paco", "Pedro Nina Colque"),
    ),
    (
        "Medidas de proteccion a favor de la victima Ana Lucia Vargas Sandoval, "
        "disponiendose la salida del agresor Luis Fernando Ortega Rojas del "
        "domicilio conyugal ubicado en avenida Integracion N 88.",
        "penal",
        "SINTETICO: Ley 348, violencia",
        True,
        ("Ana Lucia Vargas Sandoval", "Luis Fernando Ortega Rojas"),
    ),
]
