# Audit real de taller, VM y Git

**Fecha de la medición:** 2026-09-28
**Pedido:** auditar taller, VM y Git contra capacidades reales.
**Sujeto:** `brain-env` mediante el gateway MUDH, host Android/ADB mediante el servicio ADB, ENNEXUS mediante SQLite y `gatehot59-star/custos-legis-tarija` mediante GitHub.
**Modo:** TITAN FULL.

## 1. Herramientas y alcance

Se usaron únicamente lecturas y diagnósticos. No se apagó ni encendió el runner, no se modificó la VM, no se escribió ENNEXUS y no se tocó producción.

- Gateway MUDH: listado de servicios y schemas reales.
- `build.run`: intento de shell dentro de `brain-env`.
- `sqlite.query` y `sqlite.get_estado`: lectura de ENNEXUS.
- `adb.doctor`, `adb.list_devices`, `adb.list_avds`: diagnóstico del host ADB y su emulador.
- GitHub: ramas, PRs abiertos, commits de `main`, `ESTADO.md` y `PENDIENTES.md`.

## 2. Taller (`brain-env`): resultado real

El servicio `build` figura disponible en el gateway, pero el contenedor que debe ejecutar el shell no está corriendo. Se intentó una orden mínima y después se reintentó con otra orden mínima. Las dos fallaron antes de ejecutar el comando.

Evidencia cruda, primer intento:

```text
exit=1
--- STDOUT ---

--- STDERR ---
Error response from daemon: Container 6c09d8604b07d3d0c60440680435b5aa46a87c4f354a614f021223d46e84d7a2 is not running
```

Evidencia cruda, reintento:

```text
exit=1
--- STDOUT ---

--- STDERR ---
Error response from daemon: Container 6c09d8604b07d3d0c60440680435b5aa46a87c4f354a614f021223d46e84d7a2 is not running
```

**Veredicto:** el taller existe como servicio registrado, pero su runtime de ejecución está caído/no iniciado en esta medición. CPU, RAM, disco, usuario, toolchain, procesos, runner self-hosted, logs locales y acceso Git desde dentro de `brain-env` quedan **NO MEDIDOS** en esta corrida. No se puede afirmar que estén ausentes: no se llegó a ejecutar `id`, `uname`, `free`, `df`, `git` ni `ps` dentro del contenedor.

No existe en el schema descubierto una herramienta downstream para reiniciar el contenedor. No se hizo una operación fuera del alcance de lectura.

## 3. ENNEXUS: estado disponible, pero con deriva temporal

Las tablas presentes en la base compartida fueron:

```text
agentes
bitacora
decisiones
eventos_estado
mediciones
mensajes
reportes
sqlite_sequence
estado
trabajos_vivos
```

La tabla `estado` tiene las columnas `clave`, `valor`, `agente` y `ts`. No hay claves actuales para `build`, `brain-env`, `vm`, `custos` o `runner`; las consultas directas a esas claves devolvieron `[]`.

Sí existe una entrada histórica `via-libre-brain` con valor `activa desde 2026-08-28; adb desbloqueado + git con credenciales en brain-env`, pero no sustituye la medición actual: el intento actual contra `build` contradice que el runtime esté disponible ahora.

ENNEXUS también conserva recibos históricos de la VM de septiembre, incluido staging Django separado con Gunicorn en `127.0.0.1:8001`, pero esos recibos no son una sonda actual de la VM y se conservan como **estado histórico, no como verde vigente**.

## 4. Host de ADB/VM Android: medido

El diagnóstico real del servicio ADB devolvió:

```text
adb-mcp server version: 0.22.2 (latest: https://github.com/iksnerd/adb-mcp/releases — update with `adb-mcp update`; a restarted MCP client picks up the new binary)

• Android SDK: /home/estudiante/Android
✓ adb: Android Debug Bridge version 1.0.41 (/home/estudiante/Android/platform-tools/adb)
✓ emulator: 1 AVD(s): mudh_api34
• devices: none attached
✓ java: openjdk version "17.0.20" 2026-07-21
⚠ gradle (system): not on PATH — only needed so scaffold_android_project can generate a Gradle wrapper; projects that already have ./gradlew are unaffected
```

`list_devices` devolvió:

```text
No devices attached.
```

`list_avds` devolvió:

```text
Available AVDs:
mudh_api34
```

**Veredicto:** el host ADB tiene SDK, `adb`, emulador instalado y Java 17; no tiene un dispositivo/emulador adjunto en esta medición; no tiene Gradle de sistema en PATH. El AVD instalado existe, pero no se lo arrancó porque el pedido era auditar, no modificar el runtime.

Esto mide el host del servicio ADB. No prueba el estado de la VM pública `corpus-vm.icca-engine.com`; esa VM queda **NO MEDIDA en vivo** en esta corrida.

## 5. Git de Custos: estado real observado

Repositorio: `gatehot59-star/custos-legis-tarija`.

`main` está en:

```text
b37fce3d968b6b40f42e2b5c81de669bf333a950
```

El commit es el merge de PR #16, titulado `Merge PR #16: integrar MVP vertical persistente`, fechado 2026-09-28 18:48:29 UTC.

Ramas relevantes observadas:

```text
main                                      b37fce3d968b6b40f42e2b5c81de669bf333a950
feat/piloto-codeable-20260928            b377a2df94d2fd9a0d82c8ba7c0b6e1094bf33eb
experiment/pg-restart-flow-20260928      dccb6b17f17276845e0de07d0f68b58fd87df4fc
```

