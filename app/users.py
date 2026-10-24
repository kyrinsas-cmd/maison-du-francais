"""Comptes (un seul système pour tout le monde) : inscription, confirmation de l'e-mail, connexion, mot de passe oublié, mon compte.

Pages publiques bilingues (zh à la racine, fr sous /fr) : /compte/inscription, /compte/connexion, /compte/…
Rôles : eleve | parent | professeur (choisis à l'inscription) ; moderateur | admin (donnés seulement par un administrateur).
- eleve : 15 ans et plus (case obligatoire) ; en dessous, c'est le parent qui a un compte (cahier des charges §4–5, RGPD art. 8).
- professeur : l'espace professeur (/espace) s'ouvre quand l'équipe relie le compte à une fiche (« Valider »).
- moderateur : admin sauf Tarifs, Utilisateurs et suppression de fiches ; admin : tout.
Après connexion : admin/moderateur → /admin ; professeur relié → /espace ; sinon → « Mon compte ».
Données minimales (nom, e-mail, type de compte) ; chacun peut supprimer son compte. Le rôle est relu à chaque requête.
Avertissement : les comptes élève/parent sur ce serveur en France vont à l'encontre du §11–12 du cahier des charges
(données des familles en Chine) ; choix de l'utilisateur du 2026-10-24, à faire valider par l'avocat.
"""
import hashlib
import secrets

from flask import abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import web
from db import connect
from i18n import texts

ROLES = ("eleve", "parent", "professeur", "moderateur", "admin")
SELF_ROLES = ("eleve", "parent", "professeur")
STAFF = ("moderateur", "admin")
MIN_PASSWORD = 7  # choix de l'utilisateur (2026-10-24)
HOURS = {"verify": 24, "reset": 1, "invite": 24 * 7}


# ---------- outils ----------

def _h(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def new_token(c, uid, purpose):
    tok = secrets.token_urlsafe(32)
    c.execute("UPDATE user_tokens SET used_at=now() WHERE user_id=%s AND purpose=%s AND used_at IS NULL", (uid, purpose))
    c.execute(f"INSERT INTO user_tokens (token_hash, user_id, purpose, expires_at) VALUES (%s,%s,%s, now() + interval '{HOURS[purpose]} hours')",
              (_h(tok), uid, purpose))
    return tok


def _use_token(c, tok, purposes):
    return c.execute("""SELECT u.*, k.token_hash, k.purpose FROM user_tokens k JOIN users u ON u.id=k.user_id
                        WHERE k.token_hash=%s AND k.purpose = ANY(%s) AND k.used_at IS NULL AND k.expires_at > now() AND u.active""",
                     (_h(tok), list(purposes))).fetchone()


def _limited(c, scope, per, window):
    h = web.ip_hash()
    n = c.execute(f"SELECT count(*) AS n FROM admin_login_failures WHERE scope=%s AND ip_hash=%s AND at > now() - interval '{window}'", (scope, h)).fetchone()["n"]
    return n >= per, h


def _fail(c, scope, h):
    c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, %s)", (h, scope))


def check_csrf():
    if not session.get("csrf") or request.form.get("csrf") != session.get("csrf"):
        abort(400)


def link(endpoint, lang, **kw):
    return url_for(endpoint, lang=lang, _external=True, **kw)


# ---------- session ----------

def current():
    """Compte connecté (ou None), relu en base à chaque requête : un rôle retiré ou un compte désactivé coupe l'accès."""
    if "user" not in g:
        g.user = None
        uid = session.get("user_id")
        if uid:
            with connect() as c:
                g.user = c.execute("SELECT * FROM users WHERE id=%s AND active AND email_verified_at IS NOT NULL AND password_hash IS NOT NULL", (uid,)).fetchone()
            if not g.user:
                session.pop("user_id", None)
    return g.user


def role():
    u = current()
    return u["role"] if u else None


def is_admin():
    return role() == "admin"


def is_staff():
    return role() in STAFF


def login_user(uid):
    session.pop("user_id", None)
    session["user_id"] = uid
    session["csrf"] = secrets.token_urlsafe(24)
    session.permanent = True
    g.pop("user", None)


def landing(u, lang):
    if u["role"] in STAFF:
        return url_for("admin.applications")
    if u["role"] == "professeur" and u["teacher_id"]:
        return url_for("espace.home")
    return url_for("account_home", lang=lang)


