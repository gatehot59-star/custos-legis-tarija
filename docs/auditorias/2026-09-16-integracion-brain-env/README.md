# Custos: integración ejecutada en brain-env, cuatro rojos

**No es aprobación de producción. No se corrigió código del producto.**

Corrida: 2026-09-16 03:18:49 a 03:18:54 UTC (00:18 ART). Máquina: brain-env, servicio build del gateway MUDH, uid 1000. Código: `446e17d029751ebeeecbf89bb57417ed91a1fe16`; `git diff` entre ese commit y el de la auditoría inicial `cc935d7b1c5b12f8f49fe1c7653cc46424e38be1` no mostró cambios en backend/infra.

## Evidencia reproducible

- [Salida JSON íntegra](resultados.json), SHA256 `7c7bea3a7c91d73622697e5be9f6fccba410981d2a99fbd8ce17b5163a622877`.
- [Instrumento ejecutado](run_integration.py), SHA256 `80ef0d41c8f3c027888d807d40c1e4bba19ca4ebaa2f6c080bce9eea9a0d2df3`.

Después de publicar, se hizo fetch y se calculó SHA256 del contenido de ambos archivos en origin/main: coincidieron exactamente con los originales del taller. Los resultados no fueron reescritos ni resumidos para generar el JSON. El JSON incluye colas de salida de suites, no sus logs completos; los logs completos quedaron en la carpeta de prueba.

## Resultado

Las suites existentes terminaron con exit 0: `test_api.py` (65 verdes, almacenamiento SQLite), `guard_esquema.py`, `test_rls.py` (16 verdes sobre PostgreSQL real) y `test_plazos.py` (71 verdes). Estos verdes no probaron los bordes nuevos.

El instrumento nuevo completó 18 comprobaciones: **14 pasan, 4 fallan**, sin error del arnés. El conjunto mezcla controles de preparación, integración HTTP y una prueba del motor; no lo presento como 18 casos completos de usuario ni como porcentaje global de calidad.

### 1. Login válido rechazado: confirmado por ejecución

POST /sesion con usuario activo sintético y contraseña correcta devolvió **401**, esperado 200. Control positivo: el usuario existía en PostgreSQL y su contraseña verificó dentro del tenant. El rol usado por la API era `custos_app`, sin superusuario y sin BYPASSRLS. La consulta de usuarios sin tenant vio cero filas.

Esto reemplaza el NO MEDIDO de ejecución del hallazgo 2 de la auditoría inicial por una reproducción real en este entorno. No se resolvió el defecto.

### 2. Rechazo posterior ignorado: confirmado por ejecución

Se registró una aprobación a las 03:18:53.003948 UTC y un rechazo del mismo contenido y caso a las 03:18:53.068071 UTC. Ambos persistieron en PostgreSQL. La solicitud posterior devolvió **200, AUTORIZADA_PERO_NO_EJECUTADA**, esperado 403.

No se envió un escrito: el endpoint no implementa ejecución externa. El fallo medido es la autorización después del rechazo.

### 3. Texto de búsqueda en logs: confirmado en el handler real

La API original recibió una consulta sintética. Su stdout incluyó:

```text
127.0.0.1 GET /buscar "GET /buscar?q=CANARIO_AUDITORIA_793 HTTP/1.1" 200 -
```

Esta vez no se copió un método a una reproducción mínima: se ejecutó `api.servir()` y el handler del producto. El corpus remoto se sustituyó por un doble vacío para no usar datos reales ni hacer llamadas externas. Se probaron ruta HTTP, registro de uso en PostgreSQL y logging, no la integración con el corpus vivo.

### 4. Inicio cautelar penal: divergencia de contrato reproducida

El motor real, con calendario sintético cubierto y notificación 2026-09-11, tres días y `medida_cautelar=True`, devolvió **2026-09-16**, frente a **2026-09-14** del contrato de contar desde el día siguiente en corridos. La traza omite sábado 12 y domingo 13 antes del inicio, y cuenta lunes, martes y miércoles.

No es un dictamen jurídico. El contraste usa el contrato declarado, no validación profesional del artículo aplicable a una causa real ni calendario oficial.

