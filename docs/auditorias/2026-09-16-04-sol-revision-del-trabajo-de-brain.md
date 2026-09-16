# Sol: revisión del trabajo posterior de Brain en Custos

2026-09-16. Alcance: cambios posteriores al cierre de integración de las 03:22 UTC y disponibles al consultar, último commit leído 875378aa906d2889ce46f07edd90d5cf3000db4a. Rol solicitado por Abraham: auditor-sol. No reescribo la autoría de las corridas anteriores ni considero que un cambio de nombre aporte independencia.

## Veredicto

**Brain aportó una reproducción y un experimento causal útil; no corrigió los cuatro defectos del producto.** Contrasté sus afirmaciones con Git y los archivos reales de brain-env, no solo con su relato.

## Confirmado

1. Segunda ejecución: `integration-results.json` del taller indica 04:39:31.343139 a 04:39:35.879868 UTC. Sus 18 registros `checks` coinciden exactamente con la primera corrida respaldada en `corrida1/`. Los hashes de fuentes también coinciden. Resultado numérico reproducido: 14 pasan / 4 fallan.
2. El instrumento conserva SHA256 `80ef0d41c8f3c027888d807d40c1e4bba19ca4ebaa2f6c080bce9eea9a0d2df3`. Las cuatro suites existentes volvieron a registrar exit 0.
3. El falsador del login contrasta control, BYPASSRLS temporal y reversión: contraseña válida 401 -> 200 -> 401; contraseña incorrecta y email inexistente permanecen en 401. Su salida registra rol restaurado sin superusuario ni bypass y cierre del cluster. El log PostgreSQL termina con `database system is shut down`.
4. El JSON del falsador en Git y el del taller son estructuralmente idénticos. Difieren en un byte de espacio final (2456 frente a 2457; iguales después de strip), no en resultados. No corresponde describirlos como idénticos byte por byte, pero no hay diferencia de contenido JSON.
5. No hubo cambios de producto: `git diff --stat 446e17d029751ebeeecbf89bb57417ed91a1fe16 origin/main -- backend infra` no devolvió diferencias. La consulta de PRs de Custos no devolvió ninguno.
6. Su corrección de diez a nueve verdes con sesión sintética es correcta: conté nueve checks aprobados cuyo alcance declara sesión sintética.

## El aporte importante

El verde `wrong password rejected` no demuestra por sí solo validación correcta de contraseñas: con el login bloqueado por RLS también rechaza la contraseña buena. El experimento añadió el control positivo que faltaba por la misma ruta HTTP. Acepto esa corrección a la interpretación de mi instrumento: **14 aserciones satisfechas no equivalen a 14 capacidades independientemente demostradas**.

El brazo BYPASSRLS es un diagnóstico sobre el cluster de prueba, NO una corrección aceptable de producción. No propongo aplicarlo al producto.

## Dos reparos a su revisión

**Duración, afirmación refutada por el instrumento:** su Doc anterior dice que 4,45 segundos no alcanzan para las suites y que esa ventana cubre solo los 18 checks. En `run_integration.py`, `started_utc` se toma antes de arrancar PostgreSQL y de ejecutar las suites por subprocess; `finished_utc` se toma después del cierre. Por construcción, la ventana incluye esas suites. No se puede recortar el alcance por una intuición sobre cuánto deberían tardar.

**Reversión del falsador, debilidad estática:** en `falsador_login.py`, `ALTER ROLE ... NOBYPASSRLS` está en el camino normal, no en `finally`. El finally detiene el cluster pero no garantiza revocar si hay una excepción entre elevar y revocar. La corrida registrada sí revirtió; no afirmo que haya dejado bypass activo. Falta probar una interrupción en ese intervalo antes de afirmar reversión garantizada.

El nombre `search text absent from HTTP log` expresa la propiedad esperada mientras `actual` contiene la presencia del canario: es una etiqueta ambigua, no una inversión de la aserción, porque el valor esperado es False. Conviene renombrar la observación; no altera el rojo medido.

## Qué no se midió que importa

No ejecuté otra vez los tests ni el falsador: revisé las corridas de Brain. No hay correcciones de login, revocación, logs o plazo; sigue faltando recorrido completo desde login, PostgreSQL 16, corpus vivo y validación jurídica. La segunda corrida permanece en archivos de brain-env según la evidencia disponible; el JSON versionado de integración sigue siendo la primera. El falsador nuevo sí está versionado.

Nexus: consulta de reportes, mensajes y eventos desde 03:18 UTC solo devolvió el cierre retrospectivo de auditor-sol. No encontré cierre de Brain sobre este trabajo en esa consulta. El aviso directo que yo había propuesto antes no se envió, pues no recibió confirmación; no afirmo haberle notificado.

## Salida de comparación de esta revisión

```text
falsador_bytes 2456 2457 json_equal True trim_equal True
checks_equal True source_hashes_equal True
baselines [('test_api.py', 0), ('guard_esquema.py', 0), ('test_rls.py', 0), ('test_plazos.py', 0)]
synthetic_passed 9
```

## Fuentes

- [Informe de Brain](https://github.com/gatehot59-star/custos-legis-tarija/blob/875378aa906d2889ce46f07edd90d5cf3000db4a/docs/auditorias/2026-09-16-03-corri-el-instrumento-yo-y-lo-false.md)
- [Falsador](https://github.com/gatehot59-star/custos-legis-tarija/blob/875378aa906d2889ce46f07edd90d5cf3000db4a/docs/auditorias/2026-09-16-integracion-brain-env/falsador_login.py)
- [Resultados del falsador](https://github.com/gatehot59-star/custos-legis-tarija/blob/875378aa906d2889ce46f07edd90d5cf3000db4a/docs/auditorias/2026-09-16-integracion-brain-env/falsador-login-resultados.json)
- [Doc de revisión inicial de Brain](https://app.clickup.com/90171457413/docs/2kza6fw5-11897/2kza6fw5-14157)

## Método

Lectura de commits y patches, fuente completa del falsador, consulta a Nexus y comparación estructural de archivos en brain-env por el servicio build. Sin reinicios, cambios de rol, código de producto ni mensajes. La comparación de checks podía devolver False; el diff podía mostrar cambios; el predicado de cobertura temporal se verificó en el instrumento.

Rúbrica de esta revisión acotada, no del producto: completitud 20/25 (sin nueva corrida ni prueba de excepciones); razonamiento 23/25 (distingue observación y garantía); documentación 22/25 (fuentes, versiones y salida de comparación); proceso 20/25 (contraste de git, taller y Nexus; no certificación independiente de todo el sistema). **85/100: parcial, sin aprobación de producto.** Las corridas previas de esta misma conversación no adquieren independencia retroactiva.
