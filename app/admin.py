"""Admin (/admin, en français, hors du système de langues).

Accès réservé aux comptes de l'équipe qui ont le rôle « admin » (staff.py, /compte). Le rôle est relu à chaque requête.
Le rôle se donne depuis la page Équipe (/admin/equipe) ou en ligne de commande : sudo ./ops/make-admin.sh <e-mail>.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from db import connect

bp = Blueprint("admin", __name__, url_prefix="/admin")
PARIS = ZoneInfo("Europe/Paris")


@bp.app_context_processor
def admin_ctx():
    return {"paris": PARIS}

STATUSES = {"new": "Nouvelle", "contacted": "Contactée", "accepted": "Retenue", "rejected": "Refusée"}
SESSION_HOURS = 12
PAGE = 50


def _check_csrf():
    if not session.get("csrf") or request.form.get("csrf") != session.get("csrf"):
        abort(400)


def _logged_in():
    import staff
    return staff.is_admin()


@bp.before_request
def guard():
    import staff
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    if not staff.current():
        return redirect(url_for("compte.login", next=request.full_path if request.method == "GET" else None))
    if not staff.is_admin():
        return redirect(url_for("compte.home"))  # connecté mais sans rôle : page « en attente »
    return None


@bp.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@bp.route("/login")
def login():
    """Ancienne adresse de connexion : redirige vers la connexion de l'équipe."""
    return redirect(url_for("compte.login", next=request.args.get("next")))


@bp.route("/logout", methods=["POST"])
def logout():
    return redirect(url_for("compte.logout"), code=307)


# ---------- équipe ----------

@bp.route("/equipe", methods=["GET", "POST"])
def team():
    import staff
    me = staff.current()
    msg = error = None
    if request.method == "POST":
        _check_csrf()
        uid = request.form.get("user_id", type=int)
        action = request.form.get("action")
        with connect() as c:
            u = c.execute("SELECT * FROM staff_users WHERE id=%s", (uid,)).fetchone()
            admins = c.execute("SELECT count(*) AS n FROM staff_users WHERE role='admin' AND active").fetchone()["n"]
            if not u:
                abort(404)
            if u["id"] == me["id"] and action in ("revoke", "disable", "delete"):
                error = "Vous ne pouvez pas retirer votre propre accès (demandez à un autre administrateur)."
            elif action in ("revoke", "disable", "delete") and u["role"] == "admin" and admins <= 1:
                error = "Impossible : ce serait le dernier administrateur."
            elif action == "grant":
                if not u["email_verified_at"]:
                    error = "Ce compte n'a pas encore confirmé son adresse e-mail."
                else:
                    c.execute("UPDATE staff_users SET role='admin' WHERE id=%s", (uid,)); msg = f"{u['name']} est maintenant administrateur."
            elif action == "revoke":
                c.execute("UPDATE staff_users SET role='none' WHERE id=%s", (uid,)); msg = f"Rôle administrateur retiré à {u['name']}."
            elif action in ("disable", "enable"):
                c.execute("UPDATE staff_users SET active=%s WHERE id=%s", (action == "enable", uid)); msg = "Compte mis à jour."
            elif action == "delete":
                c.execute("DELETE FROM staff_users WHERE id=%s", (uid,)); msg = "Compte supprimé."
            else:
                abort(400)
    with connect() as c:
        users = c.execute("SELECT * FROM staff_users ORDER BY role='admin' DESC, created_at").fetchall()
    return render_template("admin/team.html", users=users, me=me, msg=msg, error=error)


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
