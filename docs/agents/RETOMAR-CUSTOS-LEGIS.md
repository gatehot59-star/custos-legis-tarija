# RETOMAR CUSTOS LEGIS · contexto completo para otra instancia

**Escrito:** 2026-09-26 (madrugada) · **Autor:** BRAIN · **Para:** quien retome
Custos Legis en una instancia nueva, sin memoria de esta conversación.

> **Leé esto primero, después `ESTADO.md`, después `PENDIENTES.md`.**
> Los tres son la verdad medida. El README y los ADRs son la intención.
> Donde difieran, ganan los tres primeros.

---

## 1 · Qué es Custos Legis, en dos frases

SaaS multi-inquilino para bufetes de Tarija: vigila plazos judiciales, arma la
estrategia y redacta el memorial, **con el abogado aprobando siempre al final**
(gate HITL por matrícula sobre el sha256 exacto del contenido). Es la segunda
parte de la suite: **consume** `corpus-legal-tarija` (producto independiente) y
**no** lo contiene. ADR-001 fija la frontera: el corpus se usa solo por su
contrato HTTP; multi-tenancy, expedientes privados y plazos viven acá, nunca
en el corpus.

---

## 2 · Entorno y capacidades (medido, no asumido)

### Máquinas disponibles

| Máquina | Qué es | Estado |
|---|---|---|
| **VM Abacus** (`corpus-tarija.abacusai.cloud`) | x86_64, **2 núcleos**, 6,3 GB RAM libre de 8, **sin swap**, 35 GB disco libre de 48, `/dev/kvm` usable (API 12), docker presente | VIVA: sirve el corpus en producción endurecida |
| **build container** (gateway `build`) | shell aislado, `/workspace` escribible, sin acceso al home del host | VIVO |
| **playwright** (gateway) | navegador real para verificación en vivo | VIVO |
| **brain-env / Actions** | GitHub Actions gratis en repo público, x64/arm64 | VIVO |
| **Kaggle** | GPU disponible | disponible, no usado aún |

Acceso a la VM: gateway `build` → `/workspace/bin/vm-corpus.sh '<comando>'`.
`sudo -n` funciona para systemctl y lectura de `/etc`.

### Servicios corriendo en la VM (medido 2026-09-26)

- `corpus-django-staging.service`: gunicorn 127.0.0.1:8001, **producción
  endurecida** (sin synthetic), usuarios activos solo `luz` y `abraham`.
- `corpus-api.service`: API vieja python3, **ya en 127.0.0.1:8080** (loopback,
  riesgo Fable §9.11 mitigado).
- nginx :80/:443, cloudflared-corpus (tunnel SSH).
- **Custos Legis NO está desplegado.** No hay Postgres corriendo para él en la
  VM todavía.

### Advertencia de capacidad (medida en README §2)

El diseño fuente pedía PostgreSQL + Redis + Qdrant + Celery + FastAPI sobre los
**2 núcleos compartidos con el corpus que el bufete usa**. Eso es una colisión
anunciada. Decisión pendiente: VM separada para Custos (recomendada) vs todo en
la misma. **NO MEDIDO:** costo/hora de una VM Abacus y cuánto degrada el
buscador un stack de agentes en 2 núcleos. Medir antes de elegir.

### Inventario canónico

`00-ENTORNOS-Y-CAPACIDADES.md` en `gatehot59-star/mudh-mobile` (se **linkea**,
no se copia). Antes de declarar "no puedo", medir de nuevo: el inventario se
re-mide, no se recuerda.

---

## 3 · Estado REAL del proyecto (leído del código, 2026-09-26)

**El diseño declaraba FASE 1-5 ✅ sin código. La verdad medida es otra y está en
`ESTADO.md`. Lo que SÍ existe y corre (verde en CI):**

