-- CUSTOS LEGIS TARIJA · persistencia del vertical MVP
-- Se aplica después de infra/init.sql. Todos los objetos llevan tenant_id y RLS.

CREATE TABLE IF NOT EXISTS public.cl_mvp_documents (
  id              TEXT PRIMARY KEY,
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id         UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
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
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id     UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
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
  id          TEXT PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id     UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
  payload     JSONB NOT NULL,
  creado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
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
  id          TEXT PRIMARY KEY,
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id     UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
  draft_id    TEXT NOT NULL,
  payload     JSONB NOT NULL,
  creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
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
  tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  case_id     UUID REFERENCES public.cases(id) ON DELETE CASCADE,
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

CREATE OR REPLACE FUNCTION app.cl_mvp_immutable_event() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'los eventos MVP son evidencia inmutable: % no permitido', TG_OP;
END $$;
DROP TRIGGER IF EXISTS t_cl_mvp_decisions_immutable ON public.cl_mvp_decisions;
CREATE TRIGGER t_cl_mvp_decisions_immutable
  BEFORE UPDATE OR DELETE ON public.cl_mvp_decisions
  FOR EACH ROW EXECUTE FUNCTION app.cl_mvp_immutable_event();
DROP TRIGGER IF EXISTS t_cl_mvp_audit_immutable ON public.cl_mvp_audit_events;
CREATE TRIGGER t_cl_mvp_audit_immutable
  BEFORE UPDATE OR DELETE ON public.cl_mvp_audit_events
  FOR EACH ROW EXECUTE FUNCTION app.cl_mvp_immutable_event();

GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_documents TO custos_app;
GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_searches TO custos_app;
GRANT SELECT, INSERT, UPDATE ON public.cl_mvp_drafts TO custos_app;
GRANT SELECT, INSERT ON public.cl_mvp_decisions TO custos_app;
GRANT SELECT, INSERT ON public.cl_mvp_audit_events TO custos_app;