También existen ramas históricas `titan/*`, incluidas `titan/mvp-integrado-limpio-20260926`, `titan/mvp-persistence-20260926`, `titan/fix-directed-graph-20260926` y ramas de falsadores/QA de septiembre.

PRs abiertos contra `main` observados:

| PR | Estado | Head | Lectura |
|---|---|---|---|
| [#18](https://github.com/gatehot59-star/custos-legis-tarija/pull/18) | abierto, no draft | `b377a2d...` | pendientes codeables del piloto; no mergeado |
| [#11](https://github.com/gatehot59-star/custos-legis-tarija/pull/11) | abierto, draft | `cce68f0...` | investigación histórica de agentes; no mergeado |
| [#3](https://github.com/gatehot59-star/custos-legis-tarija/pull/3) | abierto, draft | `9eaece7...` | suite/guards históricos; no mergeado |

La rama experimental de reinicio PostgreSQL existe, pero no apareció como PR abierto en la lista actual consultada. Por lo tanto, el experimento no forma parte de `main` ni de un PR abierto observado en esta llamada.

## 6. Contraste con el estado versionado

`ESTADO.md` en `main` conserva una fotografía anterior, fechada 2026-09-10, donde todavía declara que no existían endpoints/FastAPI, persistencia del MVP ni agentes desplegados. Esa fotografía ya no describe todo el árbol actual: el merge de PR #16 agregó el MVP HTTP persistente y el CI PostgreSQL posterior.

`PENDIENTES.md` sí conserva el orden de producto correcto: primero abogado real, plazo visible, compuerta cableada, cliente Corpus autenticado y nombre; después agentes. También prohíbe empezar el grafo LangGraph de seis agentes antes del piloto.

**Hallazgo de deriva documental:** Git ya avanzó más rápido que `ESTADO.md`. No se debe usar ese archivo viejo como prueba de que el MVP actual no existe. La evidencia actual más fuerte para el código es `main` en `b37fce3...`, los checks del merge y la rama/PR #18.

## 7. Capacidades: bien, mal y NO MEDIDO

| Área | Resultado real |
|---|---|
| Gateway MUDH y servicios registrados | **BIEN**, `build`, `sqlite` y `adb` disponibles según listado |
| Shell dentro de `brain-env` | **MAL en esta medición**, el contenedor no está corriendo |
| Recursos de `brain-env` | **NO MEDIDO** ahora |
| Git ejecutado desde `brain-env` | **NO MEDIDO** ahora |
| ENNEXUS lectura | **BIEN**, tablas y filas legibles |
| ENNEXUS estado actual de build/VM/runner | **NO MEDIDO**, no hay claves actuales |
| ADB/SDK/Java | **BIEN**, diagnóstico real positivo |
| Dispositivo Android conectado | **MAL**, ninguno adjunto |
| AVD instalable | **BIEN**, `mudh_api34` listado |
| Gradle de sistema en host ADB | **MAL**, no está en PATH |
| VM pública Corpus/Custos en vivo | **NO MEDIDO** |
| `main` de Custos | **BIEN**, SHA observado y merge PR #16 confirmado |
| PR #18 | **ABIERTO**, no mergeado |
| PRs históricos #11 y #3 | **ABIERTOS EN DRAFT**, no mergeados |

## 8. Conclusión operativa

El mapa real no es “el taller está disponible” ni “el taller no existe”. Es: **el gateway ve el servicio, pero el contenedor de `brain-env` no está ejecutando**. La VM Android está preparada pero sin dispositivo; ENNEXUS tiene memoria histórica útil pero no un estado actual de esas claves; Git está sano en `main` y tiene el PR #18 pendiente.

La próxima acción correcta, antes de afirmar capacidades del taller o ejecutar pruebas locales, es restaurar el runtime `build` por la vía autorizada y repetir el mismo medidor. No se debe inferir CPU/RAM/Git/runner a partir del inventario viejo ni de ENNEXUS histórico.

## 9. NO MEDIDO explícito

- CPU, RAM, disco, procesos y usuario actuales de `brain-env`.
- Estado actual del runner self-hosted y sus logs locales.
- Git desde el shell del taller.
- Estado actual de la VM pública del Corpus.
- Estado actual de `custos-legis-tarija` desplegado fuera de GitHub.
- Acceso real a PostgreSQL desde el taller.
- Ejecución local del test MVP después del merge.
- Estado actual de Actions para todos los commits; en esta pasada se auditó Git, no se releyeron los check runs individuales.

## 10. Método TITAN

```text
--- METODO TITAN ---
Accion delicada: NO
Modo aplicado:   TITAN FULL
Rubrica:         N/A (auditoría de estado y evidencia)
N/A declarados:  implementación, despliegue, merge, reinicio del runner y arranque del AVD
Review externo:  no solicitado; este archivo conserva evidencia cruda para revisión
Instrumento:     gateway MUDH build/sqlite/adb + GitHub MCP; falló build con exit=1 antes de ejecutar el shell
Maquina:         brain-env (no ejecutó), host ADB (diagnóstico ejecutado), GitHub Actions no ejecutado en esta pasada
Artefactos:      este archivo + Doc público de ClickUp enlazado desde el cierre
```
