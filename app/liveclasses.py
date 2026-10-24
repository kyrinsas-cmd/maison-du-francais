"""直播课 : page /cours-en-direct (zh) et /fr/cours-en-direct, avec le catalogue des classes et des filtres à droite ;
gestion des classes dans /admin/classes.

- Classe = niveau, âges, professeur, jours, heure de début en heure de Pékin, date de début, places (5 au plus), statut.
- L'heure de Paris est calculée (6 ou 7 h d'écart selon l'heure d'été).
- Affichage seulement : la réservation (essai, inscription) se fait par WeChat ; les places sont tenues à jour par l'équipe.
- Les filtres de la barre de droite (filters.html) sont aussi utilisés par 老师 (teachers.py) et 教材库 (resources.py).
"""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from flask import abort, g, redirect, render_template, request, url_for

import teachers as T
import web
from admin import _check_csrf, bp
from db import connect
from i18n import texts

BJ, PARIS = ZoneInfo("Asia/Shanghai"), ZoneInfo("Europe/Paris")
AGE_GROUPS = {"6-8": (6, 8), "9-12": (9, 12), "13-17": (13, 17)}
MOMENTS = {"matin": (time(0), time(12)), "apres-midi": (time(12), time(18)), "soir": (time(18), time(23, 59))}
STATUSES = {"open": "Ouverte", "soon": "Bientôt", "full": "Complète (liste d'attente)", "closed": "Fermée"}


def arg_list(name, allowed):
    return [v for v in request.args.getlist(name) if v in allowed]


def overlaps(a_min, a_max, lo, hi):
    a_min, a_max = a_min or 0, a_max or 99
    return a_min <= hi and a_max >= lo


def paris_time(start_bj, start_date):
    d = start_date or date.today()
    return datetime.combine(d, start_bj, BJ).astimezone(PARIS).strftime("%H:%M")


def filter_groups(t, groups):
    """Décrit les groupes de la barre de filtres : (nom, titre, type, [(valeur, libellé)])."""
    return [{"name": n, "label": lab, "type": typ, "options": opts, "values": request.args.getlist(n)} for n, lab, typ, opts in groups]


def age_options(t):
    return [(k, t.lib_ages.format(a=f"{a}–{b}")) for k, (a, b) in AGE_GROUPS.items()]


# ---------- public ----------

@web.route("/cours-en-direct")
def live():
    t = texts(g.lang)
    levels = arg_list("niveau", T.LEVELS)
    age = request.args.get("age") if request.args.get("age") in AGE_GROUPS else None
    days = [int(d) for d in arg_list("jour", [str(i) for i in range(1, 8)])]
    moments = arg_list("moment", MOMENTS)
    seats = request.args.get("places") == "1"
    with connect() as c:
        rows = c.execute("""SELECT l.*, t.first_name, t.last_initial, t.slug, t.published AS t_pub FROM live_classes l
                            LEFT JOIN teachers t ON t.id=l.teacher_id WHERE l.published AND l.status <> 'closed'
                            ORDER BY l.sort, l.level, l.start_bj""").fetchall()
    total = len(rows)
    out = []
    for r in rows:
        if levels and r["level"] not in levels:
            continue
        if age and not overlaps(r["ages_min"], r["ages_max"], *AGE_GROUPS[age]):
            continue
        if days and not set(days) & set(r["days"] or []):
            continue
        if moments and not any(lo <= r["start_bj"] < hi for lo, hi in (MOMENTS[m] for m in moments)):
            continue
        left = max(0, r["capacity"] - r["seats_taken"])
        if seats and (left == 0 or r["status"] == "full"):
            continue
        out.append(dict(r, left=left, full=left == 0 or r["status"] == "full",
                        days_label=" ".join(t[f"day_{d}"] for d in sorted(r["days"] or [])),
                        bj=r["start_bj"].strftime("%H:%M"), paris=paris_time(r["start_bj"], r["start_date"]),
                        teacher=T.display_name(r) if r["first_name"] else None,
                        ages=t.lib_ages.format(a=f"{r['ages_min']}–{r['ages_max']}") if r["ages_min"] and r["ages_max"] else None,
                        note=(r["note_fr"] if g.lang == "fr" and r["note_fr"] else r["note_zh"])))
    groups = filter_groups(t, [
        ("niveau", t.lib_level, "checkbox", [(lv, lv) for lv in T.LEVELS]),
        ("age", t.f_age, "radio", age_options(t)),
        ("jour", t.f_day, "checkbox", [(str(i), t[f"day_{i}"]) for i in range(1, 8)]),
        ("moment", t.f_time, "checkbox", [(k, t[f"f_time_{k.replace('-', '_')}"]) for k in MOMENTS]),
        ("places", t.f_seats_h, "checkbox", [("1", t.f_seats)]),
    ])
    active = bool(levels or age or days or moments or seats)
    return render_template("live.html", classes=out, total=total, groups=groups, active=active)