| Pieza | Archivo | Estado | Evidencia |
|---|---|---|---|
| Compuerta de publicación (privacidad) | `backend/anonimizador.py` | 53/53 | test_anonimizador.py |
| Motor de plazos por materia (Ley 439 art. 90, CPP art. 130) | `backend/plazos.py` | 71/71 | test_plazos.py |
| Calendario judicial por departamento | `backend/calendario_judicial.py` | 36/36 | test_calendario.py |
| Esquema Postgres con RLS forzado (5 tablas) | `infra/init.sql` | 16/16 | test_rls.py contra PostgreSQL 16 real |
| API HTTP stdlib con gate HITL | `backend/api.py` | corre | api-e2e.yml verde |
| Cliente del corpus (3 estados de vigencia) | `backend/corpus_cliente.py` | existe | lee el contrato del corpus |
| 18 falsadores que DAN ROJO | varios | activos | workflow tests.yml #20 passing |

**Total: 176 aserciones verdes + 18 falsadores. Cero abogados que lo hayan
usado.**

**Lo que NO existe (declarado en ESTADO §6, no confundir con "fase verde"):**

- Los 6 agentes / grafo LangGraph: **NO EXISTE**.
- FastAPI formal: **NO EXISTE** (la API es stdlib `ThreadingHTTPServer`).
- La compuerta CABLEADA en el buscador del corpus: **NO** (vive acá, no en
  corpus-legal-tarija).
- Scraper judicial, Qdrant, facturación, despliegue en Abacus: **NO EXISTE**.
- Corpus municipal de Tarija, decretos departamentales, TCP incorporado:
  **NO EXISTE** (huecos del corpus, no de este repo).

### Decisiones clave ya tomadas (no rediscutir sin motivo)

- **ADR-001:** frontera corpus/Custos. El corpus es independiente y vendible.
- **Tres estados de vigencia** (VIGENTE/DEROGADA/NO_MEDIDO) con advertencia
  obligatoria en la cita. Nunca "vigente" hardcodeado (D2 de Fable).
- **Gate HITL:** ninguna acción externa sale sin aprobación por matrícula
  sobre el sha256 exacto, y la ÚLTIMA decisión manda (rechazo revoca).
- **Sesiones sin degradación de tenant:** sin tenant, SinTenant, no WHERE
  ampliado.
- **Sensor de uso con q_hash**, no el texto de la búsqueda jurídica.
- **Loopback por defecto** en la API (lección del 0.0.0.0 del corpus).
- **Fail-fast:** la API no arranca sin Postgres con RLS.

### Los 9 defectos de Fable: 6 cerrados, 3 pendientes (ESTADO §5)

Pendientes: **D5** (Constitucionalista audita estrategia que no existe: no hay
grafo), **D6** (Depends sin consumir: no aplica aún, no hay FastAPI), **D8**
(modelos hardcodeados detrás del gateway).

---

## 4 · Las mejoras, priorizadas (regla: un abogado real antes que otro test)

Esta es la lista de `PENDIENTES.md`, ordenada. **El grafo LangGraph es
anti-tarea hasta que un abogado use el núcleo.**

### A · Esta semana (antes que cualquier agente nuevo)

1. **Un abogado real con un caso real.** El gate HITL nunca fue cruzado por un
   expediente de verdad. Es la única medición que falta y la más barata.
2. **Motor de plazos visible.** `plazos.py` está enterrado: exponer un
   endpoint/UI mínima donde el abogado carga notificación + materia y ve el
   vencimiento día por día con fundamento. Es lo más vendible del sistema.
3. **Decidir la compuerta con el 17,3% sobre la mesa** (ESTADO §0). Opción
   ya implementada: (a) capa pública solo normativa + jurisprudencia tras
   login. Cablearla en el corpus o matar el módulo separado.
4. **Apuntar `corpus_cliente.py` al contrato autenticado.** Hoy
   `BASE = https://150448fcc6.abacusai.cloud` y `/buscar` público da 503 por
   diseño. Cuando corpus exponga API keys con scope, Custos es el primer
   consumidor con key propia.
