"""Gestion des élèves (administration, /admin/eleves) — décidé le 2026-11-09 : l'équipe gère élèves et classes, le professeur consulte.

- Un élève (table students) = un enfant d'un compte parent, ou l'élève lui-même (compte élève). Prénom affiché en classe et dans les bilans.
- Créé automatiquement au premier test de niveau (placement.py) ; l'équipe peut aussi le créer à la main à partir de l'e-mail du compte.
- Fiche : prénom, âge, niveau CECRL retenu, statut, notes internes ; classes (inscrire, retirer, changer de classe) ;
  tests de niveau ; présence et bilans des cours.
- Les places d'une classe (live_classes.seats_taken, affichées sur 直播课) sont recalculées à chaque inscription : élèves inscrits actifs, hors essais.
"""
from flask import abort, redirect, render_template, request, url_for

import users as U
from admin import _check_csrf, bp
from db import connect

LEVELS = ("A1.1", "A1", "A2", "B1", "B2", "C1")
KINDS = {"student": "Élève inscrit", "trial": "Essai (试听)"}


def sync_seats(c, class_id):
    """Places occupées = élèves inscrits actifs (les essais ne prennent pas de place, cahier des charges §8)."""
    c.execute("""UPDATE live_classes SET seats_taken = LEAST(capacity, (SELECT count(*) FROM class_members m
                 WHERE m.class_id=%(c)s AND m.status='active' AND m.kind='student')), updated_at=now() WHERE id=%(c)s""", {"c": class_id})


def ensure_student(c, user_id, first_name, age=None):
    """Élève (compte + prénom) : le retrouve ou le crée. Utilisé par le test de niveau et l'inscription en classe."""
    first_name = (first_name or "").strip()[:40]
    if not first_name:
        first_name = c.execute("SELECT name FROM users WHERE id=%s", (user_id,)).fetchone()["name"]
    row = c.execute("SELECT * FROM students WHERE user_id=%s AND lower(first_name)=lower(%s)", (user_id, first_name)).fetchone()
    if row:
        if age and not row["age"]:
            c.execute("UPDATE students SET age=%s, updated_at=now() WHERE id=%s", (age, row["id"]))
        return row["id"]
    return c.execute("INSERT INTO students (user_id, first_name, age) VALUES (%s,%s,%s) RETURNING id", (user_id, first_name, age)).fetchone()["id"]


def enroll(c, student_id, class_id, kind="student"):
    """Inscrit un élève dans une classe (ou le réinscrit), puis recalcule les places. Renvoie un message d'erreur ou None."""
    s = c.execute("SELECT * FROM students WHERE id=%s", (student_id,)).fetchone()
    cls = c.execute("SELECT * FROM live_classes WHERE id=%s", (class_id,)).fetchone()
    if not s or not cls:
        return "Élève ou classe introuvable."
    if kind == "student":
        taken = c.execute("""SELECT count(*) AS n FROM class_members WHERE class_id=%s AND status='active' AND kind='student'
                             AND student_id <> %s""", (class_id, student_id)).fetchone()["n"]
        if taken >= cls["capacity"]:
            return f"La classe est complète ({taken} / {cls['capacity']}). Inscrivez l'élève en essai ou augmentez la capacité."
    c.execute("""INSERT INTO class_members (class_id, user_id, student_id, child_label, kind) VALUES (%s,%s,%s,%s,%s)
                 ON CONFLICT (class_id, student_id) DO UPDATE SET kind=EXCLUDED.kind, child_label=EXCLUDED.child_label, status='active'""",
              (class_id, s["user_id"], student_id, s["first_name"], kind))
    sync_seats(c, class_id)
    return None


def class_label(r):
    days = {1: "lun", 2: "mar", 3: "mer", 4: "jeu", 5: "ven", 6: "sam", 7: "dim"}
    who = f" · {r['first_name']}" if r.get("first_name") else ""
    when = " ".join(days[d] for d in (r.get("days") or [])) + (f" {r['start_bj'].strftime('%H:%M')} Pékin" if r.get("start_bj") else "")
    return f"{r['level']}{who} · {when}".strip()


