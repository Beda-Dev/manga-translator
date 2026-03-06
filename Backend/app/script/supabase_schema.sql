-- ═══════════════════════════════════════════════════════════════════════════════
-- Manga Translator — Schéma Supabase
-- À exécuter dans: Supabase Dashboard → SQL Editor → New query
-- ═══════════════════════════════════════════════════════════════════════════════

-- Extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. TABLE: translation_jobs
--    Stocke les métadonnées de chaque job de traduction.
--    Le backend FastAPI écrit ici à chaque étape du pipeline.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.translation_jobs (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          TEXT        NOT NULL UNIQUE,   -- ID généré par FastAPI (UUID string)
    filename        TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending','extracting','processing','packaging','completed','failed')),
    progress        NUMERIC(5,2) NOT NULL DEFAULT 0
                                CHECK (progress >= 0 AND progress <= 100),
    total_pages     INTEGER     NOT NULL DEFAULT 1,
    processed_pages INTEGER     NOT NULL DEFAULT 0,

    -- Options de traduction utilisées
    ocr_engine          TEXT    NOT NULL DEFAULT 'easyocr',
    translation_engine  TEXT    NOT NULL DEFAULT 'marian',
    source_lang         TEXT    NOT NULL DEFAULT 'auto',
    target_lang         TEXT    NOT NULL DEFAULT 'fr',
    output_format       TEXT    NOT NULL DEFAULT 'cbz',

    -- Résultats
    output_url      TEXT,       -- URL publique Supabase Storage du package final
    error_message   TEXT,       -- Message d'erreur si status='failed'

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- Index pour les lookups fréquents
CREATE INDEX IF NOT EXISTS idx_translation_jobs_job_id   ON public.translation_jobs (job_id);
CREATE INDEX IF NOT EXISTS idx_translation_jobs_status   ON public.translation_jobs (status);
CREATE INDEX IF NOT EXISTS idx_translation_jobs_created  ON public.translation_jobs (created_at DESC);

-- Trigger: met à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON public.translation_jobs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.translation_jobs IS
    'Métadonnées des jobs de traduction manga/webtoon. '
    'Créé par le backend FastAPI à chaque POST /translate.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. TABLE: translation_pages
--    Résultat de traitement pour chaque page d'un job.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.translation_pages (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              TEXT    NOT NULL REFERENCES public.translation_jobs(job_id) ON DELETE CASCADE,
    page_index          INTEGER NOT NULL,       -- 0-based
    filename            TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('success','error','skipped','pending')),

    -- URLs des images
    original_image_url  TEXT,   -- Image originale (optionnel)
    image_url           TEXT,   -- Image traduite — URL Supabase Storage

    -- Données OCR/traduction
    text_regions_count  INTEGER NOT NULL DEFAULT 0,
    processing_time_ms  INTEGER,
    error_message       TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (job_id, page_index)
);

CREATE INDEX IF NOT EXISTS idx_pages_job_id     ON public.translation_pages (job_id);
CREATE INDEX IF NOT EXISTS idx_pages_status     ON public.translation_pages (status);

COMMENT ON TABLE public.translation_pages IS
    'Résultat de traitement de chaque page image d''un job de traduction.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. TABLE: text_regions