5. **Consolidar el nombre** (colisiona con el log HMAC de KAMPE IR).

### B · Después del piloto

6. Leer arts. Ley 548 (NNA) y 348 (violencia) para que la reserva legal tenga
   texto.
7. Confirmar tabla de plazos con arts. 252, 261, 365 Ley 439; régimen "de
   momento a momento" art. 264 Ley 1340 (identificado, no medido).
8. Medir recall de la compuerta contra texto real (hoy 9 fixtures, y quien
   escribió el detector eligió los fixtures: W-01).
9. Confirmar el bind loopback del corpus y cerrar §9.11.

### C · NO hacer (anti-tareas)

- **No empezar el grafo LangGraph de 6 agentes** hasta que un abogado use el
  núcleo. En el corpus costó 33 commits sin mover el producto.
- **No agregar más falsadores** antes del primer usuario real.
- **No construir multi-bufete a fondo** (facturación, 200 tenants) para un
  piloto de 1-2 estudios.
- **No meter Qdrant** sin medir antes léxico vs vectorial con 10 consultas
  reales de un abogado (ADR-001: para "Art. 252 CPC" BM25 le gana a la
  similitud semántica).

---

## 5 · Huecos legales que pueden invalidar el producto (CONTEXTO §4)

- **H1:** ¿es legal que un agente redacte un memorial bajo matrícula? Ancla:
  Ley 387 (no un Colegio). Nadie lo prohibe expresamente, pero la
  responsabilidad es del abogado que firma.
- **H2:** vigencia: 86% de las abrogaciones no nombra su objeto; la vigencia
  automática completa no existe con esa fuente. El filtro "vigente"
  descartaría el 97,5% del corpus o dejaría pasar lo no medido.
- **H3:** scraping judicial con "rotación de cabeceras para mimetizar humano"
  es evadir un control del Estado. Límite: CP art. 363 ter (sin autorización
  Y perjuicio, acumulativos). Vía legítima posible: Ciudadanía Digital (Éforo
  ya la usa).
- **H4:** cero abogados usaron nada de la suite.
- **H5:** costo por caso no estimado (6 nodos LLM, hasta 2 ciclos por rechazo).

---

## 6 · Cómo trabajar acá (disciplina heredada)

- **Leer antes de afirmar:** `ESTADO.md`, `PENDIENTES.md`, este archivo, el
  ADR-001, y el código real. Responder de memoria es sospechoso.
- **Commitear la evidencia cruda verbatim** (W-01): el recibo lo firma quien
  corrió el instrumento; el veredicto va aparte. Prohibido ser el único
  testigo de un resultado propio.
- **Ningún script se commitea sin ejecutarlo.** Un comentario denso no es
  verificación.
- **Tres estados:** bien, mal, y NO MEDIDO. Un pendiente falso cuesta lo
  mismo que uno real.
- **Rama `titan/<tema>`** primero, nunca directo a `main`. Commit con el
  porqué y el bloque de METODO TITAN.
- **Prioridad:** lo que hace que el producto exista (un abogado usándolo) va
  primero. Arreglar la maquinaria de verificación es necesario y no es lo
  mismo que avanzar.

---

## 7 · Punteros exactos

- Repo: `github.com/gatehot59-star/custos-legis-tarija` (público, main).
- Corpus que consume: `github.com/gatehot59-star/corpus-legal-tarija`.
- Rama de trabajo del corpus: `titan/ocr-human-review`.
- Estado medido: `ESTADO.md` · Pendientes: `PENDIENTES.md` · Contexto vivo:
  `docs/agents/CONTEXTO-CUSTOS-LEGIS.md` · Frontera:
  `docs/adr/2026-09-10-01-frontera-entre-corpus-y-custos-legis.md`.
- Producción del corpus: `https://corpus-tarija.abacusai.cloud/corpus/login/`.
