#!/usr/bin/env bash
# Donne (ou retire) le rôle administrateur à un compte de l'équipe déjà créé sur /compte/inscription.
# Usage : sudo ./ops/make-admin.sh <e-mail>            → administrateur
#         sudo ./ops/make-admin.sh <e-mail> --retirer  → sans accès
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Lancer avec sudo" >&2; exit 1; }
[ $# -ge 1 ] || { echo "Usage : sudo $0 <e-mail> [--retirer]" >&2; exit 1; }
role=admin; [ "${2:-}" = "--retirer" ] && role=none
sudo -u postgres psql -d maisondufrancais -v ON_ERROR_STOP=1 -v email="$1" -v role="$role" -At <<'SQL'
SELECT CASE WHEN count(*) = 0 THEN 'AUCUN COMPTE avec cette adresse (créez-le d''abord sur /compte/inscription)'
            WHEN bool_and(email_verified_at IS NULL) THEN 'ADRESSE NON CONFIRMÉE : ouvrez d''abord le lien reçu par e-mail'
            ELSE 'ok' END FROM users WHERE lower(email) = lower(:'email');
UPDATE users SET role = :'role' WHERE lower(email) = lower(:'email') AND email_verified_at IS NOT NULL
RETURNING name || ' <' || email || '> → rôle : ' || role;
SQL
