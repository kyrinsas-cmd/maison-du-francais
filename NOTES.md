# maisondufrancais.fr (法语之家) — notes pour toute personne ou tout agent qui travaille sur ce dépôt

Vitrine France de Maison du français : école de français en ligne, classes en direct de 5 élèves au plus, professeurs FLE basés en France.
Flask + psycopg3 + Jinja2, même VPS OVH que chine-france.fr et gofestival.fr (Ubuntu, nginx, gunicorn, PostgreSQL 16). Ne pas toucher aux deux autres sites.

Cahier des charges : https://claude.ai/artifact/La25GRwcXGfBv5ZMV1duMB · maquette de l'accueil : https://claude.ai/artifact/C8ovCKXcAM5H1zJNBd4HQF

## Périmètre (important)
- **Ce serveur n'héberge que la vitrine en français** (§10 du cahier des charges) : méthode, parcours, professeurs, recrutement.
- **La plateforme élèves/parents reste hors d'ici** : comptes famille, test, réservation, paiement en yuans, classe en direct. Elle doit tourner sur des serveurs en Chine (ICP, données qui restent en Chine, entité chinoise pour WeChat Pay/Alipay, SDK TRTC/Agora/ZEGO, §11–12 et §15).
- **Aucune donnée personnelle d'élève ou de parent situé en Chine sur ce serveur.** Les parents passent par WeChat (QR code dans le pied de page). Seules les candidatures de professeurs (en France, RGPD) sont stockées ici.
- **Professeurs** : aucune fiche publiée sans l'accord écrit de la personne (même règle que chine-france, cf. son NOTES.md).

## Règles de travail
1. Ce dépôt est la source de vérité : modifier ici, commiter, puis `./ops/deploy.sh`. Ne jamais éditer `/var/www/maisondufrancais/app` directement.
2. Jamais de secrets dans le dépôt. Le `.env` est dans `/var/www/maisondufrancais/.env` (600, propriétaire `maisondufrancais`). Ne jamais l'afficher en entier.
3. Aucun compte, mot de passe ni clé API ne se saisit par un agent : c'est à l'utilisateur de le faire.
4. Sauvegarde : `backup-sites` (chaque nuit) inclut automatiquement la base `maisondufrancais` et `/var/www/maisondufrancais`.

## Dépôt GitHub
- Privé : `kyrinsas-cmd/maison-du-francais` (branche `main`). Deploy key dédiée `~/.ssh/github_maisondufrancais`, hôte SSH `github-maisondufrancais` (distincte de celle de chine-france).
- Flux : `git pull` → modifier → `git commit` → `git push` → `./ops/deploy.sh`.

## Serveur
- Créé avec `sudo newsite maisondufrancais maisondufrancais.fr --python` (2026-10-24) : utilisateur système et rôle/base PostgreSQL `maisondufrancais`, venv dans `/var/www/maisondufrancais/app/venv` (non versionné).
- Service : `maisondufrancais-web` (gunicorn sur `/run/maisondufrancais/gunicorn.sock`, app en lecture seule, seul `uploads/` est inscriptible). Copie de l'unité dans `ops/systemd/`.
- nginx : `/etc/nginx/sites-available/maisondufrancais` (copie dans `ops/nginx/`). `www` et HTTP → 301 vers `https://maisondufrancais.fr`. Certificat Let's Encrypt (certbot, renouvellement automatique testé).
- Surveillance : le domaine est dans `/etc/sites-monitored` (`sites-healthcheck`, toutes les heures).
- `./ops/deploy.sh` : compile, rsync, `pip install` si `requirements.txt` a changé, `db.py init` (applique `schema.sql`, idempotent), redémarrage, `/healthz`, `ops/smoke.sh`.
- Pas de navigateur sur le serveur : pas de capture d'écran possible.

