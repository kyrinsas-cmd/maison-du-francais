"""Devoirs, programme et profil élève côté professeur (2026-11-11).

Décisions de l'utilisateur : les devoirs sont donnés par le professeur depuis la page de sa classe et rendus par l'élève
seulement, depuis son compte (numéro MF… ou compte élève de 15 ans et plus) ; note sur 20.
- Devoir : titre, consigne, pièce jointe facultative (PDF, image, audio, Word, PowerPoint), date limite (par défaut le cours suivant).
- Rendu : texte et/ou fichier (photo du cahier, PDF, audio) ; modifiable tant qu'il n'est pas corrigé.
- Correction : note sur 20 (demi-points), commentaire ; l'élève voit la note.
- Programme : unités par niveau (program_units) ; le professeur marque « en cours » / « terminé » pour sa classe.
- Le professeur crée aussi une séance immédiate (« démarrer un cours maintenant ») et consulte le profil de ses élèves.
Fichiers : uploads/homework/ (noms aléatoires), servis après contrôle d'accès.
"""
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from flask import abort, redirect, render_template, request, send_from_directory, url_for

import users as U
import web
import bo_i18n
from accounts import bp as espace_bp, current as teacher_current
from db import connect
from liveclasses import BJ, PARIS

UPLOADS = os.path.join(os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads"), "homework")
FILE_MAX = 20 * 1024 * 1024
NAME_RE = re.compile(r"[hs]\d+-[0-9a-f]{12}\.(pdf|mp3|m4a|png|jpg|docx|pptx)")


@web.app.before_request
def homework_upload_size():
    """Le site limite les envois à 1 Mo ; les devoirs (photo du cahier, audio, PDF) acceptent 20 Mo."""
    if request.endpoint in ("espace.class_homework_new", "pupil_homework_one"):
        request.max_content_length = FILE_MAX + 1024 * 1024


def save_upload(prefix, f):
    """Enregistre un fichier envoyé (type vérifié par sa signature) ; renvoie (nom, type) ou lève ValueError."""
    from resources import _detect
    head = f.stream.read(16)
    kind, ext = _detect(head, f.filename or "")
    if not kind:
        raise ValueError("format")
    os.makedirs(UPLOADS, exist_ok=True)
    name = f"{prefix}-{secrets.token_hex(6)}.{ext}"
    path, size = os.path.join(UPLOADS, name), len(head)
    with open(path, "wb") as out:
        out.write(head)
        while chunk := f.stream.read(1024 * 1024):
            size += len(chunk)
            if size > FILE_MAX:
                out.close(); os.remove(path)
                raise ValueError("size")
            out.write(chunk)
    return name, kind


def remove_upload(name):
    if name and NAME_RE.fullmatch(name):
        try:
            os.remove(os.path.join(UPLOADS, name))
        except FileNotFoundError:
            pass


def _teacher_class(c, cid):
    u = teacher_current()
    cls = c.execute("SELECT * FROM live_classes WHERE id=%s AND teacher_id=%s", (cid, u["teacher_id"])).fetchone() if u else None
    if not cls:
        abort(404)
    return u, cls


def next_session_at(c, class_id):
    r = c.execute("SELECT min(starts_at) AS t FROM class_sessions WHERE class_id=%s AND status='scheduled' AND starts_at > now()", (class_id,)).fetchone()
    return r["t"]


def program_for(c, cls):
    rows = c.execute("""SELECT u.*, p.status FROM program_units u LEFT JOIN class_progress p ON p.unit_id=u.id AND p.class_id=%s
                        WHERE u.level=%s ORDER BY u.sort""", (cls["id"], cls["level"])).fetchall()
    done = sum(1 for r in rows if r["status"] == "done")
    return rows, done, (round(100 * done / len(rows)) if rows else 0)


def homeworks_for_class(c, cls):
    rows = c.execute("""SELECT h.*, (SELECT count(*) FROM homework_submissions s WHERE s.homework_id=h.id) AS n_sub,
                          (SELECT count(*) FROM homework_submissions s WHERE s.homework_id=h.id AND s.grade IS NOT NULL) AS n_graded,
                          (SELECT round(avg(s.grade), 1) FROM homework_submissions s WHERE s.homework_id=h.id AND s.grade IS NOT NULL) AS avg
                        FROM homeworks h WHERE h.class_id=%s ORDER BY h.created_at DESC""", (cls["id"],)).fetchall()
    return [dict(r, due_paris=r["due_at"].astimezone(PARIS) if r["due_at"] else None) for r in rows]


# ---------- professeur : actions depuis la page de la classe ----------

@espace_bp.route("/classes/<int:cid>/demarrer", methods=["POST"])
def class_start_now(cid):
    """Le professeur lance un cours maintenant : séance immédiate (salle ouverte 1 h 30), puis il entre dans la salle."""
    import classroom
    U.check_csrf()
    with connect() as c:
        _, cls = _teacher_class(c, cid)
        now = datetime.now(timezone.utc)
        open_s = c.execute("""SELECT * FROM class_sessions WHERE class_id=%s AND status='scheduled'
                              AND starts_at - interval '30 minutes' <= %s AND starts_at + make_interval(mins => duration_min) + interval '30 minutes' >= %s
                              ORDER BY starts_at LIMIT 1""", (cid, now, now)).fetchone()
        if open_s:                      # un cours est déjà ouvert : on y va plutôt que d'en créer un deuxième
            sid = open_s["id"]
        else:
            sid = c.execute("INSERT INTO class_sessions (class_id, starts_at, duration_min) VALUES (%s,%s,%s) RETURNING id",
                            (cid, now.replace(second=0, microsecond=0), classroom.SESSION_MIN)).fetchone()["id"]
    return redirect(url_for("classroom", sid=sid, lang=bo_i18n.bo_lang()))


@espace_bp.route("/classes/<int:cid>/programme", methods=["POST"])
def class_program(cid):
    U.check_csrf()
    with connect() as c:
        _, cls = _teacher_class(c, cid)
        for u in c.execute("SELECT id FROM program_units WHERE level=%s", (cls["level"],)).fetchall():
            st = request.form.get(f"u{u['id']}", "")
            if st in ("doing", "done"):
                c.execute("""INSERT INTO class_progress (class_id, unit_id, status) VALUES (%s,%s,%s)
                             ON CONFLICT (class_id, unit_id) DO UPDATE SET status=EXCLUDED.status, updated_at=now()""", (cid, u["id"], st))
            elif st == "todo":
                c.execute("DELETE FROM class_progress WHERE class_id=%s AND unit_id=%s", (cid, u["id"]))
    return redirect(url_for("espace.my_class", cid=cid, ok="programme") + "#programme")


@espace_bp.route("/classes/<int:cid>/devoirs", methods=["POST"])
def class_homework_new(cid):
    U.check_csrf()
    with connect() as c:
        u, cls = _teacher_class(c, cid)
        title = (request.form.get("title") or "").strip()[:200]
        if not title:
            return redirect(url_for("espace.my_class", cid=cid, err="titre") + "#devoirs")
        due = None
        if request.form.get("due"):
            try:   # date et heure saisies en heure de Paris par le professeur
                due = datetime.strptime(request.form["due"], "%Y-%m-%dT%H:%M").replace(tzinfo=PARIS)
            except ValueError:
                return redirect(url_for("espace.my_class", cid=cid, err="date") + "#devoirs")
        else:
            due = next_session_at(c, cid)
        hid = c.execute("""INSERT INTO homeworks (class_id, title, instructions, due_at, created_by) VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                        (cid, title, (request.form.get("instructions") or "").strip()[:4000] or None, due, u["id"])).fetchone()["id"]
        f = request.files.get("file")
        if f and f.filename:
            try:
                name, kind = save_upload(f"h{hid}", f)
                c.execute("UPDATE homeworks SET file_name=%s, file_kind=%s WHERE id=%s", (name, kind, hid))
            except ValueError as e:
                c.execute("DELETE FROM homeworks WHERE id=%s", (hid,))
                return redirect(url_for("espace.my_class", cid=cid, err="fichier-" + str(e)) + "#devoirs")
    return redirect(url_for("espace.my_class", cid=cid, ok="devoir") + "#devoirs")


@espace_bp.route("/devoirs/<int:hid>", methods=["GET", "POST"])
def homework_teacher(hid):
    """Rendus d'un devoir : qui a rendu, correction (note sur 20 + commentaire), suppression du devoir."""
    with connect() as c:
        h = c.execute("SELECT * FROM homeworks WHERE id=%s", (hid,)).fetchone()
        if not h:
            abort(404)
        _, cls = _teacher_class(c, h["class_id"])
        msg, errors = None, []
        if request.method == "POST":
            U.check_csrf()
            if request.form.get("action") == "delete":
                files = [h["file_name"]] + [r["file_name"] for r in c.execute("SELECT file_name FROM homework_submissions WHERE homework_id=%s", (hid,)).fetchall()]
                c.execute("DELETE FROM homeworks WHERE id=%s", (hid,))
                for fn in files:
                    remove_upload(fn)
                return redirect(url_for("espace.my_class", cid=cls["id"], ok="devoir-supprime") + "#devoirs")
            sub = c.execute("SELECT * FROM homework_submissions WHERE id=%s AND homework_id=%s", (request.form.get("sub", type=int), hid)).fetchone()
            if sub:
                raw = (request.form.get("grade") or "").strip().replace(",", ".")
                try:
                    grade = Decimal(raw)
                    if grade < 0 or grade > 20 or grade * 2 != int(grade * 2):
                        raise InvalidOperation
                except (InvalidOperation, ValueError):
                    errors.append("La note doit être un nombre entre 0 et 20 (demi-points acceptés).")
                else:
                    c.execute("UPDATE homework_submissions SET grade=%s, feedback=%s, graded_at=now() WHERE id=%s",
                              (grade, (request.form.get("feedback") or "").strip()[:2000] or None, sub["id"]))
                    return redirect(url_for("espace.homework_teacher", hid=hid, ok=1) + f"#r{sub['id']}")
        rows = c.execute("""SELECT m.student_id, m.child_label, m.kind, s.id AS sub_id, s.text_answer, s.file_name, s.file_kind, s.submitted_at,
                                   s.grade, s.feedback, s.graded_at, st.login_id
                            FROM class_members m LEFT JOIN homework_submissions s ON s.homework_id=%s AND s.student_id=m.student_id
                            LEFT JOIN students st ON st.id=m.student_id
                            WHERE m.class_id=%s AND m.status='active' ORDER BY m.kind, m.child_label""", (hid, cls["id"])).fetchall()
    return render_template("espace/homework.html", h=dict(h, due_paris=h["due_at"].astimezone(PARIS) if h["due_at"] else None), cls=cls,
                           rows=[dict(r, sub_paris=r["submitted_at"].astimezone(PARIS) if r["submitted_at"] else None) for r in rows],
                           errors=errors, ok=request.args.get("ok"))


@espace_bp.route("/eleves/<int:sid>")
def student_profile(sid):
    """Profil d'un élève pour son professeur (lecture seule) : niveau, présence, bilans, devoirs, tests."""
    u = teacher_current()
    with connect() as c:
        s = c.execute("""SELECT s.* FROM students s WHERE s.id=%s AND EXISTS (SELECT 1 FROM class_members m JOIN live_classes l ON l.id=m.class_id
                         WHERE m.student_id=s.id AND l.teacher_id=%s)""", (sid, u["teacher_id"])).fetchone()
        if not s:
            abort(404)
        classes = c.execute("""SELECT l.*, m.kind, m.status AS m_status FROM class_members m JOIN live_classes l ON l.id=m.class_id
                               WHERE m.student_id=%s AND l.teacher_id=%s ORDER BY m.status, l.level""", (sid, u["teacher_id"])).fetchall()
        reports = c.execute("""SELECT r.*, x.starts_at, l.level FROM session_reports r JOIN class_members m ON m.id=r.member_id
                               JOIN class_sessions x ON x.id=r.session_id JOIN live_classes l ON l.id=x.class_id
                               WHERE m.student_id=%s AND l.teacher_id=%s ORDER BY x.starts_at DESC LIMIT 30""", (sid, u["teacher_id"])).fetchall()
        att = {r["status"]: r["n"] for r in c.execute("""SELECT r.status, count(*) AS n FROM session_reports r JOIN class_members m ON m.id=r.member_id
                                                          WHERE m.student_id=%s GROUP BY 1""", (sid,)).fetchall()}
        hws = c.execute("""SELECT h.id, h.title, h.due_at, l.level, s.submitted_at, s.grade FROM homeworks h JOIN live_classes l ON l.id=h.class_id
                           JOIN class_members m ON m.class_id=h.class_id AND m.student_id=%s
                           LEFT JOIN homework_submissions s ON s.homework_id=h.id AND s.student_id=%s
                           WHERE l.teacher_id=%s ORDER BY h.created_at DESC""", (sid, sid, u["teacher_id"])).fetchall()
        tests = c.execute("""SELECT created_at, step, est_level, writing_level, oral_level, final_level FROM placement_tests
                             WHERE student_id=%s ORDER BY created_at DESC""", (sid,)).fetchall()
    graded = [h["grade"] for h in hws if h["grade"] is not None]
    done = sum(att.values())
    return render_template("espace/student.html", s=s, classes=classes, reports=reports, att=att, hws=hws, tests=tests,
                           avg=round(sum(graded) / len(graded), 1) if graded else None, done=done,
                           rate=round(100 * (att.get("present", 0) + att.get("late", 0)) / done) if done else None)


# ---------- élève : mes devoirs ----------

def homeworks_for_student(c, st):
    rows = c.execute("""SELECT h.*, l.level, s.id AS sub_id, s.submitted_at, s.grade, s.graded_at FROM homeworks h
                        JOIN live_classes l ON l.id=h.class_id
                        JOIN class_members m ON m.class_id=h.class_id AND m.student_id=%s AND m.status='active'
                        LEFT JOIN homework_submissions s ON s.homework_id=h.id AND s.student_id=%s
                        ORDER BY (s.id IS NULL) DESC, h.due_at NULLS LAST, h.created_at DESC""", (st["id"], st["id"])).fetchall()
    now = datetime.now(timezone.utc)
    return [dict(r, due_bj=r["due_at"].astimezone(BJ) if r["due_at"] else None, late=bool(r["due_at"] and r["due_at"] < now and not r["sub_id"]))
            for r in rows]


@web.route("/eleve/devoirs/<int:hid>", methods=["GET", "POST"])
def pupil_homework_one(hid):
    import pupil
    st = pupil.me_student()
    if not st:
        return redirect(url_for("pupil_login"))
    T = pupil.tx()
    error = None
    with connect() as c:
        h = c.execute("""SELECT h.*, l.level FROM homeworks h JOIN live_classes l ON l.id=h.class_id
                         JOIN class_members m ON m.class_id=h.class_id AND m.student_id=%s AND m.status='active' WHERE h.id=%s""", (st["id"], hid)).fetchone()
        if not h:
            abort(404)
        sub = c.execute("SELECT * FROM homework_submissions WHERE homework_id=%s AND student_id=%s", (hid, st["id"])).fetchone()
        if request.method == "POST":
            U.check_csrf()
            if sub and sub["grade"] is not None:
                abort(409)                                   # corrigé : plus de modification
            text = (request.form.get("text") or "").strip()[:8000] or None
            f = request.files.get("file")
            name = kind = None
            if f and f.filename:
                try:
                    name, kind = save_upload(f"s{st['id']}", f)
                except ValueError as e:
                    error = T["hw_err_size"] if str(e) == "size" else T["hw_err_format"]
            if not error and not text and not name and not (sub and sub["file_name"]):
                error = T["hw_err_empty"]
            if not error:
                if sub:
                    if name:
                        remove_upload(sub["file_name"])
                    c.execute("""UPDATE homework_submissions SET text_answer=%s, file_name=coalesce(%s, file_name), file_kind=coalesce(%s, file_kind),
                                 submitted_at=now() WHERE id=%s""", (text, name, kind, sub["id"]))
                else:
                    c.execute("INSERT INTO homework_submissions (homework_id, student_id, text_answer, file_name, file_kind) VALUES (%s,%s,%s,%s,%s)",
                              (hid, st["id"], text, name, kind))
                return redirect(url_for("pupil_homework_one", hid=hid, ok=1))
    resp = web.app.make_response(render_template("pupil/homework_one.html", s=st, h=dict(h, due_bj=h["due_at"].astimezone(BJ) if h["due_at"] else None),
                                                 sub=sub, error=error, ok=request.args.get("ok")))
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------- fichiers (devoir du professeur, rendu de l'élève) ----------

@web.route("/devoirs/fichier/<what>/<int:oid>")
def homework_file(what, oid):
    """what = « devoir » (pièce jointe du professeur) ou « rendu » (fichier de l'élève). Accès : professeur de la classe, équipe,
    élève concerné (numéro ou compte élève), parent de l'élève."""
    import pupil
    u, st = U.current(), pupil.current_student()
    with connect() as c:
        if what == "devoir":
            row = c.execute("SELECT h.file_name, h.class_id, NULL::bigint AS student_id FROM homeworks h WHERE h.id=%s", (oid,)).fetchone()
        elif what == "rendu":
            row = c.execute("""SELECT s.file_name, h.class_id, s.student_id FROM homework_submissions s JOIN homeworks h ON h.id=s.homework_id
                               WHERE s.id=%s""", (oid,)).fetchone()
        else:
            abort(404)
        if not row or not row["file_name"]:
            abort(404)
        cls = c.execute("SELECT teacher_id FROM live_classes WHERE id=%s", (row["class_id"],)).fetchone()
        ok = False
        if u and (u["role"] in U.STAFF or (u["role"] == "professeur" and u["teacher_id"] == cls["teacher_id"])):
            ok = True
        else:
            me = st or (pupil.me_student() if u and u["role"] == "eleve" else None)
            if me:
                ok = (row["student_id"] == me["id"]) if what == "rendu" else bool(c.execute(
                    "SELECT 1 FROM class_members WHERE class_id=%s AND student_id=%s AND status='active'", (row["class_id"], me["id"])).fetchone())
            elif u and u["role"] == "parent":
                ok = bool(c.execute("""SELECT 1 FROM students s JOIN class_members m ON m.student_id=s.id WHERE s.user_id=%s AND m.class_id=%s
                                       AND (%s IS NULL OR s.id=%s)""", (u["id"], row["class_id"], row["student_id"], row["student_id"])).fetchone())
        if not ok:
            abort(403)
    resp = send_from_directory(UPLOADS, row["file_name"], conditional=True, max_age=0)
    resp.headers["Cache-Control"] = "private, no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp
