-- ============================================================================
-- CUSTOS LEGIS TARIJA · esquema PostgreSQL con aislamiento por bufete
--
-- EL DEFECTO QUE ESTE ARCHIVO ARREGLA (D3 de la auditoria de Fable):
--
--   El diseno original pone RLS en `cases` y `documents`, y despues manda a
--   LangGraph a persistir su estado con `PostgresSaver`. Ese saver crea sus
--   propias tablas (`checkpoints`, `checkpoint_writes`) con el estado COMPLETO
--   del grafo serializado: el memorial redactado, los documentos privados del
--   caso, la estrategia legal. Esas tablas NO tienen `tenant_id` ni RLS.
--
--   O sea: el RLS de `cases` protege los metadatos y deja el contenido
--   confidencial en una tabla abierta al lado. El aislamiento se ve verde en
--   el test de `cases` y esta roto donde importa.
--
--   Es exactamente el patron que este proyecto persigue: un guard que da verde
--   porque mira el sujeto equivocado.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS app;

-- El tenant se inyecta por transaccion desde el backend. STABLE, no IMMUTABLE:
-- cambia entre transacciones.
CREATE OR REPLACE FUNCTION app.current_tenant_id() RETURNS UUID
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.tenant_id', TRUE), '')::UUID
$$;

CREATE OR REPLACE FUNCTION app.set_tenant(p UUID) RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
  -- TRUE = local a la transaccion. Sin esto el tenant se filtra al siguiente
  -- request que reuse la conexion del pool.
  PERFORM set_config('app.tenant_id', p::TEXT, TRUE);
END $$;

-- ============================================================================
-- 1. BUFETES
-- Sin RLS: la administra el servicio, no un inquilino.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.tenants (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug              TEXT UNIQUE NOT NULL,
  nombre_bufete     TEXT NOT NULL,
  nit               TEXT,
  ciudad            TEXT NOT NULL DEFAULT 'Tarija',
  plan              TEXT NOT NULL DEFAULT 'basico'
                    CHECK (plan IN ('basico','premium','enterprise')),
  activo            BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. ABOGADOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.users (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  email             TEXT NOT NULL,
  password_hash     TEXT NOT NULL,
  nombre_completo   TEXT NOT NULL,
  matricula_cab     TEXT,
  rol               TEXT NOT NULL DEFAULT 'asociado'
                    CHECK (rol IN ('socio','asociado','asistente','admin_tenant')),
  activo            BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- UNIQUE compuesto, NO global: dos bufetes pueden tener el mismo email
  UNIQUE (tenant_id, email)
);
CREATE INDEX IF NOT EXISTS ix_users_tenant ON public.users (tenant_id, email);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_users ON public.users;
CREATE POLICY p_users ON public.users USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- ============================================================================
-- 3. EXPEDIENTES
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.cases (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  abogado_id        UUID REFERENCES public.users(id),
  nro_expediente    TEXT,
  -- DOS columnas de sistema a proposito: el SIGC es SOLO PENAL, con piloto en
  -- Chuquisaca, y en marzo-2026 su despliegue nacional era un anteproyecto de
  -- Bs 160 M. Civil y familiar de Tarija siguen en SIREJ. Medido, no supuesto.
  sistema_origen    TEXT NOT NULL DEFAULT 'sirej'
                    CHECK (sistema_origen IN ('sirej','sigc','eforo','manual')),
  juzgado           TEXT NOT NULL,
  materia           TEXT NOT NULL CHECK (materia IN (
                      'civil','penal','administrativo','familiar','laboral',
                      'tributario','constitucional','agroambiental')),
  parte_actora      TEXT,
  parte_demandada   TEXT,
  estado_procesal   TEXT NOT NULL DEFAULT 'activo' CHECK (estado_procesal IN (
                      'activo','en_espera','plazo_corriendo','sentenciado',
                      'archivado','apelacion')),
  ultimo_actuado        TEXT,
  ultimo_actuado_hash   TEXT,
  fecha_ultimo_actuado  TIMESTAMPTZ,
  plazo_dias_habiles    INTEGER,
  -- Se llama _habiles porque el D4 de Fable era justamente contar corridos.
  fecha_vencimiento     DATE,
  -- La etiqueta viaja CON el dato: mientras ningun abogado confirme la tabla de
  -- plazos, el sistema no puede mostrarlo como cierto.
  plazo_confirmado      BOOLEAN NOT NULL DEFAULT FALSE,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, nro_expediente, sistema_origen)
);
CREATE INDEX IF NOT EXISTS ix_cases_tenant ON public.cases (tenant_id, estado_procesal);
CREATE INDEX IF NOT EXISTS ix_cases_venc ON public.cases (tenant_id, fecha_vencimiento)
  WHERE estado_procesal = 'plazo_corriendo';

ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cases FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cases ON public.cases;
CREATE POLICY p_cases ON public.cases USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- ============================================================================
-- 4. DOCUMENTOS DEL BUFETE
--
-- REGLA HEREDADA DEL CORPUS, y es el D1 de Fable: EL CRUDO NO SE TOCA.
-- El diseno original tenia un `_limpiar_texto_legal` que unia guiones, borraba
-- lineas cortas e inyectaba `##` markdown. En un corpus legal eso es alterar
-- prueba: si el OCR leyo mal, se guarda mal Y SE DECLARA, no se "mejora".
-- Por eso hay DOS columnas: `texto_crudo` inmutable y `texto_normalizado`.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.documents (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id           UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
  subido_por        UUID REFERENCES public.users(id),
  tipo_documento    TEXT NOT NULL CHECK (tipo_documento IN (
                      'memorial_presentado','auto_notificado','sentencia',
                      'prueba_documental','contrato','poder_notarial')),
  nombre_archivo    TEXT NOT NULL,
  sha256            TEXT NOT NULL,
  texto_crudo       TEXT,
  texto_normalizado TEXT,
  via_texto         TEXT CHECK (via_texto IN ('nativo_pdf','ocr','manual')),
  confianza_texto   NUMERIC(4,3),
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, case_id, sha256)
);
CREATE INDEX IF NOT EXISTS ix_docs_tenant ON public.documents (tenant_id, case_id);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_docs ON public.documents;
CREATE POLICY p_docs ON public.documents USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- Bloquea la reescritura del crudo a nivel de motor, no de codigo Python.
CREATE OR REPLACE FUNCTION app.crudo_inmutable() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.texto_crudo IS NOT NULL AND NEW.texto_crudo IS DISTINCT FROM OLD.texto_crudo THEN
    RAISE EXCEPTION 'texto_crudo es inmutable (regla del corpus): usar texto_normalizado';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS t_crudo_inmutable ON public.documents;
