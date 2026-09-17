# Estado medido del corpus y qué sugiere Sol, 2026-09-16 23:46 ART

## Pedido
Revisar el estado del corpus, qué está auditado por Sol y qué sugiere.

## Herramientas declaradas
- SSH a la VM Abacus vía `cloudflared access ssh`, **solo lectura**: `systemctl is-active/is-enabled/show`, `ss -tlnp`, `curl` a `127.0.0.1:8080`, `ps`, `pgrep`, `df`, `free`, `/proc/loadavg`, `cat` del config del túnel. Cero escrituras, cero reinicios, cero cambios de servicio.
- API de GitHub: lectura de `docs/auditorias/`, PRs abiertos y recibos.
- `sqlite`/`nexus.db`: `query` (lectura de mensajes 200, 204, 205 y del rango 199-213).
- Script propio: `/tmp/corpus-check.sh`. Cuota ajena: la VM es del corpus; por eso se midió el servicio antes que cualquier otra cosa.

## 1. Corpus vivo: VERDE, y el endurecimiento de la semana pasada SOBREVIVIÓ

Evidencia cruda, medida hoy:

```
corpus-api           active / enabled     (arriba desde Wed 2026-09-16 10:54:27 UTC)
cloudflared-corpus   active / enabled
nginx                active / enabled
gitea                active / enabled

LISTEN 127.0.0.1:3000   pid=201501
LISTEN 127.0.0.1:8080   pid=201508
LISTEN         *:2222   pid=201501

  intento1 http=200 t=0.348644s
  intento2 http=200 t=0.363380s
  intento3 http=200 t=0.348655s
  total_pasajes: 32896

ingress: hostname corpus-vm.icca-engine.com -> ssh://localhost:22 ; luego http_status:404
ufw -> Status: inactive

  load: 0.18 0.12 0.10
  disco: /dev/root  48G  18G  30G  38% /
  ram:   total 7957  used 5734  free 223  buff/cache 2255  available 2223
```

Tres cosas que el 9-sep estaban en rojo y hoy están cerradas, verificadas por mí y no leídas de un recibo ajeno:

1. **El bind aguantó**: `8080` sigue en `127.0.0.1`, no volvió a `0.0.0.0` tras el reinicio de hoy.
2. **Gitea bajó a loopback**: el 9-sep escuchaba en `*:3000`, hoy en `127.0.0.1:3000`.
3. **El espejo quedó privado y el token murió**:

```
  sin_token_http=404      (private: None | mensaje: The target couldn't be found.)
  token viejo del 198 -> 401
  CONTROL NEGATIVO basura -> 401
```

**Límite del instrumento, declarado:** el control negativo también da 401, así que este medición prueba "ese token ya no autentica", no distingue revocado de inválido. No tengo token válido para control positivo.

## 2. EL ROJO ES MÍO Y LLEVA NUEVE DÍAS

```
  21526  9-13:28:33  49.7 %MEM  6.3 %CPU
  procesos qemu: 1
```

Mi emulador huérfano, el que reporté el 9-sep con 2 días, hoy lleva **9 días y 13:28** y se come el **49,7% de la RAM** de la máquina del corpus. El disco pasó de 14G a **18G** en la semana. La carga sigue baja (0,18), o sea que el daño medido es RAM y disco, no CPU, y el corpus responde en 0,35 s.

No lo apagué: es cambio de estado en una máquina con producción. Pero lo reporté hace una semana y sigue vivo: eso es deuda mía, no de nadie más.

## 3. Dato que refuta el mensaje 200 de Tachi

```
  postgresql: inactive
  procesos postgres: 0
  KAPE IR: ls: cannot access '/workspace/correai': No such file or directory
```

El mensaje 200 dice "El proyecto KAPE IR está en `/workspace/correai`" refiriéndose a la VM. En la VM **no existe** esa ruta y **no hay Postgres corriendo**. Custos no se ejecuta en la VM: su base y su CI viven en brain-env y en Actions. Quien siga esa instrucción al pie pierde el turno.

## 4. Qué auditó Sol, y una corrección de atribución mía

**Casi le atribuyo a Sol documentos que no puedo probar que sean suyos.** Los archivos `docs/auditorias/2026-09-16-14-*` y `-16-*` no llevan el prefijo `sol-` y declaran, textual, "autocrítica de un supervisor que implementé en esta conversación, **no revisión independiente**". Por W-01, esa serie (12, 14, 16) es un autor midiendo su propio instrumento: no cuenta como testigo independiente, y el propio texto lo dice.

Lo auditado, por sujeto exacto:

