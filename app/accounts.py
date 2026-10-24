"""Espace professeur (/espace, en français) : comptes e-mail + mot de passe, créés sur invitation depuis l'admin.

- Inscription : l'équipe crée le compte depuis la fiche du professeur et lui envoie le lien d'invitation (7 jours).
  Le professeur choisit son mot de passe sur ce lien. Pas d'inscription libre.
- Mot de passe oublié : l'équipe génère un lien de réinitialisation (24 h). Pas encore d'envoi d'e-mail automatique.
- Ce que le professeur modifie (textes, photo, vidéo) est enregistré comme « proposition » (teachers.pending) :
  rien ne change sur le site avant la validation par l'équipe (cahier des charges §6–7).
- Les jetons ne sont jamais stockés en clair (sha256).
"""
import hashlib
import secrets

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for
from psycopg.types.json import Jsonb
from werkzeug.security import check_password_hash, generate_password_hash

import teachers as T
import web
from admin import _check_csrf, bp as admin_bp
from db import connect

bp = Blueprint("espace", __name__, url_prefix="/espace")

MIN_PASSWORD = 12
MAX_FAILURES, FAILURE_WINDOW = 5, "15 minutes"
INVITE_DAYS, RESET_HOURS = 7, 24
# Champs que le professeur peut proposer de modifier
FIELDS = ("diplomas", "ages_min", "ages_max", "levels", "bio_zh", "bio_fr", "courses_zh", "courses_fr")
LABELS = {"diplomas": "Diplômes", "ages_min": "Âge minimum", "ages_max": "Âge maximum", "levels": "Niveaux",
          "bio_zh": "Présentation (chinois)", "bio_fr": "Présentation (français)",
          "courses_zh": "Cours (chinois)", "courses_fr": "Cours (français)"}


# ---------- jetons ----------

def _h(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def new_token(c, account_id, purpose):
    tok = secrets.token_urlsafe(32)
    span = f"{INVITE_DAYS} days" if purpose == "invite" else f"{RESET_HOURS} hours"
    c.execute("UPDATE account_tokens SET used_at=now() WHERE account_id=%s AND used_at IS NULL", (account_id,))  # un seul lien valide à la fois
    c.execute(f"INSERT INTO account_tokens (token_hash, account_id, purpose, expires_at) VALUES (%s,%s,%s, now() + interval '{span}')",
              (_h(tok), account_id, purpose))
    return tok


def _token_account(c, tok):
    return c.execute("""SELECT a.*, k.purpose, k.token_hash FROM account_tokens k JOIN teacher_accounts a ON a.id=k.account_id
                        WHERE k.token_hash=%s AND k.used_at IS NULL AND k.expires_at > now() AND a.active""", (_h(tok),)).fetchone()


# ---------- e-mails ----------

def email_link(acc_email, first_name, link, purpose):
    import mailer
    if purpose == "invite":
        subject = "Votre espace professeur — Maison du français"
        body = (f"Bonjour {first_name},\n\nL'équipe de Maison du français a créé votre espace professeur. "
                f"Choisissez votre mot de passe avec ce lien, valable {INVITE_DAYS} jours :\n\n{link}\n\n"
                "Vous pourrez ensuite compléter votre profil et envoyer votre vidéo de présentation.")
    else:
        subject = "Nouveau mot de passe — Maison du français"
        body = (f"Bonjour {first_name},\n\nVoici le lien pour choisir un nouveau mot de passe, valable {RESET_HOURS} heures :\n\n{link}\n\n"
                "Si vous n'avez rien demandé, ignorez ce message : votre mot de passe actuel reste valable.")
    return mailer.send(acc_email, subject, body + mailer.SIGN)


# ---------- session ----------

def current():
    if "espace_acc" not in g:
        g.espace_acc = None
        aid = session.get("teacher_acc")
        if aid:
            with connect() as c:
                g.espace_acc = c.execute("""SELECT a.*, t.first_name FROM teacher_accounts a JOIN teachers t ON t.id=a.teacher_id
                                            WHERE a.id=%s AND a.active AND a.password_hash IS NOT NULL""", (aid,)).fetchone()
            if not g.espace_acc:
                session.pop("teacher_acc", None)
    return g.espace_acc


@bp.before_request
def guard():
    if request.endpoint == "espace.profile":
        request.max_content_length = T.UPLOAD_MAX
    if request.endpoint in ("espace.login", "espace.activate", "espace.forgot"):
        return None
    if not current():
        return redirect(url_for("espace.login"))
    return None


@bp.after_request
def no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@bp.app_context_processor
def espace_ctx():
    return {"espace_user": current}


def _login(account_id):
    session.pop("admin", None)
    session["teacher_acc"] = account_id
    session["csrf"] = secrets.token_urlsafe(24)
    session.permanent = True


@bp.route("/connexion", methods=["GET", "POST"])
def login():
    if current():
        return redirect(url_for("espace.home"))
    error = None
    email = ""
    if request.method == "POST":
        _check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        h = web.ip_hash()
        with connect() as c:
            n = c.execute(f"SELECT count(*) AS n FROM admin_login_failures WHERE scope='espace' AND ip_hash=%s AND at > now() - interval '{FAILURE_WINDOW}'", (h,)).fetchone()["n"]
            acc = c.execute("SELECT * FROM teacher_accounts WHERE lower(email)=lower(%s) AND active AND password_hash IS NOT NULL", (email,)).fetchone()
            if n >= MAX_FAILURES:
                error = "Trop de tentatives. Réessayez dans 15 minutes."
            elif acc and check_password_hash(acc["password_hash"], request.form.get("password", "")):
                c.execute("DELETE FROM admin_login_failures WHERE scope='espace' AND ip_hash=%s", (h,))
                c.execute("UPDATE teacher_accounts SET last_login_at=now() WHERE id=%s", (acc["id"],))
                _login(acc["id"])
                return redirect(url_for("espace.home"))
            else:
                c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'espace')", (h,))
                error = "E-mail ou mot de passe incorrect."
    return render_template("espace/login.html", error=error, email=email), (401 if error else 200)