@web.app.context_processor
def users_ctx():
    return {"current_user": current, "is_admin": is_admin, "is_staff": is_staff, "ROLES": ROLES}


def role_label(r, lang):
    return texts(lang)[f"ac_role_{r}"]


# ---------- e-mails ----------

MAILS = {
    "verify": {"zh": ("请确认您的邮箱 — 法语之家", "{name}，您好：\n\n请打开以下链接确认邮箱并激活账户（24小时内有效）：\n\n{link}\n\n如果不是您本人注册，请忽略此邮件。"),
               "fr": ("Confirmez votre adresse — Maison du français", "Bonjour {name},\n\nPour confirmer votre adresse et activer votre compte, ouvrez ce lien (valable 24 heures) :\n\n{link}\n\nSi vous n'avez pas créé de compte, ignorez ce message.")},
    "exists": {"zh": ("您的账户已存在 — 法语之家", "您好：\n\n有人（应该是您本人）尝试用此邮箱注册，但该邮箱已有账户。\n登录：{login}\n忘记密码：{forgot}"),
               "fr": ("Votre compte existe déjà — Maison du français", "Bonjour,\n\nQuelqu'un (vous, sans doute) a essayé de créer un compte avec cette adresse, qui en a déjà un.\nConnexion : {login}\nMot de passe oublié : {forgot}")},
    "reset": {"zh": ("重置密码 — 法语之家", "{name}，您好：\n\n请打开以下链接设置新密码（1小时内有效）：\n\n{link}\n\n如果您没有申请，请忽略此邮件，当前密码依然有效。"),
              "fr": ("Nouveau mot de passe — Maison du français", "Bonjour {name},\n\nPour choisir un nouveau mot de passe, ouvrez ce lien (valable 1 heure) :\n\n{link}\n\nSi vous n'avez rien demandé, ignorez ce message : votre mot de passe actuel reste valable.")},
    "invite": {"fr": ("Votre espace professeur — Maison du français", "Bonjour {name},\n\nL'équipe de Maison du français a créé votre espace professeur. Choisissez votre mot de passe avec ce lien, valable 7 jours :\n\n{link}\n\nVous pourrez ensuite compléter votre profil et envoyer votre vidéo de présentation.")},
    "teacher_ok": {"fr": ("Votre espace professeur est ouvert — Maison du français", "Bonjour {name},\n\nL'équipe a validé votre compte professeur. Connectez-vous pour compléter votre fiche et envoyer votre vidéo :\n\n{login}")},
}


def send_mail(kind, to, lang, **kw):
    import mailer
    m = MAILS[kind].get(lang) or MAILS[kind].get("fr") or MAILS[kind]["zh"]
    return mailer.send(to, m[0], m[1].format(**kw) + mailer.SIGN)


# ---------- pages ----------

def _render(tpl, **kw):
    resp = web.app.make_response(render_template(tpl, **kw))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@web.route("/compte/")
def account_home():
    u = current()
    if not u:
        return redirect(url_for("account_login"))
    if u["role"] in STAFF or (u["role"] == "professeur" and u["teacher_id"]):
        return redirect(landing(u, g.lang))
    import placement
    tests = placement.tests_for_account(u["id"], g.lang) if u["role"] in ("parent", "eleve") else []
    return _render("compte/home.html", u=u, role_label=role_label(u["role"], g.lang), ok=request.args.get("ok"),
                   tests=tests, p=placement.pt(g.lang), rec_deleted=request.args.get("enregistrements"))