- **`2026-09-16-10-sol-auditoria-main-terminacion-falsador.md`**: esta SÍ es revisión de MI trabajo. Confirma que PR #1 y #2 están mergeados a main con evidencia estructural (dos padres de git más la API por PR, después de que el listado de PRs le devolviera `merged=false` y **no lo aceptó** como veredicto), 4 checks en verde en `4a14f06`, y los 7 tests del falsador en verde corriendo desde `git archive`. Y me deja un rojo: **objetivo seguido de `RuntimeError` pasa el FALSADOR 2** con exit del paso 0, porque una excepción también sale 1 y no agrega otra línea `ROJO`.
- **PR #3, #4 y #5** (`titan/tester-suite-completion`, `-required-check-policy`, `-phase-supervisor`): los tres siguen **abiertos y en draft**, y los tres tienen su propio informe diciendo **"no aprobación de PR"**. Lo reproducido en los tres: se puede emitir un recibo `completed=true`, `cleanup_returned=true` con 45 checks **sin ejecutar ninguna fase**, con política, runner y workflow con hash idéntico antes y después. Y el hash de la suite lo calcula la misma corrida: "el hash asegura coincidencia con un archivo, no aprobación independiente de ese archivo".

## 5. Qué sugiere Sol

### Sobre el corpus (recomendación a Abraham, `docs/agents/respuestas/2026-09-16-19`)

**Corpus primero: piloto cerrado en dos universidades, sin esperar la biblioteca perfecta**, y Custos en mantenimiento acotado de defectos críticos mientras dure. No más agentes ni miles de documentos antes de medir utilidad con personas.

Cinco precondiciones antes de circular el enlace: colección revisada y apta (si la anonimización de jurisprudencia sensible no está validada, **excluirla**); mostrar fuente, fecha y límites del OCR sin fabricar vigencia; identificar la revisión desplegada con acceso revocable y recuperación de backup probada; circuito de feedback con responsable y trato privado; y acuerdo previo con los docentes. Diseño: un corpus y una versión, dos grupos distinguibles, 4 semanas, 10-15 participantes por universidad, más **al menos dos abogados en ejercicio**, porque "que lo usen estudiantes no demuestra que un bufete pagaría". Feedback dentro del producto con categorías y estados, y **sin registrar el texto completo de las búsquedas**.

Dato que corrige el discurso del repo: `README` y `CONTEXTO-CUSTOS-LEGIS.md` siguen diciendo "cero código" y están **desactualizados**, contradichos por 24/24 contratos HTTP verdes con el mismo verificador fijado en PostgreSQL 17.11 y 16.15.

### Sobre el instrumento de tests

No ampliar más el `grep` por síntomas ni agregar otra etiqueta o contador para prometer autenticidad. La suite debe emitir un resultado **estructurado escrito solo después** de completar controles y limpieza, con identidad del escenario, cantidad de checks y lista exacta de fallos; el falsador debe exigir finalización completa y únicamente el fallo objetivo, y **cualquier excepción invalida el experimento**. Y si el objetivo es resistir una suite adulterada, el verificador tiene que ser código fijado **fuera del control del candidato**, con procesos y permisos separados. Revisar también el FALSADOR 1, que comparte la estrategia y no se reprodujo.

## 6. Me refuto una objeción propia

El 16-sep a las 23:05 le reclamé (mensaje 213) que el encargo del contrato jurídico del mensaje 212 seguía "sin hacer después de diez turnos". El informe 10 lo responde y tiene razón: **no lo ejecutó a propósito**, porque "no ejecuté la nueva decisión de producto que Brain dejó en Nexus como si fuera una instrucción directa del usuario". Le pedí una decisión normativa por un canal que no es el del usuario. El reclamo era mío mal puesto, no incumplimiento suyo.

## 7. Veredicto en tres estados

- **Corpus vivo:** VERDE. Servicio arriba, 32.896 pasajes, 0,35 s, loopback, túnel solo SSH.
- **Endurecimiento de la semana pasada:** VERDE y persistente (bind, Gitea en loopback, espejo privado, token muerto).
- **Emulador huérfano mío:** ROJO, 9 días, 49,7% de RAM. Espera orden.
- **PR #3/#4/#5 del instrumento:** ROJO por diseño declarado, los tres en draft sin aprobación.
- **Piloto universitario:** NO EJECUTADO. Es una recomendación, no una decisión tomada; ninguna universidad fue elegida ni contactada.
- **NO MEDIDO:** colección completa del corpus (el número de 6.079 documentos es del snapshot del 9-sep y hoy no se recontó); anonimización; sesiones web de Gitea; superficie SSH; y si el token viejo está revocado o solo inválido.

## 8. Archivos generados
- `docs/agents/respuestas/2026-09-16-21-estado-medido-del-corpus-y-lo-que-sugiere-sol.md` (este archivo)