@bp.route("/deconnexion", methods=["POST"])
def logout():
    _check_csrf()
    session.pop("teacher_acc", None)
    return redirect(url_for("espace.login"))


@bp.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def forgot():
    import mailer
    sent = False
    if request.method == "POST" and mailer.configured():
        _check_csrf()
        email = (request.form.get("email") or "").strip()[:200]
        h = web.ip_hash()
        with connect() as c:
            n = c.execute("SELECT count(*) AS n FROM admin_login_failures WHERE scope='forgot' AND ip_hash=%s AND at > now() - interval '1 hour'", (h,)).fetchone()["n"]
            c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'forgot')", (h,))  # chaque demande compte : 5 par heure
            acc = None
            if n < 5:
                acc = c.execute("""SELECT a.*, t.first_name FROM teacher_accounts a JOIN teachers t ON t.id=a.teacher_id
                                   WHERE lower(a.email)=lower(%s) AND a.active AND a.password_hash IS NOT NULL""", (email,)).fetchone()
            if acc:
                link = url_for("espace.activate", tok=new_token(c, acc["id"], "reset"), _external=True)
        if acc:
            email_link(acc["email"], acc["first_name"], link, "reset")
        sent = True  # même réponse que l'adresse existe ou non
    return render_template("espace/forgot.html", self_service=mailer.configured(), sent=sent)


@bp.route("/activer/<tok>", methods=["GET", "POST"])
def activate(tok):
    with connect() as c:
        acc = _token_account(c, tok)
    if not acc:
        return render_template("espace/activate.html", invalid=True), 410
    errors = []
    if request.method == "POST":
        _check_csrf()
        p1, p2 = request.form.get("password", ""), request.form.get("password2", "")
        if len(p1) < MIN_PASSWORD:
            errors.append(f"Le mot de passe doit faire au moins {MIN_PASSWORD} caractères.")
        elif p1 != p2:
            errors.append("Les deux mots de passe sont différents.")
        if acc["purpose"] == "invite" and not request.form.get("privacy"):
            errors.append("Merci de confirmer que vous avez lu la politique de confidentialité.")
        if not errors:
            with connect() as c:
                c.execute("UPDATE account_tokens SET used_at=now() WHERE token_hash=%s", (acc["token_hash"],))
                c.execute("UPDATE teacher_accounts SET password_hash=%s, activated_at=COALESCE(activated_at, now()), last_login_at=now() WHERE id=%s",
                          (generate_password_hash(p1), acc["id"]))
            _login(acc["id"])
            return redirect(url_for("espace.home", bienvenue=1))
    return render_template("espace/activate.html", acc=acc, errors=errors)


# ---------- espace ----------

def _teacher(c):
    return c.execute("SELECT * FROM teachers WHERE id=%s", (current()["teacher_id"],)).fetchone()


def video_state(t):
    pend = t["pending"] or {}
    if pend.get("video_file"):
        return "Nouvelle vidéo en attente de validation par l'équipe"
    return {"approved": "Validée", "changes": "À modifier", "pending": "En attente de validation par l'équipe"}.get(t["video_status"], "Aucune vidéo")


@bp.route("/")
def home():
    with connect() as c:
        t = _teacher(c)
    import reviews
    with connect() as c:
        rsum = reviews.summary(c, t["id"])
    return render_template("espace/home.html", t=t, video_state=video_state(t), problems=T.publish_problems(t), rsum=rsum,
                           welcome=request.args.get("bienvenue"), sent=request.args.get("envoye"))


