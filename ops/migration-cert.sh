#!/usr/bin/env bash
# Bascule vers le serveur Ecole, étape 2 (APRÈS le changement du DNS) : vrai certificat Let's Encrypt, config nginx du dépôt,
# certificat de LiveKit, suppression du certificat provisoire.
# Usage : sudo ./ops/migration-cert.sh
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Lancer avec sudo" >&2; exit 1; }
cd "$(dirname "$0")/.."
IP=141.94.98.159
for d in maisondufrancais.fr www.maisondufrancais.fr; do
  got=$(getent ahostsv4 $d | awk 'NR==1{print $1}')
  [ "$got" = "$IP" ] || { echo "$d pointe encore vers ${got:-rien}, pas vers $IP : attendre la propagation DNS" >&2; exit 1; }
done
certbot certonly --nginx --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring \
  -d maisondufrancais.fr -d www.maisondufrancais.fr
install -m644 ops/nginx/maisondufrancais.conf /etc/nginx/sites-available/maisondufrancais
nginx -t && systemctl reload nginx
RENEWED_DOMAINS="maisondufrancais.fr www.maisondufrancais.fr" RENEWED_LINEAGE=/etc/letsencrypt/live/maisondufrancais.fr \
  /etc/letsencrypt/renewal-hooks/deploy/livekit.sh
rm -rf /etc/ssl/maisondufrancais-temp
certbot renew --dry-run --cert-name maisondufrancais.fr
SMOKE_REMOTE=1 ./ops/smoke.sh
echo "certificat OK"
