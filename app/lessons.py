"""课 — leçons du programme (2026-11-14, demande de l'utilisateur : « une série complète de supports : contenu du professeur,
manuel de l'élève et exercices, par niveau, tous les aspects, but : réussir le DELF / le HSK »).

Niveau → unité (program_units) → leçon (lessons). Une leçon = un cours de 45 min + 15 min de devoirs et questions, avec :
- le guide du professeur (objectifs, déroulé minuté, erreurs fréquentes, adaptation à l'âge), dans la langue des professeurs ;
- la fiche de l'élève (vocabulaire, grammaire, texte, culture), expliquée dans la langue des élèves, imprimable ;
- des exercices corrigés automatiquement (QCM, vrai/faux, phrase à compléter, associer) et une tâche de production (devoir) ;
- des audios (script dans la leçon, fichier envoyé par l'équipe ; une question d'écoute sans fichier n'est pas posée).
Contenu : JSON (colonne content), vérifié par validate(). Circuit : brouillon → en relecture (les professeurs lisent et commentent)
→ publiée (seule une leçon publiée est visible des élèves et des parents). Les leçons de la graine (lessons_seed.py) arrivent
« en relecture » : un professeur natif les relit avant toute publication.

Accès élève (contenu payant) : élève inscrit à une classe (pas l'essai), leçons publiées du niveau de sa classe, dans les unités
commencées ou terminées par la classe, ou faites en cours ; si la classe n'a encore rien commencé, la 1re unité.
Les parents voient la fiche (sans les exercices) et les résultats de leur enfant."""
import json
import os
import random
import re
import secrets
from datetime import datetime, timezone

from flask import abort, g, redirect, render_template, request, send_from_directory, url_for
from psycopg.types.json import Jsonb

import users as U
import web
from accounts import bp as espace_bp, current as teacher_current
from admin import _check_csrf, bp as admin_bp
from db import connect
from teachers import LEVELS
from lesson_content import SKELETON, dumps, validate  # noqa: F401

