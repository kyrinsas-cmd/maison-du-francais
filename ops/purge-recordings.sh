#!/usr/bin/env bash
# Supprime les enregistrements oraux des tests de niveau arrivés à échéance (30 j après l'évaluation, 60 j au plus).
# Lancé chaque jour par le minuteur maisondufrancais-purge.timer ; à la main : sudo ./ops/purge-recordings.sh
set -euo pipefail
cd /var/www/maisondufrancais/app
sudo -u maisondufrancais ./venv/bin/python -c "import web, placement; print('enregistrements supprimés :', placement.purge_recordings())"
