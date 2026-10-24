#!/usr/bin/env bash
# Test de fumée après déploiement : les pages clés doivent répondre 200/301/302 (404 attendu sur une page inexistante).
set -u
BASE="${1:-https://maisondufrancais.fr}"
URLS="/ /methode /cours /professeurs /atelier-paris /enseigner /contact /mentions-legales /confidentialite /fr/ /fr/methode /fr/cours /fr/professeurs /fr/atelier-paris /fr/enseigner /fr/contact /fr/mentions-legales /fr/confidentialite /zh/ /robots.txt /sitemap.xml /favicon.ico /apple-touch-icon.png /static/site.css /static/site.js /static/vendor/motion.js /static/fonts/nunito-latin.woff2 /static/img/logo-icon.png /admin/login /espace/connexion /espace/mot-de-passe-oublie /healthz"
bad=0
for u in $URLS; do
  c=$(curl -s -o /dev/null -m 30 -w '%{http_code}' "$BASE$u")
  case "$c" in 200|301|302) ;; *) echo "  ✗ $c $u"; bad=$((bad+1));; esac
done
c=$(curl -s -o /dev/null -m 30 -w '%{http_code}' "$BASE/page-qui-n-existe-pas")
[ "$c" = "404" ] || { echo "  ✗ $c sur une page inexistante (404 attendu)"; bad=$((bad+1)); }
if [ "$bad" -gt 0 ]; then echo "test de fumée : $bad page(s) en erreur" >&2; exit 1; fi
echo "test de fumée OK ($(echo $URLS | wc -w) pages + 404)"