@web.route("/compte/inscription", methods=["GET", "POST"])
def account_signup():
    t = texts(g.lang)
    errors, form, done = [], {"role": request.args.get("role") if request.args.get("role") in SELF_ROLES else None}, False
    if request.method == "POST":
        check_csrf()
        f = request.form
        form = {"name": (f.get("name") or "").strip()[:80], "email": (f.get("email") or "").strip()[:200], "role": f.get("role")}
        if f.get("website"):  # champ piège
            return _render("compte/signup.html", done=True, form=form)
        p1, p2 = f.get("password", ""), f.get("password2", "")
        if form["role"] not in SELF_ROLES:
            errors.append(t.ac_err_role)
        if form["role"] == "eleve" and not f.get("over15"):
            errors.append(t.ac_err_over15)
        if len(form["name"]) < 2:
            errors.append(t.ac_err_name)
        if not web.EMAIL_RE.match(form["email"]):
            errors.append(t.err_email)
        if len(p1) < MIN_PASSWORD:
            errors.append(t.ac_err_pw_len)
        elif p1 != p2:
            errors.append(t.ac_err_pw_same)
        if not f.get("privacy"):
            errors.append(t.ac_err_privacy)
        if not errors:
            with connect() as c:
                limited, h = _limited(c, "signup", 5, "1 hour")
                if limited:
                    errors.append(t.ac_err_rate)
                else:
                    _fail(c, "signup", h)
                    u = c.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (form["email"],)).fetchone()
                    if not u:
                        u = c.execute("""INSERT INTO users (email, name, password_hash, role, lang, over15, privacy_at)
                                         VALUES (%s,%s,%s,%s,%s,%s, now()) RETURNING *""",
                                      (form["email"], form["name"], generate_password_hash(p1), form["role"], g.lang, form["role"] == "eleve")).fetchone()
                        kind = "verify"
                    elif not u["email_verified_at"] and u["role"] in SELF_ROLES:
                        c.execute("UPDATE users SET name=%s, password_hash=%s, role=%s, lang=%s, over15=%s, privacy_at=now() WHERE id=%s",
                                  (form["name"], generate_password_hash(p1), form["role"], g.lang, form["role"] == "eleve", u["id"]))
                        kind = "verify"
                    else:
                        kind = "exists"  # ne rien changer, ne rien révéler
                    tok = new_token(c, u["id"], "verify") if kind == "verify" else None
            if not errors:
                if kind == "verify":
                    send_mail("verify", form["email"], g.lang, name=form["name"], link=link("account_verify", g.lang, tok=tok))
                else:
                    send_mail("exists", form["email"], g.lang, login=link("account_login", g.lang), forgot=link("account_forgot", g.lang))
                done = True
    return _render("compte/signup.html", errors=errors, form=form, done=done)


@web.route("/compte/confirmer/<tok>")
def account_verify(tok):
    with connect() as c:
        u = _use_token(c, tok, ("verify",))
        if not u:
            return _render("compte/message.html", title=texts(g.lang).ac_invalid_title, text=texts(g.lang).ac_invalid_text), 410
        c.execute("UPDATE user_tokens SET used_at=now() WHERE token_hash=%s", (u["token_hash"],))
        c.execute("UPDATE users SET email_verified_at=COALESCE(email_verified_at, now()), last_login_at=now() WHERE id=%s", (u["id"],))
    login_user(u["id"])
    if u["role"] == "professeur":
        import mailer
        mailer.notify_team("Nouveau compte professeur à valider",
                           f"Un professeur vient de créer son compte. À valider (et à relier à une fiche) :\n{web.SITE_URL}/admin/utilisateurs?role=professeur" + mailer.SIGN)
    return redirect(url_for("account_home", ok="verified"))


@web.route("/compte/connexion", methods=["GET", "POST"])
def account_login():
    t = texts(g.lang)
    if current():
        return redirect(landing(current(), g.lang))
    error, email = None, ""
    if request.method == "POST":
        check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        with connect() as c:
            limited, h = _limited(c, "login", 5, "15 minutes")
            u = c.execute("SELECT * FROM users WHERE lower(email)=lower(%s) AND active AND password_hash IS NOT NULL", (email,)).fetchone()
            if limited:
                error = t.ac_err_too_many
            elif u and check_password_hash(u["password_hash"], request.form.get("password", "")):
                if not u["email_verified_at"]:
                    error = t.ac_err_unverified
                else:
                    c.execute("DELETE FROM admin_login_failures WHERE scope='login' AND ip_hash=%s", (h,))
                    c.execute("UPDATE users SET last_login_at=now() WHERE id=%s", (u["id"],))
                    login_user(u["id"])
                    nxt = request.args.get("next") or ""
                    if nxt.startswith("/admin") and u["role"] in STAFF or nxt.startswith("/espace") and u["role"] == "professeur":
                        return redirect(nxt)
                    return redirect(landing(u, g.lang))
            else:
                _fail(c, "login", h)
                error = t.ac_err_login
    return _render("compte/login.html", error=error, email=email), (401 if error else 200)


@web.route("/compte/deconnexion", methods=["POST"])
def account_logout():
    check_csrf()
    session.pop("user_id", None)
    return redirect(url_for("account_login"))


