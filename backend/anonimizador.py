#!/usr/bin/env python3
"""Compuerta de publicacion del corpus. Solo stdlib.

--------------------------------------------------------------------------------
EL PROBLEMA MEDIDO QUE ESTE ARCHIVO ATACA
--------------------------------------------------------------------------------
El 10-sep-2026 se midio que `q=Mamani` en el buscador PUBLICO SIN LOGIN devolvia
1.232 pasajes, y el primero nombraba a las dos partes de una causa de violacion
de un menor. Es el bloqueador #1 del proyecto.

--------------------------------------------------------------------------------
POR QUE ESTO NO ES "UN ANONIMIZADOR"
--------------------------------------------------------------------------------
Un anonimizador borra lo que reconoce **y deja lo que no reconoce**. Es
FAIL-OPEN: si el detector falla, el nombre se publica. En una causa de NNA o de
violencia, una sola omision es la violacion que el producto vino a evitar.

Asi que la pieza central NO es el detector: es la COMPUERTA, y es fail-closed.

  1. La capa publica NO publica texto libre de jurisprudencia por defecto.
  2. Reparte por NATURALEZA del documento, no por confianza en un detector:
       - NORMATIVO (ley, decreto, resolucion ministerial, gaceta): no tiene
         partes por naturaleza. Publico.
       - JURISPRUDENCIAL (sentencia, auto supremo, auto de vista, SCP): tiene
         partes por naturaleza. Pasa por la compuerta.
  3. Materias de RESERVA LEGAL (NNA, violencia, familia con menores): NO se
     publican, ni anonimizadas. No hay compuerta que las habilite.
  4. Si la compuerta encuentra UN candidato que no puede clasificar, RETIENE el
     documento. No lo publica "mejorado".

Eso conserva el valor del corpus (las normas, que son la mayoria y las que se
vcitan) sin apostar a que un regex entienda apellidos bolivianos.

--------------------------------------------------------------------------------
LA CATEGORIA IMPORTA (E-01) Y AQUI SE PAGA CARO
--------------------------------------------------------------------------------
No todo nombre propio en una resolucion es un dato a proteger:

  - "Magistrado Relator: Dr. Carlos Alberto Eguez Anez" es un acto publico de
    una autoridad en ejercicio. Borrarlo destruye la trazabilidad de la cita.
  - "la denuncia presentada por Maria Elena Choque Villca" es una parte.
  - "Editorial Amanecer S.A." es una persona JURIDICA: no la protege el art.
    21.2 CPE, que habla de "las bolivianas y los bolivianos".

Un anonimizador que trata a los tres igual arruina el producto en un caso y no
protege nada en el otro. Por eso hay clasificacion por ROL, no solo deteccion.

--------------------------------------------------------------------------------
QUE ES NO MEDIDO, y es mucho
--------------------------------------------------------------------------------
  1. RECALL CONTRA EL CORPUS REAL. Intente correr el endpoint del corpus el
     2026-09-10 y NO RESPONDIO. Todo lo medido aca es contra 9 fixtures, 6
     reales y 3 sinteticos. Es un piso, no un veredicto.
  2. INDEPENDENCIA (W-01). Escribi el detector Y elegi los fixtures. Los 6
     reales reducen el problema, no lo eliminan. La medicion que vale es
     contra el corpus, y con un tercero eligiendo la muestra.
  3. La lista de encabezados institucionales sale de los documentos que vi. Un
     "Conjuez", un "Secretario de Camara" o una forma de Tarija que no vi van a
     caer como no clasificados, y eso RETIENE el documento. Falso negativo de
     publicacion, no fuga: el error va del lado seguro a proposito.
  4. Nombres en una sola palabra ("contra Mamani") no se detectan como parte:
     el detector pide 2 tokens. Declarado abajo y con test que lo demuestra.
  5. Los arts. de la Ley 548 (NNA) y 348 (violencia) que fundan la reserva NO
     los lei. La reserva esta puesta por prudencia, no por texto medido.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# CLASES DE DOCUMENTO
# ---------------------------------------------------------------------------


class Clase(str, Enum):
    NORMATIVO = "normativo"          # ley, decreto, gaceta: sin partes
    JURISPRUDENCIAL = "jurisprudencial"  # sentencia, AS, AV, SCP: con partes
    DESCONOCIDO = "desconocido"      # ni una ni otra: se retiene


class Decision(str, Enum):
    PUBLICO = "publico"
    RETENIDO = "retenido"
    RESERVA_LEGAL = "reserva_legal"


# ---------------------------------------------------------------------------
# RESERVA LEGAL. No hay compuerta que la habilite.
# NO MEDIDO: los articulos exactos de la Ley 548 y la Ley 348. Prudencia.
# ---------------------------------------------------------------------------
MATERIAS_RESERVA = frozenset({"familiar", "familia", "ninez_adolescencia", "nna"})

# Disparadores de reserva en el TEXTO, no en la etiqueta de materia. Un penal
# etiquetado "penal" puede ser una causa de NNA y la etiqueta no lo dice.
DISPARADORES_RESERVA: tuple[tuple[str, str], ...] = (
    (r"\bmenor(?:es)?\b", "menciona a un menor"),
    (r"\badolescente", "menciona a un adolescente"),
    (r"\binfante\b", "menciona a un infante"),
    (r"\bnina\b|\bnino\b", "menciona a nina o nino"),
    (r"\bNNA\b", "NNA"),
    (r"\bviolacion\b", "delito contra la libertad sexual"),
    (r"\bviolencia\s+(?:familiar|domestica|intrafamiliar|contra\s+la\s+mujer)",
     "violencia (Ley 348)"),
    (r"\bfeminicidio\b", "feminicidio"),
    (r"\babuso\s+sexual\b", "abuso sexual"),
    (r"\bestupro\b", "estupro"),
    (r"\btrata\s+(?:y\s+trafico|de\s+personas)", "trata y trafico"),
    (r"\bmedidas\s+de\s+proteccion\b", "medidas de proteccion"),
    (r"\bagresor\b", "agresor identificado"),
    (r"\bvictima\b", "victima identificada"),
    (r"\btutela\b", "tutela"),
    (r"\bfiliacion\b", "filiacion"),
    (r"\basistencia\s+familiar\b", "asistencia familiar"),
)

# ---------------------------------------------------------------------------
# NATURALEZA DEL DOCUMENTO
# ---------------------------------------------------------------------------
# FUERTES: solo aparecen en el cuerpo de una norma. Establecen la clase.
SENAS_NORMATIVO_FUERTES: tuple[str, ...] = (
    r"\bLEY\s+N[o\u00b0\.\s]*\d", r"\bDECRETO\s+SUPREMO\b",
    r"\bRESOLUCION\s+MINISTERIAL\b", r"\bGACETA\s+OFICIAL\b",
    r"\bLA\s+ASAMBLEA\s+LEGISLATIVA\s+PLURINACIONAL\b",
    r"\bEN\s+CONSEJO\s+DE\s+MINISTROS\b",
    r"\bDECRETA\s*:", r"\bPROMULGA\b", r"\bPor\s+cuanto,\s+la\s+Asamblea",
    r"\bha\s+sancionado\s+la\s+siguiente\s+Ley\b",
)
# DEBILES: NO establecen nada. La jurisprudencia cita articulos todo el tiempo.
#
# ESTO ES UN DEFECTO QUE ENCONTRE MIDIENDO, no una precaucion teorica: la v1
# tenia `ARTICULO \d+` y `CODIGO` entre las senas normativas, y con eso
# clasifico un fragmento de la SCP 0693/2023-S4 como NORMATIVO. Como los
# normativos se publican sin compuerta, esa Sentencia Constitucional habria
# salido a la capa publica por citar el art. 130 del CPP.
SENAS_NORMATIVO_DEBILES: tuple[str, ...] = (
    r"\bCODIGO\b", r"\bARTICULO\s+\d+", r"\bART\.\s*\d+", r"\bart\.\s*\d+",
)
SENAS_JURISPRUDENCIAL: tuple[str, ...] = (
    r"\bAUTO\s+SUPREMO\b", r"\bAUTO\s+DE\s+VISTA\b", r"\bSENTENCIA\b",
    r"\bSENTENCIA\s+CONSTITUCIONAL\b", r"\bSCP\b", r"\bAS/\d",
    r"\bVISTOS\b", r"\bPOR\s+TANTO\b", r"\bexpediente\b", r"\bdemandante\b",
    r"\bdemandado\b", r"\bimputado\b", r"\baccionante\b", r"\brecurrente\b",
    r"\bSALA\s+(?:CIVIL|PENAL|SOCIAL|CONTENCIOSA|CONSTITUCIONAL)",
    r"\bMagistrado\s+Relator\b", r"\bResolucion\s+de\s+Sala\s+Plena\b",
    r"\bDistrito:", r"\bdenuncia\b", r"\bse\s+declara\b",
)

# ---------------------------------------------------------------------------
# ROLES. Lo que precede a un nombre dice de que categoria es.
# ---------------------------------------------------------------------------
# Autoridad en ejercicio: acto publico, NO se tapa (destruiria la cita).
ROL_INSTITUCIONAL: tuple[str, ...] = (
    r"Magistrad[oa]\s+Relator[a]?\s*:?", r"Magistrad[oa]s?", r"Vocal(?:es)?",
    r"Juez[a]?", r"Juec(?:es|as)", r"Secretari[oa]", r"Conjuez",
    r"Presidente(?:\s+del\s+\w+)*", r"Decan[oa]", r"Fiscal",
    r"Fdo\.", r"Dr[a]?\.", r"MSc\.", r"Lic\.", r"Abg\.",
)
# Parte o interviniente: se protege.
ROL_PARTE: tuple[str, ...] = (
    r"contra", r"c/", r"demandante", r"demandad[oa]", r"actor[a]?",
    r"imputad[oa]", r"acusad[oa]", r"procesad[oa]", r"sentenciad[oa]",
    r"victima", r"agresor[a]?", r"denunciante", r"denunciad[oa]",
    r"querellante", r"accionante", r"recurrente", r"tercer[oa]\s+interesad[oa]",
    r"testigo", r"presentada\s+por", r"interpuesta\s+por", r"a\s+favor\s+de",
    r"en\s+representacion\s+de", r"heredero[as]?", r"causante", r"acreedor[a]?",
    r"deudor[a]?", r"beneficiari[oa]",
    # Formas verbales completas. La v1 solo tenia "interpuesta por" y por eso
    # "recurso interpuestO por Maria Elena..." caia como no_clasificado: la
    # concordancia de genero del participio rompia el patron.
    r"interpuest[oa]\s+por", r"present(?:ada|ado)\s+por",
    r"planteada?\s+por", r"formulada?\s+por", r"deducida?\s+por",
    r"seguido\s+por", r"iniciad[oa]\s+por", r"suscrit[oa]\s+por",
    r"en\s+contra\s+de", r"sr[a]?\.", r"senor[a]?", r"ciudadan[oa]",
)
# Persona juridica: el art. 21.2 CPE habla de personas naturales.
SUFIJOS_JURIDICA: tuple[str, ...] = (
    r"S\.A\.", r"S\.R\.L\.", r"SRL", r"LTDA\.?", r"S\.A\.F\.I\.",
    r"Sociedad", r"Empresa", r"Cooperativa", r"Fundacion", r"Asociacion",
    r"Banco", r"Editorial", r"Comunicaciones", r"Ministerio", r"Tribunal",
    r"Gobierno", r"Municipal", r"Universidad", r"Consejo", r"Corporacion",
)

# Palabras que empiezan con mayuscula y NO son nombres de persona. Sin esto el
# detector marca "Sala Civil" o "Codigo Civil" como si fueran personas.
STOP_MAYUSCULA = frozenset("""
Auto Autos Supremo Suprema Sentencia Sentencias Constitucional Plurinacional
Sala Salas Civil Comercial Penal Social Administrativa Contenciosa Familiar
Tribunal Tribunales Departamental Departamentales Justicia Supremo Agroambiental
Magistrado Magistrada Magistrados Vocal Vocales Juez Jueza Jueces Secretario
Secretaria Presidente Presidenta Decana Decano Fiscal Ministerio Publico Estado
Codigo Ley Leyes Decreto Supremo Gaceta Oficial Constitucion Politica Republica
Bolivia Boliviano Boliviana Bolivianos Tarija Sucre Potosi Oruro Paz Cruz Beni
Pando Cochabamba Chuquisaca Santa Yacuiba Bermejo Villamontes Padcaya Uriondo
Lorenzo Roque Distrito Expediente Resolucion Resoluciones Plena Considerando
Considerandos Vistos Tanto Fundamento Juridico Articulo Art Numeral Paragrafo
Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Setiembre Octubre
Noviembre Diciembre Lunes Martes Miercoles Jueves Viernes Sabado Domingo
Sin Con Por Para Que Los Las Del Una Uno Este Esta Esto Ese Esa Aquel Segun
Asimismo Ahora Bien Empero Sin Embargo Consiguientemente Consecuencia Efecto
Carnaval Santo Corpus Christi Navidad Ano Nuevo Aymara Amazonico Independencia
Todos Santos Trabajo Difuntos Tablada Batalla Vacacion Judicial Colectiva
Anual Calendario Habil Habiles Inhabil Inhabiles Plazo Plazos Termino Terminos
Nurej WebID SIREJ SIGC Eforo Ciudadania Digital Organo Judicial Magistratura
Cuando Como Donde Porque Pero Aunque Mientras Desde Hasta Entre Sobre Bajo
Confirma Revoca Anula Declara Probada Improbada Resuelve Dispone Ordena
Notifiquese Registrese Cumplase Deliberacion Relator Ponente Voto Disidente
Recurso Recursos Apelacion Casacion Amparo Habeas Data Accion Libertad
Cumplimiento Popular Inconstitucionalidad Interlocutorio Definitivo Providencia
Trata Trafico Personas Delito Delitos Libertad Sexual Violencia Familiar
Proteccion Medidas Victima Agresor Menor Menores Nina Nino Adolescente Infante
Bs USD NIT CI Zona Calle Avenida Barrio Domicilio Domiciliada Domiciliado
""".split())

_MAY = r"[A-ZÁÉÍÓÚÑÜ]"
_MIN = r"[a-záéíóúñü]"
# Un candidato: 2 a 5 tokens capitalizados seguidos. Acepta MAYUSCULA TOTAL
# porque los memoriales bolivianos escriben las partes asi.
RE_CANDIDATO = re.compile(
    rf"\b(?:{_MAY}{_MIN}+|{_MAY}{{2,}})(?:\s+(?:de|del|la|las|los|y)\s+|\s+)"
    rf"(?:(?:{_MAY}{_MIN}+|{_MAY}{{2,}})(?:\s+(?:de|del|la|las|los|y)\s+|\s+)?)"
    rf"{{1,4}}"
)
# Iniciales tipo K.M.CH. o A.L.: la fuente ya las publica asi, no son un dato
# a proteger, pero SI son senal de que la causa tiene reserva.
RE_INICIALES = re.compile(r"\b(?:[A-ZÑ]\.){2,}(?:[A-ZÑ]{1,3}\.)?")


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _norm_tok(t: str) -> str:
    return _sin_tildes(t).strip(".,;:()").lower()


STOP_NORM = frozenset(_norm_tok(w) for w in STOP_MAYUSCULA)


@dataclass
class Candidato:
    texto: str
    inicio: int
    fin: int
    rol: str  # institucional | parte | juridica | no_clasificado
    contexto: str


@dataclass
class Veredicto:
    decision: Decision
    clase: Clase
    motivos: list[str] = field(default_factory=list)
    candidatos: list[Candidato] = field(default_factory=list)
    texto_publicable: str | None = None

    @property
    def publicable(self) -> bool:
        return self.decision is Decision.PUBLICO

    def como_texto(self) -> str:
        out = [f"[{self.decision.value.upper()}] clase={self.clase.value}"]
        for m in self.motivos:
            out.append(f"  motivo: {m}")
        for c in self.candidatos:
            out.append(f"  candidato {c.rol:16s} {c.texto!r}")
        return "\n".join(out)


def clasificar(texto: str, tipo_declarado: str | None = None
               ) -> tuple[Clase, list[str]]:
    """Naturaleza del documento.

    REGLA 1: si el corpus DECLARA el tipo, se le cree al corpus. Adivinar por
    texto lo que un metadato ya dice es reemplazar un dato por una heuristica.
    REGLA 2: jurisprudencial gana. Si hay senal de las dos, se trata como el
    caso peligroso.
    REGLA 3: solo las senas normativas FUERTES establecen la clase. Citar un
    articulo no convierte un fallo en una ley.
    """
    if tipo_declarado:
        td = _sin_tildes(tipo_declarado).lower()
        if any(k in td for k in ("ley", "decreto", "resolucion ministerial",
                                 "gaceta", "codigo", "reglamento")):
            return Clase.NORMATIVO, [f"tipo declarado por el corpus: {tipo_declarado}"]
        if any(k in td for k in ("sentencia", "auto", "scp", "as", "sala",
                                 "jurisprudencia", "acuerdo")):
            return Clase.JURISPRUDENCIAL, [
                f"tipo declarado por el corpus: {tipo_declarado}"]
        return Clase.DESCONOCIDO, [
            f"tipo declarado '{tipo_declarado}' no reconocido: no se adivina"]

    t = _sin_tildes(texto)
    jur = [p for p in SENAS_JURISPRUDENCIAL if re.search(p, t, re.I)]
    fuertes = [p for p in SENAS_NORMATIVO_FUERTES if re.search(p, t, re.I)]
    debiles = [p for p in SENAS_NORMATIVO_DEBILES if re.search(p, t, re.I)]
    if jur:
        return Clase.JURISPRUDENCIAL, [f"{len(jur)} senas jurisprudenciales"]
    if fuertes:
        return Clase.NORMATIVO, [f"{len(fuertes)} senas normativas FUERTES"]
    if debiles:
        return Clase.DESCONOCIDO, [
            f"{len(debiles)} senas normativas DEBILES (cita de articulos) y "
            "ninguna fuerte: citar una norma no convierte al documento en norma"]
    return Clase.DESCONOCIDO, ["sin senas de ninguna clase"]


def reserva_legal(texto: str, materia: str | None = None) -> list[str]:
    """Motivos de reserva. Si devuelve algo, NO se publica ni anonimizado."""
    motivos = []
    if materia and _sin_tildes(materia).lower() in MATERIAS_RESERVA:
        motivos.append(f"materia de reserva: {materia}")
    t = _sin_tildes(texto)
    for patron, razon in DISPARADORES_RESERVA:
        if re.search(patron, t, re.I):
            motivos.append(f"disparador: {razon}")
    return motivos


def _rol_de(texto_previo: str, nombre: str) -> str:
    prev = _sin_tildes(texto_previo)[-60:]
    nom = _sin_tildes(nombre)
    for p in SUFIJOS_JURIDICA:
        if re.search(p, nom, re.I):
            return "juridica"
    for p in ROL_INSTITUCIONAL:
        if re.search(p + r"\s*$", prev, re.I):
            return "institucional"
    for p in ROL_PARTE:
        if re.search(r"\b" + p + r"\s*$", prev, re.I):
            return "parte"
    return "no_clasificado"


def candidatos(texto: str) -> list[Candidato]:
    """Nombres propios candidatos, con su rol. NO garantiza recall: ver el
    docstring del modulo, punto 1 de NO MEDIDO."""
    out: list[Candidato] = []
    for m in RE_CANDIDATO.finditer(texto):
        bruto = m.group(0).strip(" ,.;:")
        toks = [t for t in re.split(r"\s+", bruto)
                if t.lower() not in ("de", "del", "la", "las", "los", "y")]
        if len(toks) < 2:
            continue
        # Si TODOS los tokens estan en la stoplist, no es un nombre de persona.
        # Comparacion SIN CASO: los memoriales escriben "SALA CONTENCIOSA" en
        # mayuscula total y "Sala Contenciosa" en el encabezado. La v1 comparaba
        # con caso y por eso "SALA CONTENCIOSA" salia como nombre de persona.
        if all(_norm_tok(t) in STOP_NORM for t in toks):
            continue
        # Si el PRIMER token es de la stoplist, el candidato arranca en una
        # palabra institucional: se recorta y se reevalua el resto.
        while toks and _norm_tok(toks[0]) in STOP_NORM:
            toks = toks[1:]
        while toks and _norm_tok(toks[-1]) in STOP_NORM:
            toks = toks[:-1]
        if len(toks) < 2:
            continue
        nombre = " ".join(toks)
        # El span se recalcula sobre los tokens que QUEDARON. La v1 usaba
        # m.start()/m.end() y el reemplazo se comia el espacio siguiente:
        # "[PARTE-X]contra". Un seudonimo que pega dos palabras es un bug de
        # legibilidad hoy y un bug de busqueda manana.
        ini = texto.find(toks[0], m.start(), m.end())
        fin = texto.find(toks[-1], ini) + len(toks[-1])
        if ini < 0 or fin <= ini:
            ini, fin = m.start(), m.end()
        rol = _rol_de(texto[:ini], nombre)
        out.append(Candidato(texto=nombre, inicio=ini, fin=fin,
                             rol=rol, contexto=texto[max(0, ini - 40):
                                                     ini].strip()))
    return out


def seudonimo(nombre: str, sal: str = "custos-legis") -> str:
    """Reemplazo ESTABLE: el mismo nombre da la misma etiqueta en todo el corpus.

    Se usa hash con sal, no las iniciales: las iniciales reidentifican en un
    juzgado chico. La sal NO se publica.
    """
    h = hashlib.sha256((sal + "|" + _sin_tildes(nombre).lower()).encode()).hexdigest()
    return f"[PARTE-{h[:8].upper()}]"


def evaluar(texto: str, materia: str | None = None, *,
            tipo_declarado: str | None = None,
            aprobado_por_matricula: str | None = None) -> Veredicto:
    """LA COMPUERTA. Fail-closed: la duda RETIENE.

    Orden de decision, y el orden importa:
      1. Reserva legal -> RESERVA_LEGAL. Ni anonimizado.
      2. Clase desconocida -> RETENIDO.
      3. NORMATIVO -> PUBLICO, pero si aparece un candidato de rol `parte` se
         RETIENE igual: una ley con una parte adentro es OCR sangrado o un anexo
         con nombres, y en los dos casos hay que mirarlo a mano.
      4. JURISPRUDENCIAL -> la capa publica NO muestra su texto. Metadatos, cita
         y enlace oficial. El extracto seudonimizado existe, pero SOLO si un
         abogado con matricula lo aprueba documento por documento.

    POR QUE EL EXTRACTO NO ES EL DEFAULT, y esto lo MEDI en vez de suponerlo:
    corri cuatro textos adversarios contra el detector (un apellido solo,
    nombre en minuscula por OCR, nombre abreviado "R. Villca T.", apellido en
    mayuscula suelta). **Se fugaron los cuatro de cuatro**: el detector no los
    vio, el gate no tuvo nada que retener, y el nombre habria salido publicado.

    Un detector que no ve un nombre no puede protegerlo. Por eso el control
    real NO es el detector: es que la capa publica no muestre texto libre de
    jurisprudencia. Con eso la superficie de fuga es CERO por construccion, y no
    depende de que un regex entienda apellidos bolivianos.
    """
    res = reserva_legal(texto, materia)
    clase, motivos_clase = clasificar(texto, tipo_declarado)
    cands = candidatos(texto)

    if res:
        return Veredicto(decision=Decision.RESERVA_LEGAL, clase=clase,
                         motivos=res + motivos_clase, candidatos=cands)

    if clase is Clase.DESCONOCIDO:
        return Veredicto(decision=Decision.RETENIDO, clase=clase,
                         motivos=motivos_clase +
                         ["clase desconocida: no se publica lo que no se sabe "
                          "que es"],
                         candidatos=cands)

    if clase is Clase.NORMATIVO:
        partes = [c for c in cands if c.rol == "parte"]
        if partes:
            return Veredicto(
                decision=Decision.RETENIDO, clase=clase,
                motivos=motivos_clase +
                [f"documento normativo con {len(partes)} nombre(s) en rol de "
                 "parte: revisar a mano (OCR sangrado o anexo con nombres)"],
                candidatos=cands)
        return Veredicto(decision=Decision.PUBLICO, clase=clase,
                         motivos=motivos_clase +
                         ["normativo: no tiene partes por naturaleza"],
                         candidatos=cands, texto_publicable=texto)

    # JURISPRUDENCIAL
    sin_clasificar = [c for c in cands if c.rol == "no_clasificado"]
    if sin_clasificar:
        return Veredicto(
            decision=Decision.RETENIDO, clase=clase,
            motivos=motivos_clase +
            [f"{len(sin_clasificar)} nombre(s) que no pude clasificar: "
             + ", ".join(repr(c.texto) for c in sin_clasificar[:3])
             + ". La duda retiene, no publica"],
            candidatos=cands)

    if not aprobado_por_matricula:
        return Veredicto(
            decision=Decision.RETENIDO, clase=clase,
            motivos=motivos_clase +
            ["la capa publica NO muestra texto de jurisprudencia: metadatos, "
             "cita y enlace oficial. El extracto seudonimizado requiere "
             "aprobacion de un abogado con matricula (Ley 387 art. 6). "
             "MEDIDO: 4 de 4 textos adversarios se fugaron del detector, asi "
             "que el detector no puede ser el control"],
            candidatos=cands)

    fuera = texto
    for c in sorted([c for c in cands if c.rol == "parte"],
                    key=lambda c: -c.inicio):
        fuera = fuera[:c.inicio] + seudonimo(c.texto) + fuera[c.fin:]
    return Veredicto(
        decision=Decision.PUBLICO, clase=clase,
        motivos=motivos_clase +
        [f"{sum(1 for c in cands if c.rol == 'parte')} parte(s) "
         "seudonimizada(s); autoridades e instituciones intactas",
         f"extracto aprobado por matricula {aprobado_por_matricula}: la "
         "responsabilidad de que no quede un nombre suelto es de quien aprueba, "
         "no del detector"],
        candidatos=cands, texto_publicable=fuera)


def ficha_publica(meta: dict) -> dict:
    """Lo que la capa publica SI muestra de un documento jurisprudencial.

    Sin texto libre. Con esto el corpus publico sigue sirviendo para lo que un
    abogado necesita (encontrar el fallo y abrirlo en la fuente oficial) sin
    apostar a un detector de nombres.
    """
    permitidos = ("uid", "tipo_norma", "numero", "anio", "fecha", "sala",
                  "organo", "materia", "fuente_url", "sha256", "vigencia")
    ficha = {k: meta.get(k) for k in permitidos}
    ficha["texto"] = None
    ficha["nota"] = ("texto no publicado en la capa abierta: contiene nombres de "
                     "partes. Abrir en fuente_url o acceder con login")
    return ficha


if __name__ == "__main__":
    import fixtures_reales as F
    for texto, materia, proc, sint, esperados in F.FIXTURES:
        v = evaluar(texto, materia)
        tag = "SINTETICO" if sint else "REAL"
        print(f"\n=== [{tag}] {proc}")
        print(v.como_texto())
