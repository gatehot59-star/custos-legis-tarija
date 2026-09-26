# Custos Legis: reconciliación de agentes, orquestación, taller y VM

**Fecha de medición:** 2026-09-26 03:39-04:00 ART  
**Alcance:** ClickUp histórico, GitHub, `brain-env` y VM `corpus-vm`  
**Veredicto:** el informe anterior dijo «0 agentes» con un alcance demasiado amplio. La forma correcta es: **hay una arquitectura histórica de agentes y orquestación documentada, pero no hay evidencia de que esa implementación específica de Custos haya sido consolidada, construida o desplegada. El repo actual, el taller y la VM no contienen el producto multiagente de Custos.**

## 1. Qué quedó demostrado

### Diseño histórico

Los Docs de agosto describen una aplicación Tauri/Rust/React, OpenClaw, RAG, skills judiciales, generación y verificación de memoriales, API Gateway, BullMQ/Redis, worker y Telegram. El [Master consolidado](https://app.clickup.com/90171457413/docs/2kza6fw5-937/2kza6fw5-1637) dice explícitamente **«consolidación documental completa, release no verificado»** y enumera como bloqueos el repositorio físico único, módulos faltantes, smoke runtime, RLS, build Windows y E2E. La [auditoría global](https://app.clickup.com/90171457413/docs/2kza6fw5-917/2kza6fw5-1597) repite que los créditos eran Docs separados y que no había un checkout físico único ejecutado.

El [Crédito 4/5](https://app.clickup.com/90171457413/docs/2kza6fw5-857/2kza6fw5-1357) documenta el contrato del Gateway y Worker: Fastify, HMAC, nonce, resolución de tenant, BullMQ y worker determinista. El [Crédito 5/5](https://app.clickup.com/90171457413/docs/2kza6fw5-877/2kza6fw5-1457) documenta la UI, Telegram, hardening y deploy, pero concluye «listo para la fase de integración física», no release final.

**Eso prueba diseño y código documentado. No prueba que existiera el árbol ejecutable.**

### GitHub actual

La búsqueda de repositorios de `gatehot59-star` devuelve un único repositorio de Custos: [custos-legis-tarija](https://github.com/gatehot59-star/custos-legis-tarija). Su raíz en `main` contiene solamente `README.md`, `ESTADO.md`, `PENDIENTES.md`, `backend/`, `docs/`, `infra/` y workflows. No contiene `package.json`, `Cargo.toml`, `tauri.conf.json`, `src-tauri/`, `src/`, `apps/`, `workspace/skills/`, `openclaw.json`, `legislacion.db` ni `docker-compose` del producto original.

Las ocho ramas públicas inspeccionadas tienen la misma forma de árbol backend/documentación/infraestructura. La rama de arquitectura solo agrega documentación; no agrega Tauri, Rust, React, OpenClaw, BullMQ ni seis agentes.

El repositorio actual sí tiene un núcleo Python verificable: API HTTP de loopback, PostgreSQL/RLS, cliente HTTP del corpus, anonimización fail-closed, plazos y gates HITL. Ese núcleo no es el producto multiagente histórico.

### Taller `brain-env`

La llamada real al servicio `build/run` mostró que `/workspace/cl` es un checkout del mismo `custos-legis-tarija` actual: `.git`, `README.md`, `backend/`, `docs/` e `infra/`, sin árbol Tauri/Rust/React.

Los worktrees `custos-completion-20260916` y `custos-integration-20260916-0314` contienen pruebas, logs, PostgreSQL aislado y el mismo backend Python. Una búsqueda de manifiestos no encontró `package.json`, `Cargo.toml`, `tauri.conf.json`, `openclaw.json` ni `legislacion.db` en esos árboles. El único archivo local con nombre directo de Custos fue un instrumento de auditoría, `/workspace/audita/custos_legis.py`, no el producto.

El inventario canónico fue leído desde `/workspace/mudh/00-ENTORNOS-Y-CAPACIDADES.md`; el taller fue medido mediante el servicio `build`, no mediante el sandbox auxiliar.

### VM

La conexión SSH real a `corpus-vm.icca-engine.com` funcionó y devolvió:

- `hostname`: `vm`.
- `uptime`: 4 días, 10 horas y 41 minutos en la medición.
- Servicios activos: `cloudflared-corpus.service`, `corpus-api.service` y `corpus-django-staging.service`.
- No apareció ningún servicio `custos`, `legis`, `openclaw`, `agent` o `worker` de Custos.
- No aparecieron rutas ni archivos `custos`, `custos_legis`, `skill_memorial`, `skill_verificador` o `legislacion.db` en `/opt`, `/var/www` o `/home/ubuntu`.
- Los procesos activos relevantes son el corpus, Gunicorn y Nginx. No hay un proceso OpenClaw, Hermes o Custos ejecutándose.

La VM sí tiene runtimes genéricos: OpenClaw `2026.6.10` en `/opt/abacus-npm/lib/node_modules/openclaw` y Hermes Agent v0.19.0 en `/opt/hermes-agent`. Sus propios metadatos los identifican como productos genéricos de sus respectivos proyectos, no como una instalación de Custos. **Tener el runtime no equivale a tener agentes de Custos configurados.**

## 2. Matriz de estado

| Pieza | Diseñada | Código documentado | Committida en Custos actual | Construida | En taller | Corriendo en VM |
|---|---:|---:|---:|---:|---:|---:|
| Arquitectura multiagente Custos | Sí | Sí | No | No medido como producto | No | No |
| «Seis agentes» de Custos | Sí, como diseño futuro | Parcial, mezclados con módulos y skills | 0 | 0 | 0 | 0 |
| Orquestación específica de Custos | Sí, LangGraph/OpenClaw/worker según documentos | Sí, por contratos | No | No | No | No |
| Runtime OpenClaw/Hermes genérico | No es propiedad de Custos | Sí, externo | No | Sí, instalado | Sí, disponible | Instalado, detenido |
| Núcleo backend Python actual | No corresponde al diseño viejo | Sí | Sí | Sí, probado por suites/CI y corridas aisladas | Sí | No desplegado |
| Corpus legal | No es Custos | Sí, producto separado | Sí, en repo propio | Sí | Sí | Sí |

## 3. Respuesta directa a la duda

Abraham tenía razón en una parte importante: **no era correcto decir que Custos nunca tuvo agentes ni orquestación**. Sí existió una especificación amplia, con código reconstruido en Docs y un diseño de integración alrededor de OpenClaw y un Worker Engine.

Pero la evidencia viva no permite decir que «los agentes estaban resueltos» en el sentido de producto ejecutable. En ningún lugar inspeccionado apareció el checkout físico completo, un commit de esos agentes en `custos-legis-tarija`, un build Tauri/React/Rust, un `openclaw.json` de Custos, una skill `skill_memorial`/`skill_verificador` operativa, un grafo LangGraph, un worker de Custos arrancado o un despliegue de Custos en la VM.

**Conclusión de ingeniería:** el diseño viejo es una especificación y un backlog de extracción; el backend actual es una reconstrucción posterior y acotada. No son dos partes ocultas del mismo build: son dos estados distintos del proyecto.

## 4. Riesgo descubierto durante la medición

El checkout local `/workspace/cl` conserva una URL de remoto con una credencial embebida. No se copia ni se publica el valor en este informe. La credencial debe considerarse expuesta y revocarse/rotarse antes de reutilizar ese checkout para pull o push. No se modificó el remoto ni se revocó nada porque eso cambia acceso y requiere decisión del propietario.

## 5. Próximo paso correcto

No conviene intentar «activar» el runtime genérico y llamarlo Custos. Hay que decidir entre:

1. **Retomar el backend actual** y añadir primero un solo flujo vertical: documento → búsqueda citada → plazo verificable → revisión humana → salida; o
2. **Reconstruir el producto histórico** desde la especificación, empezando por extraer un repositorio físico mínimo con contratos, un agente de búsqueda, un agente de plazos, un generador y un verificador, todos con falsadores y gate humano.

Mi recomendación es la opción 1 con una interfaz de agentes pequeña después de validar el flujo. El diseño de seis agentes antes de tener el recorrido usado por un abogado vuelve a abrir el proyecto grande sin haber probado la necesidad.

## Método y límites

- **Máquinas:** `brain-env` mediante gateway `build/run`; VM mediante SSH por `corpus-vm.icca-engine.com`; GitHub y ClickUp para fuentes documentales.
- **Instrumentos:** listado de servicios y herramientas; `find`, `git`, inventario canónico, árbol GitHub, búsqueda de repositorios y SSH remoto de solo lectura.
- **Independencia:** se conservaron los hechos por fuente y se separó diseño documental de estado ejecutable.
- **No medido:** no se inspeccionaron cuentas externas de Abacus distintas de la VM alcanzada ni artefactos que no sean visibles desde esos cuatro puntos.
- **Acción delicada:** NO. No se modificó producción, VM, `main`, credenciales ni configuración.
- **Modo:** TITAN FULL.
