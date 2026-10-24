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

-- 2026-10-24 : réglages modifiables dans l'admin (ex. tarifs)
CREATE TABLE IF NOT EXISTS settings (
    key        text PRIMARY KEY,
    value      jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- 2026-10-24 : espace professeur (comptes e-mail + mot de passe, créés sur invitation depuis l'admin)
CREATE TABLE IF NOT EXISTS teacher_accounts (
    id            bigserial PRIMARY KEY,
    teacher_id    bigint UNIQUE NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    email         text NOT NULL,
    password_hash text,                          -- NULL tant que l'invitation n'est pas acceptée
    active        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    activated_at  timestamptz,
    last_login_at timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS teacher_accounts_email ON teacher_accounts (lower(email));
CREATE TABLE IF NOT EXISTS account_tokens (
    token_hash text PRIMARY KEY,                 -- sha256 du jeton ; le jeton lui-même n'est jamais stocké
    account_id bigint NOT NULL REFERENCES teacher_accounts(id) ON DELETE CASCADE,
    purpose    text NOT NULL,                    -- invite | reset
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    used_at    timestamptz
);
-- Modifications proposées par le professeur, en attente de validation par l'équipe
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS pending jsonb;
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS pending_at timestamptz;
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS pending_feedback text;   -- message de l'équipe si refus
-- Échecs de connexion : admin et espace professeur
ALTER TABLE admin_login_failures ADD COLUMN IF NOT EXISTS scope text NOT NULL DEFAULT 'admin';

-- 2026-10-24 : notes et avis sur les professeurs (cahier des charges §18)
-- Saisis et modérés par l'équipe à partir d'avis réels recueillis auprès des familles (WeChat, questionnaire) :
-- source et accord de publication obligatoires ; jamais d'avis inventé ni rémunéré.
CREATE TABLE IF NOT EXISTS reviews (
    id              bigserial PRIMARY KEY,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    teacher_id      bigint NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    rating          smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment_zh      text,
    comment_fr      text,                      -- traduction (facultative)
    author_label    text NOT NULL,             -- ex. « Léo 的妈妈 » : jamais de nom complet
    level           text,                      -- A1, A2…
    course_month    date,                      -- mois du cours évalué (1er du mois)
    source          text NOT NULL,             -- d'où vient l'avis : « message WeChat du 20/10/2026 »…
    consent_publish boolean NOT NULL DEFAULT false,
    status          text NOT NULL DEFAULT 'pending',  -- pending | published | rejected
    reject_reason   text,
    published_at    timestamptz
);
CREATE INDEX IF NOT EXISTS reviews_teacher ON reviews (teacher_id, status, published_at DESC);

-- 2026-10-24 : réclamations (cahier des charges §18) — visibles par l'équipe seulement.
-- Enregistrées par l'équipe à partir des messages reçus (WeChat, e-mail…) ; la famille suit le statut avec un numéro (/suivi).
-- Données minimales : pseudonyme de l'auteur, pas de téléphone ni d'adresse.
CREATE TABLE IF NOT EXISTS complaints (
    id                bigserial PRIMARY KEY,
    code              text UNIQUE NOT NULL,          -- numéro de suivi donné à la famille (ex. R-7KQ4-M2XD)
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    category          text NOT NULL,
    severity          text NOT NULL DEFAULT 'normal', -- normal | high | grave
    teacher_id        bigint REFERENCES teachers(id) ON DELETE SET NULL,
    complainant_label text NOT NULL,                  -- « Léo 的妈妈 »
    complainant_role  text NOT NULL DEFAULT 'parent', -- parent | eleve
    channel           text NOT NULL,                  -- wechat | email | phone | other
    channel_ref       text,                           -- repère pour retrouver la conversation (jamais affiché à la famille)
    description       text NOT NULL,
    assignee          text,
    status            text NOT NULL DEFAULT 'new',    -- new | in_progress | waiting | resolved | closed
    resolution        text,                           -- résultat (interne)
    public_message    text,                           -- message visible par la famille sur /suivi
    closed_at         timestamptz
);
CREATE INDEX IF NOT EXISTS complaints_status ON complaints (status, severity, created_at DESC);
CREATE TABLE IF NOT EXISTS complaint_events (
    id           bigserial PRIMARY KEY,
    complaint_id bigint NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    at           timestamptz NOT NULL DEFAULT now(),
    text         text NOT NULL
);

-- 2026-10-24 : comptes nominatifs de l'équipe (remplacent le mot de passe unique de l'admin)
-- Inscription libre mais sans aucun accès : seul un administrateur donne le rôle « admin ».
CREATE TABLE IF NOT EXISTS staff_users (
    id                bigserial PRIMARY KEY,
    email             text NOT NULL,
    name              text NOT NULL,
    password_hash     text NOT NULL,
    role              text NOT NULL DEFAULT 'none',   -- none | admin
    active            boolean NOT NULL DEFAULT true,
    email_verified_at timestamptz,
    created_at        timestamptz NOT NULL DEFAULT now(),
    last_login_at     timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS staff_users_email ON staff_users (lower(email));
CREATE TABLE IF NOT EXISTS staff_tokens (
    token_hash text PRIMARY KEY,                 -- sha256 ; le jeton n'est jamais stocké
    user_id    bigint NOT NULL REFERENCES staff_users(id) ON DELETE CASCADE,
    purpose    text NOT NULL,                    -- verify | reset
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    used_at    timestamptz
);