@bp.route("/profil", methods=["GET", "POST"])
def profile():
    with connect() as c:
        t = _teacher(c)
    pend = dict(t["pending"] or {})
    cur = {k: t[k] for k in FIELDS}
    cur.update(pend.get("fields", {}))  # le formulaire montre la dernière proposition
    errors = []
    if request.method == "POST":
        _check_csrf()
        f = request.form

        def num(k):
            v = (f.get(k) or "").strip()
            return int(v) if v.isdigit() and 0 < int(v) < 100 else None
        new = {
            "diplomas": (f.get("diplomas") or "").strip()[:300] or None,
            "ages_min": num("ages_min"), "ages_max": num("ages_max"),
            "levels": [lv for lv in T.LEVELS if f.get(f"level_{lv}")],
            "bio_zh": (f.get("bio_zh") or "").strip()[:4000] or None,
            "bio_fr": (f.get("bio_fr") or "").strip()[:4000] or None,
            "courses_zh": (f.get("courses_zh") or "").strip()[:2000] or None,
            "courses_fr": (f.get("courses_fr") or "").strip()[:2000] or None,
        }
        changed = {k: v for k, v in new.items() if v != t[k]}
        old_files = []
        try:
            ph, vd = request.files.get("photo"), request.files.get("video")
            if ph and ph.filename:
                old_files.append(pend.get("photo_file"))
                pend["photo_file"] = T._save_photo(t["id"], ph)
            if vd and vd.filename:
                old_files.append(pend.get("video_file"))
                pend["video_file"] = T._save_video(t["id"], vd)
        except ValueError as e:
            errors.append(str(e))
        pend["fields"] = changed
        has_change = bool(changed or pend.get("photo_file") or pend.get("video_file"))
        with connect() as c:
            c.execute("UPDATE teachers SET pending=%s, pending_at=CASE WHEN %s THEN now() END, pending_feedback=NULL, updated_at=now() WHERE id=%s",
                      (Jsonb(pend) if has_change else None, has_change, t["id"]))
        for name in old_files:
            T._remove(name)
        if has_change:
            import mailer
            mailer.notify_team(f"Modifications proposées par {T.display_name(t)}",
                               f"Le professeur {T.display_name(t)} a envoyé des modifications de sa fiche, à valider :\n{web.SITE_URL}/admin/professeurs/{t['id']}" + mailer.SIGN)
        if not errors:
            return redirect(url_for("espace.home", envoye=1 if has_change else None))
        cur.update(new)
    return render_template("espace/profile.html", t=t, cur=cur, pend=pend, levels=T.LEVELS, errors=errors)


@bp.route("/mot-de-passe", methods=["GET", "POST"])
def password():
    errors, ok = [], False
    if request.method == "POST":
        _check_csrf()
        acc = current()
        p1, p2 = request.form.get("password", ""), request.form.get("password2", "")
        if not check_password_hash(acc["password_hash"], request.form.get("current", "")):
            errors.append("Mot de passe actuel incorrect.")
        elif len(p1) < MIN_PASSWORD:
            errors.append(f"Le nouveau mot de passe doit faire au moins {MIN_PASSWORD} caractères.")
        elif p1 != p2:
            errors.append("Les deux mots de passe sont différents.")
        else:
            with connect() as c:
                c.execute("UPDATE teacher_accounts SET password_hash=%s WHERE id=%s", (generate_password_hash(p1), acc["id"]))
            ok = True
    return render_template("espace/password.html", errors=errors, ok=ok)


# ---------- admin : compte et propositions ----------

def account_for(tid):
    with connect() as c:
        return c.execute("SELECT * FROM teacher_accounts WHERE teacher_id=%s", (tid,)).fetchone()


def pending_view(t):
    """Liste lisible des changements proposés, pour la fiche admin."""
    p = t["pending"] or {}
    rows = []
    for k, v in (p.get("fields") or {}).items():
        fmt = lambda x: " · ".join(x) if isinstance(x, list) else (x if x not in (None, "") else "—")
        rows.append({"label": LABELS.get(k, k), "old": fmt(t[k]), "new": fmt(v)})
    return {"rows": rows, "photo": p.get("photo_file"), "video": p.get("video_file"), "at": t["pending_at"]}


def default_email(t):
    if t["application_id"]:
        with connect() as c:
            a = c.execute("SELECT email FROM teacher_applications WHERE id=%s", (t["application_id"],)).fetchone()
        return a["email"] if a else ""
    return ""


