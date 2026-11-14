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

-- 2026-10-24 : espace professeur
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


-- 2026-10-24 : un seul système de comptes (remplace teacher_accounts / account_tokens / staff_users / staff_tokens, vides à ce moment-là)
DROP TABLE IF EXISTS account_tokens, teacher_accounts, staff_tokens, staff_users CASCADE;
-- Rôles : eleve (15 ans et plus) | parent | professeur (espace prof dès qu'il est relié à une fiche) | moderateur | admin.
-- eleve, parent, professeur : choisis à l'inscription ; moderateur et admin : donnés seulement par un administrateur.
-- Données minimales : ni téléphone, ni adresse, ni profil d'enfant.
CREATE TABLE IF NOT EXISTS users (
    id                bigserial PRIMARY KEY,
    email             text NOT NULL,
    name              text NOT NULL,
    password_hash     text,                         -- NULL tant qu'une invitation n'est pas acceptée
    role              text NOT NULL CHECK (role IN ('eleve','parent','professeur','moderateur','admin')),
    active            boolean NOT NULL DEFAULT true,
    email_verified_at timestamptz,
    lang              text NOT NULL DEFAULT 'zh',   -- langue des e-mails
    over15            boolean NOT NULL DEFAULT false,
    privacy_at        timestamptz,
    teacher_id        bigint UNIQUE REFERENCES teachers(id) ON DELETE SET NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    last_login_at     timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS users_email ON users (lower(email));
CREATE TABLE IF NOT EXISTS user_tokens (
    token_hash text PRIMARY KEY,                    -- sha256 ; le jeton n'est jamais stocké
    user_id    bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose    text NOT NULL,                       -- verify | reset | invite
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    used_at    timestamptz
);

-- 2026-10-24 : bibliothèque de ressources 教材库 (cahier des charges §7, §9)
-- Supports faits par l'équipe ; tout élément tiers : source + autorisation obligatoires pour publier.
-- Visibilité : public (tout le monde) | members (comptes connectés) | teachers (professeurs et équipe).
CREATE TABLE IF NOT EXISTS resources (
    id            bigserial PRIMARY KEY,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    title_zh      text NOT NULL,
    title_fr      text,
    desc_zh       text,
    desc_fr       text,
    level         text,                         -- A1 A2 B1 B2, NULL = tous niveaux
    skill         text NOT NULL DEFAULT 'mixte', -- co | eo | ce | ee | mixte (听 说 读 写 综合)
    theme         text,
    ages_min      int,
    ages_max      int,
    file_name     text,                         -- dans uploads/resources/
    file_kind     text,                         -- pdf | audio | image | doc
    file_size     bigint,
    visibility    text NOT NULL DEFAULT 'members',
    origin        text NOT NULL DEFAULT 'maison', -- maison | tiers
    tp_source     text,                         -- élément tiers : d'où il vient
    tp_license    text,                         -- élément tiers : autorisation / licence
    published     boolean NOT NULL DEFAULT false,
    sort          int NOT NULL DEFAULT 0,
    downloads     int NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS resources_pub ON resources (published, level, skill);
CREATE TABLE IF NOT EXISTS resource_hits (            -- statistiques (§7) : qui ouvre quoi, par type de compte, sans identité
    id          bigserial PRIMARY KEY,
    resource_id bigint NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    at          timestamptz NOT NULL DEFAULT now(),
    role        text NOT NULL                    -- visiteur | eleve | parent | professeur | moderateur | admin
);
CREATE INDEX IF NOT EXISTS resource_hits_res ON resource_hits (resource_id, at);

-- 2026-10-24 : catalogue des classes en direct (直播课, §5 « choix de la classe », §8) — affichage seulement,
-- la réservation se fait par WeChat. Horaire saisi en heure de Pékin (UTC+8, sans changement d'heure).
CREATE TABLE IF NOT EXISTS live_classes (
    id           bigserial PRIMARY KEY,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    level        text NOT NULL,                 -- A1 A2 B1 B2
    ages_min     int,
    ages_max     int,
    teacher_id   bigint REFERENCES teachers(id) ON DELETE SET NULL,
    days         int[] NOT NULL DEFAULT '{}',   -- 1 = lundi … 7 = dimanche
    start_bj     time NOT NULL,                 -- heure de début, Pékin
    start_date   date,                          -- première séance
    capacity     int NOT NULL DEFAULT 5 CHECK (capacity BETWEEN 1 AND 5),
    seats_taken  int NOT NULL DEFAULT 0,
    status       text NOT NULL DEFAULT 'open',  -- open | soon | full | closed
    note_zh      text,
    note_fr      text,
    published    boolean NOT NULL DEFAULT false,
    sort         int NOT NULL DEFAULT 0
);

-- 2026-10-24 : données de démonstration (demandées par l'utilisateur pour voir le rendu ; à supprimer : python demo.py remove)
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false;
ALTER TABLE live_classes ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false;

-- 2026-10-25 : test de niveau (cahier des charges §5, §8) — écrit (QCM A1→B2 + rédaction) et oral (enregistrement avec
-- consentement du parent, supprimé 30 jours après la notation ou 60 jours au plus ; ou entretien en direct).
CREATE TABLE IF NOT EXISTS placement_items (           -- banque de questions (en français ; consignes traduites)
    id          bigserial PRIMARY KEY,
    key         text UNIQUE NOT NULL,                  -- identifiant stable (graine : placement_seed.py)
    level       text NOT NULL,                         -- A1 A2 B1 B2
    section     text NOT NULL,                         -- vocab | grammar | reading | listening
    passage     text,                                  -- texte à lire (compréhension écrite)
    transcript  text,                                  -- texte de l'audio (compréhension orale) : à enregistrer par l'équipe
    question    text NOT NULL,
    options     jsonb NOT NULL,                        -- liste de réponses
    answer      int NOT NULL,                          -- index de la bonne réponse
    audio_file  text,                                  -- uploads/placement-audio/ ; une question d'écoute sans audio n'est pas posée
    active      boolean NOT NULL DEFAULT true,
    sort        int NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS placement_tests (
    id            bigserial PRIMARY KEY,
    user_id       bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_label   text,                                -- pseudo de l'enfant (compte parent) ; jamais de nom complet
    age           int,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    step          text NOT NULL DEFAULT 'qcm',         -- qcm | writing | oral | submitted | evaluated
    qcm_level_idx int NOT NULL DEFAULT 0,              -- niveau en cours dans le QCM (0 = A1)
    answers       jsonb NOT NULL DEFAULT '{}',         -- {id_question: index_choisi}
    scores        jsonb NOT NULL DEFAULT '{}',         -- {niveau: [bonnes, total]}
    est_level     text,                                -- estimation automatique (QCM)
    writing_text  text,
    oral_mode     text,                                -- record | live
    oral_consent_at timestamptz,
    submitted_at  timestamptz,
    writing_level text,                                -- notes du professeur
    oral_level    text,
    final_level   text,
    class_id      bigint REFERENCES live_classes(id) ON DELETE SET NULL,
    family_msg    text,                                -- message visible par la famille
    notes         text,                                -- interne
    evaluated_at  timestamptz,
    evaluated_by  bigint REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS placement_tests_user ON placement_tests (user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS placement_recordings (
    id         bigserial PRIMARY KEY,
    test_id    bigint NOT NULL REFERENCES placement_tests(id) ON DELETE CASCADE,
    task       int NOT NULL,                           -- 1 présentation | 2 lecture | 3 question
    file_name  text NOT NULL,                          -- uploads/placement/
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (test_id, task)
);

-- 2026-10-25 : centres d'examen DELF-DALF en Chine et sessions (source : NEEA 教育部教育考试院 ; gérés dans /admin/centres)
CREATE TABLE IF NOT EXISTS exam_centres (
    id        bigserial PRIMARY KEY,
    key       text UNIQUE,                   -- graine (examcentres_seed.py)
    city_zh   text NOT NULL,
    city_fr   text,
    name_zh   text NOT NULL,
    name_fr   text,
    address   text,
    phone     text,
    website   text,
    published boolean NOT NULL DEFAULT true,
    sort      int NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS exam_sessions (
    id          bigserial PRIMARY KEY,
    key         text UNIQUE,
    title_zh    text NOT NULL,
    title_fr    text,
    levels      text,                        -- ex. « A1 A2 B1 B2 C1 C2 » ou « Prim A1.1–A2 · Junior A1–B2 »
    exams_zh    text,                        -- dates d'examen (texte)
    exams_fr    text,
    register_zh text,                        -- période d'inscription (texte)
    register_fr text,
    first_day   date,                        -- 1er jour d'examen (tri, « passée »)
    source_url  text,
    published   boolean NOT NULL DEFAULT true
);

-- 2026-10-25 : questions générées (placement_gen.py, 250 par niveau) — à relire par un professeur ; filtrables dans l'admin
ALTER TABLE placement_items ADD COLUMN IF NOT EXISTS generated boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS placement_items_level ON placement_items (level, section, active);
ALTER TABLE resources ADD COLUMN IF NOT EXISTS url text;  -- lien vers un site officiel (file_kind = 'link', rien n'est hébergé)

-- 2026-11-09 : salle de classe en direct (classroom.py, moteur LiveKit sur ce serveur)
CREATE TABLE IF NOT EXISTS class_members (              -- élèves d'une classe (compte parent ou élève) ; essai = 试听
    id          bigserial PRIMARY KEY,
    class_id    bigint NOT NULL REFERENCES live_classes(id) ON DELETE CASCADE,
    user_id     bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_label text,                                   -- prénom ou pseudo de l'enfant affiché dans la salle
    kind        text NOT NULL DEFAULT 'student' CHECK (kind IN ('student', 'trial')),
    status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended')),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (class_id, user_id)
);
CREATE TABLE IF NOT EXISTS class_sessions (             -- une séance = un cours d'une classe = une salle LiveKit
    id           bigserial PRIMARY KEY,
    class_id     bigint NOT NULL REFERENCES live_classes(id) ON DELETE CASCADE,
    starts_at    timestamptz NOT NULL,
    duration_min int NOT NULL DEFAULT 60,               -- 45 min de cours + 15 min de devoirs et questions
    status       text NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'cancelled', 'done')),
    started_at   timestamptz,                           -- entrée du professeur
    ended_at     timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (class_id, starts_at)
);
CREATE INDEX IF NOT EXISTS class_sessions_starts ON class_sessions (starts_at);
CREATE TABLE IF NOT EXISTS session_attendance (         -- présence : chaque entrée dans la salle
    session_id  bigint NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    user_id     bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_id   bigint REFERENCES class_members(id) ON DELETE SET NULL,
    role        text NOT NULL,
    first_join  timestamptz NOT NULL DEFAULT now(),
    last_join   timestamptz NOT NULL DEFAULT now(),
    joins       int NOT NULL DEFAULT 1,
    PRIMARY KEY (session_id, user_id, role)
);
-- 2026-11-09 : appel et bilan après le cours (§6), absences signalées par les familles (§17)
CREATE TABLE IF NOT EXISTS session_absences (           -- absence signalée par la famille, au moins 24 h avant
    session_id  bigint NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    member_id   bigint NOT NULL REFERENCES class_members(id) ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, member_id)
);
CREATE TABLE IF NOT EXISTS session_reports (            -- appel et petit mot du professeur, visible par la famille
    session_id  bigint NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    member_id   bigint NOT NULL REFERENCES class_members(id) ON DELETE CASCADE,
    status      text NOT NULL CHECK (status IN ('present', 'late', 'absent', 'excused')),
    comment     text,
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, member_id)
);

-- 2026-11-09 : gestion des élèves (admin). Un élève = un enfant (compte parent) ou l'élève lui-même (compte élève).
CREATE TABLE IF NOT EXISTS students (
    id          bigserial PRIMARY KEY,
    user_id     bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- compte parent ou élève
    first_name  text NOT NULL,                                            -- prénom ou pseudo affiché (en classe, dans les bilans)
    age         int,
    level       text,                                                     -- niveau CECRL retenu par l'équipe (A1.1 … B2)
    status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'left')),
    notes       text,                                                     -- notes internes de l'équipe
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS students_user_name ON students (user_id, lower(first_name));
ALTER TABLE class_members ADD COLUMN IF NOT EXISTS student_id bigint REFERENCES students(id) ON DELETE CASCADE;
ALTER TABLE placement_tests ADD COLUMN IF NOT EXISTS student_id bigint REFERENCES students(id) ON DELETE SET NULL;
-- reprise de l'existant : un élève par (compte, prénom) trouvé dans les tests et les classes
INSERT INTO students (user_id, first_name, age, level)
SELECT t.user_id, coalesce(nullif(trim(t.child_label), ''), u.name), max(t.age), max(t.final_level)
FROM placement_tests t JOIN users u ON u.id = t.user_id WHERE t.student_id IS NULL
GROUP BY t.user_id, coalesce(nullif(trim(t.child_label), ''), u.name)
ON CONFLICT DO NOTHING;
INSERT INTO students (user_id, first_name)
SELECT m.user_id, coalesce(nullif(trim(m.child_label), ''), u.name) FROM class_members m JOIN users u ON u.id = m.user_id WHERE m.student_id IS NULL
ON CONFLICT DO NOTHING;
UPDATE placement_tests t SET student_id = s.id FROM students s, users u
 WHERE t.student_id IS NULL AND u.id = t.user_id AND s.user_id = t.user_id AND lower(s.first_name) = lower(coalesce(nullif(trim(t.child_label), ''), u.name));
UPDATE class_members m SET student_id = s.id FROM students s, users u
 WHERE m.student_id IS NULL AND u.id = m.user_id AND s.user_id = m.user_id AND lower(s.first_name) = lower(coalesce(nullif(trim(m.child_label), ''), u.name));
-- un parent peut avoir deux enfants dans la même classe : unicité par élève, plus par compte
ALTER TABLE class_members DROP CONSTRAINT IF EXISTS class_members_class_id_user_id_key;
CREATE UNIQUE INDEX IF NOT EXISTS class_members_class_student ON class_members (class_id, student_id);

-- 2026-11-09 : comptes élèves créés par les parents (identifiant MF + 6 chiffres généré par le site, mot de passe), sans e-mail
ALTER TABLE students ADD COLUMN IF NOT EXISTS login_id text;
ALTER TABLE students ADD COLUMN IF NOT EXISTS password_hash text;
ALTER TABLE students ADD COLUMN IF NOT EXISTS login_enabled boolean NOT NULL DEFAULT true;
ALTER TABLE students ADD COLUMN IF NOT EXISTS last_login_at timestamptz;
CREATE UNIQUE INDEX IF NOT EXISTS students_login_id ON students (login_id) WHERE login_id IS NOT NULL;

-- 2026-11-11 : programme par niveau et avancement des classes ; devoirs (rendus par l'élève, note sur 20)
CREATE TABLE IF NOT EXISTS program_units (              -- programme indicatif par niveau (program_seed.py), modifiable par l'équipe
    id        bigserial PRIMARY KEY,
    level     text NOT NULL,
    sort      int NOT NULL,
    title_fr  text NOT NULL,
    title_zh  text NOT NULL,
    goals_fr  text,
    goals_zh  text,
    UNIQUE (level, sort)
);
CREATE TABLE IF NOT EXISTS class_progress (             -- avancement d'une classe dans le programme
    class_id   bigint NOT NULL REFERENCES live_classes(id) ON DELETE CASCADE,
    unit_id    bigint NOT NULL REFERENCES program_units(id) ON DELETE CASCADE,
    status     text NOT NULL CHECK (status IN ('doing', 'done')),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (class_id, unit_id)
);
ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS unit_id bigint REFERENCES program_units(id) ON DELETE SET NULL;  -- unité travaillée
ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS topic text;                                                     -- ce qui a été fait
CREATE TABLE IF NOT EXISTS homeworks (
    id           bigserial PRIMARY KEY,
    class_id     bigint NOT NULL REFERENCES live_classes(id) ON DELETE CASCADE,
    session_id   bigint REFERENCES class_sessions(id) ON DELETE SET NULL,
    title        text NOT NULL,
    instructions text,
    file_name    text,                                    -- pièce jointe du professeur (uploads/homework/)
    file_kind    text,
    due_at       timestamptz,
    created_by   bigint REFERENCES users(id) ON DELETE SET NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS homework_submissions (
    id           bigserial PRIMARY KEY,
    homework_id  bigint NOT NULL REFERENCES homeworks(id) ON DELETE CASCADE,
    student_id   bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    text_answer  text,
    file_name    text,
    file_kind    text,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    grade        numeric(4,1) CHECK (grade >= 0 AND grade <= 20),
    feedback     text,
    graded_at    timestamptz,
    UNIQUE (homework_id, student_id)
);

-- Langue choisie pour l'espace connecté (2026-11-12) : NULL = défaut (français pour l'équipe et les professeurs, langue de l'adresse pour les familles)
ALTER TABLE users ADD COLUMN IF NOT EXISTS ui_lang text CHECK (ui_lang IN ('zh', 'fr'));
ALTER TABLE students ADD COLUMN IF NOT EXISTS ui_lang text CHECK (ui_lang IN ('zh', 'fr'));

-- Espace élève : exercices (练习题) et examens blancs (模拟考试), 2026-11-12. Questions de placement_items.
CREATE TABLE IF NOT EXISTS pupil_quizzes (
    id          bigserial PRIMARY KEY,
    student_id  bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    kind        text NOT NULL CHECK (kind IN ('practice', 'mock')),
    level       text NOT NULL,
    section     text,                                  -- NULL = mélangé (exercices) ; toujours NULL pour un examen blanc
    item_ids    jsonb NOT NULL,                        -- questions, dans l'ordre affiché
    perms       jsonb NOT NULL,                        -- ordre mélangé des réponses par question {item_id: [index d'origine…]}
    answers     jsonb,                                 -- {item_id: index d'origine choisi ou null}
    score       int,
    total       int NOT NULL,
    by_section  jsonb,
    deadline    timestamptz,                           -- examen blanc : fin du temps
    late        boolean NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
);
CREATE INDEX IF NOT EXISTS pupil_quizzes_student ON pupil_quizzes (student_id, kind, created_at DESC);

-- 作业库 : devoirs types par unité du programme (homework_seed.py + ajouts de l'équipe et des professeurs), 2026-11-12
CREATE TABLE IF NOT EXISTS homework_bank (
    id          bigserial PRIMARY KEY,
    key         text UNIQUE,                            -- devoirs de la graine seulement
    unit_id     bigint NOT NULL REFERENCES program_units(id) ON DELETE CASCADE,
    kind        text NOT NULL DEFAULT 'ecrit' CHECK (kind IN ('ecrit', 'oral')),
    title_fr    text NOT NULL,
    title_zh    text,
    instr_fr    text,
    instr_zh    text,
    file_name   text,                                   -- pièce jointe (uploads/homework/, préfixe b)
    file_kind   text,
    sort        int NOT NULL DEFAULT 0,
    source      text NOT NULL DEFAULT 'team' CHECK (source IN ('seed', 'team', 'teacher')),
    created_by  bigint REFERENCES users(id) ON DELETE SET NULL,
    active      boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS homework_bank_unit ON homework_bank (unit_id, sort);
ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS bank_id bigint REFERENCES homework_bank(id) ON DELETE SET NULL;
ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS unit_id bigint REFERENCES program_units(id) ON DELETE SET NULL;

-- 课 : leçons du programme (lessons.py, lessons_seed.py), 2026-11-14
CREATE TABLE IF NOT EXISTS lessons (
    id           bigserial PRIMARY KEY,
    key          text UNIQUE,                            -- leçons de la graine seulement
    unit_id      bigint NOT NULL REFERENCES program_units(id) ON DELETE CASCADE,
    sort         int NOT NULL,
    title_fr     text NOT NULL,
    title_zh     text NOT NULL,
    content      jsonb NOT NULL,                         -- guide, fiche, exercices (voir lessons.validate)
    audio_files  jsonb NOT NULL DEFAULT '{}',            -- {piste: fichier dans uploads/lessons/}
    status       text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'published')),
    edited       boolean NOT NULL DEFAULT false,         -- modifiée par l'équipe : la graine n'y touche plus
    updated_at   timestamptz NOT NULL DEFAULT now(),
    updated_by   bigint REFERENCES users(id) ON DELETE SET NULL,
    published_at timestamptz,
    published_by bigint REFERENCES users(id) ON DELETE SET NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS lessons_unit ON lessons (unit_id, sort);
CREATE TABLE IF NOT EXISTS lesson_comments (                -- remarques de relecture (professeurs, équipe)
    id          bigserial PRIMARY KEY,
    lesson_id   bigint NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    user_id     bigint REFERENCES users(id) ON DELETE SET NULL,
    body        text NOT NULL,
    resolved_at timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS lesson_attempts (                -- exercices en ligne d'une leçon, par élève
    id          bigserial PRIMARY KEY,
    lesson_id   bigint NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    student_id  bigint NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    perms       jsonb NOT NULL,                          -- ordre mélangé des choix {exercice: [index d'origine…]}
    answers     jsonb,
    score       int,
    total       int NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
);
CREATE INDEX IF NOT EXISTS lesson_attempts_student ON lesson_attempts (student_id, lesson_id, finished_at DESC);
ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS lesson_id bigint REFERENCES lessons(id) ON DELETE SET NULL;  -- leçon faite en cours