@web.route("/compte/mot-de-passe-oublie", methods=["GET", "POST"])
def account_forgot():
    sent = False
    if request.method == "POST":
        check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        with connect() as c:
            limited, h = _limited(c, "forgot", 5, "1 hour")
            _fail(c, "forgot", h)
            u = None if limited else c.execute("SELECT * FROM users WHERE lower(email)=lower(%s) AND active AND email_verified_at IS NOT NULL", (email,)).fetchone()
            tok = new_token(c, u["id"], "reset") if u else None
        if u:
            send_mail("reset", u["email"], u["lang"], name=u["name"], link=link("account_reset", u["lang"], tok=tok))
        sent = True  # même réponse que l'adresse existe ou non
    return _render("compte/forgot.html", sent=sent)


@web.route("/compte/nouveau-mot-de-passe/<tok>", methods=["GET", "POST"])
def account_reset(tok):
    """Sert aussi aux invitations des professeurs (choix du premier mot de passe, qui confirme l'e-mail)."""
    t = texts(g.lang)
    with connect() as c:
        u = _use_token(c, tok, ("reset", "invite"))
    if not u:
        return _render("compte/message.html", title=t.ac_invalid_title, text=t.ac_invalid_text), 410
    errors = []
    if request.method == "POST":
        check_csrf()
        p1, p2 = request.form.get("password", ""), request.form.get("password2", "")
        if len(p1) < MIN_PASSWORD:
            errors.append(t.ac_err_pw_len)
        elif p1 != p2:
            errors.append(t.ac_err_pw_same)
        if u["purpose"] == "invite" and not request.form.get("privacy"):
            errors.append(t.ac_err_privacy)
        if not errors:
            with connect() as c:
                c.execute("UPDATE user_tokens SET used_at=now() WHERE token_hash=%s", (u["token_hash"],))
                c.execute("""UPDATE users SET password_hash=%s, email_verified_at=COALESCE(email_verified_at, now()), last_login_at=now(),
                               privacy_at=CASE WHEN %s THEN now() ELSE privacy_at END WHERE id=%s""",
                          (generate_password_hash(p1), u["purpose"] == "invite", u["id"]))
                u = c.execute("SELECT * FROM users WHERE id=%s", (u["id"],)).fetchone()
            login_user(u["id"])
            return redirect(landing(u, g.lang))
    return _render("compte/reset.html", u=u, errors=errors, invite=u["purpose"] == "invite")


@web.route("/compte/mot-de-passe", methods=["GET", "POST"])
def account_password():
    t = texts(g.lang)
    u = current()
    if not u:
        return redirect(url_for("account_login"))
    errors, ok = [], False
    if request.method == "POST":
        check_csrf()
        p1, p2 = request.form.get("password", ""), request.form.get("password2", "")
        if not check_password_hash(u["password_hash"], request.form.get("current", "")):
            errors.append(t.ac_err_current)
        elif len(p1) < MIN_PASSWORD:
            errors.append(t.ac_err_pw_len)
        elif p1 != p2:
            errors.append(t.ac_err_pw_same)
        else:
            with connect() as c:
                c.execute("UPDATE users SET password_hash=%s WHERE id=%s", (generate_password_hash(p1), u["id"]))
            ok = True
    return _render("compte/password.html", errors=errors, ok=ok)


@web.route("/compte/supprimer", methods=["POST"])
def account_delete():
    """Suppression par la personne elle-même (RGPD). Un administrateur ne peut pas se supprimer s'il est le dernier."""
    check_csrf()
    u = current()
    if not u:
        return redirect(url_for("account_login"))
    with connect() as c:
        if u["role"] == "admin" and c.execute("SELECT count(*) AS n FROM users WHERE role='admin' AND active").fetchone()["n"] <= 1:
            abort(403)
        c.execute("DELETE FROM users WHERE id=%s", (u["id"],))  # la fiche professeur éventuelle reste, sans compte
    session.pop("user_id", None)
    if u["role"] == "professeur" and u["teacher_id"]:
        import mailer
        mailer.notify_team("Un professeur a supprimé son compte",
                           f"Un professeur a supprimé son compte. Sa fiche est toujours là : vérifiez s'il faut la dépublier (accord retiré ?).\n{web.SITE_URL}/admin/professeurs/{u['teacher_id']}" + mailer.SIGN)
    return _render("compte/message.html", title=texts(g.lang).ac_deleted, text="")
