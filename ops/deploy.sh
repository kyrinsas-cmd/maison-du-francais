#!/usr/bin/env bash
# Déploie app/ (ce dépôt) vers /var/www/maisondufrancais/app, applique le schéma (idempotent) et redémarre le service web.
# Usage : ./ops/deploy.sh            (tout)
#         ./ops/deploy.sh --no-restart
# Ne touche jamais à : venv/, au .env (hors de app/), ni aux uploads.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=/var/www/maisondufrancais/app
U=maisondufrancais

# 1. Vérifie que tout compile avant de copier
python3 -m compileall -q app >/dev/null
find app -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true

# 2. Copie (sans --delete : on ne supprime rien sur le serveur)
sudo rsync -a --chown=$U:$U --exclude=venv --exclude=__pycache__ --exclude='*.pyc' app/ "$DEST/"

# 3. Dépendances (seulement si requirements.txt a changé)
new=$(sha256sum app/requirements.txt | cut -d' ' -f1)
old=$(sudo cat "$DEST/venv/.requirements.sha256" 2>/dev/null || true)
if [ "$new" != "$old" ]; then
    sudo -u $U env HOME=/var/www/maisondufrancais "$DEST/venv/bin/pip" install -q -r "$DEST/requirements.txt"
    echo "$new" | sudo -u $U tee "$DEST/venv/.requirements.sha256" >/dev/null
    echo "dépendances mises à jour"
fi

# 4. Schéma idempotent
sudo -u $U sh -c "cd $DEST && ./venv/bin/python db.py init && ./venv/bin/python placement_seed.py && ./venv/bin/python placement_gen.py && ./venv/bin/python examcentres_seed.py"

# 5. Redémarrage
if [ "${1:-}" != "--no-restart" ]; then
    sudo systemctl restart maisondufrancais-web
    sleep 2
    code=$(curl -s -o /dev/null -w '%{http_code}' https://maisondufrancais.fr/healthz)
    echo "healthz: $code"
    [ "$code" = "200" ] || { echo "ÉCHEC : le site ne répond pas correctement" >&2; exit 1; }
    ./ops/smoke.sh || { echo "ÉCHEC : le test de fumée a échoué — corriger tout de suite" >&2; exit 1; }
fi
echo "déploiement OK"