# ---- propre au site ----
SITE = {"target": "fr", "guide": "fr", "sheet": "zh"}      # langue apprise, langue du guide du professeur, langue des explications élève
UPLOADS = os.path.join(os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads"), "lessons")
# ------------------------

STATUSES = {"draft": "Brouillon", "review": "En relecture", "published": "Publiée"}
AUDIO_RE = re.compile(r"l\d+-[a-z0-9]{1,12}-[0-9a-f]{12}\.(mp3|m4a)")
AUDIO_MAX = 15 * 1024 * 1024

LBL = {
    "zh": {"objectives": "教学目标", "can_do": "学完这一课，我能……", "skills": "技能", "exam": "对应考试能力", "materials": "教具",
           "vocab": "生词", "grammar": "语法", "text": "课文", "steps": "教学步骤", "mistakes": "常见错误", "diff": "按年龄调整",
           "young": "6–10岁", "teen": "11–17岁", "culture": "文化", "exercises": "练习", "task": "课后任务", "audio": "录音",
           "minutes": "分钟", "co": "听", "eo": "说", "ce": "读", "ee": "写", "warmup": "热身", "present": "讲解", "practice": "操练",
           "produce": "输出", "wrapup": "小结", "say": "老师可以说", "tip": "小班提示", "oral": "口头", "ecrit": "书面",
           "audio_missing": "录音待上传", "script": "录音文本", "check": "提交答案", "again": "再做一次", "score": "得分",
           "correct": "正确答案", "your": "你的答案", "true": "对", "false": "错", "choose": "请选择", "print": "打印",
           "listen_note": "听录音，然后回答。", "best": "最好成绩", "done_at": "完成时间", "no_ex": "这一课还没有可以在线做的练习。",
           "unanswered": "未作答", "saved": "已提交，看看下面的答案。", "lesson": "第{n}课", "unit": "第{n}单元", "colon": "："},
    "fr": {"objectives": "Objectifs", "can_do": "À la fin de la leçon, je sais…", "skills": "Compétences", "exam": "Lien avec l'examen",
           "materials": "Matériel", "vocab": "Vocabulaire", "grammar": "Grammaire", "text": "Texte", "steps": "Déroulé du cours",
           "mistakes": "Erreurs fréquentes", "diff": "Adapter à l'âge", "young": "6–10 ans", "teen": "11–17 ans", "culture": "Culture",
           "exercises": "Exercices", "task": "À faire après le cours", "audio": "Audio", "minutes": "min", "co": "Écouter", "eo": "Parler",
           "ce": "Lire", "ee": "Écrire", "warmup": "Échauffement", "present": "Découverte", "practice": "Entraînement", "produce": "Production",
           "wrapup": "Bilan", "say": "Le professeur peut dire", "tip": "En classe de 5", "oral": "Oral", "ecrit": "Écrit",
           "audio_missing": "audio à venir", "script": "Script", "check": "Vérifier mes réponses", "again": "Recommencer", "score": "Score",
           "correct": "Bonne réponse", "your": "Ta réponse", "true": "Vrai", "false": "Faux", "choose": "Choisis", "print": "Imprimer",
           "listen_note": "Écoute, puis réponds.", "best": "Meilleur score", "done_at": "Fait le", "no_ex": "Pas encore d'exercice en ligne pour cette leçon.",
           "unanswered": "pas de réponse", "saved": "C'est corrigé : regarde les réponses ci-dessous.", "lesson": "Leçon {n}", "unit": "Unité {n}", "colon": " : "},
}

TX = {   # espace élève et parents (langue de la page)
    "zh": {"nav": "我的课本", "lead": "老师上过的课都在这里：生词、语法、课文和练习。可以打印，也可以在线做练习。",
           "none": "还没有可以看的课。上课以后，这里会出现你的课本。", "not_enrolled": "课本只对已报名课程的学员开放。",
           "back": "返回我的课本", "kid_h": "课本和练习", "kid_none": "还没有可以看的课。", "kid_lead": "孩子上过的课和在线练习的成绩。",
           "open": "打开", "ex": "练习", "not_done": "还没做"},
    "fr": {"nav": "Mon manuel", "lead": "Les leçons vues en cours : vocabulaire, grammaire, texte et exercices. À imprimer ou à faire en ligne.",
           "none": "Pas encore de leçon. Elles apparaîtront ici après tes cours.", "not_enrolled": "Le manuel est réservé aux élèves inscrits à un cours.",
           "back": "Retour à mon manuel", "kid_h": "Manuel et exercices", "kid_none": "Pas encore de leçon.", "kid_lead": "Les leçons vues en cours et les résultats aux exercices en ligne.",
           "open": "Ouvrir", "ex": "Exercices", "not_done": "pas encore fait"},
}


def tx():
    return TX.get(getattr(g, "lang", "zh"), TX["zh"])


@web.app.context_processor
def lessons_ctx():
    from liveclasses import PARIS
    return {"lsx": tx(), "LESSON_SITE": SITE, "PARIS_TZ": PARIS}


# ---------- audio ----------

def audio_files(lesson):
    """Pistes du contenu avec leur fichier (s'il a été envoyé)."""
    files = lesson.get("audio_files") or {}
    return {a["id"]: dict(a, file=files.get(a["id"])) for a in (lesson["content"] or {}).get("audio", [])}


@web.app.route("/lecons/<int:lid>/audio/<slot>")
def lesson_audio(lid, slot):
    with connect() as c:
        lesson = c.execute("SELECT * FROM lessons WHERE id=%s", (lid,)).fetchone()
        if not lesson or not can_read(c, lesson):
            abort(404)
    name = (lesson["audio_files"] or {}).get(slot)
    if not name or not AUDIO_RE.fullmatch(name):
        abort(404)
    resp = send_from_directory(UPLOADS, name, conditional=True, max_age=0)
    resp.headers["Cache-Control"] = "private, no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


# ---------- accès ----------

def student_classes(c, st):
    """Classes où l'élève est inscrit (pas l'essai)."""
    return c.execute("""SELECT l.* FROM class_members m JOIN live_classes l ON l.id=m.class_id
                        WHERE m.student_id=%s AND m.status='active' AND m.kind='student'""", (st["id"],)).fetchall()


def visible_for_student(c, st):
    """Leçons publiées visibles par l'élève (voir l'en-tête du module), dans l'ordre du programme."""
    classes = student_classes(c, st)
    if not classes:
        return []
    ids = [x["id"] for x in classes]
    rows = c.execute("""
        SELECT DISTINCT ON (u.level, u.sort, l.sort) l.*, u.level, u.sort AS unit_sort, u.title_fr AS unit_fr, u.title_zh AS unit_zh,
               (SELECT max(a.score * 100 / nullif(a.total, 0)) FROM lesson_attempts a WHERE a.lesson_id=l.id AND a.student_id=%(s)s AND a.finished_at IS NOT NULL) AS best,
               (SELECT max(a.finished_at) FROM lesson_attempts a WHERE a.lesson_id=l.id AND a.student_id=%(s)s) AS last_at
        FROM lessons l JOIN program_units u ON u.id=l.unit_id JOIN live_classes k ON k.level=u.level AND k.id = ANY(%(c)s)
        WHERE l.status='published' AND (
              EXISTS (SELECT 1 FROM class_progress p WHERE p.class_id=k.id AND p.unit_id=u.id)
           OR EXISTS (SELECT 1 FROM class_sessions x WHERE x.class_id=k.id AND x.lesson_id=l.id)
           OR (NOT EXISTS (SELECT 1 FROM class_progress p WHERE p.class_id=k.id)
               AND u.sort = (SELECT min(u2.sort) FROM program_units u2 WHERE u2.level=u.level)))
        ORDER BY u.level, u.sort, l.sort""", {"s": st["id"], "c": ids}).fetchall()
    return rows


def can_read(c, lesson):
    """Fiche et audio : équipe, professeurs (leçons en relecture ou publiées), élève ou parent d'un élève qui voit la leçon."""
    u = U.current()
    if u and u["role"] in U.STAFF:
        return True
    if u and u["role"] == "professeur" and u["teacher_id"]:
        return lesson["status"] in ("review", "published")
    if lesson["status"] != "published":
        return False
    import pupil
    sts = []
    st = pupil.me_student()
    if st:
        sts.append(st)
    if u and u["role"] == "parent":
        sts += c.execute("SELECT * FROM students WHERE user_id=%s AND status='active'", (u["id"],)).fetchall()
    return any(lesson["id"] in {r["id"] for r in visible_for_student(c, s)} for s in sts)


def get_lesson(c, lid):
    return c.execute("""SELECT l.*, u.level, u.sort AS unit_sort, u.title_fr AS unit_fr, u.title_zh AS unit_zh
                        FROM lessons l JOIN program_units u ON u.id=l.unit_id WHERE l.id=%s""", (lid,)).fetchone()


# ---------- exercices ----------

def playable(lesson):
    """Exercices posables en ligne : on retire les écoutes dont le fichier n'est pas encore là. Renvoie [(index d'origine, exercice)]."""
    files = lesson["audio_files"] or {}
    return [(i, x) for i, x in enumerate((lesson["content"] or {}).get("exercises", [])) if not x.get("audio") or files.get(x["audio"])]


def new_perms(items):
    perms = {}
    for i, x in items:
        if x["type"] in ("qcm", "fill"):
            p = list(range(len(x["choices"]))); random.shuffle(p); perms[str(i)] = p
        elif x["type"] == "match":
            p = list(range(len(x["pairs"]))); random.shuffle(p); perms[str(i)] = p
    return perms


def build(items, perms, answers=None):
    """Exercices prêts à afficher (choix dans l'ordre mélangé ; avec les réponses : correction)."""
    out = []
    for i, x in items:
        p = perms.get(str(i))
        d = dict(x, idx=i)
        if x["type"] in ("qcm", "fill"):
            d["shown"] = [x["choices"][k] for k in p]
            if answers is not None:
                a = answers.get(str(i))
                d["picked"] = x["choices"][a] if isinstance(a, int) else None
                d["ok"] = a == x["answer"]
                d["right"] = x["choices"][x["answer"]]
        elif x["type"] == "tf":
            if answers is not None:
                a = answers.get(str(i))
                d["picked"] = a
                d["ok"] = a is x["answer"]
        elif x["type"] == "match":
            d["rights"] = [x["pairs"][k][1] for k in p]
            if answers is not None:
                a = answers.get(str(i)) or {}
                d["rows"] = [{"left": l, "right": r, "picked": x["pairs"][a[str(j)]][1] if isinstance(a.get(str(j)), int) else None,
                              "ok": a.get(str(j)) == j} for j, (l, r) in enumerate(x["pairs"])]
        out.append(d)
    return out


def grade(items, perms, form):
    answers, score, total = {}, 0, 0
    for i, x in items:
        k = str(i)
        if x["type"] in ("qcm", "fill"):
            total += 1
            pos = form.get(f"e{i}", type=int)
            a = perms[k][pos] if pos is not None and 0 <= pos < len(perms[k]) else None
            answers[k] = a
            score += a == x["answer"]
        elif x["type"] == "tf":
            total += 1
            v = form.get(f"e{i}")
            a = True if v == "1" else (False if v == "0" else None)
            answers[k] = a
            score += a is x["answer"]
        elif x["type"] == "match":
            a = {}
            for j in range(len(x["pairs"])):
                total += 1
                pos = form.get(f"e{i}_{j}", type=int)
                a[str(j)] = perms[k][pos] if pos is not None and 0 <= pos < len(perms[k]) else None
                score += a[str(j)] == j
            answers[k] = a
    return answers, score, total


# ---------- élève ----------

def _pupil():
    import pupil
    return pupil, pupil.me_student()


@web.route("/eleve/manuel")
def pupil_lessons():
    pupil, st = _pupil()
    if not st:
        return redirect(url_for("pupil_login"))
    with connect() as c:
        enrolled = bool(student_classes(c, st))
        rows = visible_for_student(c, st)
    return pupil._page("pupil/lessons.html", s=st, rows=rows, enrolled=enrolled, L=LBL[g.lang if g.lang in LBL else "zh"])


@web.route("/eleve/manuel/<int:lid>", methods=["GET", "POST"])
def pupil_lesson(lid):
    pupil, st = _pupil()
    if not st:
        return redirect(url_for("pupil_login"))
    with connect() as c:
        lesson = get_lesson(c, lid)
        if not lesson or lid not in {r["id"] for r in visible_for_student(c, st)}:
            abort(404)
        items = playable(lesson)
        att = c.execute("""SELECT * FROM lesson_attempts WHERE lesson_id=%s AND student_id=%s AND finished_at IS NULL
                           ORDER BY created_at DESC LIMIT 1""", (lid, st["id"])).fetchone()
        result = None
        if request.method == "POST":
            U.check_csrf()
            if request.form.get("action") == "again" or not att:
                c.execute("INSERT INTO lesson_attempts (lesson_id, student_id, perms, total) VALUES (%s,%s,%s,0)",
                          (lid, st["id"], Jsonb(new_perms(items))))
                return redirect(url_for("pupil_lesson", lid=lid) + "#exercices")
            answers, score, total = grade(items, att["perms"], request.form)
            c.execute("UPDATE lesson_attempts SET answers=%s, score=%s, total=%s, finished_at=now() WHERE id=%s",
                      (Jsonb(answers), score, total, att["id"]))
            return redirect(url_for("pupil_lesson", lid=lid, fait=att["id"]) + "#exercices")
        done_id = request.args.get("fait", type=int)
        if done_id:
            result = c.execute("SELECT * FROM lesson_attempts WHERE id=%s AND student_id=%s AND lesson_id=%s AND finished_at IS NOT NULL",
                               (done_id, st["id"], lid)).fetchone()
        if not result and not att and items:
            att = c.execute("INSERT INTO lesson_attempts (lesson_id, student_id, perms, total) VALUES (%s,%s,%s,0) RETURNING *",
                            (lid, st["id"], Jsonb(new_perms(items)))).fetchone()
        history = c.execute("""SELECT score, total, finished_at FROM lesson_attempts WHERE lesson_id=%s AND student_id=%s AND finished_at IS NOT NULL
                               ORDER BY finished_at DESC LIMIT 5""", (lid, st["id"])).fetchall()
    ex = build(items, result["perms"], result["answers"]) if result else (build(items, att["perms"]) if att else [])
    return pupil._page("pupil/lesson.html", s=st, l=lesson, c=lesson["content"], audio=audio_files(lesson), L=LBL[g.lang if g.lang in LBL else "zh"],
                       ex=ex, result=result, history=history, mode="pupil")


# ---------- parent ----------

def kid_lessons(c, st):
    return visible_for_student(c, st)


@web.route("/compte/enfants/<int:sid>/manuel/<int:lid>")
def family_lesson(sid, lid):
    u = U.current()
    if not u or u["role"] != "parent":
        return redirect(url_for("account_login", next=request.path))
    with connect() as c:
        st = c.execute("SELECT * FROM students WHERE id=%s AND user_id=%s AND status='active'", (sid, u["id"])).fetchone()
        if not st:
            abort(404)
        lesson = get_lesson(c, lid)
        if not lesson or lid not in {r["id"] for r in visible_for_student(c, st)}:
            abort(404)
        history = c.execute("""SELECT score, total, finished_at FROM lesson_attempts WHERE lesson_id=%s AND student_id=%s AND finished_at IS NOT NULL
                               ORDER BY finished_at DESC LIMIT 5""", (lid, sid)).fetchall()
    import pupil
    return pupil._page("pupil/lesson.html", s=st, l=lesson, c=lesson["content"], audio=audio_files(lesson), L=LBL[g.lang if g.lang in LBL else "zh"],
                       ex=[], result=None, history=history, mode="parent")


# ---------- professeur ----------

def _levels_param():
    lv = request.args.get("niveau")
    return lv if lv in LEVELS else None


@espace_bp.route("/lecons")
def lessons_teacher():
    u = teacher_current()
    with connect() as c:
        level = _levels_param()
        if not level:
            r = c.execute("SELECT level FROM live_classes WHERE teacher_id=%s ORDER BY id LIMIT 1", (u["teacher_id"],)).fetchone()
            level = r["level"] if r and r["level"] in LEVELS else LEVELS[0]
        units = c.execute("SELECT * FROM program_units WHERE level=%s ORDER BY sort", (level,)).fetchall()
        rows = c.execute("""SELECT l.id, l.unit_id, l.sort, l.title_fr, l.title_zh, l.status,
                                   (SELECT count(*) FROM lesson_comments k WHERE k.lesson_id=l.id AND k.resolved_at IS NULL) AS open_comments
                            FROM lessons l JOIN program_units u ON u.id=l.unit_id WHERE u.level=%s AND l.status IN ('review','published')
                            ORDER BY l.sort""", (level,)).fetchall()
    by_unit = {}
    for r in rows:
        by_unit.setdefault(r["unit_id"], []).append(r)
    return render_template("espace/lessons.html", level=level, levels=LEVELS, units=units, by_unit=by_unit, statuses=STATUSES)


@espace_bp.route("/lecons/<int:lid>", methods=["GET", "POST"])
def lesson_teacher(lid):
    u = teacher_current()
    with connect() as c:
        lesson = get_lesson(c, lid)
        if not lesson or lesson["status"] not in ("review", "published"):
            abort(404)
        if request.method == "POST":
            U.check_csrf()
            body = (request.form.get("body") or "").strip()[:4000]
            if body:
                c.execute("INSERT INTO lesson_comments (lesson_id, user_id, body) VALUES (%s,%s,%s)", (lid, u["id"], body))
            return redirect(url_for("espace.lesson_teacher", lid=lid, ok=1) + "#remarques")
        comments = _comments(c, lid)
        classes = c.execute("SELECT id, level FROM live_classes WHERE teacher_id=%s AND level=%s AND status <> 'closed' ORDER BY id",
                            (u["teacher_id"], lesson["level"])).fetchall()
    return render_template("espace/lesson.html", l=lesson, c=lesson["content"], audio=audio_files(lesson), L=LBL[SITE["guide"]],
                           S=LBL[SITE["sheet"]], comments=comments, statuses=STATUSES, classes=classes, ok=request.args.get("ok"),
                           ex=build(list(enumerate(lesson["content"].get("exercises", []))),
                                    {str(i): list(range(len(x.get("choices") or x.get("pairs") or []))) for i, x in enumerate(lesson["content"].get("exercises", []))}))


def lesson_prefill(c, lid, level):
    """Formulaire « Donner un devoir » rempli d'après la tâche d'une leçon (page de la classe, ?lecon=)."""
    lesson = get_lesson(c, lid)
    if not lesson or lesson["level"] != level or lesson["status"] not in ("review", "published"):
        return None
    tk = lesson["content"].get("task") or {}
    if not tk.get("instr"):
        return None
    title = (tk.get("title") or (lesson["title_zh"] if SITE["guide"] == "zh" else lesson["title_fr"]))[:200]
    instr = "\n\n".join(x for x in (tk.get("instr"), tk.get("instr_guide")) if x)
    return {"id": None, "unit_id": lesson["unit_id"], "title": title, "instructions": instr[:4000], "file_name": None}


def lessons_for_unit(c, unit_id, statuses=("review", "published")):
    return c.execute("SELECT id, sort, title_fr, title_zh, status FROM lessons WHERE unit_id=%s AND status = ANY(%s) ORDER BY sort",
                     (unit_id, list(statuses))).fetchall()


def _comments(c, lid):
    return c.execute("""SELECT k.*, u.name, u.role FROM lesson_comments k LEFT JOIN users u ON u.id=k.user_id
                        WHERE k.lesson_id=%s ORDER BY k.resolved_at IS NOT NULL, k.created_at""", (lid,)).fetchall()


# ---------- administration ----------

@admin_bp.route("/lecons")
def lessons_admin():
    level = _levels_param() or LEVELS[0]
    with connect() as c:
        units = c.execute("SELECT * FROM program_units WHERE level=%s ORDER BY sort", (level,)).fetchall()
        rows = c.execute("""SELECT l.id, l.unit_id, l.sort, l.title_fr, l.title_zh, l.status, l.updated_at,
                                   (SELECT count(*) FROM lesson_comments k WHERE k.lesson_id=l.id AND k.resolved_at IS NULL) AS open_comments
                            FROM lessons l JOIN program_units u ON u.id=l.unit_id WHERE u.level=%s ORDER BY l.sort""", (level,)).fetchall()
        counts = {(r["level"], r["status"]): r["n"] for r in c.execute(
            "SELECT u.level, l.status, count(*) AS n FROM lessons l JOIN program_units u ON u.id=l.unit_id GROUP BY 1, 2").fetchall()}
    by_unit = {}
    for r in rows:
        by_unit.setdefault(r["unit_id"], []).append(r)
    return render_template("admin/lessons.html", level=level, levels=LEVELS, units=units, by_unit=by_unit, counts=counts, statuses=STATUSES,
                           ok=request.args.get("ok"))


@admin_bp.route("/lecons/nouvelle", methods=["POST"])
def lesson_new():
    _check_csrf()
    unit_id = request.form.get("unit_id", type=int)
    with connect() as c:
        if not c.execute("SELECT 1 FROM program_units WHERE id=%s", (unit_id,)).fetchone():
            abort(400)
        sort = c.execute("SELECT coalesce(max(sort), 0) + 1 AS s FROM lessons WHERE unit_id=%s", (unit_id,)).fetchone()["s"]
        lid = c.execute("""INSERT INTO lessons (unit_id, sort, title_fr, title_zh, content, updated_by) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (unit_id, sort, "Nouvelle leçon", "新课", Jsonb(SKELETON), U.current()["id"])).fetchone()["id"]
    return redirect(url_for("admin.lesson_admin", lid=lid))


def _save_audio(lid, slot, f):
    head = f.stream.read(16)
    ext = "mp3" if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") else ("m4a" if head[4:8] == b"ftyp" else None)
    if not ext:
        raise ValueError("format")
    os.makedirs(UPLOADS, exist_ok=True)
    name = f"l{lid}-{slot}-{secrets.token_hex(6)}.{ext}"
    path, size = os.path.join(UPLOADS, name), len(head)
    with open(path, "wb") as out:
        out.write(head)
        while chunk := f.stream.read(1024 * 1024):
            size += len(chunk)
            if size > AUDIO_MAX:
                out.close(); os.remove(path)
                raise ValueError("size")
            out.write(chunk)
    return name


def _remove_audio(name):
    if name and AUDIO_RE.fullmatch(name):
        try:
            os.remove(os.path.join(UPLOADS, name))
        except FileNotFoundError:
            pass


@web.app.before_request
def lesson_upload_size():
    if request.endpoint == "admin.lesson_admin" and request.method == "POST":
        request.max_content_length = AUDIO_MAX + 1024 * 1024


@admin_bp.route("/lecons/<int:lid>", methods=["GET", "POST"])
def lesson_admin(lid):
    errors, raw = [], None
    with connect() as c:
        lesson = get_lesson(c, lid)
        if not lesson:
            abort(404)
        me = U.current()
        if request.method == "POST":
            _check_csrf()
            act = request.form.get("action")
            if act == "save":
                raw = request.form.get("content", "")
                try:
                    content = json.loads(raw)
                except ValueError as ex:
                    errors.append(f"JSON invalide : {ex}")
                    content = None
                if content is not None:
                    errors += validate(content)
                tf, tz = (request.form.get("title_fr") or "").strip()[:200], (request.form.get("title_zh") or "").strip()[:200]
                if not tf or not tz:
                    errors.append("Les deux titres sont obligatoires.")
                unit_id = request.form.get("unit_id", type=int)
                sort = request.form.get("sort", type=int)
                if not c.execute("SELECT 1 FROM program_units WHERE id=%s", (unit_id,)).fetchone() or not sort or sort < 1:
                    errors.append("Unité ou numéro de leçon invalide.")
                if not errors:
                    c.execute("""UPDATE lessons SET content=%s, title_fr=%s, title_zh=%s, unit_id=%s, sort=%s, updated_at=now(), updated_by=%s,
                                 edited=true WHERE id=%s""", (Jsonb(content), tf, tz, unit_id, sort, me["id"], lid))
                    return redirect(url_for("admin.lesson_admin", lid=lid, ok="Leçon enregistrée."))
            elif act == "status" and request.form.get("status") in STATUSES:
                st = request.form["status"]
                if st == "published" and validate(lesson["content"]):
                    errors.append("Le contenu a des erreurs : corrigez-les avant de publier.")
                else:
                    c.execute("""UPDATE lessons SET status=%s, published_at=CASE WHEN %s='published' THEN now() ELSE published_at END,
                                 published_by=CASE WHEN %s='published' THEN %s ELSE published_by END, updated_at=now() WHERE id=%s""",
                              (st, st, st, me["id"], lid))
                    return redirect(url_for("admin.lesson_admin", lid=lid, ok=f"État : {STATUSES[st]}."))
            elif act == "comment":
                body = (request.form.get("body") or "").strip()[:4000]
                if body:
                    c.execute("INSERT INTO lesson_comments (lesson_id, user_id, body) VALUES (%s,%s,%s)", (lid, me["id"], body))
                return redirect(url_for("admin.lesson_admin", lid=lid) + "#remarques")
            elif act == "resolve":
                c.execute("UPDATE lesson_comments SET resolved_at=CASE WHEN resolved_at IS NULL THEN now() END WHERE id=%s AND lesson_id=%s",
                          (request.form.get("cid", type=int), lid))
                return redirect(url_for("admin.lesson_admin", lid=lid) + "#remarques")
            elif act in ("audio", "audio_remove"):
                slot = request.form.get("slot", "")
                if slot not in audio_files(lesson):
                    abort(400)
                files = dict(lesson["audio_files"] or {})
                if act == "audio":
                    f = request.files.get("file")
                    try:
                        if not f or not f.filename:
                            raise ValueError("vide")
                        name = _save_audio(lid, slot, f)
                    except ValueError as ex:
                        errors.append({"format": "Audio refusé : MP3 ou M4A.", "size": "Audio trop lourd (15 Mo au plus).", "vide": "Choisissez un fichier."}[str(ex)])
                    else:
                        _remove_audio(files.get(slot))
                        files[slot] = name
                        c.execute("UPDATE lessons SET audio_files=%s WHERE id=%s", (Jsonb(files), lid))
                        return redirect(url_for("admin.lesson_admin", lid=lid, ok="Audio envoyé.") + "#audio")
                else:
                    _remove_audio(files.pop(slot, None))
                    c.execute("UPDATE lessons SET audio_files=%s WHERE id=%s", (Jsonb(files), lid))
                    return redirect(url_for("admin.lesson_admin", lid=lid, ok="Audio retiré.") + "#audio")
            elif act == "delete" and U.is_admin():
                for name in (lesson["audio_files"] or {}).values():
                    _remove_audio(name)
                level = lesson["level"]
                c.execute("DELETE FROM lessons WHERE id=%s", (lid,))
                return redirect(url_for("admin.lessons_admin", niveau=level, ok="Leçon supprimée."))
        comments = _comments(c, lid)
        units = c.execute("SELECT id, level, sort, title_fr FROM program_units ORDER BY level, sort").fetchall()
        lesson = get_lesson(c, lid)
    content = lesson["content"]
    items = list(enumerate(content.get("exercises", [])))
    return render_template("admin/lesson.html", l=lesson, c=content, raw=raw if raw is not None else dumps(content), errors=errors,
                           problems=validate(content), statuses=STATUSES, comments=comments, units=units, audio=audio_files(lesson),
                           L=LBL[SITE["guide"]], S=LBL[SITE["sheet"]], ok=request.args.get("ok"),
                           ex=build(items, {str(i): list(range(len(x.get("choices") or x.get("pairs") or []))) for i, x in items}))
