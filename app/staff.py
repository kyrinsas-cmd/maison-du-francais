"""Comptes de l'équipe (/compte, en français) : inscription, confirmation de l'e-mail, connexion, mot de passe oublié.

- L'inscription est ouverte mais ne donne AUCUN accès : un compte sans rôle voit seulement « en attente ».
- Le rôle « admin » est donné par un administrateur (page /admin/equipe) ou en ligne de commande (ops/make-admin.sh).
- Le rôle est relu à chaque requête : retirer le rôle ou désactiver un compte coupe l'accès immédiatement.
- Connexion possible seulement après confirmation de l'e-mail. Jetons hachés (sha256), à usage unique.
- Les professeurs ont leurs propres comptes (/espace, accounts.py) ; les familles n'ont pas de compte ici.
"""
import hashlib
import secrets

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import web
from db import connect

bp = Blueprint("compte", __name__, url_prefix="/compte")

MIN_PASSWORD = 12
VERIFY_HOURS, RESET_HOURS = 24, 1


def _h(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def _token(c, uid, purpose):
    tok = secrets.token_urlsafe(32)
    hours = VERIFY_HOURS if purpose == "verify" else RESET_HOURS
    c.execute("UPDATE staff_tokens SET used_at=now() WHERE user_id=%s AND purpose=%s AND used_at IS NULL", (uid, purpose))
    c.execute(f"INSERT INTO staff_tokens (token_hash, user_id, purpose, expires_at) VALUES (%s,%s,%s, now() + interval '{hours} hours')",
              (_h(tok), uid, purpose))
    return tok


def _use_token(c, tok, purpose):
    row = c.execute("""SELECT u.*, k.token_hash FROM staff_tokens k JOIN staff_users u ON u.id=k.user_id
                       WHERE k.token_hash=%s AND k.purpose=%s AND k.used_at IS NULL AND k.expires_at > now() AND u.active""",
                    (_h(tok), purpose)).fetchone()
    return row


def _limited(c, scope, per, window):
    h = web.ip_hash()
    n = c.execute(f"SELECT count(*) AS n FROM admin_login_failures WHERE scope=%s AND ip_hash=%s AND at > now() - interval '{window}'", (scope, h)).fetchone()["n"]
    return n >= per, h


def _check_csrf():
    if not session.get("csrf") or request.form.get("csrf") != session.get("csrf"):
        abort(400)


# ---------- session ----------

def current():
    """Le compte connecté (ou None), relu en base à chaque requête."""
    if "staff_user" not in g:
        g.staff_user = None
        uid = session.get("staff_id")
        if uid:
            with connect() as c:
                g.staff_user = c.execute("SELECT * FROM staff_users WHERE id=%s AND active AND email_verified_at IS NOT NULL", (uid,)).fetchone()
            if not g.staff_user:
                session.pop("staff_id", None)
    return g.staff_user


def is_admin():
    u = current()
    return bool(u and u["role"] == "admin")


@web.app.context_processor
def staff_ctx():
    return {"staff_user": current, "is_admin": is_admin}


@bp.after_request
def no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


def _login(uid):
    session.pop("staff_id", None)
    session["staff_id"] = uid
    session["csrf"] = secrets.token_urlsafe(24)
    session.permanent = True


def _mail(to, subject, body):
    import mailer
    return mailer.send(to, subject, body + mailer.SIGN)


# ---------- pages ----------

@bp.route("/")
def home():
    u = current()
    if not u:
        return redirect(url_for("compte.login"))
    if u["role"] == "admin":
        return redirect(url_for("admin.applications"))
    return render_template("compte/waiting.html", u=u)


@bp.route("/inscription", methods=["GET", "POST"])
def signup():
    errors, form, done = [], {}, False
    if request.method == "POST":
        _check_csrf()
        f = request.form
        form = {"name": (f.get("name") or "").strip()[:80], "email": (f.get("email") or "").strip()[:200]}
        if f.get("website"):  # champ piège
            return render_template("compte/signup.html", done=True, form=form)
        p1, p2 = f.get("password", ""), f.get("password2", "")
        if len(form["name"]) < 2:
            errors.append("Indiquez votre nom.")
        if not web.EMAIL_RE.match(form["email"]):
            errors.append("Indiquez une adresse e-mail valide.")
        if len(p1) < MIN_PASSWORD:
            errors.append(f"Le mot de passe doit faire au moins {MIN_PASSWORD} caractères.")
        elif p1 != p2:
            errors.append("Les deux mots de passe sont différents.")
        if not f.get("privacy"):
            errors.append("Merci de confirmer que vous avez lu la politique de confidentialité.")
        if not errors:
            with connect() as c:
                limited, h = _limited(c, "signup", 5, "1 hour")
                if limited:
                    errors.append("Trop d'inscriptions depuis cette connexion. Réessayez dans une heure.")
                else:
                    c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'signup')", (h,))
                    u = c.execute("SELECT * FROM staff_users WHERE lower(email)=lower(%s)", (form["email"],)).fetchone()
                    mail = None
                    if not u:
                        u = c.execute("INSERT INTO staff_users (email, name, password_hash) VALUES (%s,%s,%s) RETURNING *",
                                      (form["email"], form["name"], generate_password_hash(p1))).fetchone()
                        mail = "verify"
                    elif not u["email_verified_at"]:
                        c.execute("UPDATE staff_users SET name=%s, password_hash=%s WHERE id=%s", (form["name"], generate_password_hash(p1), u["id"]))
                        mail = "verify"
                    else:
                        mail = "exists"
                    link = url_for("compte.verify", tok=_token(c, u["id"], "verify"), _external=True) if mail == "verify" else None
            if not errors:
                # Même réponse que l'adresse soit nouvelle ou déjà inscrite (on ne révèle pas qui a un compte).
                if mail == "verify":
                    _mail(form["email"], "Confirmez votre adresse — Maison du français",
                          f"Bonjour {form['name']},\n\nPour confirmer votre adresse et activer votre compte, ouvrez ce lien (valable {VERIFY_HOURS} heures) :\n\n{link}\n\n"
                          "Si vous n'avez pas créé de compte, ignorez ce message.")
                else:
                    _mail(form["email"], "Votre compte existe déjà — Maison du français",
                          f"Bonjour,\n\nQuelqu'un (vous, sans doute) a essayé de créer un compte avec cette adresse, qui en a déjà un.\n"
                          f"Pour vous connecter : {url_for('compte.login', _external=True)}\nMot de passe oublié : {url_for('compte.forgot', _external=True)}")
                done = True
    return render_template("compte/signup.html", errors=errors, form=form, done=done)