def merge(c, src, dst):
    """Fusionne la fiche src dans dst (même compte) : tests, inscriptions, présence et bilans passent sur dst ; src est supprimée."""
    c.execute("UPDATE placement_tests SET student_id=%s WHERE student_id=%s", (dst, src))
    for m in c.execute("SELECT * FROM class_members WHERE student_id=%s", (src,)).fetchall():
        other = c.execute("SELECT * FROM class_members WHERE student_id=%s AND class_id=%s", (dst, m["class_id"])).fetchone()
        if not other:
            c.execute("UPDATE class_members SET student_id=%s WHERE id=%s", (dst, m["id"]))
            continue
        for table in ("session_reports", "session_absences"):     # même classe des deux côtés : on garde la ligne de dst
            c.execute(f"""UPDATE {table} SET member_id=%s WHERE member_id=%s
                          AND NOT EXISTS (SELECT 1 FROM {table} x WHERE x.member_id=%s AND x.session_id={table}.session_id)""", (other["id"], m["id"], other["id"]))
        c.execute("UPDATE session_attendance SET member_id=%s WHERE member_id=%s", (other["id"], m["id"]))
        if m["status"] == "active":
            c.execute("UPDATE class_members SET status='active', kind=CASE WHEN %s='student' THEN 'student' ELSE kind END WHERE id=%s", (m["kind"], other["id"]))
        c.execute("DELETE FROM class_members WHERE id=%s", (m["id"],))
        sync_seats(c, m["class_id"])
    d = c.execute("SELECT * FROM students WHERE id=%s", (dst,)).fetchone()
    s = c.execute("SELECT * FROM students WHERE id=%s", (src,)).fetchone()
    c.execute("UPDATE students SET age=coalesce(age, %s::int), level=coalesce(level, %s::text), notes=nullif(concat_ws(E'\n', notes, %s::text), ''), updated_at=now() WHERE id=%s",
              (s["age"], s["level"], s["notes"], dst))
    c.execute("DELETE FROM students WHERE id=%s", (src,))
    c.execute("UPDATE class_members SET child_label=%s WHERE student_id=%s", (d["first_name"], dst))


# ---------- liste ----------

@bp.route("/eleves")
def students_admin():
    f = {"q": (request.args.get("q") or "").strip()[:80], "niveau": request.args.get("niveau") if request.args.get("niveau") in LEVELS else "",
         "classe": request.args.get("classe", ""), "statut": request.args.get("statut") if request.args.get("statut") in ("active", "left") else "active"}
    where, args = ["s.status=%s"], [f["statut"]]
    if f["q"]:
        where.append("(s.first_name ILIKE %s OR u.name ILIKE %s OR u.email ILIKE %s)"); args += [f"%{f['q']}%"] * 3
    if f["niveau"]:
        where.append("s.level=%s"); args.append(f["niveau"])
    if f["classe"] == "sans":
        where.append("NOT EXISTS (SELECT 1 FROM class_members m WHERE m.student_id=s.id AND m.status='active')")
    elif f["classe"].isdigit():
        where.append("EXISTS (SELECT 1 FROM class_members m WHERE m.student_id=s.id AND m.status='active' AND m.class_id=%s)"); args.append(int(f["classe"]))
    with connect() as c:
        rows = c.execute(f"""SELECT s.*, u.name AS account_name, u.email, u.role AS account_role,
                  (SELECT string_agg(l.level || CASE WHEN m.kind='trial' THEN ' (essai)' ELSE '' END, ', ' ORDER BY l.level)
                     FROM class_members m JOIN live_classes l ON l.id=m.class_id WHERE m.student_id=s.id AND m.status='active') AS classes,
                  (SELECT t.final_level FROM placement_tests t WHERE t.student_id=s.id AND t.step='evaluated' ORDER BY t.evaluated_at DESC LIMIT 1) AS test_level,
                  (SELECT t.step FROM placement_tests t WHERE t.student_id=s.id ORDER BY t.created_at DESC LIMIT 1) AS test_step
                  FROM students s JOIN users u ON u.id=s.user_id WHERE {' AND '.join(where)} ORDER BY s.first_name""", args).fetchall()
        classes = c.execute("SELECT l.*, t.first_name FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id ORDER BY l.level, l.start_bj").fetchall()
        counts = {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) AS n FROM students GROUP BY 1").fetchall()}
    return render_template("admin/students.html", rows=rows, f=f, levels=LEVELS, classes=classes, class_label=class_label, counts=counts)


