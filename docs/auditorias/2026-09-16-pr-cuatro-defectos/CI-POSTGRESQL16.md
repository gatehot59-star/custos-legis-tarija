# El CI corrio en PostgreSQL 16, y las corridas incompletas dieron ROJO

Esto cierra el unico NO MEDIDO que quedaba del punto 5 del encargo. Las corridas
de brain-env fueron sobre PostgreSQL **17.11**, porque el 16 embebido del taller
no trae las extensiones. La version del CI es la que manda, y ahora esta medida.

Consultado por la API publica de GitHub (`/actions/workflows/api-e2e.yml/runs`),
que devuelve campos estructurados. No es el mensaje de un commit ni un log que
pueda citarme a mi mismo.

## La progresion es un falsador que no planee, y es el mejor dato

| corrida | commit | que habia | conclusion |
|---|---|---|---|
| 1 | `a7ca3683` | solo el workflow, cero arreglos | **failure** |
| 2 | `37ff83e3` | + `almacen.py` (D1) | **failure** |
| 3 | `13f70c52` | + `api.py` (D2, D3) | **failure** |
| 4 | `212779b6` | + `plazos.py` (D4) | **success** |

Y el paso exacto que fallo en la corrida 3, leido de la API:

    11 failure  REGRESIONES e2e desde login REAL (sin sesiones inyectadas)
    12 skipped  FALSADOR DEL CI - con el defecto de vuelta esto DEBE dar rojo
    13 skipped  el arbol quedo sin modificar

O sea: con D1, D2 y D3 corregidos pero **D4 sin corregir**, el CI dio ROJO en el
paso que corresponde. **Este CI puede detectar los defectos que dice cubrir**, y
no hace falta creerme: el rojo esta en el historial de Actions y es de GitHub, no
mio.

Eso era exactamente el hueco que la auditoria del 15-sep habia medido: el CI
anterior pasaba verde con el login roto porque no ejecutaba `test_api.py`, ni
`guard_esquema.py`, ni el adaptador `PostgresAlmacen`.

## Los 13 pasos de la corrida 4, verdes, en `postgres:16`

     1 success  Set up job
     2 success  Initialize containers
     3 success  Run actions/checkout@v4
     4 success  instalar cliente y driver
     5 success  version del motor (queda escrita, no se asume)
     6 success  aplicar el esquema
     7 success  CONTROL DEL INSTRUMENTO - el rol de la app no tiene atajos
     8 success  guard del esquema
     9 success  suite de API
    10 success  RLS con PostgresAlmacen real
    11 success  REGRESIONES e2e desde login REAL (sin sesiones inyectadas)
    12 success  FALSADOR DEL CI - con el defecto de vuelta esto DEBE dar rojo
    13 success  el arbol quedo sin modificar

runner `ubuntu-24.04`, job `api-e2e`, conclusion `success`.

Tres pasos que valen mas que los otros diez:

- **7** verifica que `custos_app` no sea superusuario ni tenga BYPASSRLS. Sin ese
  control, los 40 checks de aislamiento de abajo serian un verde vacio.
- **12** reintroduce el bug del gate (invierte el orden de las decisiones) y
  EXIGE que la suite falle. Si pasara, el job se cae con "este CI no puede
  detectar el bug que dice cubrir". Que este verde significa que el CI
  discrimina.
- **13** confirma que el paso 12 dejo el arbol como lo encontro.

## Y lo que se verifico DESPUES de subir los archivos

Los tres archivos del backend no se subieron byte por byte iguales a los que
medi en brain-env: al pasarlos por la API de GitHub tambien corregi tres
docstrings que habian quedado viejos (decian que `PostgresAlmacen` nunca se habia
ejecutado, y que la Ley 1173 no estaba verificada; las dos cosas ya eran falsas).

**Un cambio de comentario "no puede romper nada" es justo la clase de suposicion
que este proyecto no acepta.** Asi que se bajaron los tres archivos DESDE GIT al
taller y se volvio a correr la verificacion completa: **7 de 7 suites verdes**
con exactamente lo que quedo versionado. La corrida 4 del CI lo confirma de forma
independiente sobre PostgreSQL 16.

## Lo que sigue NO MEDIDO

- Corpus vivo, proxy/TLS, produccion, concurrencia, arranque `__main__` como
  servicio.
- La tabla de plazos por acto sigue `HIPOTESIS`: se verifico el art. 130 CPP para
  el arranque cautelar, no toda la legislacion.
- Un testigo que no sea yo. El CI de GitHub es evidencia EXTERNA y eso cambia
  algo real, pero el instrumento lo escribi yo.