# ---------- admin ----------

def _values(f):
    errors = []
    num = lambda k, lo, hi: int(f[k]) if (f.get(k) or "").isdigit() and lo <= int(f[k]) <= hi else None
    try:
        hh, mm = (f.get("start_bj") or "").split(":")[:2]
        start = time(int(hh), int(mm))
    except ValueError:
        start = None
        errors.append("Indiquez l'heure de début (heure de Pékin).")
    try:
        start_date = date.fromisoformat(f["start_date"]) if f.get("start_date") else None
    except ValueError:
        start_date = None
        errors.append("Date de début invalide.")
    v = {
        "level": f.get("level") if f.get("level") in T.LEVELS else None,
        "ages_min": num("ages_min", 1, 99), "ages_max": num("ages_max", 1, 99),
        "teacher_id": int(f["teacher_id"]) if (f.get("teacher_id") or "").isdigit() else None,
        "days": [int(d) for d in f.getlist("days") if d in [str(i) for i in range(1, 8)]],
        "start_bj": start, "start_date": start_date,
        "capacity": num("capacity", 1, 5) or 5,
        "seats_taken": num("seats_taken", 0, 5) or 0,
        "status": f.get("status") if f.get("status") in STATUSES else "open",
        "note_zh": (f.get("note_zh") or "").strip()[:500] or None,
        "note_fr": (f.get("note_fr") or "").strip()[:500] or None,
        "published": bool(f.get("published")),
        "sort": int(f["sort"]) if (f.get("sort") or "").lstrip("-").isdigit() else 0,
    }
    if not v["level"]:
        errors.append("Choisissez le niveau.")
    if not v["days"]:
        errors.append("Choisissez au moins un jour.")
    if v["seats_taken"] > v["capacity"]:
        errors.append("Plus de places occupées que de places dans la classe.")
    return v, errors


@bp.route("/classes")
def classes_admin():
    with connect() as c:
        rows = c.execute("""SELECT l.*, t.first_name, t.last_initial FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id
                            ORDER BY l.published DESC, l.sort, l.level, l.start_bj""").fetchall()
    days = {1: "lun", 2: "mar", 3: "mer", 4: "jeu", 5: "ven", 6: "sam", 7: "dim"}
    return render_template("admin/classes.html", rows=rows, statuses=STATUSES, days=days, paris_time=paris_time, display_name=T.display_name)


@bp.route("/classes/nouvelle", methods=["GET", "POST"])
def class_new():
    return class_edit(None)


@bp.route("/classes/<int:cid>", methods=["GET", "POST"])
def class_edit(cid):
    row = None
    if cid:
        with connect() as c:
            row = c.execute("SELECT * FROM live_classes WHERE id=%s", (cid,)).fetchone()
        if not row:
            abort(404)
    with connect() as c:
        teachers = c.execute("SELECT id, first_name, last_initial FROM teachers ORDER BY first_name").fetchall()
    v, errors = (dict(row) if row else {"capacity": 5, "seats_taken": 0, "status": "open", "days": []}), []
    if request.method == "POST":
        _check_csrf()
        if row and request.form.get("action") == "delete":
            with connect() as c:
                c.execute("DELETE FROM live_classes WHERE id=%s", (cid,))
            return redirect(url_for("admin.classes_admin", supprimee=1))
        v, errors = _values(request.form)
        if not errors:
            with connect() as c:
                if row:
                    c.execute("""UPDATE live_classes SET level=%(level)s, ages_min=%(ages_min)s, ages_max=%(ages_max)s, teacher_id=%(teacher_id)s,
                                   days=%(days)s, start_bj=%(start_bj)s, start_date=%(start_date)s, capacity=%(capacity)s, seats_taken=%(seats_taken)s,
                                   status=%(status)s, note_zh=%(note_zh)s, note_fr=%(note_fr)s, published=%(published)s, sort=%(sort)s, updated_at=now()
                                 WHERE id=%(id)s""", dict(v, id=cid))
                else:
                    cid = c.execute("""INSERT INTO live_classes (level, ages_min, ages_max, teacher_id, days, start_bj, start_date, capacity, seats_taken,
                                                                 status, note_zh, note_fr, published, sort)
                                       VALUES (%(level)s,%(ages_min)s,%(ages_max)s,%(teacher_id)s,%(days)s,%(start_bj)s,%(start_date)s,%(capacity)s,
                                               %(seats_taken)s,%(status)s,%(note_zh)s,%(note_fr)s,%(published)s,%(sort)s) RETURNING id""", v).fetchone()["id"]
            return redirect(url_for("admin.class_edit", cid=cid, ok=1))
    return render_template("admin/class.html", row=row, v=v, errors=errors, teachers=teachers, levels=T.LEVELS, statuses=STATUSES,
                           display_name=T.display_name, msg=request.args.get("ok") and "Enregistré.",
                           paris=paris_time(v["start_bj"], v.get("start_date")) if v.get("start_bj") else None)
