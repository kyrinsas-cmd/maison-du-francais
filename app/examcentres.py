"""Centres d'examen DELF-DALF en Chine et sessions : page /centres-examen (zh) et /fr/centres-examen (sous-menu 课程体系),
gestion dans /admin/centres. Source : NEEA 教育部教育考试院 (examcentres_seed.py). En Chine, l'inscription se fait uniquement
sur le site de la NEEA (delf-dalf.neea.edu.cn), pas auprès du centre.
"""
from datetime import date

from flask import abort, g, redirect, render_template, request, url_for

import web
from admin import _check_csrf, bp
from db import connect

NEEA = "https://delf-dalf.neea.edu.cn"
NEEA_CENTRES = "https://www.neea.edu.cn/html1/folder/16103/1132-1.htm"
CHECKED = date(2026, 10, 25)


@web.route("/centres-examen")
def exam_centres():
    with connect() as c:
        centres = c.execute("SELECT * FROM exam_centres WHERE published ORDER BY sort, id").fetchall()
        sessions = c.execute("SELECT * FROM exam_sessions WHERE published ORDER BY first_day DESC NULLS LAST, id DESC").fetchall()
    today = date.today()
    return render_template("centres.html", centres=centres, sessions=[dict(s, past=bool(s["first_day"] and s["first_day"] < today)) for s in sessions],
                           neea=NEEA, neea_centres=NEEA_CENTRES, checked=CHECKED)


# ---------- admin ----------

CENTRE_FIELDS = ("city_zh", "city_fr", "name_zh", "name_fr", "address", "phone", "website")
SESSION_FIELDS = ("title_zh", "title_fr", "levels", "exams_zh", "exams_fr", "register_zh", "register_fr", "source_url")


@bp.route("/centres")
def centres_admin():
    with connect() as c:
        centres = c.execute("SELECT * FROM exam_centres ORDER BY sort, id").fetchall()
        sessions = c.execute("SELECT * FROM exam_sessions ORDER BY first_day DESC NULLS LAST, id DESC").fetchall()
    return render_template("admin/centres.html", centres=centres, sessions=sessions, msg=request.args.get("ok") and "Enregistré.")


def _edit(table, fields, rid, required):
    row = None
    if rid:
        with connect() as c:
            row = c.execute(f"SELECT * FROM {table} WHERE id=%s", (rid,)).fetchone()
        if not row:
            abort(404)
    errors, v = [], dict(row) if row else {"published": True}
    if request.method == "POST":
        _check_csrf()
        f = request.form
        if row and f.get("action") == "delete":
            with connect() as c:
                c.execute(f"DELETE FROM {table} WHERE id=%s", (rid,))
            return redirect(url_for("admin.centres_admin", ok=1))
        v = {k: (f.get(k) or "").strip()[:500] or None for k in fields}
        v["published"] = bool(f.get("published"))
        if table == "exam_sessions":
            try:
                v["first_day"] = date.fromisoformat(f["first_day"]) if f.get("first_day") else None
            except ValueError:
                errors.append("Date invalide."); v["first_day"] = None
        else:
            v["sort"] = int(f["sort"]) if (f.get("sort") or "").lstrip("-").isdigit() else 0
        for k in required:
            if not v.get(k):
                errors.append(f"Champ obligatoire : {k}.")
        if not errors:
            cols = list(v)
            with connect() as c:
                if row:
                    c.execute(f"UPDATE {table} SET " + ", ".join(f"{k}=%({k})s" for k in cols) + " WHERE id=%(id)s", dict(v, id=rid))
                else:
                    c.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('%(' + k + ')s' for k in cols)})", v)
            return redirect(url_for("admin.centres_admin", ok=1))
    return render_template("admin/centre_edit.html", table=table, row=row, v=v, errors=errors, fields=fields)


@bp.route("/centres/centre/<int:rid>", methods=["GET", "POST"])
@bp.route("/centres/centre/nouveau", methods=["GET", "POST"], defaults={"rid": None})
def centre_edit(rid):
    return _edit("exam_centres", CENTRE_FIELDS, rid, ("city_zh", "name_zh"))


@bp.route("/centres/session/<int:rid>", methods=["GET", "POST"])
@bp.route("/centres/session/nouvelle", methods=["GET", "POST"], defaults={"rid": None})
def session_edit(rid):
    return _edit("exam_sessions", SESSION_FIELDS, rid, ("title_zh",))
