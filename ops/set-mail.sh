#!/usr/bin/env bash
# Configure l'envoi d'e-mails (Resend) de maisondufrancais.fr, puis envoie un e-mail de test.
# Usage : sudo ./ops/set-mail.sh
# La clé API est saisie au clavier (rien ne s'affiche) et écrite seulement dans le .env (600).
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Lancer avec sudo" >&2; exit 1; }
ENV=/var/www/maisondufrancais/.env
APP=/var/www/maisondufrancais/app
read -rsp "Clé API Resend (commence par re_) : " key; echo
[[ "$key" == re_* ]] || { echo "Ce n'est pas une clé Resend (elle commence par re_)." >&2; exit 1; }
read -rp "Adresse de l'équipe (alertes, notifications, réponses) : " team
[[ "$team" == *@*.* ]] || { echo "Adresse invalide." >&2; exit 1; }
read -rp "Expéditeur [Maison du français <no-reply@maisondufrancais.fr>] : " from
from=${from:-Maison du français <no-reply@maisondufrancais.fr>}
tmp=$(mktemp)
grep -v -E '^(RESEND_API_KEY|TEAM_EMAIL|MAIL_FROM)=' "$ENV" > "$tmp" || true
{ printf "RESEND_API_KEY='%s'\n" "$key"; printf "TEAM_EMAIL='%s'\n" "$team"; printf "MAIL_FROM='%s'\n" "$from"; } >> "$tmp"
cat "$tmp" > "$ENV"; rm -f "$tmp"; unset key
systemctl restart maisondufrancais-web
echo "Configuration enregistrée. Envoi d'un e-mail de test à $team…"
sudo -u maisondufrancais sh -c "cd $APP && ./venv/bin/python mailer.py test"
