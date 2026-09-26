# Recibo de verificación: vertical MVP

**Fecha:** 2026-09-26  
**Rama:** `titan/mvp-vertical-20260926`  
**Base analizada:** commit `3b7aaf139e8123daafd8b3a8e6eb9003ded03688` más los commits de esta rama.

## Instrumento y comandos exactos

Ejecutado dentro del checkout aislado `/workspace/cl`, después de traer esta rama:

```sh
cd backend
python3 -m py_compile mvp_contract.py mvp.py benchmark_busqueda.py test_mvp.py test_benchmark_busqueda.py
python3 test_mvp.py
python3 test_benchmark_busqueda.py
```

## Salida cruda del vertical

```text
OK   documento conserva hash
OK   una cita pasa a allowed_citations
OK   candidato sin vigencia queda unread
OK   precedente derogado queda invalidado
OK   workflow tiene cuatro roles
OK   verificador acepta el borrador
OK   exportación sin aprobación bloquea
OK   aprobación registra hash exacto
OK   DOCX se crea tras aprobación
OK   DOCX contiene document.xml
OK   DOCX contiene la cita
OK   cambio posterior rompe hash
OK   cita sin fuente no es exportable
{"checks": 13, "failures": []}
VERDE benchmark: medido y no medido se distinguen
```

**Exit code:** `0`.

## Regresión existente

También se ejecutó la batería existente de privacidad, calendario, plazos, API, HITL y falsadores junto con el vertical. La corrida devolvió `exit=0`; la suite reportó 53/53, 36/36 y 71/71 en los tres primeros módulos y completó la API/HITL sin error.

`test_rls.py` quedó **NO MEDIDO** en este runtime: requiere `DATABASE_URL` y el módulo `psycopg`, que no están disponibles en el contenedor. No se lo convierte en verde por inferencia.

## Qué demuestra

- El contrato de cita puede dar rojo ante fuente ausente.
- `NO_MEDIDO` y `MEASURED` son estados distintos.
- La aprobación está atada a caso, borrador y hash exacto.
- Un cambio posterior invalida la exportación.
- La exportación DOCX produce un contenedor con `word/document.xml` y cadena de custodia.

## Qué sigue abierto

- Benchmark real de 10-30 consultas contra el corpus autenticado.
- Corrida con un abogado real y caso autorizado.
- Validación externa de vigencia, tabla de días por acto y contenido jurídico.
- RLS contra PostgreSQL 16 en CI o runtime con `psycopg`.
- Integración de estas etapas como rutas del servidor HTTP principal, conservando la autenticación y RLS existentes.

--- METODO TITAN ---
Accion delicada: NO
Modo aplicado:   TITAN FULL
Rubrica:         N/A para recibo de verificación
N/A declarados:  RLS de PostgreSQL, porque el runtime no tenía DATABASE_URL ni psycopg
Review externo:  no pedido; este recibo no equivale a aprobación
Instrumento:     Python 3 en build, comandos arriba, exit 0; salida cruda del vertical incluida
