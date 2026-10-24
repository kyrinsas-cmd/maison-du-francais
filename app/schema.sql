-- Schéma idempotent (CREATE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS). Toute évolution s'ajoute à la fin.
-- Règle : aucune donnée personnelle d'élève ou de parent situé en Chine sur ce serveur (cahier des charges §11–12).

-- Candidatures des professeurs FLE (basés en France, RGPD)
CREATE TABLE IF NOT EXISTS teacher_applications (
    id          bigserial PRIMARY KEY,
    created_at  timestamptz NOT NULL DEFAULT now(),
    full_name   text NOT NULL,
    email       text NOT NULL,
    diploma     text NOT NULL,
    message     text,
    ip_hash     text,               -- hash à sel quotidien, uniquement pour limiter les envois abusifs
    status      text NOT NULL DEFAULT 'new'  -- new | contacted | rejected | accepted
);
CREATE INDEX IF NOT EXISTS teacher_applications_created ON teacher_applications (created_at);

-- 2026-10-24 : admin des candidatures
ALTER TABLE teacher_applications ADD COLUMN IF NOT EXISTS note text;          -- note privée de l'équipe
ALTER TABLE teacher_applications ADD COLUMN IF NOT EXISTS updated_at timestamptz;
CREATE TABLE IF NOT EXISTS admin_login_failures (
    id      bigserial PRIMARY KEY,
    at      timestamptz NOT NULL DEFAULT now(),
    ip_hash text NOT NULL
);
CREATE INDEX IF NOT EXISTS admin_login_failures_at ON admin_login_failures (at);

-- 2026-10-24 : fiches professeurs (gérées par l'équipe dans /admin ; publiées seulement avec l'accord écrit du professeur)
CREATE TABLE IF NOT EXISTS teachers (
    id             bigserial PRIMARY KEY,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    first_name     text NOT NULL,
    last_initial   text,                         -- affiché « Marie D. »
    slug           text UNIQUE NOT NULL,
    diplomas       text,                         -- ex. « Master FLE, habilitation DELF »
    ages_min       int,
    ages_max       int,
    levels         text[] NOT NULL DEFAULT '{}', -- A1 A2 B1 B2
    bio_zh         text,
    bio_fr         text,
    courses_zh     text,                         -- un cours par ligne
    courses_fr     text,
    photo_file     text,                         -- nom du fichier dans uploads/teachers/
    video_file     text,
    video_status   text NOT NULL DEFAULT 'none', -- none | pending | approved | changes
    video_feedback text,                         -- message au professeur si « à modifier »
    consent_at     date,                         -- date de l'accord écrit
    consent_ref    text,                         -- où est conservé l'accord (e-mail du…, contrat…)
    published      boolean NOT NULL DEFAULT false,
    sort           int NOT NULL DEFAULT 0,
    application_id bigint REFERENCES teacher_applications(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS teachers_published ON teachers (published, sort, id);
