-- CUSTOS LEGIS TARIJA · persistencia del vertical MVP
-- Se aplica después de infra/init.sql. Todos los objetos llevan tenant_id y RLS.

CREATE TABLE IF NOT EXISTS public.cl_mvp_documents (
  id              TEXT PRIMARY KEY,
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
  case_id         UUID NOT NULL REFERENCES public.cases(id) ON DELETE RESTRICT,
  content_sha256  TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
  payload         JSONB NOT NULL,
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cl_mvp_documents_tenant
  ON public.cl_mvp_documents (tenant_id, case_id, creado_en DESC);
ALTER TABLE public.cl_mvp_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_mvp_documents FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cl_mvp_documents ON public.cl_mvp_documents;
CREATE POLICY p_cl_mvp_documents ON public.cl_mvp_documents
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE TABLE IF NOT EXISTS public.cl_mvp_searches (
  id          TEXT PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
  case_id     UUID NOT NULL REFERENCES public.cases(id) ON DELETE RESTRICT,
  payload     JSONB NOT NULL,
  creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cl_mvp_searches_tenant
  ON public.cl_mvp_searches (tenant_id, case_id, creado_en DESC);
ALTER TABLE public.cl_mvp_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_mvp_searches FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cl_mvp_searches ON public.cl_mvp_searches;
CREATE POLICY p_cl_mvp_searches ON public.cl_mvp_searches
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE TABLE IF NOT EXISTS public.cl_mvp_drafts (
  id              TEXT PRIMARY KEY,
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
  case_id         UUID NOT NULL REFERENCES public.cases(id) ON DELETE RESTRICT,
  payload         JSONB NOT NULL,
  content         TEXT NOT NULL,
  content_sha256  TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cl_mvp_drafts_tenant
  ON public.cl_mvp_drafts (tenant_id, case_id, actualizado_en DESC);
ALTER TABLE public.cl_mvp_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_mvp_drafts FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cl_mvp_drafts ON public.cl_mvp_drafts;
CREATE POLICY p_cl_mvp_drafts ON public.cl_mvp_drafts
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE TABLE IF NOT EXISTS public.cl_mvp_decisions (
  id              TEXT PRIMARY KEY,
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
  case_id         UUID NOT NULL REFERENCES public.cases(id) ON DELETE RESTRICT,
  draft_id        TEXT NOT NULL,
  content_sha256  TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
  actor_user_id   TEXT NOT NULL,
  actor_role      TEXT NOT NULL,
  matricula       TEXT,
  decision        TEXT NOT NULL CHECK (decision IN ('aprobado','rechazado','correccion')),
  fundamento     TEXT NOT NULL DEFAULT '',
  payload         JSONB NOT NULL,
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cl_mvp_decisions_gate
  ON public.cl_mvp_decisions (tenant_id, case_id, draft_id, creado_en DESC, id DESC);
ALTER TABLE public.cl_mvp_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_mvp_decisions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cl_mvp_decisions ON public.cl_mvp_decisions;
CREATE POLICY p_cl_mvp_decisions ON public.cl_mvp_decisions
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

CREATE TABLE IF NOT EXISTS public.cl_mvp_audit_events (
  id          TEXT PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
  case_id     UUID REFERENCES public.cases(id) ON DELETE RESTRICT,
  event       TEXT NOT NULL,
  payload     JSONB NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_cl_mvp_audit_tenant
  ON public.cl_mvp_audit_events (tenant_id, created_at DESC);
ALTER TABLE public.cl_mvp_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cl_mvp_audit_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_cl_mvp_audit_events ON public.cl_mvp_audit_events;
CREATE POLICY p_cl_mvp_audit_events ON public.cl_mvp_audit_events
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- Compatibilidad de migración: materializa en columnas tipadas lo que antes vivía
-- únicamente dentro de payload. Si una fila heredada no es íntegra, la migración
-- falla en vez de convertirla silenciosamente en evidencia válida.
ALTER TABLE public.cl_mvp_drafts ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE public.cl_mvp_drafts ADD COLUMN IF NOT EXISTS content_sha256 TEXT;
UPDATE public.cl_mvp_drafts
   SET content = COALESCE(content, payload->>'content'),
       content_sha256 = COALESCE(content_sha256, payload->>'content_sha256')
 WHERE content IS NULL OR content_sha256 IS NULL;
ALTER TABLE public.cl_mvp_drafts ALTER COLUMN content SET NOT NULL;
ALTER TABLE public.cl_mvp_drafts ALTER COLUMN content_sha256 SET NOT NULL;

ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS content_sha256 TEXT;
ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS actor_user_id TEXT;
ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS actor_role TEXT;
ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS matricula TEXT;
ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS decision TEXT;
ALTER TABLE public.cl_mvp_decisions ADD COLUMN IF NOT EXISTS fundamento TEXT;
UPDATE public.cl_mvp_decisions
   SET content_sha256 = COALESCE(content_sha256, payload->>'content_sha256'),
       actor_user_id = COALESCE(actor_user_id, payload->>'user_id', payload->>'actor_user_id'),
       actor_role = COALESCE(actor_role, payload->>'role', payload->>'actor_role'),
       matricula = COALESCE(matricula, payload->>'matricula'),
       decision = COALESCE(decision, payload->>'decision'),
       fundamento = COALESCE(fundamento, payload->>'fundamento', '')
 WHERE content_sha256 IS NULL OR actor_user_id IS NULL OR actor_role IS NULL
    OR decision IS NULL OR fundamento IS NULL;
ALTER TABLE public.cl_mvp_decisions ALTER COLUMN content_sha256 SET NOT NULL;
ALTER TABLE public.cl_mvp_decisions ALTER COLUMN actor_user_id SET NOT NULL;
ALTER TABLE public.cl_mvp_decisions ALTER COLUMN actor_role SET NOT NULL;
ALTER TABLE public.cl_mvp_decisions ALTER COLUMN decision SET NOT NULL;
ALTER TABLE public.cl_mvp_decisions ALTER COLUMN fundamento SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_cl_mvp_drafts_hash') THEN
    ALTER TABLE public.cl_mvp_drafts ADD CONSTRAINT ck_cl_mvp_drafts_hash
      CHECK (content_sha256 ~ '^[0-9a-f]{64}$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_cl_mvp_decisions_hash') THEN
    ALTER TABLE public.cl_mvp_decisions ADD CONSTRAINT ck_cl_mvp_decisions_hash
      CHECK (content_sha256 ~ '^[0-9a-f]{64}$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_cl_mvp_decisions_kind') THEN
    ALTER TABLE public.cl_mvp_decisions ADD CONSTRAINT ck_cl_mvp_decisions_kind
      CHECK (decision IN ('aprobado','rechazado','correccion'));
  END IF;
END $$;

CREATE OR REPLACE FUNCTION app.cl_mvp_validate_draft() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.content_sha256 <> encode(digest(convert_to(NEW.content, 'UTF8'), 'sha256'), 'hex') THEN
    RAISE EXCEPTION 'hash de borrador no coincide con su contenido';
  END IF;
  IF NEW.payload->>'content' IS DISTINCT FROM NEW.content
     OR NEW.payload->>'content_sha256' IS DISTINCT FROM NEW.content_sha256 THEN
    RAISE EXCEPTION 'payload de borrador no coincide con columnas tipadas';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS t_cl_mvp_validate_draft ON public.cl_mvp_drafts;
CREATE TRIGGER t_cl_mvp_validate_draft
  BEFORE INSERT OR UPDATE ON public.cl_mvp_drafts
  FOR EACH ROW EXECUTE FUNCTION app.cl_mvp_validate_draft();

CREATE OR REPLACE FUNCTION app.cl_mvp_draft_approved_immutable() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.cl_mvp_decisions
     WHERE tenant_id = OLD.tenant_id AND draft_id = OLD.id AND decision = 'aprobado'
  ) THEN
    RAISE EXCEPTION 'borrador aprobado: no se puede modificar';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS t_cl_mvp_draft_approved_immutable ON public.cl_mvp_drafts;
CREATE TRIGGER t_cl_mvp_draft_approved_immutable
  BEFORE UPDATE ON public.cl_mvp_drafts
  FOR EACH ROW EXECUTE FUNCTION app.cl_mvp_draft_approved_immutable();

CREATE OR REPLACE FUNCTION app.cl_mvp_validate_decision() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE expected_hash TEXT;
BEGIN
  IF NEW.payload->>'tenant_id' IS DISTINCT FROM NEW.tenant_id::TEXT
     OR NEW.payload->>'case_id' IS DISTINCT FROM NEW.case_id::TEXT
     OR NEW.payload->>'draft_id' IS DISTINCT FROM NEW.draft_id
     OR NEW.payload->>'content_sha256' IS DISTINCT FROM NEW.content_sha256
     OR NEW.payload->>'decision' IS DISTINCT FROM NEW.decision THEN
    RAISE EXCEPTION 'payload de decisión no coincide con columnas tipadas';
  END IF;
  IF NEW.payload->>'user_id' IS DISTINCT FROM NEW.actor_user_id
     AND NEW.payload->>'actor_user_id' IS DISTINCT FROM NEW.actor_user_id THEN
    RAISE EXCEPTION 'actor de decisión no coincide con payload';
  END IF;
  SELECT d.content_sha256 INTO expected_hash
    FROM public.cl_mvp_drafts d
   WHERE d.id = NEW.draft_id AND d.tenant_id = NEW.tenant_id;
  IF expected_hash IS NULL OR expected_hash <> NEW.content_sha256 THEN
    RAISE EXCEPTION 'decisión no está ligada al hash persistido del borrador';
  END IF;
  IF NEW.decision = 'aprobado'
     AND (NEW.actor_role NOT IN ('socio','asociado') OR NULLIF(trim(NEW.matricula), '') IS NULL) THEN
    RAISE EXCEPTION 'aprobación sin rol o matrícula válida';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS t_cl_mvp_validate_decision ON public.cl_mvp_decisions;
CREATE TRIGGER t_cl_mvp_validate_decision
  BEFORE INSERT OR UPDATE ON public.cl_mvp_decisions
  FOR EACH ROW EXECUTE FUNCTION app.cl_mvp_validate_decision();

-- Reemplaza las cascadas en evidencia. El DELETE real debe fallar y conservar
-- la prueba, no borrar hijos antes de que el trigger de inmutabilidad los vea.
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT n.nspname, c.relname, con.conname
      FROM pg_constraint con
      JOIN pg_class c ON c.oid = con.conrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relname IN ('cl_mvp_documents','cl_mvp_searches','cl_mvp_drafts',
                         'cl_mvp_decisions','cl_mvp_audit_events')
       AND con.contype = 'f'
  LOOP
    EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT %I', r.nspname, r.relname, r.conname);
  END LOOP;
END $$;
ALTER TABLE public.cl_mvp_documents
  ADD CONSTRAINT fk_cl_mvp_documents_tenant FOREIGN KEY (tenant_id)
  REFERENCES public.tenants(id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_cl_mvp_documents_case FOREIGN KEY (case_id)
  REFERENCES public.cases(id) ON DELETE RESTRICT;
ALTER TABLE public.cl_mvp_searches
  ADD CONSTRAINT fk_cl_mvp_searches_tenant FOREIGN KEY (tenant_id)
  REFERENCES public.tenants(id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_cl_mvp_searches_case FOREIGN KEY (case_id)
  REFERENCES public.cases(id) ON DELETE RESTRICT;
ALTER TABLE public.cl_mvp_drafts
  ADD CONSTRAINT fk_cl_mvp_drafts_tenant FOREIGN KEY (tenant_id)
  REFERENCES public.tenants(id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_cl_mvp_drafts_case FOREIGN KEY (case_id)
  REFERENCES public.cases(id) ON DELETE RESTRICT;
ALTER TABLE public.cl_mvp_decisions
  ADD CONSTRAINT fk_cl_mvp_decisions_tenant FOREIGN KEY (tenant_id)
  REFERENCES public.tenants(id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_cl_mvp_decisions_case FOREIGN KEY (case_id)
  REFERENCES public.cases(id) ON DELETE RESTRICT;
ALTER TABLE public.cl_mvp_audit_events
  ADD CONSTRAINT fk_cl_mvp_audit_tenant FOREIGN KEY (tenant_id)
  REFERENCES public.tenants(id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_cl_mvp_audit_case FOREIGN KEY (case_id)
  REFERENCES public.cases(id) ON DELETE RESTRICT;

GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_documents TO custos_app;
GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_searches TO custos_app;
GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_drafts TO custos_app;
GRANT SELECT, INSERT ON public.cl_mvp_decisions TO custos_app;
GRANT SELECT, INSERT ON public.cl_mvp_audit_events TO custos_app;
