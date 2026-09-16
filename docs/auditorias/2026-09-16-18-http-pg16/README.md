# El mismo verificador HTTP pasa 24/24 con PostgreSQL 16 real

Ejecución de auditor-sol por pedido de Abraham: repetir el verificador fijado contra PostgreSQL 16. Es una medición propia con evidencia, no una auditoría independiente de mi instrumento.

## Resultado y comparación

PostgreSQL responde `server_version_num=160015`: **16.15 (Debian 16.15-1.pgdg13+2)**. El proceso real `backend/api.py` del candidato `24e2490442e872498b61a8534dbfe714922fdf3e` recibió las peticiones del verificador separado. Las 24 comprobaciones pasaron, exit 0, completed=true. El control siempre-200 fue rechazado: exit 1, cuatro fallos, completed=false. No se importaron tests ni recibos del candidato, y no se inyectaron sesiones: los tokens vinieron del login HTTP.

Mismo candidato y mismos bytes de verificador que la corrida PostgreSQL 17.11 anterior. Se cambió el runtime de PostgreSQL y se crearon fixtures equivalentes en un cluster nuevo, no se reutilizó la base anterior. El coordinador agregó la aserción explícita `160000 <= server_version_num < 170000` y consultó las extensiones instaladas.

Verificador: [verifier.py fijado en git](https://github.com/gatehot59-star/custos-legis-tarija/blob/7bb2f5eae0f1cc55c181efd5cde731f1a2aafe7a/docs/auditorias/2026-09-16-17-http-pinned/verifier.py).

SHA256 antes y después: `516b5f4757ccc2eade0cee4a7f5875075f6dd281d12168bb111b8459f0e14939`.

## Entorno y procedencia

Máquina: brain-env, x86_64, usuario sin privilegios. Paquetes descargados por HTTPS del índice oficial PGDG para trixie, hashes contrastados con ese índice, extraídos con `dpkg-deb -x` en directorio privado. No se instaló un servicio global. No se verificó por separado la firma del índice, por lo que esto no es una certificación de cadena de suministro.

- [Servidor PostgreSQL 16.15](https://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-16/postgresql-16_16.15-1.pgdg13+2_amd64.deb), SHA256 `89e7d4676954a496cd85ce1bae1e94af41a728a098a7043d46a38b704bb8c399`.
- [Cliente PostgreSQL 16.15](https://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-16/postgresql-client-16_16.15-1.pgdg13+2_amd64.deb), SHA256 `82e1dfb1c8f6aed02811c43bff4ead374343ebafe61bca9af3662fc75a83a4b7`.

El bundle 16.2 previo no traía uuid-ossp ni pgcrypto. Se resolvió obteniendo los paquetes completos, **sin quitar ni simular extensiones**. SQL observó pgcrypto 1.3, uuid-ossp 1.1 y plpgsql 1.0. Se reutilizaron las bibliotecas auxiliares privadas de la instalación previa; el servidor ejecutado y consultado fue 16.15.

## Reproducción y custodia

Directorio de esta corrida en brain-env: `/workspace/custos-pinned-http-pg16-20260916`. Contiene `run.py`, `verifier.py`, `candidate/`, `packages.json`, `http-result.json`, `negative.json`, `results.json`, logs de API y PostgreSQL y el cluster ya detenido. Son rastros locales; la evidencia durable de resultados está en este directorio de git.

Coordinador ejecutado: `/workspace/custos-integration-20260916-0314/venv/bin/python /workspace/custos-pinned-http-pg16-20260916/run.py`. SHA256 del coordinador `4aa6c16809fd8fc48c010ce91a7003e9cafb6052b8a271d559c878a04c4c1f62`.

El coordinador extrae `git archive 24e2490442e872498b61a8534dbfe714922fdf3e`, inicializa PostgreSQL UTF8 sin TCP y con socket 0700, aplica intactos `infra/init.sql` y `infra/2026-09-16-cierra-el-borrado-de-un-bufete.sql`, y siembra dos tenants sintéticos `audit-a`/`audit-b`. Usa email `same@audit.invalid`, contraseña sintética `SYNTHETIC-ONLY-HTTP-20260916`, PBKDF2 SHA256 200000 iteraciones con sal aleatoria y rol socio. El hash de contraseña se calcula sin importar auxiliares del candidato.

Arranca `backend/api.py` por su entrypoint en proceso separado, con `DATABASE_URL_APP` del usuario `custos_app`, host 127.0.0.1 y puerto libre. SQL verificó que ese rol no es superusuario ni BYPASSRLS. Espera `/salud` y ejecuta `python3 verifier.py http://127.0.0.1:<puerto-asignado>` fuera del árbol candidato, quitando DATABASE_URL, DATABASE_URL_APP y PYTHONPATH del ambiente del verificador. Repite el mismo instrumento contra un servidor local siempre-200 como control negativo.

Finalmente detuvo API y PostgreSQL: api_stopped=true, pg_stop=0, pg_status=3. Comparó todos los archivos backend/infra contra git: ninguna diferencia. El canario de query estuvo ausente en el log de la ruta de error; es una observación del coordinador, no un check adicional entre los 24.

## Alcance y lo que no prueba

Cierra el hueco de versión 16 para estos 24 checks: autenticación, separación de tenants, caso propio/ajeno, aprobación y revocación, restricciones por contenido/caso, fecha penal del contrato sintético, calendario no confiable y cierre de sesión.

No acredita seguridad integral, exactitud jurídica completa, rendimiento, concurrencia, `/buscar`, corpus vivo ni despliegue. No ejecutó un nuevo CI y no modificó los PR3/4/5. La separación de procesos con mismo uid no aísla contra un candidato malicioso capaz de alterar archivos o fabricar respuestas específicas. El control siempre-200 demuestra rechazo de ese fallo, no de todo servidor falso posible.

## Antes de firmar

- PostgreSQL 16 real -> consulta SQL de versión con aserción de rango -> podía fallar ante 17 -> confirmado para esta corrida.
- 24 contratos HTTP -> verificador fijado y proceso API real -> podía fallar, control negativo rechazado -> confirmado para los checks enumerados en resultados.json.
- Producto listo para producción -> este instrumento no cubre todas las superficies -> NO MEDIDO.

## Método y error propio

TITAN LIGERO, ejecución acotada sin código de producto, merges, despliegues ni cambios de permisos. Rúbrica formal N/A. Evidencia e interpretación separadas. El primer intento de descarga usó saltos de línea que el transporte convirtió en literales y falló antes de ejecutar Python; se corrigió la forma de transporte, sin cambio de objetivo ni de verificador.
