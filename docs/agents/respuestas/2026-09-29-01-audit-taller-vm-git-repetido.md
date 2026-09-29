# Audit repetido de taller, VM y Git contra capacidades reales

**Fecha:** 2026-09-28 22:35 ART / 2026-09-29 UTC  
**Pedido:** auditar taller, VM y Git contra capacidades reales.  
**Sujeto:** `brain-env` por MUDH Gateway, host Android/ADB, Nexus (`nexus.db`) y `gatehot59-star/custos-legis-tarija`.  
**Escritura:** no se escribió en Nexus, no se reinició el contenedor, no se arrancó el AVD, no se tocó producción.

## 1. Instrumentos

- MUDH Gateway: `gateway_list_services`, `gateway_list_tools`, `gateway_get_service`, `gateway_call_tool`.
- Taller: `build.run`.
- Android: `adb.doctor`, `adb.list_devices`, `adb.list_avds`.
- Nexus: `sqlite.list_tables`, `sqlite.query`.
- GitHub: ramas, PRs, árboles y archivos de contexto/estado.

## 2. Taller `brain-env`: MAL para ejecutar, capacidades NO MEDIDAS

El servicio figura disponible, pero el runtime falla antes de ejecutar cualquier shell.

Evidencia cruda, dos intentos:

```text
exit=1
--- STDOUT ---

--- STDERR ---
Error response from daemon: Container 6c09d8604b07d3d0c60440680435b5aa46a87c4f354a614f021223d46e84d7a2 is not running
```

El segundo intento devolvió exactamente el mismo resultado. `gateway_get_service` lo reportó como `available: true`, `serverInfo.name: brain-env`, `version: 1.0.0`, con `lastConnectedAt: 2026-09-29T01:45:37.780Z`; eso prueba registro/conexión del servicio, no ejecución del contenedor.

**No se pudo medir dentro de brain-env:** identidad, CPU, RAM, disco, procesos, runner self-hosted, logs locales, Git, Python, PostgreSQL, Android SDK ni acceso al repo desde el shell.

## 3. VM/host Android: parcialmente VERDE

Evidencia cruda de `adb.doctor`:

```text
adb-mcp server version: 0.22.2
• Android SDK: /home/estudiante/Android
✓ adb: Android Debug Bridge version 1.0.41 (/home/estudiante/Android/platform-tools/adb)
✓ emulator: 1 AVD(s): mudh_api34
• devices: none attached
✓ java: openjdk version "17.0.20" 2026-07-21
⚠ gradle (system): not on PATH — only needed so scaffold_android_project can generate a Gradle wrapper; projects that already have ./gradlew are unaffected
```

`adb.list_devices`: `No devices attached.`  
`adb.list_avds`: `Available AVDs: mudh_api34`.

**Veredicto:** SDK, adb, emulador instalado y Java 17: BIEN. Dispositivo adjunto: MAL. Gradle de sistema: MAL/no está en PATH. El AVD no se arrancó porque arrancarlo cambia estado y no era necesario para auditar. Esto no mide la VM pública de Corpus/Custos.

## 4. Nexus: legible, pero sin estado vivo utilizable del taller

Tablas observadas:

```text
agentes, bitacora, decisiones, estado, eventos_estado, mediciones,
mensajes, reportes, sqlite_sequence, trabajos_vivos
```

La tabla `estado` tiene `clave`, `valor`, `agente`, `ts`. La lectura de las últimas filas no contiene claves actuales `build`, `brain-env`, `vm`, `custos` ni `runner`. Sí existe el evento histórico `via-libre-brain`:

```text
activa desde 2026-08-28; adb desbloqueado + git con credenciales en brain-env
```

Ese evento no se usa como verde vigente porque la sonda actual de `build.run` lo contradice. `mediciones` y `trabajos_vivos` contienen principalmente recibos históricos de otros trabajos; no hay una medición actual que rescate la ejecución del contenedor.

## 5. Git de Custos: estado observado

`main`:

```text
b37fce3d968b6b40f42e2b5c81de669bf333a950
```

Ramas relevantes:

```text
audit/2026-09-28-taller-vm-git-capacidades  1d681ed...
experiment/pg-restart-flow-20260928       dccb6b1...
feat/piloto-codeable-20260928              b377a2d...
main                                       b37fce3...
research/2026-09-26-agentes-legales-eficientes cce68f0...
```

PRs abiertos contra `main`:

- [PR #18](https://github.com/gatehot59-star/custos-legis-tarija/pull/18): abierto, no draft, pendientes codeables del piloto, head `b377a2df...`.
- [PR #11](https://github.com/gatehot59-star/custos-legis-tarija/pull/11): abierto en draft, investigación de agentes, head `cce68f0...`.
- [PR #3](https://github.com/gatehot59-star/custos-legis-tarija/pull/3): abierto en draft, suite/guards históricos, head `9eaece7...`.

La rama experimental PostgreSQL existe, pero no apareció como PR abierto en la consulta actual. Por tanto, no forma parte de `main` ni de un PR abierto observado.

## 6. Deriva documental medida

`docs/agents/CONTEXTO-CUSTOS-LEGIS.md` y `ESTADO.md` en `main` siguen fechados 2026-09-10 y todavía dicen `cero código`, `cero base` y `cero agente`. Eso contradice el merge posterior del MVP HTTP/persistente en `b37fce3...` y los workflows presentes en `.github/workflows/` (`api-e2e.yml`, `mvp-http.yml`, `mvp-persistence.yml`, `tests.yml`).

`PENDIENTES.md` en la rama del piloto sí refleja el orden actual: abogado real antes que agentes, plazo visible, compuerta, contrato autenticado del Corpus y nombre.

## 7. Resultado en tres estados

| Área | Estado |
|---|---|
| Servicios MUDH registrados | BIEN |
| Shell de `brain-env` | MAL en esta corrida |
| Recursos/toolchain/Git/runner dentro de `brain-env` | NO MEDIDO |
| Nexus lectura/esquema | BIEN |
| Nexus estado vivo de build/VM/runner | NO MEDIDO |
| Android SDK/adb/Java/AVD | BIEN |
| Dispositivo Android | MAL: ninguno |
| Gradle de sistema en host ADB | MAL |
| `main` de Custos | BIEN: SHA observado |
| PR #18 | ABIERTO, no mergeado |
| PR #11 y #3 | ABIERTOS EN DRAFT |
| VM pública de Corpus/Custos | NO MEDIDO |
| Checks individuales actuales de Actions | NO MEDIDO en esta corrida |

## 8. Próximo paso

Restaurar el runtime `build` por una vía autorizada y repetir el mismo medidor. Hasta entonces no se puede afirmar capacidad real de CPU, RAM, Git, runner o tests locales del taller. No se arrancó el AVD ni se reinició infraestructura.

## Método

```text
Maquina: brain-env (sonda no ejecutó) | host ADB (diagnóstico ejecutado) | GitHub
Artefactos: este archivo commiteado; Doc público de ClickUp pendiente de enlace
NO MEDIDO: todo lo que requería shell dentro de brain-env, VM pública y checks individuales actuales
```
