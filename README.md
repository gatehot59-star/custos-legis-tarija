# CUSTOS LEGIS TARIJA

**Segunda parte de la suite legal de Tarija.** Un SaaS multi-inquilino para bufetes: vigila los plazos judiciales, arma la estrategia y redacta el memorial, con el abogado decidiendo siempre al final.

Proyecto de **Jorge Abraham Mendieta**. Repositorio creado el 2026-09-10.

---

## §1 · LA SEPARACIÓN DE PRODUCTOS, y va primero

Esto es lo primero que hay que entender, y es una decisión de Abraham, no una interpretación mía:

> **`corpus-legal-tarija` es un PRODUCTO INDEPENDIENTE y debe seguir mejorando por su cuenta.**
> No es un módulo de Custos Legis. No es su capa de datos. **Es un producto con su propia hoja de ruta, sus propios usuarios y su propia deuda técnica.**

| | `corpus-legal-tarija` | `custos-legis-tarija` |
|---|---|---|
| Qué es | **Buscador de normativa y jurisprudencia** | **SaaS de gestión de causas con agentes** |
| Estado | **VIVO en producción**, 6.079 documentos | **cero código**, recién fundado |
| Cliente | cualquiera que necesite el texto legal | bufetes con expedientes activos |
| Datos | **solo públicos** | **públicos + confidenciales del bufete** |
| Repo | público | este |
| Relación | **es consumido por** Custos Legis | **consume** el corpus |

**Y la dirección de la dependencia importa:** Custos Legis depende del corpus, el corpus **no** depende de Custos Legis. Si Custos Legis se cancela mañana, el corpus sigue siendo un producto vendible. Al revés no.

### Custos Legis va a necesitar OTROS corpus

El corpus actual **no alcanza** para lo que Custos Legis promete, y eso es un hecho medible, no una opinión. Lo que hay hoy y lo que falta:

| Corpus | Estado |
|---|---|
| Jurisprudencia TSJ (GENESIS) | **5.030 documentos, VIVO** |
| Gaceta Oficial de Tarija | **1.034 documentos, VIVO** |
| Normativa nacional (LexiVox) | **15 documentos.** Faltan Código Civil, Penal y LGT de fuente oficial |
| **Jurisprudencia constitucional (TCP)** | **censada (2.939 + 3 gestiones de Gaceta), CERO incorporada** |
| **Normativa municipal de Tarija** | **NO EXISTE.** Ni censada |
| **Ejecutivo departamental (decretos)** | **NO EXISTE** |
| **Corpus privado por bufete** | **NO EXISTE.** Es lo que Custos Legis tiene que construir |

El diseño pide una jerarquía de tres niveles (nacional / departamental / municipal) para que un agente sepa qué norma prevalece. **El nivel municipal hoy es un hueco total.**

---

## §2 · DÓNDE SE IMPLEMENTA

**En Abacus.AI, igual que el corpus.** Decisión de Abraham.

Medido hoy sobre la VM que ya sirve el corpus:

| Recurso | Valor |
|---|---|
| Arquitectura | `x86_64` |
| Núcleos | **2** |
| RAM disponible | 6,3 GB de 8 |
| Swap | **ninguna** |
| Disco libre | 35 GB de 48 |
| `/dev/kvm` | **usable, API 12** |
| `docker` | presente |
| Uso actual del corpus | `corpus-api` en **24,8 MB** de RAM |

**Y acá hay un conflicto que hay que decidir antes de escribir código, no después:** el diseño del documento fuente pide PostgreSQL + Redis + Qdrant + Celery workers + FastAPI. Eso en **2 núcleos compartidos con el buscador que el bufete va a usar** es una colisión anunciada.

Dos caminos, y el segundo es el que yo recomiendo:

1. Todo en la misma VM. Barato, y **degrada el corpus** cuando los agentes trabajen.
2. **VM separada para Custos Legis.** Cuesta más, y respeta que son **dos productos**. Coherente con el §1.

**NO MEDIDO:** el costo por hora de una VM de Abacus, y cuánto degrada el buscador un stack de agentes en 2 núcleos. Los dos hay que medirlos antes de elegir.

---

## §3 · DOS COSAS DEL DOCUMENTO FUENTE QUE MEDÍ, Y UNA ESTÁ MAL

El documento de diseño trae una auditoría ajena. La verifiqué antes de construir sobre ella.

### 3.1 · El "HALLAZGO CRÍTICO #1" (SIGC reemplaza al SIREJ): **CIERTO, pero mal dimensionado**

