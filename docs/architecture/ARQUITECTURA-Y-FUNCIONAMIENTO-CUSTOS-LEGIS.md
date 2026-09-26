# Custos Legis Tarija: arquitectura y funcionamiento real

**Fecha:** 2026-09-26  
**Estado de esta nota:** arquitectura medida sobre el código de `main`; separa lo implementado de lo diseñado y todavía ausente.

## 1. Qué producto es

Custos Legis es un SaaS multi-inquilino para bufetes de Tarija. Su núcleo debe vigilar plazos judiciales, consultar fundamentos, conservar expedientes privados y preparar escritos, pero el abogado decide siempre al final. Ninguna acción externa debe salir sin aprobación de un abogado habilitado, con matrícula, sobre el hash exacto del contenido aprobado.

La frontera con `corpus-legal-tarija` es obligatoria: el corpus es otro producto, independiente y vendible. Custos lo consume por HTTP y no lee su SQLite, no copia su base y no le agrega multi-tenancy, expedientes ni plazos.

## 2. Arquitectura que existe hoy

```text
Cliente HTTP / futura UI
          |
          v
ThreadingHTTPServer stdlib, loopback 127.0.0.1:8090
          |
          v
backend/api.py: App + sesiones + rutas + gates
     |             |                 |
     |             |                 +--> backend/plazos.py
     |             |                 +--> backend/anonimizador.py
     |             +--------------------> backend/corpus_cliente.py --> corpus por HTTP
     +----------------------------------> backend/almacen.py --> PostgreSQL + RLS
                                                        |
                                                        +--> tenants, users, cases
                                                        +--> documents
                                                        +--> cl_checkpoints
                                                        +--> agent_runs
                                                        +--> aprobaciones
                                                        +--> uso_consultas
```

Esto no es todavía el diseño completo de producción del documento original. Es el núcleo ejecutable que existe y que CI verifica. La API formal FastAPI, el frontend, el grafo LangGraph de seis agentes, Redis, Celery, Qdrant, scraper judicial, facturación y despliegue de Custos no existen todavía.

## 3. Capas y responsabilidad de cada una

### 3.1 API y sesión

`backend/api.py` levanta un `ThreadingHTTPServer` de la biblioteca estándar. Por defecto escucha en loopback, no en `0.0.0.0`. El proceso exige `DATABASE_URL_APP`, prueba la conexión antes de empezar a servir y termina con error si PostgreSQL no está disponible. Esto evita que systemd vea un servicio arriba que falla recién con el primer request.

Las únicas rutas públicas son `GET /salud` y `POST /sesion`. Todo lo demás exige `Bearer token`:

- `POST /sesion`: busca por bufete y email, verifica PBKDF2-SHA256 con comparación constante y crea una sesión de 8 horas.
- `DELETE /sesion`: cierra la sesión.
- `GET /buscar`: consulta el corpus, aplica la compuerta de privacidad y registra uso con hash de la consulta.
- `GET /casos`, `POST /casos`: lista o crea expedientes del bufete autenticado.
- `GET /plazo`: calcula un vencimiento solo para materias modeladas y devuelve el cómputo día por día.
- `POST /aprobar`: registra una decisión de abogado, aprobada o rechazada.
- `POST /acciones/externa`: comprueba el gate HITL. Autoriza, pero no simula ejecución.
- `GET /uso`: informa el número de consultas registradas.

Los logs no imprimen la query string ni el cuerpo HTTP. Esto importa porque una búsqueda jurídica puede revelar la estrategia de un caso y una URL puede contener credenciales o datos privados.

### 3.2 Persistencia y aislamiento entre bufetes

`PostgresAlmacen` es el camino de producción. Cada operación abre una transacción y ejecuta `app.set_tenant(tenant_id)` antes de tocar datos. PostgreSQL aplica `FORCE ROW LEVEL SECURITY` sobre usuarios, expedientes, documentos, checkpoints, corridas de agentes y aprobaciones. El rol `custos_app` no tiene `BYPASSRLS`.