## Lo que sí pasó en la integración

No sesión -> 401. Crear caso en PostgreSQL -> 201. A ve su caso y B no lo ve. Sin aprobación -> 403. Con aprobación -> autorizada pero no ejecutada. Cambiar contenido -> 403. Reutilizar aprobación desde otro tenant -> 403. El esquema del producto se aplicó sin cambios.

**Límite fundamental:** como el login falla, para probar lo posterior se crearon sesiones sintéticas directamente con `app.sesiones.abrir()`. No se elevó el rol PostgreSQL ni se desactivó RLS. Es integración de componentes con sesión de prueba, NO un recorrido completo exitoso desde autenticación.

## Aislamiento y versiones

Se creó `/workspace/custos-integration-20260916-0314`, clon separado, venv y cluster nuevo. PostgreSQL sin TCP (`listen_addresses=''`), socket Unix exclusivo en directorio 0700. HTTP en 127.0.0.1, puerto efímero 42245. Son aislamientos de datos y endpoints dentro de brain-env, no una VM independiente ni una frontera frente a otros procesos del mismo uid.

Python 3.12.14, psycopg y psycopg-binary 3.3.5. No había servidor PostgreSQL ni psycopg instalado inicialmente. `pgserver==0.1.4` aportó PostgreSQL 16.2 pero carecía de uuid-ossp/pgcrypto; no se suprimieron las extensiones del esquema para forzar un verde. Se descargaron paquetes Debian y extrajeron con dpkg-deb a un prefijo privado: PostgreSQL **17.11**, cliente, libpq5, libxml2 y libicu76. No se instalaron servicios globales ni se ejecutó apt install.

**Diferencia respecto del CI:** usa PostgreSQL 16. Esta corrida valida/reproduce en 17.11; no sustituye una matriz de compatibilidad en 16.

El arnés inicia y detiene solo su cluster. Cierre comprobado: `pg_ctl stop` exit 0, después `pg_ctl status` exit 3 con `no server running`. La API se cerró con shutdown/server_close. Se conservaron datos sintéticos y herramientas para reproducir; no quedaron sirviendo. No se tocaron la VM Abacus, el corpus, credenciales de producción ni código del producto. `git diff --exit-code HEAD -- backend infra` devolvió 0.

## Reproducir sin pisar esta evidencia

El instrumento conserva la ruta exacta usada; no es un instalador portable. Para repetir, preparar otra carpeta y cluster, ajustar ROOT en una copia y conservar nueva evidencia. No reejecutarlo sobre una base de producción ni sobre la corrida original: aplica init.sql y vuelve a sembrar fixtures. Dependencias del venv registradas: fasteners 0.20, pgserver 0.1.4, platformdirs 4.11.8, psutil 7.2.2, psycopg 3.3.5, psycopg-binary 3.3.5 y typing_extensions 4.16.0; el motor ejecutado fue el paquete Debian 17.11, no el de pgserver.

## Qué sigue sin probar

Arranque del bloque `api.py __main__` como servicio systemd, proxy/TLS, corpus vivo, concurrencia y carga, reproducción en PostgreSQL 16, exactitud jurídica de plazos, capacidad de entrega en producción y revisión independiente del arnés. Tampoco se agregaron estas pruebas al workflow CI: la petición era ejecutarlas aisladas, no cambiar el pipeline.

## Método

Afirmación -> instrumento -> posibilidad de rojo -> resultado: login operativo -> HTTP+PostgresAlmacen+RLS -> sí -> REFUTADO; rechazo revoca -> eventos SQL ordenados y HTTP -> sí -> REFUTADO; log no expone consulta -> stdout del handler real -> sí -> REFUTADO; cómputo respeta su contrato -> motor y calendario sintético -> sí -> REFUTADO en ese escenario.

Es una corrida de Brain con evidencia cruda publicada, no una certificación independiente por renombrar al ejecutor como auditor. Los controles positivos acotan causas y el código fuente no se cambió, pero el instrumento nuevo requiere revisión externa antes de usarlo como compuerta de aprobación. No se promete un producto listo ni se aplica una puntuación de preparación con estos 18 checks.
