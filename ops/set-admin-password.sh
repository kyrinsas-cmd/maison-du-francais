#!/usr/bin/env bash
# Définit (ou change) le mot de passe de l'admin https://maisondufrancais.fr/admin
# Usage : sudo ./ops/set-admin-password.sh
# Le mot de passe est saisi au clavier (rien ne s'affiche) ; seule son empreinte (scrypt) est écrite dans le .env.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Lancer avec sudo" >&2; exit 1; }
ENV=/var/www/maisondufrancais/.env
PY=/var/www/maisondufrancais/app/venv/bin/python
read -rsp "Nouveau mot de passe admin (12 caractères minimum) : " p1; echo
read -rsp "Confirmer : " p2; echo
[ "$p1" = "$p2" ] || { echo "Les deux saisies sont différentes." >&2; exit 1; }
[ ${#p1} -ge 12 ] || { echo "Trop court (12 caractères minimum)." >&2; exit 1; }
hash=$(printf '%s' "$p1" | sudo -u maisondufrancais "$PY" -c 'import sys; from werkzeug.security import generate_password_hash; print(generate_password_hash(sys.stdin.read()))')
unset p1 p2
tmp=$(mktemp)
grep -v '^ADMIN_PASSWORD_HASH=' "$ENV" > "$tmp" || true
printf "ADMIN_PASSWORD_HASH='%s'\n" "$hash" >> "$tmp"
cat "$tmp" > "$ENV"; rm -f "$tmp"
systemctl restart maisondufrancais-web
echo "Mot de passe admin enregistré. Connexion : https://maisondufrancais.fr/admin"