`tenants` queda fuera de RLS porque lo administra el servicio para resolver el bufete durante el login. Después, el usuario se lee dentro del tenant ya resuelto. El mismo email puede existir en dos bufetes, por eso el login sin `bufete` se rechaza en vez de elegir una fila arbitraria.

`SqliteAlmacen` solo sirve para probar el cableado HTTP. Exige un flag explícito, se niega en entorno de producción y no se considera evidencia de aislamiento. El aislamiento real se prueba contra PostgreSQL 16 en CI.

### 3.3 Modelo de datos sensible

- `cases`: expedientes, sistema de origen, materia, juzgado, estado y vencimiento.
- `documents`: documentos privados del bufete. `texto_crudo` es inmutable mediante trigger; las correcciones viven en `texto_normalizado`.
- `cl_checkpoints`: estado sensible del futuro grafo, incluido memorial, estrategia y documentos privados. Tiene tenant, caso, RLS y un trigger que exige que `thread_id` contenga el tenant.
- `agent_runs`: modelo, tokens, duración, resultado y `costo_usd`. El costo por caso todavía no está medido, pero el instrumento existe.
- `aprobaciones`: evidencia inmutable de una decisión humana. Guarda matrícula, usuario, tipo, `sha256_entrada`, decisión y fundamento. Cambiar de opinión crea un evento nuevo, no edita el anterior.
- `uso_consultas`: guarda `q_hash`, longitud, latencia y cantidad de resultados, no el texto de la búsqueda.

## 4. Funcionamiento de extremo a extremo

### Flujo A: login y contexto de bufete

1. El cliente envía email, contraseña y slug del bufete.
2. El servicio resuelve el tenant en `tenants`.
3. Dentro de una transacción con ese tenant, lee el usuario bajo RLS.
4. Verifica PBKDF2-SHA256. Para un email inexistente también ejecuta una verificación contra un hash imposible, evitando una respuesta temporalmente distinta.
5. Devuelve un token aleatorio con TTL de 8 horas y el tenant queda asociado a la sesión.
6. Si no hay tenant, el acceso a datos no se amplía: se levanta `SinTenant`.

### Flujo B: búsqueda jurídica

1. `GET /buscar?q=...` pasa por sesión.
2. `CorpusHTTP` llama al contrato HTTP del corpus independiente. No conoce ni toca su base.
3. El cliente normaliza cada resultado en tres estados de vigencia: `VIGENTE`, `DEROGADA` o `NO_MEDIDO`. La ausencia de dato nunca se convierte en vigente.
4. `anonimizador.evaluar()` clasifica por naturaleza del documento y aplica una compuerta fail-closed:
   - reserva legal: `RESERVA_LEGAL`, nunca se publica ni se anonimiza;
   - clase desconocida: `RETENIDO`;
   - normativa: puede mostrar texto, salvo que aparezca una parte identificable;
   - jurisprudencia: la capa abierta muestra ficha, cita, hash y enlace oficial, pero no texto libre;
   - extracto jurisprudencial seudonimizado: solo después de aprobación con matrícula.
5. La respuesta incluye `decision_compuerta`, razones y la advertencia de vigencia.
6. Se registra solo `sha256(q.lower())`, resultados y latencia.

La compuerta no confía en que un regex encuentre todos los nombres. Cuatro textos adversarios medidos escaparon al detector, por eso el control fuerte es no publicar texto libre jurisprudencial. Sobre el corpus medido, solo 17,3% de los documentos es normativo y 82,7% jurisprudencial: la aprobación por matrícula no es un caso raro, es el camino principal para cinco de cada seis documentos.

### Flujo C: expediente

1. El abogado crea un caso con expediente, juzgado y materia.
2. El sistema lo escribe con `tenant_id` y PostgreSQL impide que otro bufete lo lea o modifique.
3. Si la materia no tiene motor de plazos, el caso se crea con advertencia explícita. No se inventa un vencimiento.
4. Los documentos del caso se guardarían en `documents`, con crudo inmutable, hash y vía de extracción declarada: PDF nativo, OCR o carga manual.

### Flujo D: cálculo de plazo

