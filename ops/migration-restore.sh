#!/usr/bin/env bash
# Bascule vers le serveur Ecole, étape 1 : remplace la base et les uploads de CE serveur par la copie finale de l'ancien.
# Usage : sudo ./ops/migration-restore.sh <maisondufrancais.dump> <uploads.tgz>
#   - le dump : pg_dump -Fc de la base maisondufrancais (ancien serveur, site arrêté) ;
#   - l'archive : tar czf du dossier uploads/ (avec le chemin « uploads/… » en tête), .env facultatif (ignoré : on garde celui d'ici).
# Le site est arrêté pendant l'opération ; l'ancienne base d'ici est renommée (maisondufrancais_avant_<date>), pas supprimée,
# et les anciens uploads sont gardés dans /var/www/maisondufrancais/uploads.avant_<date>.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Lancer avec sudo" >&2; exit 1; }
[ $# -eq 2 ] || { echo "Usage : sudo $0 <dump> <uploads.tgz>" >&2; exit 1; }
DUMP=$(realpath "$1"); TGZ=$(realpath "$2"); U=maisondufrancais; B=/var/www/$U; TS=$(date +%Y%m%d_%H%M%S)
pg_restore -l "$DUMP" >/dev/null || { echo "dump illisible" >&2; exit 1; }
[ "$(tar tzf "$TGZ" | grep -c '^uploads/')" -gt 0 ] || { echo "l'archive ne contient pas uploads/" >&2; exit 1; }

echo "1. arrêt du site"
systemctl stop $U-web

echo "2. base : l'actuelle devient ${U}_avant_$TS, puis restauration"
runuser -u postgres -- psql -qv ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$U' AND pid<>pg_backend_pid()" >/dev/null
runuser -u postgres -- psql -qv ON_ERROR_STOP=1 -c "ALTER DATABASE $U RENAME TO ${U}_avant_$TS"
runuser -u postgres -- createdb -O $U $U
runuser -u postgres -- psql -d $U -qv ON_ERROR_STOP=1 -c "REVOKE ALL ON DATABASE $U FROM PUBLIC; ALTER SCHEMA public OWNER TO $U; REVOKE CREATE ON SCHEMA public FROM PUBLIC;"
cp "$DUMP" /tmp/$U-restore.dump; chown postgres /tmp/$U-restore.dump
runuser -u postgres -- pg_restore --no-owner --role=$U --no-acl -d $U /tmp/$U-restore.dump
rm -f /tmp/$U-restore.dump

echo "3. uploads : les actuels deviennent uploads.avant_$TS"
mv $B/uploads $B/uploads.avant_$TS
tar xzf "$TGZ" -C $B uploads
chown -R $U:$U $B/uploads

echo "4. schéma et données de référence (idempotent), redémarrage"
runuser -u $U -- sh -c "cd $B/app && ./venv/bin/python db.py init && ./venv/bin/python placement_seed.py && ./venv/bin/python program_seed.py && ./venv/bin/python homework_seed.py && ./venv/bin/python examcentres_seed.py" >/dev/null
systemctl start $U-web; sleep 2
runuser -u postgres -- psql -d $U -tAc "SELECT 'comptes : ' || count(*) FROM users"
code=$(curl -s --resolve maisondufrancais.fr:443:127.0.0.1 -o /dev/null -w '%{http_code}' https://maisondufrancais.fr/healthz)
echo "healthz : $code"; [ "$code" = 200 ] || { echo "ÉCHEC" >&2; exit 1; }
echo "OK. Une fois tout vérifié : sudo -u postgres dropdb ${U}_avant_$TS ; sudo rm -rf $B/uploads.avant_$TS"
