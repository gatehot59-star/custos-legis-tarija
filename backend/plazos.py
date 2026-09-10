#!/usr/bin/env python3
"""Plazos procesales bolivianos, POR MATERIA. Cero dependencias.

POR QUE ESTE ARCHIVO SE REESCRIBIO EL 2026-09-10:
La v1 arreglaba el D4 (`timedelta(days=)` donde el prompt decia habiles)
cambiando TODO a dias habiles. Medi el art. 90.II de la Ley 439 en fuente
oficial y el arreglo era incompleto: la ley pide DOS reglas, no una.

  >>> II. Los plazos transcurriran en forma ininterrumpida [...] Se exceptuan
  >>> los plazos cuya duracion no exceda de quince dias, los cuales solo se
  >>> computaran los dias habiles. En el computo de los plazos que excedan los
  >>> quince dias se computaran los dias habiles y los inhabiles.

Medido con la v1 de este propio modulo, sobre las 48 notificaciones del 1, 8,
15 y 22 de cada mes de 2026: en `traslado_demanda` (30 dias) la v1 REGALABA
HASTA 15 DIAS, y en la direccion peligrosa. Peor caso: notificacion del
2026-01-08, la v1 decia 2026-02-24 y la ley dice 2026-02-09. El abogado le cree
al sistema, presenta el 20 de febrero, y el plazo es PERENTORIO (art. 89.I).

QUE CAMBIA RESPECTO DE LA v1
  1. `materia` explicita (CIVIL / PENAL). No hay default silencioso.
  2. Umbral de 15 dias del art. 90.II para civil.
  3. Devuelve `datetime`, no `date`: la hora de vencimiento DIFIERE por materia
     (civil, cierre del juzgado, art. 90.III; penal, 24:00, art. 130).
  4. Medidas cautelares penales en dias CORRIDOS (art. 130).
  5. Vacacion judicial (art. 126 LOJ, Ley 810): SUSPENDE plazos. La v1 no la
     conocia y devolvia fechas dentro del periodo suspendido.
  6. Sin circular del Tribunal Departamental cargada, NO devuelve un numero:
     devuelve NO_MEDIDO. Un calendario inventado es peor que ningun calendario.
  7. `computo_detallado()`: el dia por dia, para que el abogado lo verifique en
     diez segundos. Un numero solo no es verificable.

QUE ES NO MEDIDO ACA, declarado arriba porque importa:
  1. LA CANTIDAD DE DIAS POR TIPO DE ACTO. Los arts. 252, 261 y 365 del CPC NO
     LOS ABRI. Cada entrada sigue en `confirmado: False`. La REGLA DE COMPUTO si
     esta confirmada por texto; la TABLA no. Son dos cosas distintas y la v1 las
     mezclaba en una sola advertencia.
  2. La hora exacta de cierre de los juzgados de Tarija (art. 90.III dice
     "ultimo momento habil del horario de funcionamiento", no una hora).
  3. Feriados departamentales de Tarija mas alla del 15 de abril.
  4. Si una medida cautelar penal en dias corridos que vence en dia inhabil se
     prorroga. Aca se prorroga, y se declara como supuesto.
  5. Ley 1173 y el buzon electronico penal: NO LEIDO. El computo penal se queda
     en el art. 130 puro.

FUENTES ABIERTAS (2026-09-10)
  Ley 439 arts. 89-91 ..... https://www.lexivox.org/norms/BO-L-N439.html
  Ley 1970 art. 130 ....... https://www.lexivox.org/norms/BO-L-1970.html
  Ley 810 (art. 126 LOJ) .. https://www.lexivox.org/norms/BO-L-N810.xhtml
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

# ---------------------------------------------------------------------------
# MATERIA. No hay default: el llamador declara, o revienta.
# ---------------------------------------------------------------------------


class Materia(str, Enum):
    CIVIL = "civil"
    PENAL = "penal"


# Estados. Tres, nunca dos.
CONFIRMADO = "CONFIRMADO"
HIPOTESIS = "HIPOTESIS"
NO_MEDIDO = "NO_MEDIDO"

# Umbral del art. 90.II Ley 439. Hasta 15 dias inclusive: solo habiles.
UMBRAL_HABILES_CIVIL = 15

# Hora de vencimiento penal: art. 130 CPP, "las veinticuatro horas".
HORA_VENCIMIENTO_PENAL = _dt.time(23, 59, 59)

# Civil: art. 90.III, "ultimo momento habil del horario de funcionamiento".
# La hora concreta es NO MEDIDA. Este default es conservador y esta declarado.
HORA_CIERRE_JUZGADO_SUPUESTA = _dt.time(18, 0, 0)

# ---------------------------------------------------------------------------
# FERIADOS NACIONALES DE BOLIVIA
# Fijos: (mes, dia). Los moviles se derivan de Pascua (Meeus/Jones/Butcher).
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
    """Feriados no laborables de un anio, con su nombre."""
    out: dict[_dt.date, str] = {}
    for mes, dia, nombre in FERIADOS_FIJOS:
        out[_dt.date(anio, mes, dia)] = nombre
    if tarija:
        for mes, dia, nombre in FERIADOS_TARIJA:
            out[_dt.date(anio, mes, dia)] = nombre
    p = pascua(anio)
    out[p - _dt.timedelta(days=48)] = "Carnaval (lunes)"
    out[p - _dt.timedelta(days=47)] = "Carnaval (martes)"
    out[p - _dt.timedelta(days=2)] = "Viernes Santo"
    out[p + _dt.timedelta(days=60)] = "Corpus Christi"
    return out


# ---------------------------------------------------------------------------
# CALENDARIO JUDICIAL
#
# Art. 126.IV LOJ (texto de la Ley 810): "Durante el periodo de vacaciones,
# todo plazo en la tramitacion de los juicios quedara suspendido y continuara
# automaticamente a la iniciacion de sus labores, debiendo establecerse con
# precision el momento de suspension y de reapertura".
#
# Esto NO es una constante anual y hay dos razones medidas:
#   a) Las fuentes publicas de la vacacion 2025-2026 se contradicen entre si
#      (unas dan hasta el 5-ene-2026, otras hasta el 2-ene-2026). Un dato de
#      produccion sale de la CIRCULAR del Tribunal Departamental, no de prensa.
#   b) Hay vacaciones EXTRAORDINARIAS: en mayo de 2026 el TDJ de La Paz declaro
#      una semana por conflictos y bloqueos, descontada de la programada.
#
# Por eso cada periodo lleva su circular, su fecha de publicacion y su
# departamento. Y por eso la ausencia de circular NO se rellena con un default.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PeriodoSuspension:
    """Un tramo en que los plazos NO corren, con su fuente citable."""

    desde: _dt.date
    hasta: _dt.date  # inclusive
    departamento: str
    circular: str
    motivo: str = "vacacion judicial"

    def contiene(self, f: _dt.date) -> bool:
        return self.desde <= f <= self.hasta


@dataclass
class CalendarioJudicial:
    """Registro de suspensiones POR DEPARTAMENTO, con cobertura explicita.

    `cobertura` declara para que (departamento, anio) hay circular cargada.
    Si el computo toca un anio sin cobertura, el resultado es NO_MEDIDO: el
    Vigilante no entrega una fecha que no puede sostener.
    """

    departamento: str = "Tarija"
    periodos: list[PeriodoSuspension] = field(default_factory=list)
    cobertura: set[int] = field(default_factory=set)

    def suspendido(self, f: _dt.date) -> PeriodoSuspension | None:
        for p in self.periodos:
            if p.departamento == self.departamento and p.contiene(f):
                return p
        return None

    def cubre(self, anio: int) -> bool:
        return anio in self.cobertura

    def registrar(self, p: PeriodoSuspension) -> None:
        self.periodos.append(p)
        for anio in range(p.desde.year, p.hasta.year + 1):
            self.cobertura.add(anio)

    def declarar_cubierto(self, anio: int) -> None:
        """Anio revisado en circular y SIN suspensiones fuera de las cargadas."""
        self.cobertura.add(anio)


# Calendario vacio a proposito. Cargarlo es una tarea con fuente, no un default.
CALENDARIO_SIN_CARGAR = CalendarioJudicial()


# ---------------------------------------------------------------------------
# DIAS
# ---------------------------------------------------------------------------


def es_habil(fecha: _dt.date, *, tarija: bool = True,
             extra: Iterable[_dt.date] = (),
             calendario: CalendarioJudicial | None = None) -> bool:
    """Habil = no fin de semana, no feriado, no suspendido, no cierre extra."""
    if fecha.weekday() >= 5:
        return False
    if fecha in feriados(fecha.year, tarija=tarija):
        return False
    if fecha in set(extra):
        return False
    if calendario is not None and calendario.suspendido(fecha) is not None:
        return False
    return True


def _marca(fecha: _dt.date, *, tarija: bool, extra: set[_dt.date],
           calendario: CalendarioJudicial | None) -> str:
    """Por que un dia no cuenta. Va al computo detallado que ve el abogado."""
    susp = calendario.suspendido(fecha) if calendario else None
    if susp is not None:
        return f"suspendido ({susp.motivo}, {susp.circular})"
    if fecha.weekday() >= 5:
        return "fin de semana"
    fer = feriados(fecha.year, tarija=tarija).get(fecha)
    if fer:
        return f"feriado: {fer}"
    if fecha in extra:
        return "cierre del juzgado"
    return "habil"


# ---------------------------------------------------------------------------
# RESULTADO
# ---------------------------------------------------------------------------


@dataclass
class Computo:
    """El resultado de un calculo, con su fundamento y su dia por dia."""

    estado: str
    vencimiento: _dt.datetime | None
    modo: str
    fundamento: str
    materia: Materia
    dias: int
    advertencias: list[str] = field(default_factory=list)
    detalle: list[dict] = field(default_factory=list)

    @property
    def confiable(self) -> bool:
        return self.estado == CONFIRMADO and self.vencimiento is not None

    def como_texto(self) -> str:
        """Para mostrarle al abogado. Nunca un numero pelado."""
        lineas = [f"[{self.estado}] materia={self.materia.value} "
                  f"plazo={self.dias} modo={self.modo}",
                  f"fundamento: {self.fundamento}"]
        if self.vencimiento:
            lineas.append(f"vence: {self.vencimiento:%Y-%m-%d %H:%M} "
                          f"({self.vencimiento:%a})")
        else:
            lineas.append("vence: NO MEDIDO, el sistema no puede sostener una fecha")
        for a in self.advertencias:
            lineas.append(f"  ADVERTENCIA: {a}")
        for d in self.detalle:
            marca = d["marca"]
            cuenta = "cuenta" if d["cuenta"] else "no cuenta"
            n = f" [{d['n']}/{self.dias}]" if d["cuenta"] else ""
            lineas.append(f"  {d['fecha']:%Y-%m-%d} {d['fecha']:%a}  "
                          f"{marca:34s} {cuenta}{n}")
        return "\n".join(lineas)


def _modo_y_fundamento(materia: Materia, dias: int,
                       medida_cautelar: bool) -> tuple[str, str]:
    """Que regla de computo aplica y con que texto se justifica."""
    if materia is Materia.PENAL:
        if medida_cautelar:
            return ("corridos",
                    "Art. 130 CPP (Ley 1970): medidas cautelares en dias corridos")
        return ("habiles",
                "Art. 130 CPP (Ley 1970): se computa solo los dias habiles, "
                "vence a las 24:00 del ultimo dia habil")
    if dias <= UMBRAL_HABILES_CIVIL:
        return ("habiles",
                f"Art. 90.II Ley 439: plazo de {dias} dias, no excede de quince, "
                "solo se computan los dias habiles")
    return ("corridos",
            f"Art. 90.II Ley 439: plazo de {dias} dias, EXCEDE de quince, "
            "se computan los dias habiles y los inhabiles")


def _hora_vencimiento(materia: Materia) -> tuple[_dt.time, str | None]:
    if materia is Materia.PENAL:
        return HORA_VENCIMIENTO_PENAL, None
    return (HORA_CIERRE_JUZGADO_SUPUESTA,
            "hora de cierre del juzgado NO MEDIDA: el art. 90.III dice 'ultimo "
            "momento habil del horario de funcionamiento'. Confirme en secretaria")


def computo_detallado(notificacion: _dt.date, dias: int, materia: Materia, *,
                      medida_cautelar: bool = False,
                      plazo_comun_ultima_notificacion: _dt.date | None = None,
                      tarija: bool = True,
                      extra: Iterable[_dt.date] = (),
                      calendario: CalendarioJudicial | None = None) -> Computo:
    """Calcula el vencimiento con la regla que corresponde a la materia.

    Dies a quo: art. 90.I Ley 439 y art. 130 CPP. El plazo arranca el dia
    SIGUIENTE. En civil, el dia siguiente HABIL. Plazos comunes: desde la
    ULTIMA notificacion (art. 90.I in fine y art. 130 in fine).
    """
    if not isinstance(materia, Materia):
        raise TypeError("materia es obligatoria: Materia.CIVIL o Materia.PENAL")

    modo, fundamento = _modo_y_fundamento(materia, dias, medida_cautelar)
    hora, aviso_hora = _hora_vencimiento(materia)
    adv: list[str] = []
    if aviso_hora:
        adv.append(aviso_hora)

    base = plazo_comun_ultima_notificacion or notificacion
    if plazo_comun_ultima_notificacion:
        adv.append("plazo comun: se computa desde la ULTIMA notificacion "
                   "(art. 90.I Ley 439 / art. 130 CPP)")

    if dias <= 0:
        return Computo(estado=CONFIRMADO,
                       vencimiento=_dt.datetime.combine(base, hora),
                       modo="sin plazo", fundamento="mero tramite, sin plazo",
                       materia=materia, dias=0, advertencias=adv)

    extra = set(extra)

    # --- COBERTURA DEL CALENDARIO -----------------------------------------
    # Ventana generosa: ningun plazo real supera un anio.
    ventana_fin = base + _dt.timedelta(days=max(dias * 3, 60))
    anios = set(range(base.year, ventana_fin.year + 1))
    if calendario is None:
        adv.append("SIN CALENDARIO JUDICIAL CARGADO: el art. 126 LOJ suspende "
                   "todo plazo durante la vacacion judicial (25 dias en "
                   "diciembre) y este calculo NO la contempla")
        sin_cobertura = sorted(anios)
    else:
        sin_cobertura = sorted(a for a in anios if not calendario.cubre(a))
        if sin_cobertura:
            adv.append("sin circular del Tribunal Departamental para "
                       + ", ".join(str(a) for a in sin_cobertura))

    # --- COMPUTO ----------------------------------------------------------
    # Art. 90.I Ley 439: el plazo corre "a partir del dia siguiente HABIL".
    # Asi que primero se busca el arranque, y ese arranque es el dia 1. Esto
    # importa cuando la notificacion cae un viernes: el sabado no es el dia 1.
    detalle: list[dict] = []
    cursor = base
    inicio: _dt.date | None = None
    for _ in range(400):
        cursor += _dt.timedelta(days=1)
        marca = _marca(cursor, tarija=tarija, extra=extra, calendario=calendario)
        if marca == "habil":
            inicio = cursor
            break
        detalle.append({"fecha": cursor, "marca": marca + "  <- antes del arranque",
                        "cuenta": False, "n": None})
    if inicio is None:
        return Computo(estado=NO_MEDIDO, vencimiento=None, modo=modo,
                       fundamento=fundamento, materia=materia, dias=dias,
                       advertencias=adv + ["no hay dia habil de arranque en 400 "
                                           "dias: revisar feriados o suspensiones"],
                       detalle=detalle)

    contados = 0
    venc: _dt.date | None = None
    cursor = inicio - _dt.timedelta(days=1)
    for _ in range(1200):
        cursor += _dt.timedelta(days=1)
        marca = _marca(cursor, tarija=tarija, extra=extra, calendario=calendario)
        habil = marca == "habil"
        suspendido = marca.startswith("suspendido")

        if modo == "habiles":
            cuenta = habil
        else:
            # Corridos: cuenta habiles E inhabiles (art. 90.II), PERO la
            # vacacion judicial SUSPENDE el plazo (art. 126.IV LOJ): esos dias
            # no lo consumen, lo pausan.
            cuenta = not suspendido

        if cuenta:
            contados += 1
        detalle.append({"fecha": cursor, "marca": marca, "cuenta": cuenta,
                        "n": contados if cuenta else None})
        if cuenta and contados == dias:
            venc = cursor
            break

    if venc is None:
        return Computo(estado=NO_MEDIDO, vencimiento=None, modo=modo,
                       fundamento=fundamento, materia=materia, dias=dias,
                       advertencias=adv + ["no se alcanzo el vencimiento en 1200 "
                                           "dias: revisar feriados o suspensiones"],
                       detalle=detalle)

    # --- PRORROGA SI EL ULTIMO DIA ES INHABIL -----------------------------
    # Civil: art. 90.III, expreso. Penal: art. 130 dice "ultimo dia HABIL
    # senalado", asi que en habiles ya cae habil por construccion; para
    # cautelares en corridos la prorroga es SUPUESTO DECLARADO.
    if not es_habil(venc, tarija=tarija, extra=extra, calendario=calendario):
        motivo = ("art. 90.III Ley 439: el ultimo dia es inhabil, el plazo queda "
                  "prorrogado al primer dia habil siguiente")
        if materia is Materia.PENAL:
            motivo = ("SUPUESTO DECLARADO (no medido): ultimo dia inhabil en "
                      "computo corrido penal, se prorroga al primer habil")
            adv.append(motivo)
        while not es_habil(venc, tarija=tarija, extra=extra, calendario=calendario):
            venc += _dt.timedelta(days=1)
            detalle.append({"fecha": venc,
                            "marca": _marca(venc, tarija=tarija, extra=extra,
                                            calendario=calendario),
                            "cuenta": False, "n": None})
        detalle[-1]["marca"] += "  <- PRORROGA (art. 90.III)"
        if materia is Materia.CIVIL:
            adv.append(motivo)

    estado = NO_MEDIDO if sin_cobertura else CONFIRMADO
    if estado is NO_MEDIDO:
        adv.append("VENCIMIENTO NO CONFIRMADO: falta calendario judicial. "
                   "La fecha de abajo es orientativa y NO debe usarse para "
                   "decidir la presentacion de un escrito")

    return Computo(estado=estado, vencimiento=_dt.datetime.combine(venc, hora),
                   modo=modo, fundamento=fundamento, materia=materia, dias=dias,
                   advertencias=adv, detalle=detalle)


def vencimiento(notificacion: _dt.date, dias: int, materia: Materia, **kw
                ) -> _dt.datetime | None:
    """Atajo. Devuelve None si el computo no es confiable, NUNCA una fecha muda."""
    c = computo_detallado(notificacion, dias, materia, **kw)
    return c.vencimiento if c.confiable else None


def habiles_restantes(desde: _dt.date, hasta: _dt.date, *, tarija: bool = True,
                      calendario: CalendarioJudicial | None = None) -> int:
    """Dias habiles que quedan. Negativo si ya vencio."""
    if hasta < desde:
        return -habiles_restantes(hasta, desde, tarija=tarija,
                                  calendario=calendario)
    n = 0
    cursor = desde
    while cursor < hasta:
        cursor += _dt.timedelta(days=1)
        if es_habil(cursor, tarija=tarija, calendario=calendario):
            n += 1
    return n


# ---------------------------------------------------------------------------
# TABLA DE PLAZOS - LA CANTIDAD DE DIAS SIGUE SIENDO HIPOTESIS
#
# La REGLA DE COMPUTO esta confirmada por texto (art. 90 Ley 439, art. 130 CPP).
# LA TABLA NO: los arts. 252, 261 y 365 no fueron abiertos. Son dos cosas
# distintas y la v1 las mezclaba en una sola advertencia.
# ---------------------------------------------------------------------------
PLAZOS: dict[str, dict] = {
    "auto_interlocutorio": {
        "dias": 3, "materia": Materia.CIVIL,
        "fundamento": "Art. 252 CPC (Ley 439)", "confirmado": False},
    "auto_definitivo": {
        "dias": 10, "materia": Materia.CIVIL,
        "fundamento": "Art. 261 CPC (Ley 439)", "confirmado": False},
    "sentencia_apelacion": {
        "dias": 10, "materia": Materia.CIVIL,
        "fundamento": "apelacion de sentencia", "confirmado": False},
    "casacion": {
        "dias": 10, "materia": Materia.CIVIL,
        "fundamento": "recurso de casacion", "confirmado": False},
    "traslado_demanda": {
        "dias": 30, "materia": Materia.CIVIL,
        "fundamento": "Art. 365 CPC (Ley 439). EXCEDE 15 dias: corridos",
        "confirmado": False},
    "contestacion_excepcion": {
        "dias": 5, "materia": Materia.CIVIL,
        "fundamento": "contestacion de excepcion", "confirmado": False},
    "decreto_mero_tramite": {
        "dias": 0, "materia": Materia.CIVIL,
        "fundamento": "sin plazo: mero tramite", "confirmado": False},
    "apelacion_incidental_penal": {
        "dias": 3, "materia": Materia.PENAL,
        "fundamento": "apelacion incidental, art. 130 CPP para el computo",
        "confirmado": False},
    "medida_cautelar_penal": {
        "dias": 3, "materia": Materia.PENAL, "medida_cautelar": True,
        "fundamento": "Art. 130 CPP: medidas cautelares en dias CORRIDOS",
        "confirmado": False},
}


def plazo_de(tipo: str) -> dict:
    """Devuelve el plazo con su etiqueta. Nunca inventa."""
    if tipo not in PLAZOS:
        return {"dias": None, "materia": None, "fundamento": "tipo no reconocido",
                "confirmado": False, "estado": NO_MEDIDO}
    d = dict(PLAZOS[tipo])
    d.setdefault("medida_cautelar", False)
    d["estado"] = CONFIRMADO if d["confirmado"] else HIPOTESIS
    return d


def urgencia(dias_restantes: int) -> str:
    if dias_restantes < 0:
        return "vencido"
    if dias_restantes <= 2:
        return "critico"
    if dias_restantes <= 5:
        return "alto"
    return "normal"
