# Evidencia cruda de la corrida (2026-09-16, brain-env)

Todo lo de abajo salio de `verificar.py` y `falsador_login_v2.py`, los dos
commiteados en este directorio. Los logs por suite quedaron en brain-env como
`verificar-<suite>.log`.

## 1. CON EL ARREGLO: 7 de 7 suites verdes

    ventana        2026-09-16T05:28:24.550987Z -> 05:28:30.414847Z
    motor          PostgreSQL 17.11 (Debian) x86_64
    rol de la app  ['custos_app', False, False]   <- sin superusuario, sin BYPASSRLS

    test_api.py                  exit=0
    guard_esquema.py             exit=0
    test_rls.py                  exit=0
    test_plazos.py               exit=0
    test_anonimizador.py         exit=0
    test_calendario.py           exit=0
    test_regresiones_hitl.py     exit=0
    suites_verdes: 7 | suites_rojas: 0

    pg_stop_rc 0 | pg_ctl status despues del stop: 3 (no server running)

## 2. CONTROL NEGATIVO: con el codigo viejo, 26 ROJOS

Se revirtio `backend/almacen.py`, `api.py` y `plazos.py` con `git checkout` y se
volvio a correr la MISMA suite. Si hubiera pasado igual, las regresiones no
servirian para nada.

    test_regresiones_hitl.py     exit=1
    rojos: 26

    ROJO viernes + 3 dias cautelares vence el lunes 14: obtenido '2026-09-16', esperado '2026-09-14'
    ROJO el dia 1 es el sabado 12, no el lunes: obtenido ['2026-09-14'], esperado ['2026-09-12']
    ROJO ultimo dia inhabil NO se declara confirmado: obtenido True, esperado False
    ROJO y dice por que: obtenido False, esperado True
    ROJO D1 credencial valida por HTTP+RLS da 200: obtenido 401, esperado 200
    ROJO D1 devuelve token real: obtenido False, esperado True
    ROJO D1 y resuelve el bufete correcto: obtenido None, esperado '8d1a0b43-...'
    ROJO D1 el mismo email en el bufete B resuelve a B: obtenido 401, esperado 200

Y las OTRAS seis suites siguieron en verde con el codigo defectuoso. Eso es
exactamente el hueco que el encargo pedia cerrar: **las suites que ya existian
no podian dar rojo por estos cuatro defectos.**

## 3. Los 41 checks de la regresion, con el arreglo

    === D4. Arranque del plazo cautelar penal (art. 130 CPP) ===
      OK   viernes + 3 dias cautelares vence el lunes 14: '2026-09-14'
      OK   el dia 1 es el sabado 12, no el lunes: ['2026-09-12']
      OK   modo corridos: 'corridos'
      OK   civil corto sigue arrancando el dia siguiente HABIL: ['2026-09-14']
      OK   civil corto vence el miercoles 16: '2026-09-16'
      OK   civil de 16 dias es CORRIDO pero arranca el lunes 14: ['2026-09-14']
      OK   civil de 16 dias corridos vence el 29-sep: '2026-09-29'
      OK   y su modo es corridos (el control discrimina de verdad): 'corridos'
      OK   ultimo dia inhabil NO se declara confirmado: False
      OK   y dice por que: True
      OK   FALSADOR: la regla vieja da lunes 14 como dia 1: '2026-09-14'
      OK   FALSADOR: vieja y nueva DIFIEREN, el test discrimina: True

    === D1/D2/D3 contra PostgreSQL REAL, rol de aplicacion ===
      OK   el rol de la app NO es superusuario: False
      OK   el rol de la app NO tiene BYPASSRLS: False
      OK   D1 credencial valida por HTTP+RLS da 200: 200
      OK   D1 devuelve token real: True
      OK   D1 y resuelve el bufete correcto: '6d07cfe4-...'
      OK   D1 password mala da 401: 401
      OK   D1 email inexistente da 401: 401
      OK   D1 bufete inexistente da 401: 401
      OK   D1 sin bufete da 401 (el email esta en DOS bufetes): 401
      OK   D1 el mismo email en el bufete B resuelve a B: 200
      OK   D1 y NO cruza al bufete A: 'abc9d12e-...'
      OK   e2e crear caso con token de login real: 201
      OK   e2e aislamiento POSITIVO: A ve su caso: True
      OK   e2e aislamiento NEGATIVO: B no ve el caso de A: False
      OK   D2 sin ninguna decision: 403
      OK   D2 aprobacion registrada: 201
      OK   D2 con aprobacion vigente: 200 (control POSITIVO)
      OK   D2 rechazo posterior registrado: 201
      OK   D2 EL DEFECTO: tras el rechazo la accion se BLOQUEA: 403
      OK   D2 aprobacion nueva registrada: 201
      OK   D2 una aprobacion NUEVA vuelve a habilitar: 200
      OK   D2 contenido alterado: 403
      OK   D2 otro tipo de accion: 403
      OK   D2 la aprobacion de A no sirve para B: 403
      OK   D3 la busqueda responde: 200
      OK   D3 la ruta de error tambien responde: 404
      OK   D3 el canario NO aparece en el log del handler real: False
      OK   D3 pero el log SI registra la ruta (no quedo mudo): True
      OK   GUARD: el trigger de inmutabilidad bloquea el DELETE en cascada: True

    verdes: 41 | rojos: 0 | VERDE

## 4. Falsador del login v2: 14 de 14, con excepcion inyectada

    === 0. Estado heredado del rol (defensa contra SIGKILL previo) ===
      OK   al arrancar, custos_app NO tiene bypass heredado: False
      OK   ni es superusuario: False

    === 1. Con el arreglo del login aplicado, el rol REAL alcanza ===
      OK   password correcta da 200 SIN bypass: 200
      OK   password incorrecta da 401: 401
      OK   y el check de password mala DISCRIMINA (no son los dos 401): True
      OK   sin bufete da 401: 401
      OK   bypassrls seguia apagado: False

    === 2. EXCEPCION INYECTADA justo despues de elevar ===
      OK   el privilegio SI estuvo puesto (el brazo no fue vacio): True
      OK   tras la excepcion, bypassrls quedo REVOCADO: False
      OK   y el error original se conservo: 'fallo simulado con el privilegio puesto'

    === 3. Brazo BYPASSRLS: confirma la CAUSA del 401 historico ===
      OK   sin set_tenant y sin bypass, users devuelve CERO filas: 0
      OK   con BYPASSRLS la misma consulta devuelve la fila: 1
      OK   tras revocar vuelve a cero (reversion verificada): 0
      OK   y el rol quedo sin bypass: False

    verdes: 14 | rojos: 0
    rol final: ('custos_app', False, False)

El punto 1 cierra el falso verde que yo mismo habia cazado: antes
`wrong password rejected` daba 401 **por la misma causa** que el rojo del login,
asi que no discriminaba. Ahora 200 contra 401: discrimina.

## 5. Lo que NO se midio

- **PostgreSQL 16.** Las dos corridas fueron sobre 17.11, porque el 16 embebido
  del taller no trae las extensiones. El workflow nuevo `api-e2e.yml` corre
  sobre `postgres:16`, pero **su primera corrida real todavia no existe**: eso
  lo dispara el push del PR.
- **Corpus vivo, proxy/TLS, produccion, concurrencia.** Fuera de alcance.
- **La exactitud juridica de la tabla de plazos por acto.** Se verifico el art.
  130 CPP para el arranque cautelar; el resto de la tabla sigue marcado
  HIPOTESIS en el codigo.
- **Un testigo que no sea yo.** El falsador cierra el hueco del instrumento, no
  el del operador.
