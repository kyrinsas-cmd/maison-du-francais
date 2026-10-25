"""Admin (/admin, en français, hors du système de langues).

Accès : comptes de rôle « admin » ou « moderateur » (users.py), relus à chaque requête.
Modérateur : tout sauf ADMIN_ONLY (tarifs, utilisateurs) et la suppression des fiches professeurs.
Rôles donnés dans /admin/utilisateurs, ou en ligne de commande : sudo ./ops/make-admin.sh <e-mail>.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from db import connect

bp = Blueprint("admin", __name__, url_prefix="/admin")
PARIS = ZoneInfo("Europe/Paris")
ADMIN_ONLY = {"admin.pricing_admin", "admin.users_admin"}


@bp.app_context_processor
def admin_ctx():
    return {"paris": PARIS}

STATUSES = {"new": "Nouvelle", "contacted": "Contactée", "accepted": "Retenue", "rejected": "Refusée"}
SESSION_HOURS = 12
PAGE = 50


def _check_csrf():
    if not session.get("csrf") or request.form.get("csrf") != session.get("csrf"):
        abort(400)


def require_admin():
    import users
    if not users.is_admin():
        abort(403)


@bp.before_request
def guard():
    import users
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    u = users.current()
    if not u:
        return redirect(url_for("account_login", lang="fr", next=request.full_path if request.method == "GET" else None))
    if u["role"] not in users.STAFF:
        return redirect(users.landing(u, "fr"))
    if request.endpoint in ADMIN_ONLY and u["role"] != "admin":
        abort(403)
    return None


@bp.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@bp.route("/login")
def login():
    """Ancienne adresse de connexion : la connexion est commune à tous les comptes."""
    return redirect(url_for("account_login", lang="fr", next=request.args.get("next")))


@bp.route("/logout", methods=["POST"])
def logout():
    return redirect(url_for("account_logout", lang="fr"), code=307)


# ---------- utilisateurs (admin seulement) ----------

@bp.route("/utilisateurs", methods=["GET", "POST"])
def users_admin():
    import teachers as T
    import users as U
    me = U.current()
    msg = error = None
    if request.method == "POST":
        _check_csrf()
        uid = request.form.get("user_id", type=int)
        action = request.form.get("action")
        with connect() as c:
            u = c.execute("SELECT * FROM users WHERE id=%s", (uid,)).fetchone()
            if not u:
                abort(404)
            admins = c.execute("SELECT count(*) AS n FROM users WHERE role='admin' AND active").fetchone()["n"]
            new_role = request.form.get("role")
            losing_admin = u["role"] == "admin" and (action in ("disable", "delete") or (action == "role" and new_role != "admin"))
            if u["id"] == me["id"] and action in ("role", "disable", "delete"):
                error = "Vous ne pouvez pas modifier votre propre compte ici (demandez à un autre administrateur)."
            elif losing_admin and admins <= 1:
                error = "Impossible : ce serait le dernier administrateur."
            elif action == "role":
                if new_role not in U.ROLES:
                    abort(400)
                if new_role in U.STAFF and not u["email_verified_at"]:
                    error = "Ce compte n'a pas encore confirmé son adresse e-mail."
                else:
                    c.execute("UPDATE users SET role=%s, teacher_id=CASE WHEN %s='professeur' THEN teacher_id END WHERE id=%s", (new_role, new_role, uid))
                    msg = f"{u['name']} : rôle « {U.role_label(new_role, 'fr')} »."
            elif action == "validate_teacher" and u["role"] == "professeur" and not u["teacher_id"]:
                if not u["email_verified_at"]:
                    error = "Ce professeur n'a pas encore confirmé son adresse e-mail."
                else:
                    first = u["name"].split()[0][:60]
                    last = u["name"].split()[-1][:1].upper() if len(u["name"].split()) > 1 else None
                    tid = c.execute("INSERT INTO teachers (first_name, last_initial, slug) VALUES (%s,%s,%s) RETURNING id",
                                    (first, last, "tmp-" + str(uid))).fetchone()["id"]
                    c.execute("UPDATE teachers SET slug=%s WHERE id=%s", (f"{T._slugify(first)}-{tid}", tid))
                    c.execute("UPDATE users SET teacher_id=%s WHERE id=%s", (tid, uid))
                    U.send_mail("teacher_ok", u["email"], "fr", name=u["name"], login=U.link("account_login", "fr"))
                    return redirect(url_for("admin.teacher", tid=tid, ok=1))
            elif action in ("disable", "enable"):
                c.execute("UPDATE users SET active=%s WHERE id=%s", (action == "enable", uid)); msg = "Compte mis à jour."
            elif action == "delete":
                import placement
                placement.delete_user_recordings(uid)  # fichiers audio des tests de niveau
                c.execute("DELETE FROM users WHERE id=%s", (uid,)); msg = "Compte supprimé."
            else:
                abort(400)
    role = request.args.get("role")
    with connect() as c:
        counts = {r["role"]: r["n"] for r in c.execute("SELECT role, count(*) AS n FROM users GROUP BY role").fetchall()}
        pending = c.execute("SELECT count(*) AS n FROM users WHERE role='professeur' AND teacher_id IS NULL AND email_verified_at IS NOT NULL").fetchone()["n"]
        rows = c.execute("""SELECT u.*, t.first_name AS t_first, t.last_initial AS t_last FROM users u LEFT JOIN teachers t ON t.id=u.teacher_id
                            """ + ("WHERE u.role=%s " if role in U.ROLES else "") +
                         "ORDER BY (u.role='professeur' AND u.teacher_id IS NULL) DESC, u.created_at DESC LIMIT 500",
                         (role,) if role in U.ROLES else ()).fetchall()
    return render_template("admin/users.html", rows=rows, me=me, msg=msg, error=error, counts=counts, role=role,
                           roles=U.ROLES, role_label=lambda r: U.role_label(r, "fr"), pending=pending)


@bp.route("/")
def index():
    return redirect(url_for("admin.applications"))


@bp.route("/candidatures")
def applications():
    status = request.args.get("statut")
    if status not in STATUSES:
        status = None
    q = (request.args.get("q") or "").strip()[:100]
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    where, args = [], []
    if status:
        where.append("status=%s")
        args.append(status)
    if q:
        where.append("(full_name ILIKE %s OR email ILIKE %s OR diploma ILIKE %s)")
        args += [f"%{q}%"] * 3
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    with connect() as c:
        counts = {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) AS n FROM teacher_applications GROUP BY status").fetchall()}
        total = c.execute(f"SELECT count(*) AS n FROM teacher_applications {sql_where}", args).fetchone()["n"]
        rows = c.execute(f"""SELECT id, created_at, full_name, email, diploma, status, note IS NOT NULL AND note <> '' AS has_note
                             FROM teacher_applications {sql_where} ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                         args + [PAGE, (page - 1) * PAGE]).fetchall()
    return render_template("admin/applications.html", rows=rows, counts=counts, total=total, status=status, q=q,
                           page=page, pages=max(1, -(-total // PAGE)), statuses=STATUSES)


@bp.route("/candidatures/<int:aid>", methods=["GET", "POST"])
def application(aid):
    with connect() as c:
        if request.method == "POST":
            _check_csrf()
            action = request.form.get("action")
            if action == "delete":
                c.execute("DELETE FROM teacher_applications WHERE id=%s", (aid,))
                return redirect(url_for("admin.applications", supprime=1))
            new_status = request.form.get("status")
            if new_status not in STATUSES:
                abort(400)
            note = (request.form.get("note") or "").strip()[:5000] or None
            c.execute("UPDATE teacher_applications SET status=%s, note=%s, updated_at=now() WHERE id=%s", (new_status, note, aid))
            return redirect(url_for("admin.application", aid=aid, ok=1))
        row = c.execute("SELECT * FROM teacher_applications WHERE id=%s", (aid,)).fetchone()
    if not row:
        abort(404)
    return render_template("admin/application.html", a=row, statuses=STATUSES, saved=request.args.get("ok"))


def init_app(app):
    app.permanent_session_lifetime = timedelta(hours=SESSION_HOURS)
    app.register_blueprint(bp)