CREATE TRIGGER t_crudo_inmutable BEFORE UPDATE ON public.documents
  FOR EACH ROW EXECUTE FUNCTION app.crudo_inmutable();

-- ============================================================================
-- 5. EL ARREGLO DEL D3: los checkpoints de LangGraph CON tenant y RLS
--
-- No se le pide a LangGraph que cambie: se envuelve. El backend escribe SIEMPRE
-- aca, y el `thread_id` lleva el tenant adentro por convencion, verificada por
-- el trigger de abajo.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.cl_checkpoints (
  id                BIGSERIAL PRIMARY KEY,
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id           UUID REFERENCES public.cases(id) ON DELETE CASCADE,
  thread_id         TEXT NOT NULL,
  checkpoint_ns     TEXT NOT NULL DEFAULT '',
  checkpoint_id     TEXT NOT NULL,
  parent_id         TEXT,
  -- El estado del grafo: memorial, docs privados, estrategia. Lo mas sensible
  -- del sistema entero.
  estado            JSONB NOT NULL,
  metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, thread_id, checkpoint_ns, checkpoint_id)
);
CREATE INDEX IF NOT EXISTS ix_ckpt_tenant ON public.cl_checkpoints (tenant_id, thread_id);

ALTER TABLE public.cl_checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_checkpoints FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_ckpt ON public.cl_checkpoints;
CREATE POLICY p_ckpt ON public.cl_checkpoints
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- GUARD QUE PUEDE DAR ROJO: un thread_id que no empieza con su tenant se
-- RECHAZA. Sin esto, un bug de armado de thread_id mezclaria hilos de dos
-- bufetes bajo el mismo id y el RLS no lo veria (mismo tenant_id, otro caso).
CREATE OR REPLACE FUNCTION app.thread_lleva_tenant() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF position(NEW.tenant_id::TEXT in NEW.thread_id) = 0 THEN
    RAISE EXCEPTION
      'thread_id % no contiene su tenant_id %: convencion violada',
      NEW.thread_id, NEW.tenant_id;
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS t_thread_tenant ON public.cl_checkpoints;
CREATE TRIGGER t_thread_tenant BEFORE INSERT OR UPDATE ON public.cl_checkpoints
  FOR EACH ROW EXECUTE FUNCTION app.thread_lleva_tenant();

