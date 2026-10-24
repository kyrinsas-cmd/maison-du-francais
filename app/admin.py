"""Admin des candidatures de professeurs : /admin (en français uniquement, hors du système de langues).

Connexion par un mot de passe unique dont seule l'empreinte est dans le .env (ADMIN_PASSWORD_HASH),
définie par l'utilisateur avec ops/set-admin-password.sh. Sans empreinte, l'admin est fermé.
"""
import os
import secrets
from datetime import timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import connect

bp = Blueprint("admin", __name__, url_prefix="/admin")
PARIS = ZoneInfo("Europe/Paris")


@bp.app_context_processor
def admin_ctx():
    return {"paris": PARIS}

STATUSES = {"new": "Nouvelle", "contacted": "Contactée", "accepted": "Retenue", "rejected": "Refusée"}
MAX_FAILURES = 5          # échecs de connexion tolérés…
FAILURE_WINDOW = "15 minutes"  # …par empreinte IP sur cette durée
SESSION_HOURS = 12
PAGE = 50


def _ip_hash():
    from web import ip_hash
    return ip_hash()


def _check_csrf():
    if not session.get("csrf") or request.form.get("csrf") != session.get("csrf"):
        abort(400)


def _logged_in():
    return session.get("admin") is True


@bp.before_request
def guard():
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    if not _logged_in():
        return redirect(url_for("admin.login", next=request.full_path if request.method == "GET" else None))
    return None


@bp.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@bp.route("/login", methods=["GET", "POST"])
def login():
    pw_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if not pw_hash:
        return render_template("admin/login.html", closed=True)
    error = None
    if request.method == "POST":
        _check_csrf()
        h = _ip_hash()
        with connect() as c:
            n = c.execute(f"SELECT count(*) AS n FROM admin_login_failures WHERE ip_hash=%s AND at > now() - interval '{FAILURE_WINDOW}'", (h,)).fetchone()["n"]
            if n >= MAX_FAILURES:
                error = "Trop de tentatives. Réessayez dans 15 minutes."
            elif check_password_hash(pw_hash, request.form.get("password", "")):
                c.execute("DELETE FROM admin_login_failures WHERE ip_hash=%s", (h,))
                session.clear()
                session["admin"] = True
                session["csrf"] = secrets.token_urlsafe(24)
                session.permanent = True
                nxt = request.args.get("next") or ""
                return redirect(nxt if nxt.startswith("/admin") else url_for("admin.applications"))
            else:
                c.execute("INSERT INTO admin_login_failures (ip_hash) VALUES (%s)", (h,))
                c.execute("DELETE FROM admin_login_failures WHERE at < now() - interval '1 day'")
                error = "Mot de passe incorrect."
    return render_template("admin/login.html", error=error), (401 if error else 200)


@bp.route("/logout", methods=["POST"])
def logout():
    _check_csrf()
    session.clear()
    return redirect(url_for("admin.login"))


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