@bp.route("/confirmer/<tok>")
def verify(tok):
    with connect() as c:
        u = _use_token(c, tok, "verify")
        if not u:
            return render_template("compte/message.html", title="Lien expiré ou déjà utilisé",
                                   text="Ce lien n'est plus valable. Recommencez l'inscription avec la même adresse pour en recevoir un nouveau."), 410
        c.execute("UPDATE staff_tokens SET used_at=now() WHERE token_hash=%s", (u["token_hash"],))
        c.execute("UPDATE staff_users SET email_verified_at=COALESCE(email_verified_at, now()), last_login_at=now() WHERE id=%s", (u["id"],))
    _login(u["id"])
    return redirect(url_for("compte.home"))


@bp.route("/connexion", methods=["GET", "POST"])
def login():
    if current():
        return redirect(url_for("compte.home"))
    error, email = None, ""
    if request.method == "POST":
        _check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        with connect() as c:
            limited, h = _limited(c, "compte", 5, "15 minutes")
            u = c.execute("SELECT * FROM staff_users WHERE lower(email)=lower(%s) AND active", (email,)).fetchone()
            if limited:
                error = "Trop de tentatives. Réessayez dans 15 minutes."
            elif u and check_password_hash(u["password_hash"], request.form.get("password", "")):
                if not u["email_verified_at"]:
                    error = "Confirmez d'abord votre adresse : ouvrez le lien reçu par e-mail (ou recommencez l'inscription pour en recevoir un nouveau)."
                else:
                    c.execute("DELETE FROM admin_login_failures WHERE scope='compte' AND ip_hash=%s", (h,))
                    c.execute("UPDATE staff_users SET last_login_at=now() WHERE id=%s", (u["id"],))
                    _login(u["id"])
                    nxt = request.args.get("next") or ""
                    if u["role"] == "admin" and nxt.startswith("/admin"):
                        return redirect(nxt)
                    return redirect(url_for("compte.home"))
            else:
                c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'compte')", (h,))
                error = "E-mail ou mot de passe incorrect."
    return render_template("compte/login.html", error=error, email=email), (401 if error else 200)


@bp.route("/deconnexion", methods=["POST"])
def logout():
    _check_csrf()
    session.pop("staff_id", None)
    return redirect(url_for("compte.login"))


@bp.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def forgot():
    sent = False
    if request.method == "POST":
        _check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        with connect() as c:
            limited, h = _limited(c, "compte-forgot", 5, "1 hour")
            c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'compte-forgot')", (h,))
            u = None if limited else c.execute("SELECT * FROM staff_users WHERE lower(email)=lower(%s) AND active AND email_verified_at IS NOT NULL", (email,)).fetchone()
            link = url_for("compte.reset", tok=_token(c, u["id"], "reset"), _external=True) if u else None
        if u:
            _mail(u["email"], "Nouveau mot de passe — Maison du français",
                  f"Bonjour {u['name']},\n\nPour choisir un nouveau mot de passe, ouvrez ce lien (valable {RESET_HOURS} heure) :\n\n{link}\n\n"
                  "Si vous n'avez rien demandé, ignorez ce message : votre mot de passe actuel reste valable.")
        sent = True
    return render_template("compte/forgot.html", sent=sent)


@bp.route("/nouveau-mot-de-passe/<tok>", methods=["GET", "POST"])
def reset(tok):
    with connect() as c:
        u = _use_token(c, tok, "reset")
    if not u:
        return render_template("compte/message.html", title="Lien expiré ou déjà utilisé",
                               text="Ce lien n'est plus valable. Refaites une demande de nouveau mot de passe."), 410
    errors = []
    if request.method == "POST":
        _check_csrf()
        p1, p2 = request.form.get("password", ""), request.form.get("password2", "")
        if len(p1) < MIN_PASSWORD:
            errors.append(f"Le mot de passe doit faire au moins {MIN_PASSWORD} caractères.")
        elif p1 != p2:
            errors.append("Les deux mots de passe sont différents.")
        else:
            with connect() as c:
                c.execute("UPDATE staff_tokens SET used_at=now() WHERE token_hash=%s", (u["token_hash"],))
                c.execute("UPDATE staff_users SET password_hash=%s WHERE id=%s", (generate_password_hash(p1), u["id"]))
            _login(u["id"])
            return redirect(url_for("compte.home"))
    return render_template("compte/reset.html", u=u, errors=errors)


# ---------- admin : équipe ----------

def init_app(app):
    app.register_blueprint(bp)