1. El cliente envía fecha de notificación, cantidad de días, materia y, si corresponde, medida cautelar.
2. `materia_modelada()` acepta hoy solo civil y penal. Familia, laboral, administrativo, tributario, constitucional, agroambiental y niñez/adolescencia permanecen `NO_MEDIDO`.
3. Civil aplica el umbral de 15 días de la Ley 439: hasta 15, días hábiles; más de 15, hábiles e inhábiles. Penal aplica días hábiles, salvo cautelares penales, que usan días corridos.
4. Se excluyen fines de semana, feriados y vacaciones judiciales cargadas por departamento.
5. La respuesta no es una fecha muda: incluye estado `CONFIRMADO`, `HIPOTESIS` o `NO_MEDIDO`, fundamento, advertencias y el detalle de cada día.
6. Sin circular judicial que cubra el año, la fecha puede aparecer como orientativa, pero el estado es `NO_MEDIDO` y la API ordena no usarla para presentar un escrito.
7. La hora civil de cierre del juzgado sigue sin medir. El default de 18:00 está marcado como supuesto. En penal se usa 23:59:59.

### Flujo E: aprobación humana y acción externa

1. Un socio o asociado con matrícula registra `POST /aprobar` sobre un tipo de acción y contenido exacto.
2. El sistema guarda el SHA-256 del contenido, caso, matrícula, usuario y decisión.
3. Antes de autorizar una acción externa, `exigir_aprobacion()` busca decisiones del mismo tenant, tipo, caso y hash exacto.
4. Ordena por timestamp e ID. La última decisión manda: un rechazo posterior revoca una aprobación anterior.
5. Sin matrícula, sin caso coincidente, sin hash coincidente o con último rechazo, responde 403 y no ejecuta.
6. Si todo coincide, responde `AUTORIZADA_PERO_NO_EJECUTADA`. No existe aún integración con SIREJ, SIGC, firma digital ni envío al juzgado, y la API no finge que sí.

## 5. Arquitectura objetivo, todavía no construida

El diseño futuro puede agregar un frontend y una API formal delante del mismo núcleo, un orquestador LangGraph con seis nodos, workers asíncronos y almacenamiento de checkpoints. Eso solo debe ocurrir después de que un abogado use el núcleo real.

La arquitectura objetivo no debe meter todo en la VM del corpus: esa máquina tiene 2 núcleos, 8 GB de RAM, sin swap y ya sirve el buscador. La recomendación es una VM separada para Custos. Qdrant tampoco entra por reflejo: primero hay que comparar BM25/léxico contra vectorial con 10 consultas reales. Para consultas con número de artículo o expediente, el corpus declara que la búsqueda léxica puede ser mejor.

## 6. Estado y límites que no se deben maquillar

**Verificado:** 176 aserciones verdes, 18 falsadores, compuerta de privacidad, motor de plazos, calendario, RLS real, API HTTP, cliente del corpus y gate HITL.

**No existe:** seis agentes, FastAPI formal, frontend, scraper, Qdrant, facturación, integración judicial y despliegue de Custos.

**No medido:** uso por abogados, recall de la compuerta contra todo el texto real, distribución por pasajes del 17,3%, tabla completa de días por acto, vigencia completa del corpus, costo por caso, hora de cierre de juzgados y legalidad operativa del acceso automatizado a expedientes.

## 7. Orden correcto para retomar

1. Probar el núcleo con un abogado real y un caso real.
2. Exponer el motor de plazos en una UI mínima: es la primera pieza vendible.
3. Decidir la política de la compuerta sabiendo que retiene 82,7% de los documentos.
4. Cambiar `corpus_cliente.py` del endpoint público cerrado al contrato autenticado con API key y scope.
5. Cerrar con abogado la tabla de plazos, reservas legales y tratamiento de datos.
6. Recién después construir agentes, FastAPI, workers, Qdrant o integraciones.

**Regla de diseño:** una fecha dudosa debe decir `NO_MEDIDO`; un texto sensible debe quedar retenido; una acción externa debe exigir aprobación sobre el hash exacto; y un dato de otro bufete no debe existir en la transacción actual.