@bp.route("/eleves/nouveau", methods=["GET", "POST"])
def student_new():
    errors, v = [], {}
    if request.method == "POST":
        _check_csrf()
        v = {k: (request.form.get(k) or "").strip() for k in ("email", "first_name", "age", "level")}
        with connect() as c:
            acc = c.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (v["email"],)).fetchone()
            if not acc or acc["role"] not in ("parent", "eleve"):
                errors.append("Aucun compte parent ou élève avec cette adresse. La famille doit d'abord créer son compte sur le site.")
            elif acc["role"] == "parent" and not v["first_name"]:
                errors.append("Indiquez le prénom de l'enfant.")
            else:
                age = int(v["age"]) if v["age"].isdigit() and 3 <= int(v["age"]) <= 99 else None
                sid = ensure_student(c, acc["id"], v["first_name"] if acc["role"] == "parent" else (v["first_name"] or acc["name"]), age)
                if v["level"] in LEVELS:
                    c.execute("UPDATE students SET level=%s WHERE id=%s", (v["level"], sid))
                return redirect(url_for("admin.student", sid=sid, ok="Élève créé."))
    return render_template("admin/student_new.html", v=v, errors=errors, levels=LEVELS)


# ---------- fiche ----------

@bp.route("/eleves/<int:sid>", methods=["GET", "POST"])
def student(sid):
    errors = []
    with connect() as c:
        s = c.execute("SELECT s.*, u.name AS account_name, u.email, u.role AS account_role, u.lang FROM students s JOIN users u ON u.id=s.user_id WHERE s.id=%s",
                      (sid,)).fetchone()
        if not s:
            abort(404)
        if request.method == "POST":
            _check_csrf()
            act = request.form.get("action")
            msg = None
            if act == "save":
                name = (request.form.get("first_name") or "").strip()[:40]
                age = request.form.get("age", "")
                if not name:
                    errors.append("Le prénom est obligatoire.")
                elif c.execute("SELECT 1 FROM students WHERE user_id=%s AND lower(first_name)=lower(%s) AND id<>%s", (s["user_id"], name, sid)).fetchone():
                    errors.append("Ce compte a déjà un élève avec ce prénom.")
                else:
                    c.execute("""UPDATE students SET first_name=%s, age=%s, level=%s, status=%s, notes=%s, updated_at=now() WHERE id=%s""",
                              (name, int(age) if age.isdigit() and 3 <= int(age) <= 99 else None,
                               request.form.get("level") if request.form.get("level") in LEVELS else None,
                               "left" if request.form.get("status") == "left" else "active", (request.form.get("notes") or "").strip()[:2000] or None, sid))
                    c.execute("UPDATE class_members SET child_label=%s WHERE student_id=%s", (name, sid))
                    if request.form.get("status") == "left":     # élève parti : retiré de ses classes
                        for m in c.execute("SELECT class_id FROM class_members WHERE student_id=%s AND status='active'", (sid,)).fetchall():
                            c.execute("UPDATE class_members SET status='ended' WHERE student_id=%s AND class_id=%s", (sid, m["class_id"]))
                            sync_seats(c, m["class_id"])
                    msg = "Fiche enregistrée."
            elif act == "enroll":
                cid = request.form.get("class_id", type=int)
                err = enroll(c, sid, cid, "trial" if request.form.get("kind") == "trial" else "student") if cid else "Choisissez une classe."
                if err:
                    errors.append(err)
                else:
                    msg = "Élève inscrit dans la classe."
            elif act == "remove":
                cid = request.form.get("class_id", type=int)
                c.execute("UPDATE class_members SET status='ended' WHERE student_id=%s AND class_id=%s", (sid, cid))
                sync_seats(c, cid)
                msg = "Élève retiré de la classe."
            elif act == "move":                                  # changer de classe : retire de l'ancienne, inscrit dans la nouvelle
                old, new = request.form.get("from_class", type=int), request.form.get("class_id", type=int)
                kind = (c.execute("SELECT kind FROM class_members WHERE student_id=%s AND class_id=%s", (sid, old)).fetchone() or {"kind": "student"})["kind"]
                err = enroll(c, sid, new, kind) if new and new != old else "Choisissez une autre classe."
                if err:
                    errors.append(err)
                else:
                    c.execute("UPDATE class_members SET status='ended' WHERE student_id=%s AND class_id=%s", (sid, old))
                    sync_seats(c, old)
                    msg = "Élève changé de classe."
            elif act == "kind":
                cid = request.form.get("class_id", type=int)
                new_kind = "student" if request.form.get("kind") == "student" else "trial"
                err = enroll(c, sid, cid, new_kind)
                if err:
                    errors.append(err)
                else:
                    msg = "Type d'inscription modifié."
            elif act == "merge":                                 # fiche en double : tout passe sur l'autre fiche du même compte
                target = request.form.get("into", type=int)
                t = c.execute("SELECT * FROM students WHERE id=%s AND user_id=%s AND id<>%s", (target, s["user_id"], sid)).fetchone()
                if not t:
                    errors.append("Choisissez l'autre fiche du même compte.")
                else:
                    merge(c, sid, t["id"])
                    return redirect(url_for("admin.student", sid=t["id"], ok=f"Fiche « {s['first_name']} » fusionnée dans celle-ci."))
            elif act == "reassign":                              # erreur de compte : l'élève (tests, classes) passe sur un autre compte
                acc = c.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", ((request.form.get("email") or "").strip(),)).fetchone()
                if not acc or acc["role"] not in ("parent", "eleve"):
                    errors.append("Aucun compte parent ou élève avec cette adresse.")
                elif acc["id"] == s["user_id"]:
                    errors.append("L'élève est déjà rattaché à ce compte.")
                elif c.execute("SELECT 1 FROM students WHERE user_id=%s AND lower(first_name)=lower(%s)", (acc["id"], s["first_name"])).fetchone():
                    errors.append("Ce compte a déjà un élève avec ce prénom : fusionnez plutôt les fiches après le rattachement, ou renommez l'élève.")
                else:
                    c.execute("UPDATE students SET user_id=%s, updated_at=now() WHERE id=%s", (acc["id"], sid))
                    c.execute("UPDATE class_members SET user_id=%s WHERE student_id=%s", (acc["id"], sid))
                    c.execute("UPDATE placement_tests SET user_id=%s WHERE student_id=%s", (acc["id"], sid))
                    msg = f"Élève rattaché au compte {acc['email']}."
            if msg and not errors:
                return redirect(url_for("admin.student", sid=sid, ok=msg))
        memberships = c.execute("""SELECT m.*, l.level, l.days, l.start_bj, l.capacity, l.seats_taken, t.first_name,
                                   (SELECT min(starts_at) FROM class_sessions x WHERE x.class_id=l.id AND x.status='scheduled' AND x.starts_at > now()) AS next_at
                                   FROM class_members m JOIN live_classes l ON l.id=m.class_id LEFT JOIN teachers t ON t.id=l.teacher_id
                                   WHERE m.student_id=%s ORDER BY m.status, l.level""", (sid,)).fetchall()
        in_classes = {m["class_id"] for m in memberships if m["status"] == "active"}
        classes = [r for r in c.execute("""SELECT l.*, t.first_name FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id
                                           WHERE l.status <> 'closed' ORDER BY l.level, l.start_bj""").fetchall() if r["id"] not in in_classes]
        tests = c.execute("""SELECT t.*, l.level AS c_level FROM placement_tests t LEFT JOIN live_classes l ON l.id=t.class_id
                             WHERE t.student_id=%s ORDER BY t.created_at DESC""", (sid,)).fetchall()
        reports = c.execute("""SELECT r.*, x.starts_at, l.level FROM session_reports r JOIN class_members m ON m.id=r.member_id
                               JOIN class_sessions x ON x.id=r.session_id JOIN live_classes l ON l.id=x.class_id
                               WHERE m.student_id=%s ORDER BY x.starts_at DESC LIMIT 20""", (sid,)).fetchall()
        attendance = {r["status"]: r["n"] for r in c.execute("""SELECT r.status, count(*) AS n FROM session_reports r JOIN class_members m ON m.id=r.member_id
                                                                 WHERE m.student_id=%s GROUP BY 1""", (sid,)).fetchall()}
        siblings = c.execute("SELECT id, first_name FROM students WHERE user_id=%s AND id<>%s ORDER BY first_name", (s["user_id"], sid)).fetchall()
    return render_template("admin/student.html", s=s, memberships=memberships, classes=classes, tests=tests, reports=reports, attendance=attendance,
                           siblings=siblings, levels=LEVELS, kinds=KINDS, class_label=class_label, errors=errors, msg=request.args.get("ok"),
                           role_label=lambda r: U.role_label(r, "fr"))
