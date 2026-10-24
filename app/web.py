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
from flask import Flask, abort, redirect, render_template, request, session, url_for

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


@app.context_processor
def inject():
    return {
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


@app.route("/")
def home():
    return render_template("home.html", levels=LEVELS)


@app.route("/enseigner", methods=["GET", "POST"])
def teach():
    if request.method == "GET":
        return redirect(url_for("home", _anchor="enseigner"))
    f = request.form
    if f.get("csrf") != session.get("csrf"):
        abort(400)
    if f.get("website"):  # champ piège : un robot l'a rempli
        return render_template("teach_done.html")
    data = {k: (f.get(k) or "").strip() for k in ("full_name", "email", "diploma", "message")}
    errors = []
    if not 2 <= len(data["full_name"]) <= 120:
        errors.append("Indiquez votre nom et prénom.")
    if not EMAIL_RE.match(data["email"]) or len(data["email"]) > 200:
        errors.append("Indiquez une adresse e-mail valide.")
    if not 2 <= len(data["diploma"]) <= 200:
        errors.append("Indiquez votre diplôme FLE.")
    if len(data["message"]) > 3000:
        errors.append("Votre message est trop long (3 000 caractères au plus).")
    if not f.get("consent"):
        errors.append("Merci d'accepter le traitement de vos données pour que nous puissions vous répondre.")
    if errors:
        return render_template("home.html", levels=LEVELS, errors=errors, form=data), 422
    from db import connect
    h = ip_hash()
    with connect() as c:
        n = c.execute("SELECT count(*) AS n FROM teacher_applications WHERE ip_hash=%s AND created_at > now() - interval '1 hour'", (h,)).fetchone()["n"]
        if n >= 5:
            return render_template("home.html", levels=LEVELS, errors=["Trop d'envois depuis cette connexion. Réessayez dans une heure."], form=data), 429
        c.execute("INSERT INTO teacher_applications (full_name, email, diploma, message, ip_hash) VALUES (%s,%s,%s,%s,%s)",
                  (data["full_name"], data["email"], data["diploma"], data["message"] or None, h))
    return render_template("teach_done.html")


@app.route("/mentions-legales")
def legal():
    return render_template("legal.html")


@app.route("/confidentialite")
def privacy():
    return render_template("privacy.html")


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n" if INDEXABLE else "User-agent: *\nDisallow: /\n"
    return app.response_class(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = ["/", "/mentions-legales", "/confidentialite"]
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