## Application (`app/`)
- **Bilingue, chinois en langue principale** (décision de l'utilisateur, 2026-10-24) : chinois simplifié à la racine (`/`), français sous `/fr/` (mêmes adresses : `/fr/mentions-legales`…). Les anciennes adresses `/zh/…` redirigent en 301 vers la racine. `x-default` = chinois. Tous les textes sont dans `i18n.py` (`T["fr"]`, `T["zh"]`, `{{ t.cle }}` dans les templates ; une clé absente en zh retombe sur le français). `python3 app/i18n.py` liste les clés manquantes. Routes déclarées avec `@route(path)` (crée les deux versions) ; `url_for` garde la langue courante. Balises `hreflang` + sélecteur de langue dans l'en-tête et le pied de page. Pas de redirection automatique selon le navigateur (mauvais pour le référencement). Mentions légales et confidentialité : gabarits séparés `*_zh.html`, la version française fait foi.
- `web.py` : routes `/`, `/enseigner` (POST, candidature prof : CSRF de session, champ piège `website`, 5 envois/h par empreinte IP), `/mentions-legales`, `/confidentialite`, `robots.txt`, `sitemap.xml`, `/healthz`.
- `schema.sql` : idempotent ; tables `teacher_applications` (+ `note`, `updated_at`) et `admin_login_failures`.
- **Admin** `/admin` (`admin.py`, en français seulement) : liste des candidatures (filtres par statut Nouvelle/Contactée/Retenue/Refusée, recherche, pages de 50), fiche (statut, note interne, suppression définitive pour le RGPD). Connexion par un mot de passe unique : seule son empreinte scrypt est dans le `.env` (`ADMIN_PASSWORD_HASH`), définie par l'utilisateur avec `sudo ./ops/set-admin-password.sh` (saisie masquée, redémarre le service). Sans empreinte, l'admin est fermé. Session de 12 h, CSRF sur tous les POST, 5 échecs / 15 min par empreinte IP, `no-store` + `noindex`. Tests : client Flask avec un `ADMIN_PASSWORD_HASH` jetable en mémoire, jamais écrit dans le `.env`.
- **Indexation coupée** tant que `SITE_INDEXABLE=1` n'est pas dans le `.env` (meta noindex, en-tête `X-Robots-Tag`, robots.txt `Disallow`). Ne l'activer qu'avec du vrai contenu (professeurs, mentions légales complètes).
- Mentions légales lues dans le `.env` : `PUBLISHER_NAME`, `PUBLISHER_ADDRESS`, `PUBLISHER_SIREN`, `PUBLISHER_DIRECTOR`, `PUBLISHER_EMAIL`, et `CONTACT_EMAIL`. Absentes → « à compléter » en surbrillance.
- Charte : bleu `#063372`, rouge `#DF333A` (texte rouge sur blanc : `#C8242B`). Police Nunito auto-hébergée (`static/fonts`, OFL) : **pas de Google Fonts ni de CDN**, bloqués ou lents depuis la Chine.
- Animations : Motion 11.11.17 (ex-Framer Motion, version JS sans React) auto-hébergé dans `static/vendor/motion.js` (MIT). `static/site.js` : apparition du hero, éléments `[data-reveal]` au scroll. Respecte `prefers-reduced-motion` ; sans JS, tout reste visible.
- Logo : original dans `/home/ubuntu/maisondufrancais-assets/logo.png`, déclinaisons détourées dans `.../out/` ; versions web dans `static/img/`.
- Tests : scripts e2e jetables avec des adresses `e2e-*@example.test`, supprimées après usage.

## À faire / ouvert
- Remettre les MX OVH (`mx1` prio 1, `mx2` prio 5, `mx3` prio 100 `.mail.ovh.net`) : ils ont été supprimés par erreur le 2026-10-24, et aucun e-mail `@maisondufrancais.fr` n'est reçu en attendant.
- Mentions légales : quelle entité édite le site (nouvelle société ou Kyrin Services) ? Durée de conservation des candidatures à valider (proposition : 2 ans).
- QR code WeChat, e-mail de contact, photos, profils des professeurs (avec leur accord), notification e-mail des candidatures (Resend non configuré).