Confirmado en fuente primaria (`tsj.bo`, 8-abr-2025): TSJ y Consejo de la Magistratura firmaron convenio para migrar el SIREJ al **Sistema Informático de Gestión de Causas (SIGC)**. El portal existe: `justicia.organojudicial.gob.bo`.

**Pero el alcance real es mucho más chico de lo que la auditoría sugiere, y eso cambia la prioridad:**

| Lo que dice la auditoría | Lo que medí |
|---|---|
| "El SIREJ está siendo reemplazado" | **solo en materia PENAL.** Civil, familiar y tributario siguen en SIREJ |
| "El proceso ya está en marcha" | piloto en **Chuquisaca**, no en Tarija |
| implicación de urgencia inmediata | prometido para el **6-ago-2025**, y en **marzo de 2026** el TSJ todavía presentó un **anteproyecto de ley** pidiendo **Bs 160 millones** para el despliegue nacional |

**Consecuencia para Custos Legis:** para un bufete de Tarija que litiga civil y familiar, **el SIREJ es el sistema y va a seguir siéndolo un buen rato**. El patrón adaptador que propone la auditoría **sigue siendo correcto** (es buena ingeniería), pero su prioridad no es "CRÍTICA": es prudencia barata.

**Y apareció una pieza que la auditoría no menciona:** existe **Éforo**, el sistema de gestión de las Oficinas Gestoras de Procesos, que **ya interopera** con SIREJ, Tritón JL del Ministerio Público, SEGIP y AGETIC. O sea que el panorama no es "SIREJ → SIGC": son **al menos tres sistemas** conviviendo. **NO MEDIDO:** cuál de los tres tiene los expedientes civiles de Tarija.

### 3.2 · "Tu MVP actual es un prototipo conversacional en AbacusAI": **FALSO, medido**

La auditoría describe `150448fcc6.abacusai.cloud/?q=asistencia+familiar` como *"prototipo funcional generado en AbacusAI"*, con *"interfaz conversacional básica"* y *"prueba de concepto"*, y lista como **faltante** el *"Corpus vectorial de Gaceta Tarija"*.

**Eso no es un prototipo: es el corpus, y la Gaceta de Tarija ya está adentro.** Medido hoy con esa misma consulta:

```
GET /buscar?q=asistencia+familiar

total_pasajes : 184
ms            : 11.23
facetas materia: Civil 108 | Familia 43 | Penal 15 | Tributaria 1 |
                 Constitucional 1 | Administrativa 1
facetas tipo   : Auto Supremo 129 | Codigo 37 | Ley 9 |
                 Ley Departamental 8 | CPE 1
```

**184 pasajes en 11,23 milisegundos, con facetas por materia, tipo y año**, sobre 6.079 documentos y 78.930 pasajes. No es conversacional: es **búsqueda de texto completo con FTS5 y BM25**. Y las **8 Leyes Departamentales** en las facetas son la Gaceta de Tarija que la auditoría declara ausente.

**El mecanismo del error, y es el que más me importa:** la auditoría concluyó sobre el sujeto sin medirlo. Es el mismo patrón que a mí me costó seis defectos en la campaña del corpus.

**Lo que la auditoría SÍ acierta sobre el corpus, y hay que decirlo:** no hay búsqueda vectorial ni semántica. Es literal, y el propio `/estado` lo declara como límite. Eso es un hueco real.

---

## §4 · ESTADO REAL DE ESTE REPO

**Cero código. Cero base de datos. Cero agente corriendo. Cero cliente.**

Lo que hay es el alcance declarado, la separación de productos y dos mediciones sobre el documento fuente. **Nada de este repo se ejecutó en ninguna máquina todavía.**

Y una advertencia que sale de la campaña del corpus: ahí hubo **33 commits en 26 horas sin mover un solo documento del producto**. Este repo arranca con esa cicatriz a la vista.

## §5 · DÓNDE VIVE CADA COSA

| Qué | Dónde |
|---|---|
| Contexto vivo del proyecto | `docs/agents/CONTEXTO-CUSTOS-LEGIS.md` |
| Decisiones de arquitectura | `docs/adr/` |
| Bitácora de entregas y evidencia | `docs/agents/respuestas/` |
| El corpus que consume | [`corpus-legal-tarija`](https://github.com/gatehot59-star/corpus-legal-tarija) |
| Inventario de máquinas (canónico) | [`00-ENTORNOS-Y-CAPACIDADES.md`](https://github.com/gatehot59-star/mudh-mobile/blob/main/00-ENTORNOS-Y-CAPACIDADES.md) |
