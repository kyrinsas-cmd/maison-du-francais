"""maisondufrancais.fr — vitrine France de Maison du français (法语之家).

Périmètre (cahier des charges §10–12) : site de marque en français (méthode, parcours, professeurs, recrutement).
La plateforme élèves/parents (comptes, paiement, classe en direct) sera hébergée en Chine : rien de tout ça ici.
"""
import hashlib
import os
import re
import secrets
from datetime import date

from dotenv import load_dotenv
from flask import Flask, abort, g, redirect, render_template, request, session, url_for

from i18n import HTML_LANG, LANGS, texts

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 7 * 24 * 3600

SITE_URL = os.environ.get("SITE_URL", "https://maisondufrancais.fr")
# Le site reste en noindex tant que SITE_INDEXABLE=1 n'est pas mis dans le .env (contenu provisoire).
INDEXABLE = os.environ.get("SITE_INDEXABLE") == "1"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Parcours (cahier des charges §16) : heures guidées indicatives DELF ÷ 0,75 h, 3 séances/semaine. Approximatif, à confirmer.
LEVELS = [
    {"code": "A1", "sessions": 133, "weeks": 44, "exam": "DELF A1"},
    {"code": "A2", "sessions": 133, "weeks": 44, "exam": "DELF A2"},
    {"code": "B1", "sessions": 233, "weeks": 78, "exam": "DELF B1"},
    {"code": "B2", "sessions": 267, "weeks": 89, "exam": "DELF B2"},
]


def publisher():
    """Mentions légales : lues dans le .env ; absentes → affichées « à compléter »."""
    return {k: os.environ.get(f"PUBLISHER_{k.upper()}") for k in ("name", "address", "siren", "director", "email")}


def route(path, **kw):
    """Enregistre la page en chinois, langue principale (path), et en français (/fr + path)."""
    def deco(f):
        app.add_url_rule(path, view_func=f, defaults={"lang": "zh"}, **kw)
        app.add_url_rule("/<any(fr):lang>" + path, view_func=f, **kw)
        return f
    return deco


@app.url_value_preprocessor
def pull_lang(endpoint, values):
    if values and "lang" in values:  # pas de route (404) : current_lang() regardera l'adresse
        g.lang = values.pop("lang")


@app.url_defaults
def add_lang(endpoint, values):
    if "lang" not in values and app.url_map.is_endpoint_expecting(endpoint, "lang"):
        values["lang"] = g.get("lang", "zh")


def current_lang():
    if "lang" not in g:  # 404 et erreurs : pas de route, on regarde l'adresse
        g.lang = "fr" if request.path == "/fr" or request.path.startswith("/fr/") else "zh"
    return g.lang


def alternates():
    """Adresses de la même page dans chaque langue (sélecteur de langue, balises hreflang)."""
    ep = request.endpoint
    if not ep or not app.url_map.is_endpoint_expecting(ep, "lang"):
        ep = "home"
    return {lang: url_for(ep, **dict(request.view_args or {}, lang=lang)) for lang in LANGS}


@app.context_processor
def inject():
    lang = current_lang()
    return {
        "lang": lang,
        "html_lang": HTML_LANG[lang],
        "other_lang": "fr" if lang == "zh" else "zh",
        "t": texts(lang),
        "alternates": alternates,
        "indexable": INDEXABLE,
        "site_url": SITE_URL,
        "year": date.today().year,
        "contact_email": os.environ.get("CONTACT_EMAIL"),
        "pub": publisher(),
        "csrf": csrf_token,
    }


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def ip_hash():
    ip = request.headers.get("X-Real-IP") or request.remote_addr or ""
    salt = f"{app.config['SECRET_KEY']}:{date.today().isoformat()}"
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]


@route("/")
def home():
    return render_template("home.html", levels=LEVELS)


@route("/methode")
def method():
    return render_template("method.html")


@route("/cours")
def path():
    return render_template("path.html", levels=LEVELS)


@route("/atelier-paris")
def atelier():
    return render_template("atelier.html")


@route("/contact")
def contact():
    return render_template("contact.html")


@route("/enseigner", methods=["GET", "POST"])
def teach_page():
    t = texts(g.lang)
    if request.method == "GET":
        return render_template("teach.html")
    f = request.form
    if f.get("csrf") != session.get("csrf"):
        abort(400)
    if f.get("website"):  # champ piège : un robot l'a rempli
        return render_template("teach_done.html")
    data = {k: (f.get(k) or "").strip() for k in ("full_name", "email", "diploma", "message")}
    errors = []
    if not 2 <= len(data["full_name"]) <= 120:
        errors.append(t.err_name)
    if not EMAIL_RE.match(data["email"]) or len(data["email"]) > 200:
        errors.append(t.err_email)
    if not 2 <= len(data["diploma"]) <= 200:
        errors.append(t.err_diploma)
    if len(data["message"]) > 3000:
        errors.append(t.err_long)
    if not f.get("consent"):
        errors.append(t.err_consent)
    if errors:
        return render_template("teach.html", errors=errors, form=data), 422
    from db import connect
    h = ip_hash()
    with connect() as c:
        n = c.execute("SELECT count(*) AS n FROM teacher_applications WHERE ip_hash=%s AND created_at > now() - interval '1 hour'", (h,)).fetchone()["n"]
        if n >= 5:
            return render_template("teach.html", errors=[t.err_rate], form=data), 429
        c.execute("INSERT INTO teacher_applications (full_name, email, diploma, message, ip_hash) VALUES (%s,%s,%s,%s,%s)",
                  (data["full_name"], data["email"], data["diploma"], data["message"] or None, h))
    return render_template("teach_done.html")


@route("/mentions-legales")
def legal():
    return render_template("legal_zh.html" if g.lang == "zh" else "legal.html")


@route("/confidentialite")
def privacy():
    return render_template("privacy_zh.html" if g.lang == "zh" else "privacy.html")


@app.route("/zh/", defaults={"rest": ""})
@app.route("/zh/<path:rest>")
def old_zh(rest):
    """Le chinois était sous /zh/ avant de devenir la langue principale (2026-10-24) : redirection définitive."""
    qs = request.query_string.decode()
    return redirect("/" + rest + ("?" + qs if qs else ""), 301)


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n" if INDEXABLE else "User-agent: *\nDisallow: /\n"
    return app.response_class(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    paths = ["/", "/methode", "/cours", "/professeurs", "/atelier-paris", "/enseigner", "/contact", "/mentions-legales", "/confidentialite"] + pricing.sitemap_paths() + teachers.sitemap_paths()
    pages = [p for path in paths for p in (path, "/fr" + path)]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(f"  <url><loc>{SITE_URL}{p}</loc></url>\n" for p in pages) + "</urlset>\n"
    return app.response_class(xml, mimetype="application/xml")


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("img/favicon.ico")


@app.route("/apple-touch-icon.png")
def apple_icon():
    return app.send_static_file("img/apple-touch-icon.png")


@app.route("/healthz")
def healthz():
    from db import connect
    with connect() as c:
        c.execute("SELECT 1")
    return "ok"


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.after_request
def secure(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    if not INDEXABLE:
        resp.headers.setdefault("X-Robots-Tag", "noindex")
    return resp


import admin  # noqa: E402  (après la définition de app et de ip_hash)
import pricing  # noqa: E402  (idem)
import teachers  # noqa: E402  (ajoute ses routes à app et au blueprint admin avant son enregistrement)
import accounts  # noqa: E402  (espace professeur + routes admin des comptes)

admin.init_app(app)
accounts.init_app(app)
