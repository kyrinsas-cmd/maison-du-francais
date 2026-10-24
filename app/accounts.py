"""Espace professeur (/espace, en français) : réservé aux comptes de rôle « professeur » reliés à une fiche.

- Comptes et connexion : users.py (/compte). Un professeur s'inscrit lui-même (rôle « professeur ») puis l'équipe le
  valide en le reliant à une fiche ; ou l'équipe l'invite depuis la fiche (lien de 7 jours pour choisir son mot de passe).
- Ce que le professeur modifie (textes, photo, vidéo) est enregistré comme « proposition » (teachers.pending) :
  rien ne change sur le site avant la validation par l'équipe (cahier des charges §6–7).
"""
from flask import Blueprint, abort, redirect, render_template, request, url_for
from psycopg.types.json import Jsonb

import teachers as T
import users as U
import web
from admin import _check_csrf, bp as admin_bp
from db import connect

bp = Blueprint("espace", __name__, url_prefix="/espace")

# Champs que le professeur peut proposer de modifier
FIELDS = ("diplomas", "ages_min", "ages_max", "levels", "bio_zh", "bio_fr", "courses_zh", "courses_fr")
LABELS = {"diplomas": "Diplômes", "ages_min": "Âge minimum", "ages_max": "Âge maximum", "levels": "Niveaux",
          "bio_zh": "Présentation (chinois)", "bio_fr": "Présentation (français)",
          "courses_zh": "Cours (chinois)", "courses_fr": "Cours (français)"}


def current():
    u = U.current()
    return u if u and u["role"] == "professeur" and u["teacher_id"] else None


@bp.before_request
def guard():
    if request.endpoint == "espace.profile":
        request.max_content_length = T.UPLOAD_MAX
    if request.endpoint in ("espace.login", "espace.forgot"):
        return None
    if not current():
        return redirect(url_for("account_login", lang="fr", next=request.path if request.method == "GET" else None))
    return None


@bp.after_request
def no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@bp.app_context_processor
def espace_ctx():
    return {"espace_user": current}


@bp.route("/connexion")
def login():
    """Ancienne adresse : la connexion est commune à tous les comptes."""
    return redirect(url_for("account_login", lang="fr"))


@bp.route("/mot-de-passe-oublie")
def forgot():
    return redirect(url_for("account_forgot", lang="fr"))


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


@bp.route("/mot-de-passe")
def password():
    return redirect(url_for("account_password", lang="fr"))


# ---------- admin : compte et propositions ----------

def account_for(tid):
    with connect() as c:
        return c.execute("SELECT * FROM users WHERE teacher_id=%s", (tid,)).fetchone()


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
    """Relier un compte à la fiche (ou inviter le professeur), envoyer un lien, désactiver, délier."""
    _check_csrf()
    action = request.form.get("action")
    link, error, kind = None, None, None
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
        if not t:
            abort(404)
        acc = c.execute("SELECT * FROM users WHERE teacher_id=%s", (tid,)).fetchone()
        if action == "create" and not acc:
            email = (request.form.get("email") or "").strip()[:200]
            other = c.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (email,)).fetchone()
            if not web.EMAIL_RE.match(email):
                error = "Adresse e-mail invalide."
            elif other and (other["role"] != "professeur" or other["teacher_id"]):
                error = "Cette adresse appartient déjà à un autre compte (autre rôle ou autre fiche)."
            elif other:  # le professeur s'est inscrit lui-même : on relie son compte
                c.execute("UPDATE users SET teacher_id=%s WHERE id=%s", (tid, other["id"]))
                acc = c.execute("SELECT * FROM users WHERE id=%s", (other["id"],)).fetchone()
                if acc["email_verified_at"] and acc["password_hash"]:
                    U.send_mail("teacher_ok", acc["email"], "fr", name=acc["name"], login=U.link("account_login", "fr"))
                else:
                    kind = "invitation"
                    link = U.link("account_reset", "fr", tok=U.new_token(c, acc["id"], "invite"))
            else:
                acc = c.execute("INSERT INTO users (email, name, role, lang, teacher_id) VALUES (%s,%s,'professeur','fr',%s) RETURNING *",
                                (email, T.display_name(t), tid)).fetchone()
                kind = "invitation"
                link = U.link("account_reset", "fr", tok=U.new_token(c, acc["id"], "invite"))
        elif action == "link" and acc:
            kind = "réinitialisation" if acc["password_hash"] else "invitation"
            link = U.link("account_reset", "fr", tok=U.new_token(c, acc["id"], "reset" if acc["password_hash"] else "invite"))
        elif action in ("disable", "enable") and acc:
            c.execute("UPDATE users SET active=%s WHERE id=%s", (action == "enable", acc["id"]))
            if action == "disable":
                c.execute("UPDATE user_tokens SET used_at=now() WHERE user_id=%s AND used_at IS NULL", (acc["id"],))
        elif action == "unlink" and acc:
            c.execute("UPDATE users SET teacher_id=NULL WHERE id=%s", (acc["id"],))
        else:
            abort(400)
    if link:
        # Envoyé par e-mail ; aussi montré une fois (jamais dans l'adresse ni les journaux).
        template = "invite" if kind == "invitation" else "reset"
        mailed = U.send_mail(template, acc["email"], "fr", name=acc["name"], link=link)
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
