-- ============================================================================
-- DECISION SOBRE EL TRIGGER DE INMUTABILIDAD  ·  2026-09-16
--
-- LA PREGUNTA ERA: el trigger `app.aprobacion_inmutable()` rechaza el DELETE de
-- una aprobacion INCLUSO cuando llega por el `ON DELETE CASCADE` de `tenants`,
-- asi que un bufete con aprobaciones NO SE PUEDE BORRAR. Eso choca con una
-- limpieza y con un pedido de borrado de datos.
--
-- LA DECISION ES: **EL TRIGGER SE QUEDA.** Una aprobacion es la firma de un
-- abogado con su matricula sobre un contenido exacto (Ley 387 arts. 6 y 32.II).
-- Si se puede borrar, no prueba nada sobre lo que se aprobo en su momento, y el
-- dia que alguien discuta un acto procesal la evidencia tiene que existir.
-- Poner una excepcion para la cascada seria dejar la puerta con la llave puesta:
-- bastaria borrar la fila del bufete para que desaparezca todo el rastro.
--
-- PERO MEDIR ESE BORDE DESTAPO ALGO PEOR, y esta es la parte que importa.
--
-- ============================================================================
-- EL AGUJERO MEDIDO (2026-09-16, PostgreSQL real, rol `custos_app`)
-- ============================================================================
--
--   1_app_borra_tenant_SIN_aprobaciones : sin error, filas_afectadas = 1
--   2_app_borra_tenant_CON_aprobaciones : RaiseException (el trigger)
--
-- La primera linea es un CONTROL POSITIVO y es la que duele: **el rol de la
-- aplicacion borro un bufete entero de una sentencia.** Y con el, por cascada,
-- sus usuarios, casos, documentos y checkpoints.
--
-- Por que pudo: `public.tenants` es la UNICA tabla de inquilino SIN RLS. El
-- comentario del esquema lo justifica bien ('la administra el servicio, no un
-- inquilino'), pero despues `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES
-- IN SCHEMA public TO custos_app` la alcanzo igual. Sin RLS y con DELETE, el rol
-- del camino de request podia borrar CUALQUIER bufete, incluido el de otro.
--
-- O sea: lo unico que impedia perder los datos de un bufete era que ese bufete
-- tuviera al menos una aprobacion registrada. Un bufete nuevo, sin aprobaciones
-- todavia, estaba a un DELETE de distancia. Eso no es una politica, es una
-- casualidad.
--
-- ============================================================================
-- QUE HACE ESTA MIGRACION
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. El rol del camino de request NO administra el ciclo de vida de un bufete.
--    Crear o borrar un bufete es una operacion administrativa. La API nunca lo
--    necesita: `abrir_sesion` solo LEE `tenants` para resolver el slug.
-- ----------------------------------------------------------------------------
REVOKE DELETE, UPDATE, INSERT ON public.tenants FROM custos_app;

-- SELECT se mantiene, y es imprescindible: el login corregido resuelve el
-- bufete leyendo `public.tenants` antes de entrar al tenant. Sin este SELECT el
-- login vuelve a romperse, asi que la regresion lo cubre con un control
-- positivo (credencial valida = 200).
GRANT SELECT ON public.tenants TO custos_app;

-- ----------------------------------------------------------------------------
-- 2. Que el rechazo se lea como lo que es.
--
--    Antes: DELETE de un tenant -> cascada -> el trigger levanta
--    'una aprobacion es evidencia y no se modifica ni borra'. El mensaje es
--    correcto pero llega desde el medio de una cascada, y para el que lo lee
--    parece un bug del sistema en vez de una regla.
--
--    Ahora la FK es RESTRICT: el motor rechaza en `tenants`, antes de tocar
--    `aprobaciones`, con un error de integridad referencial que nombra la tabla
--    que retiene. El trigger queda igual como segunda barrera, y eso es a
--    proposito: si alguien manana cambia esta FK, el trigger todavia frena.
--    Dos barreras independientes, cada una con su falsador.
-- ----------------------------------------------------------------------------
ALTER TABLE public.aprobaciones
  DROP CONSTRAINT IF EXISTS aprobaciones_tenant_id_fkey;
ALTER TABLE public.aprobaciones
  ADD CONSTRAINT aprobaciones_tenant_id_fkey
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;

COMMIT;

-- ============================================================================
-- COMO SE BORRA UN BUFETE, ENTONCES
-- ============================================================================
-- No con un DELETE, y no desde la API. El procedimiento queda escrito aca
-- porque un pedido de borrado de datos es real y va a llegar:
--
--   1. EXPORTAR la evidencia (tabla `aprobaciones` del bufete) a un archivo
--      firmado y archivarlo fuera de la base. La obligacion de conservar la
--      firma del abogado no desaparece porque el cliente se vaya.
--   2. Con el rol ADMINISTRATIVO, no con `custos_app`, borrar en orden:
--      aprobaciones exportadas -> el resto cascadea -> el tenant.
--   3. Registrar quien lo hizo y contra que pedido.
--
-- NO MEDIDO, y va declarado porque es una decision de negocio y no mia:
--   a. CUANTO TIEMPO hay que conservar la evidencia de una aprobacion. Es una
--      pregunta para un abogado, no para el esquema. Hasta que alguien la
--      responda, el borrado de un bufete con aprobaciones queda BLOQUEADO, que
--      es el lado seguro del error.
--   b. El paso 1 no esta implementado: no hay exportador de evidencia todavia.
--      Mientras no exista, el paso 2 no deberia ejecutarse.