@admin_bp.route("/professeurs/<int:tid>/compte", methods=["POST"])
def teacher_account(tid):
    _check_csrf()
    action = request.form.get("action")
    link, error = None, None
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
        if not t:
            abort(404)
        acc = c.execute("SELECT * FROM teacher_accounts WHERE teacher_id=%s", (tid,)).fetchone()
        if action == "create" and not acc:
            email = (request.form.get("email") or "").strip()[:200]
            if not web.EMAIL_RE.match(email):
                error = "Adresse e-mail invalide."
            elif c.execute("SELECT 1 FROM teacher_accounts WHERE lower(email)=lower(%s)", (email,)).fetchone():
                error = "Cette adresse est déjà utilisée par un autre compte."
            else:
                acc = c.execute("INSERT INTO teacher_accounts (teacher_id, email) VALUES (%s,%s) RETURNING *", (tid, email)).fetchone()
                link = url_for("espace.activate", tok=new_token(c, acc["id"], "invite"), _external=True)
        elif action == "link" and acc:
            purpose = "reset" if acc["password_hash"] else "invite"
            link = url_for("espace.activate", tok=new_token(c, acc["id"], purpose), _external=True)
        elif action in ("disable", "enable") and acc:
            c.execute("UPDATE teacher_accounts SET active=%s WHERE id=%s", (action == "enable", acc["id"]))
            if action == "disable":
                c.execute("UPDATE account_tokens SET used_at=now() WHERE account_id=%s AND used_at IS NULL", (acc["id"],))
        elif action == "delete" and acc:
            c.execute("DELETE FROM teacher_accounts WHERE id=%s", (acc["id"],))
        else:
            abort(400)
    if link:
        # Le lien est envoyé par e-mail si l'envoi est configuré ; il est aussi montré une fois (jamais dans l'adresse ni les journaux).
        kind = "réinitialisation" if acc and acc["password_hash"] else "invitation"
        mailed = email_link(acc["email"], t["first_name"], link, "reset" if kind == "réinitialisation" else "invite")
        return T.render_teacher_admin(tid, link=link, link_kind=kind, link_mailed=acc["email"] if mailed else None)
    return T.render_teacher_admin(tid, errors=[error] if error else None, msg=None if error else "Compte mis à jour.")


@admin_bp.route("/professeurs/<int:tid>/proposition", methods=["POST"])
def teacher_pending(tid):
    _check_csrf()
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
        if not t or not t["pending"]:
            return redirect(url_for("admin.teacher", tid=tid))
        p = t["pending"]
        if request.form.get("action") == "apply":
            vals = {k: t[k] for k in FIELDS}
            vals.update({k: v for k, v in (p.get("fields") or {}).items() if k in FIELDS})
            photo, video, status = t["photo_file"], t["video_file"], t["video_status"]
            old = []
            if p.get("photo_file"):
                old.append(photo); photo = p["photo_file"]
            if p.get("video_file"):
                old.append(video); video, status = p["video_file"], "approved"
            c.execute("""UPDATE teachers SET diplomas=%(diplomas)s, ages_min=%(ages_min)s, ages_max=%(ages_max)s, levels=%(levels)s,
                           bio_zh=%(bio_zh)s, bio_fr=%(bio_fr)s, courses_zh=%(courses_zh)s, courses_fr=%(courses_fr)s,
                           photo_file=%(photo)s, video_file=%(video)s, video_status=%(status)s, video_feedback=NULL,
                           pending=NULL, pending_at=NULL, pending_feedback=NULL, updated_at=now() WHERE id=%(id)s""",
                      dict(vals, photo=photo, video=video, status=status, id=tid))
            msg = "Modifications appliquées."
        elif request.form.get("action") == "reject":
            old = [p.get("photo_file"), p.get("video_file")]
            fb = (request.form.get("feedback") or "").strip()[:2000] or "Modifications refusées par l'équipe."
            # Un refus ne touche jamais à ce qui est publié (ni à la vidéo déjà validée) : seul le message change.
            c.execute("UPDATE teachers SET pending=NULL, pending_at=NULL, pending_feedback=%s, updated_at=now() WHERE id=%s", (fb, tid))
            msg = "Modifications refusées ; le professeur voit votre message."
        else:
            abort(400)
    for name in old:
        T._remove(name)
    acc = account_for(tid)
    if acc and acc["active"]:
        import mailer
        if request.form.get("action") == "apply":
            mailer.send(acc["email"], "Vos modifications sont en ligne — Maison du français",
                        f"Bonjour {t['first_name']},\n\nL'équipe a validé vos modifications : elles sont maintenant visibles sur votre fiche." + mailer.SIGN)
        else:
            mailer.send(acc["email"], "Vos modifications n'ont pas été validées — Maison du français",
                        f"Bonjour {t['first_name']},\n\nL'équipe n'a pas validé vos dernières modifications. Son message :\n\n{fb}\n\n"
                        f"Vous pouvez les corriger depuis votre espace : {web.SITE_URL}/espace/profil" + mailer.SIGN)
    return T.render_teacher_admin(tid, msg=msg)


def init_app(app):
    app.register_blueprint(bp)