--    Zones de texte détectées dans chaque page (pour audit/debug).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.text_regions (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id         UUID    NOT NULL REFERENCES public.translation_pages(id) ON DELETE CASCADE,
    job_id          TEXT    NOT NULL,   -- dénormalisé pour faciliter les requêtes

    -- Données OCR
    bbox            INTEGER[]  NOT NULL,    -- [x, y, width, height]
    original_text   TEXT       NOT NULL,
    translated_text TEXT,
    confidence      NUMERIC(4,3) CHECK (confidence >= 0 AND confidence <= 1),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_text_regions_page_id ON public.text_regions (page_id);
CREATE INDEX IF NOT EXISTS idx_text_regions_job_id  ON public.text_regions (job_id);

COMMENT ON TABLE public.text_regions IS
    'Zones de texte détectées par OCR dans chaque page. Utile pour debug et stats.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. TABLE: job_options
--    Stocke les options complètes de chaque job (JSON).
--    Séparé de translation_jobs pour garder cette table légère.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.job_options (
    job_id          TEXT    PRIMARY KEY REFERENCES public.translation_jobs(job_id) ON DELETE CASCADE,
    options_json    JSONB   NOT NULL DEFAULT '{}'::jsonb,
    font_options    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.job_options IS
    'Options complètes (JSON) utilisées pour un job. '
    'Inclut font_options, clés API anonymisées, etc.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. STORAGE: bucket manga-translations
--    Structure des chemins dans le bucket:
--      jobs/{job_id}/translated_{job_id}.cbz   ← package final
--      jobs/{job_id}/pages/page_0001.png        ← pages individuelles
-- ─────────────────────────────────────────────────────────────────────────────

-- Créer le bucket (si pas déjà fait par le backend Python)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'manga-translations',
    'manga-translations',
    true,               -- public: les URLs sont accessibles sans auth
    104857600,          -- 100 MB max par fichier
    ARRAY[
        'image/png', 'image/jpeg', 'image/webp',
        'application/zip', 'application/pdf',
        'application/vnd.comicbook+zip'
    ]
)
ON CONFLICT (id) DO UPDATE SET
    public = true,
    file_size_limit = 104857600;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. ROW LEVEL SECURITY (RLS)
--    Le backend utilise la service_role key → bypasse RLS.
--    Le frontend utilise la anon key → accès en lecture seule aux jobs publics.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.translation_jobs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.translation_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.text_regions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_options       ENABLE ROW LEVEL SECURITY;

-- Lecture publique (anon) — le frontend peut lire n'importe quel job via job_id
CREATE POLICY "Lecture publique jobs"
    ON public.translation_jobs FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Lecture publique pages"
    ON public.translation_pages FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Lecture publique text_regions"
    ON public.text_regions FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Lecture publique options"
    ON public.job_options FOR SELECT
    TO anon, authenticated
    USING (true);

-- Écriture réservée au service_role (backend FastAPI avec SUPABASE_SERVICE_KEY)
-- Note: service_role bypasse RLS automatiquement → pas besoin de policy INSERT/UPDATE/DELETE

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. STORAGE POLICIES
--    Accès public en lecture, upload réservé au service_role.
-- ─────────────────────────────────────────────────────────────────────────────

-- Lecture publique des fichiers du bucket
CREATE POLICY "Accès public lecture storage"
    ON storage.objects FOR SELECT
    TO public
    USING (bucket_id = 'manga-translations');

-- Upload autorisé pour tout le monde (le backend valide côté applicatif)
-- En production: remplacer TO public par TO service_role si vous voulez restreindre
CREATE POLICY "Upload autorisé"
    ON storage.objects FOR INSERT
    TO public
    WITH CHECK (bucket_id = 'manga-translations');

-- Suppression autorisée (pour le cleanup automatique)
CREATE POLICY "Suppression autorisée"
    ON storage.objects FOR DELETE
    TO public
    USING (bucket_id = 'manga-translations');

-- ─────────────────────────────────────────────────────────────────────────────
-- 8. VUE: v_job_summary
--    Vue pratique pour le frontend — résumé complet d'un job.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_job_summary AS
SELECT
    j.job_id,
    j.filename,
    j.status,
    j.progress,
    j.total_pages,
    j.processed_pages,
    j.ocr_engine,
    j.translation_engine,
    j.source_lang,
    j.target_lang,
    j.output_format,
    j.output_url,
    j.error_message,
    j.created_at,
    j.completed_at,

    -- Stats des pages
    COUNT(p.id)                                         AS pages_total,
    COUNT(p.id) FILTER (WHERE p.status = 'success')    AS pages_success,
    COUNT(p.id) FILTER (WHERE p.status = 'error')      AS pages_error,
    COUNT(p.id) FILTER (WHERE p.status = 'skipped')    AS pages_skipped,
    SUM(p.text_regions_count)                           AS total_text_regions,
    AVG(p.processing_time_ms)::INTEGER                  AS avg_page_time_ms,

    -- Durée totale de traitement
    EXTRACT(EPOCH FROM (j.completed_at - j.created_at))::INTEGER AS duration_seconds

FROM public.translation_jobs j
LEFT JOIN public.translation_pages p ON p.job_id = j.job_id
GROUP BY j.id, j.job_id;

COMMENT ON VIEW public.v_job_summary IS
    'Vue résumé d''un job avec statistiques agrégées des pages. '
    'Utilisée par le dashboard frontend.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 9. FONCTION: cleanup_old_jobs()
--    Supprime les jobs et fichiers Storage de plus de 24h.
--    À appeler via pg_cron ou Supabase Edge Functions (cron).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.cleanup_old_jobs(older_than_hours INTEGER DEFAULT 24)
RETURNS TABLE(deleted_jobs INTEGER, deleted_pages INTEGER) AS $$
DECLARE
    v_deleted_jobs  INTEGER := 0;
    v_deleted_pages INTEGER := 0;
    v_cutoff        TIMESTAMPTZ;
BEGIN
    v_cutoff := NOW() - (older_than_hours || ' hours')::INTERVAL;

    -- Compter les pages avant suppression
    SELECT COUNT(*) INTO v_deleted_pages
    FROM public.translation_pages
    WHERE job_id IN (
        SELECT job_id FROM public.translation_jobs
        WHERE created_at < v_cutoff
    );

    -- Supprimer les jobs (CASCADE supprime pages, text_regions, options)
    DELETE FROM public.translation_jobs
    WHERE created_at < v_cutoff;

    GET DIAGNOSTICS v_deleted_jobs = ROW_COUNT;

    -- Note: les fichiers Supabase Storage sont supprimés par le backend Python
    -- (storage_service.delete_job_files) ou manuellement via le dashboard

    RETURN QUERY SELECT v_deleted_jobs, v_deleted_pages;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.cleanup_old_jobs IS
    'Supprime les jobs de traduction plus vieux que N heures. '
    'Appeler via pg_cron: SELECT cron.schedule(''cleanup-jobs'', ''0 * * * *'', ''SELECT cleanup_old_jobs(24)'');';

-- ─────────────────────────────────────────────────────────────────────────────
-- 10. STATS (optionnel) — pour un éventuel dashboard admin
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_daily_stats AS
SELECT
    DATE_TRUNC('day', created_at)::DATE     AS day,
    COUNT(*)                                 AS total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_jobs,
    COUNT(*) FILTER (WHERE status = 'failed')    AS failed_jobs,
    SUM(total_pages)                         AS total_pages_processed,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)))::INTEGER AS avg_duration_seconds,
    COUNT(DISTINCT ocr_engine)               AS ocr_engines_used,
    COUNT(DISTINCT translation_engine)       AS translation_engines_used
FROM public.translation_jobs
GROUP BY DATE_TRUNC('day', created_at)::DATE
ORDER BY day DESC;

COMMENT ON VIEW public.v_daily_stats IS 'Statistiques journalières de traduction.';

-- ─────────────────────────────────────────────────────────────────────────────
-- FIN DU SCRIPT
-- Vérification: vous devriez avoir créé:
--   Tables:    translation_jobs, translation_pages, text_regions, job_options
--   Bucket:    manga-translations (public)
--   Vues:      v_job_summary, v_daily_stats
--   Fonction:  cleanup_old_jobs()
--   Policies:  RLS lecture publique + storage public
-- ─────────────────────────────────────────────────────────────────────────────

-- Vérification rapide
SELECT
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema = 'public'
     AND table_name IN ('translation_jobs','translation_pages','text_regions','job_options')) AS tables_created,
    (SELECT COUNT(*) FROM storage.buckets WHERE id = 'manga-translations') AS bucket_created;