-- ============================================================================
-- 6. AUDITORIA DE AGENTES · con costo, porque el H5 es "no se cuanto cuesta"
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.agent_runs (
  id                BIGSERIAL PRIMARY KEY,
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id           UUID REFERENCES public.cases(id) ON DELETE CASCADE,
  thread_id         TEXT NOT NULL,
  nodo              TEXT NOT NULL,
  modelo            TEXT,
  tokens_in         INTEGER,
  tokens_out        INTEGER,
  costo_usd         NUMERIC(12,6),
  duracion_ms       INTEGER,
  resultado         TEXT,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_runs_tenant ON public.agent_runs (tenant_id, creado_en DESC);

ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_runs ON public.agent_runs;
CREATE POLICY p_runs ON public.agent_runs USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- ============================================================================
-- 7. SENSOR DE USO · el T1 de Fable, y el unico instrumento que faltaba
--
-- "0 abogados que lo usaron" es un numero SIN SENSOR: no puede volverse 1
-- aunque pase. Esta tabla lo arregla.
--
-- DECISION DE PRIVACIDAD, declarada y no deducida: `q_hash` guarda el sha256 de
-- la consulta, NO el texto. Una busqueda juridica revela la estrategia de un
-- caso; el conteo alcanza para saber si el producto se usa. Si Abraham decide
-- guardar el texto, se agrega `q_texto` y se dice por escrito.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.uso_consultas (
  id                BIGSERIAL PRIMARY KEY,
  tenant_id         UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
  user_id           UUID REFERENCES public.users(id) ON DELETE SET NULL,
  q_hash            TEXT NOT NULL,
  q_largo           INTEGER NOT NULL,
  n_resultados      INTEGER NOT NULL,
  hubo_click        BOOLEAN NOT NULL DEFAULT FALSE,
  ms                INTEGER,
  ts                TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_uso_ts ON public.uso_consultas (ts DESC);

-- ============================================================================
-- 8. APROBACIONES · el HITL, y es la tabla que hace responsable a una persona
--
-- HUECO QUE ESTA TABLA TAPA, encontrado el 2026-09-10 al escribir la API:
-- `PostgresAlmacen.registrar_aprobacion()` escribia en `public.aprobaciones` y
-- **la tabla no existia en este esquema**. El gate de acciones externas habria
-- explotado en el primer INSERT contra Postgres. En SQLite funcionaba porque el
-- almacen de prueba crea su propio DDL: el clasico "verde en el mock, rojo en
-- produccion", que es justo el patron que este proyecto persigue.
--
-- POR QUE `sha256_entrada` ES EL CAMPO QUE IMPORTA:
-- sin el, la aprobacion diria "el socio aprobo presentar un escrito", y despues
-- se podria presentar OTRO escrito. Con el, la aprobacion es sobre un contenido
-- EXACTO. Aprobar un borrador y ejecutar otro es la fuga obvia de todo esquema
-- de aprobacion humana, y se cierra con un hash, no con confianza.
--
-- VA ANTES DE LOS GRANT A PROPOSITO: `GRANT ... ON ALL TABLES` solo alcanza a
-- las tablas que YA existen. Si esta tabla se creara despues, `custos_app` no
-- tendria permisos y el gate fallaria con "permission denied" recien en
-- produccion.
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.aprobaciones (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id           UUID REFERENCES public.cases(id) ON DELETE SET NULL,
  usuario_id        UUID NOT NULL REFERENCES public.users(id),
  -- Numero del Registro Publico de la Abogacia (Ley 387 art. 13). Se COPIA aca
  -- y no se lee de `users` por join: si el abogado cambia de matricula manana,
  -- la aprobacion de hoy tiene que seguir diciendo con cual firmo.
  matricula         TEXT NOT NULL CHECK (length(trim(matricula)) > 0),
  tipo              TEXT NOT NULL CHECK (tipo IN (
                      'presentar_escrito','notificar_cliente','firmar_digital',
                      'enviar_a_juzgado','consultar_con_credenciales',
                      'publicar_extracto','usar_plazo_calculado')),
  sha256_entrada    TEXT NOT NULL CHECK (sha256_entrada ~ '^[0-9a-f]{64}$'),
  decision          TEXT NOT NULL CHECK (decision IN ('aprobado','rechazado')),
  fundamento        TEXT,
  -- Trazabilidad del acto: que modelo y que prompt produjeron lo aprobado.
  modelo            TEXT,
  prompt_sha256     TEXT,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_aprob_tenant
  ON public.aprobaciones (tenant_id, creado_en DESC);
-- Indice por el hash: es la consulta del gate, en el camino caliente.
CREATE INDEX IF NOT EXISTS ix_aprob_hash
  ON public.aprobaciones (tenant_id, tipo, sha256_entrada)
  WHERE decision = 'aprobado';

ALTER TABLE public.aprobaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.aprobaciones FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_aprob ON public.aprobaciones;
CREATE POLICY p_aprob ON public.aprobaciones
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- Evidencia = inmutable. Una aprobacion que se puede editar despues no prueba
-- nada sobre lo que se aprobo en su momento. Este trigger puede dar rojo contra
-- mi propio codigo si algun dia intento "corregir" una aprobacion en vez de
-- emitir una nueva.
CREATE OR REPLACE FUNCTION app.aprobacion_inmutable() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION
    'una aprobacion es evidencia y no se modifica ni borra (intento: %). '
    'Para cambiar de decision, registrar una aprobacion NUEVA.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS t_aprob_inmutable ON public.aprobaciones;
CREATE TRIGGER t_aprob_inmutable BEFORE UPDATE OR DELETE ON public.aprobaciones
  FOR EACH ROW EXECUTE FUNCTION app.aprobacion_inmutable();

-- ============================================================================
-- 9. ROL DE LA APLICACION
-- El rol NO debe tener BYPASSRLS. Si lo tiene, todo lo de arriba es decorativo.
-- ============================================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'custos_app') THEN
    CREATE ROLE custos_app LOGIN PASSWORD 'CAMBIAR_EN_PRODUCCION';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public, app TO custos_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO custos_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO custos_app;
ALTER ROLE custos_app NOBYPASSRLS;
