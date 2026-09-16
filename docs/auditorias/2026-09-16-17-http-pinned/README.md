# Custos por HTTP: verificador separado y fijado antes de la corrida

16-sep-2026. Producto: `24e2490442e872498b61a8534dbfe714922fdf3e`, extraído por git archive a directorio nuevo. Verificador: [verifier.py](verifier.py), SHA256 fijado ANTES de ejecutarlo y comprobado DESPUÉS: `516b5f4757ccc2eade0cee4a7f5875075f6dd281d12168bb111b8459f0e14939`.

## Veredicto

**24 comprobaciones HTTP pasan contra el proceso real de Custos.** El mismo verificador falla contra un servidor que siempre responde 200 con JSON vacío. No usa la suite candidata, sus helpers, sus manifiestos ni sus recibos. El resultado lo construye el proceso externo a partir de respuestas HTTP.

No equivale a protección contra un candidato malicioso con acceso de escritura al verificador: ambos procesos ejecutaron como el mismo usuario de brain-env. La separación medida es de código, hash y proceso, no una frontera OS de permisos ni una firma externa. No se cambió CI o producto ni se desplegó nada.

## Preparación independiente

Cluster nuevo PostgreSQL17.11 en carpeta exclusiva, UTF8, socket Unix 0700, sin TCP. Aplicados infra/init.sql y la migración de restricciones de tenants de la revisión candidata. Datos exclusivamente sintéticos: tenants audit-a/audit-b con el mismo email, credencial de prueba y roles socio. El coordinador produjo el hash PBKDF2 con hashlib sin importar almacen.py.

El candidato se arrancó mediante `python -u backend/api.py`, su entrypoint real, con DATABASE_URL_APP y loopback en puerto libre. No recibió DATABASE_URL administrativo. Rol comprobado por SQL: custos_app, rolsuper=false, rolbypassrls=false.

El verificador corrió en OTRO proceso, desde fuera de la carpeta candidata, con biblioteca estándar; no recibió los DSN de base. Los tokens provienen de POST /sesion, no de inyección. No se llamó al corpus vivo: no se consultó /buscar. El canario del log se envió a una ruta de error local.

## Resultados HTTP: valores observados y esperados

Todos los siguientes registros devolvieron passed=true. Las respuestas completas pueden contener tokens y datos sintéticos; el verificador deliberadamente solo registra los valores de los checks.

| Check | Observado | Esperado |
|---|---|---|
| unauthenticated | 401 | 401 |
| bad_password | 401 | 401 |
| valid_login_a | 200 | 200 |
| token_a_present | true | true |
| valid_login_b | 200 | 200 |
| tenant_selection | true | true |
| create_case | 201 | 201 |
| own_case_visible | true | true |
| other_tenant_hidden | true | true |
| unapproved_blocked | 403 | 403 |
| approve | 201 | 201 |
| approved_authorized | 200 | 200 |
| not_executed | AUTORIZADA_PERO_NO_EJECUTADA | AUTORIZADA_PERO_NO_EJECUTADA |
| omitted_case_blocked | 403 | 403 |
| changed_content_blocked | 403 | 403 |
| other_tenant_approval_blocked | 403 | 403 |
| reject_recorded | 201 | 201 |
| rejection_revokes | 403 | 403 |
| deadline_http | 200 | 200 |
| deadline_date | 2026-09-14 | 2026-09-14 |
| unknown_calendar_not_trusted | false | false |
| error_path | 404 | 404 |
| logout | 200 | 200 |
| closed_session_rejected | 401 | 401 |

El escenario de plazo verifica el contrato del caso conocido y su incertidumbre de calendario; no es dictamen jurídico. Se verificó solo ese escenario, no toda la tabla de plazos.

## Control negativo

Se apuntó el MISMO verificador fijado a otro servidor de prueba que respondía siempre HTTP200 y {}. Resultado real: exit1, completed=false, cuatro checks fallidos (sin sesión debería401, password mala debería401, falta token, falta selección de tenant) y dos satisfechos trivialmente (HTTP200 de las solicitudes de login). Error explícito: `RuntimeError: no real login tokens; downstream tests not attempted`.

Ese control demuestra que un endpoint siempre200 no pasa. No es cobertura de todo posible servidor adversarial; un servidor que conozca las expectativas podría fingir respuestas. No se agregó un intérprete de recibos del candidato.

## Cierre observado

```json
{
  "http_exit": 0,
  "negative_exit": 1,
  "api_stopped": true,
  "pg_stop": 0,
  "pg_status": 3,
  "verifier_hash_after": "516b5f4757ccc2eade0cee4a7f5875075f6dd281d12168bb111b8459f0e14939",
  "canary_in_api_log": false,
  "candidate_changed_files": []
}
```

La ausencia de canario fue comprobada por el coordinador leyendo stdout/stderr de la API después de detenerla, no incluida entre los24 checks HTTP. Comparación de todos los archivos de backend/infra con git show de la revisión: sin cambios. API terminada y PostgreSQL detenido, status3 (sin servidor). Fixtures sintéticos conservados sin dejar servicios activos.

## Evidencia y reproducción

El verificador completo ejecutado se versiona junto con este informe. Coordinador original run.py, http-result.json, negative.json, results.json y api.log quedaron en la carpeta custos-pinned-http-20260916 de brain-env. La salida JSON íntegra de cada check se publica en resultados.json junto a esta nota.

Para reproducir usar copia aislada del producto y cluster nuevo, aplicar esquema/migración y sembrar tenants de prueba con la contraseña sintética literal que figura en verifier.py. Arrancar el entrypoint de la API con rol restringido y ejecutar `python3 verifier.py http://127.0.0.1:<puerto-de-prueba>`. No apuntar el verificador a producción: crea un caso y decisiones sintéticas. No reutilizar una base con clientes reales.

## Qué sigue fuera del alcance

PostgreSQL16 en esta corrida (se usó17.11), TLS/proxy, corpus vivo, concurrencia, latencia/carga, retención/exportación, identidad adversarial del proceso, selección exhaustiva de casos y aprobación normativa. No se incorporó este verificador al CI como parte de este pedido; se ejecutó y preservó aparte.

Es un instrumento nuevo que escribí y fijé por hash antes de probarlo: independiente de la suite candidata, no un auditor humano independiente de esta conversación. No se promete inaccesibilidad frente al mismo usuario del sistema operativo.

Rúbrica de revisión acotada: completitud13/15, razonamiento9/10, documentación9/10, innovación5/5, proceso4/5=40/45 (89/100), N/A55. No aprobación de despliegue ni del producto completo.
