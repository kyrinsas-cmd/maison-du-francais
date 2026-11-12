"""Espace élève : 练习题 (exercices) et 模拟考试 (examen blanc) — 2026-11-12.
Questions tirées de la banque du test de niveau (placement_items, questions actives ; écoute seulement si l'audio existe).
- Exercices : 10 questions d'un niveau et d'une rubrique (ou mélangées), correction tout de suite, sans limite de temps.
- Examen blanc : 30 questions d'un niveau (écoute, lecture, vocabulaire, grammaire), 30 minutes, note sur 100.
  Ce n'est pas un DELF : seulement la partie à choix multiples, pas de production écrite ni orale.
Chaque essai est enregistré (pupil_quizzes) : historique de l'élève et statistiques."""
import random
from datetime import datetime, timedelta, timezone

from flask import abort, redirect, request, url_for
from psycopg.types.json import Jsonb

import pupil as P
import users as U
import web
from db import connect
from placement import LEVELS

SECTIONS = ("vocab", "grammar", "reading", "listening")
PRACTICE_N = 10
MOCK = {"listening": 3, "reading": 9, "vocab": 9, "grammar": 9}     # 30 questions
MOCK_MINUTES = 30

TX = {
    "zh": {"nav_ex": "练习题", "nav_mock": "模拟考试", "ex_lead": "选择级别和题型，每次10道题，做完马上看到答案。",
           "mock_lead": "模拟考试：30道选择题（听力、阅读、词汇、语法），限时30分钟，满分100分。只包括选择题部分，不包括写作和口语。",
           "level": "级别", "section": "题型", "mixed": "综合", "start": "开始练习", "start_mock": "开始考试", "history": "我的记录",
           "none": "还没有记录。", "vocab": "词汇", "grammar": "语法", "reading": "阅读", "listening": "听力", "submit": "交卷",
           "result": "结果", "score": "得分", "correct": "正确答案", "your": "你的答案", "again": "再练一次", "back": "返回",
           "time_left": "剩余时间", "time_up": "时间到了，答卷已自动提交。", "late": "超时提交", "unanswered": "未作答",
           "answered": "已答", "read_text": "阅读下面的短文：", "listen": "听录音", "pass": "达到50分", "fail": "未达到50分",
           "in_progress": "未完成", "continue": "继续", "date": "日期", "kind": "类型", "per_section": "各部分得分",
           "no_items": "这个级别暂时没有足够的题目。", "st_h": "练习和模拟考试", "st_done": "完成次数", "st_acc": "练习正确率",
           "st_best": "模拟考试最好成绩", "st_month": "本月练习次数", "st_skills": "各项正确率", "st_weak": "最需要加强：{s}。可以多做这类练习题。",
           "st_mocks": "模拟考试成绩", "st_levels": "按级别", "st_mock_n": "模拟考试", "st_none": "做完第一次练习题或模拟考试以后，这里会显示你的成绩。",
           "st_trend_up": "比上一次提高了 {n} 分", "st_trend_down": "比上一次低了 {n} 分", "st_trend_same": "和上一次一样", "times": "次", "acc": "正确率", "confirm_submit": "确定交卷吗？还有题目没有作答。"},
    "fr": {"nav_ex": "Exercices", "nav_mock": "Examen blanc", "ex_lead": "Choisis un niveau et un type de questions : 10 questions, la correction s'affiche tout de suite.",
           "mock_lead": "Examen blanc : 30 questions à choix multiples (écoute, lecture, vocabulaire, grammaire) en 30 minutes, noté sur 100. Seulement la partie QCM : ni production écrite ni oral.",
           "level": "Niveau", "section": "Type", "mixed": "Tout mélangé", "start": "Commencer", "start_mock": "Commencer l'examen", "history": "Mes résultats",
           "none": "Pas encore de résultat.", "vocab": "Vocabulaire", "grammar": "Grammaire", "reading": "Lecture", "listening": "Écoute", "submit": "Rendre",
           "result": "Résultat", "score": "Score", "correct": "Bonne réponse", "your": "Ta réponse", "again": "Recommencer", "back": "Retour",
           "time_left": "Temps restant", "time_up": "Temps écoulé : ta copie a été rendue automatiquement.", "late": "rendu en retard", "unanswered": "pas de réponse",
           "answered": "Répondu", "read_text": "Lis le texte :", "listen": "Écouter", "pass": "50 points atteints", "fail": "Moins de 50 points",
           "in_progress": "pas terminé", "continue": "Reprendre", "date": "Date", "kind": "Type", "per_section": "Par partie",
           "no_items": "Pas assez de questions pour ce niveau pour l'instant.", "st_h": "Exercices et examens blancs", "st_done": "Essais terminés",
           "st_acc": "Réussite aux exercices", "st_best": "Meilleur examen blanc", "st_month": "Essais ce mois-ci", "st_skills": "Réussite par rubrique",
           "st_weak": "À travailler en priorité : {s}. Fais davantage d'exercices de ce type.", "st_mocks": "Résultats des examens blancs", "st_levels": "Par niveau",
           "st_mock_n": "Examens blancs", "st_none": "Tes résultats s'afficheront ici après ton premier exercice ou examen blanc.",
           "st_trend_up": "{n} points de plus que la fois précédente", "st_trend_down": "{n} points de moins que la fois précédente", "st_trend_same": "comme la fois précédente", "times": "essai(s)", "acc": "Réussite", "confirm_submit": "Rendre la copie ? Certaines questions n'ont pas de réponse."},
}


def tx():
    from flask import g
    return TX.get(getattr(g, "lang", "zh"), TX["zh"])


@web.app.context_processor
def practice_ctx():
    return {"prx": tx()}


def _pool(c, level, section=None):
    q = """SELECT * FROM placement_items WHERE level=%s AND active AND (section <> 'listening' OR audio_file IS NOT NULL)"""
    args = [level]
    if section:
        q += " AND section=%s"
        args.append(section)
    return c.execute(q + " ORDER BY id", args).fetchall()


def _pick(rnd, pool, n):
    """n questions ; une question de lecture vient avec les autres questions du même texte (le texte n'est lu qu'une fois)."""
    reading = [it for it in pool if it["passage"]]
    other = [it for it in pool if not it["passage"]]
    by_passage = {}
    for it in reading:
        by_passage.setdefault(it["passage"], []).append(it)
    groups = [[it] for it in other] + list(by_passage.values())
    rnd.shuffle(groups)
    out = []
    for g_ in groups:
        if len(out) >= n:
            break
        out += g_[:n - len(out)]
    return out


def _new_quiz(c, st, kind, level, section):
    rnd = random.Random()
    order = {s: i for i, s in enumerate(("listening", "reading", "vocab", "grammar"))}
    if kind == "mock":
        items = []
        for sec, n in MOCK.items():
            items += _pick(rnd, _pool(c, level, sec), n)
    else:
        items = _pick(rnd, _pool(c, level, section), PRACTICE_N)
    if not items:
        return None
    items.sort(key=lambda it: (order[it["section"]], it["passage"] or "", it["id"]))
    perms = {}
    for it in items:
        p = list(range(len(it["options"])))
        rnd.shuffle(p)
        perms[str(it["id"])] = p
    return c.execute("""INSERT INTO pupil_quizzes (student_id, kind, level, section, item_ids, perms, total, deadline)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                     (st["id"], kind, level, section, Jsonb([it["id"] for it in items]), Jsonb(perms), len(items),
                      datetime.now(timezone.utc) + timedelta(minutes=MOCK_MINUTES) if kind == "mock" else None)).fetchone()["id"]


def _history(c, st, kind):
    return c.execute("""SELECT * FROM pupil_quizzes WHERE student_id=%s AND kind=%s ORDER BY created_at DESC LIMIT 30""", (st["id"], kind)).fetchall()


def _default_level(st):
    lv = (st.get("level") or "A1")[:2]
    return lv if lv in LEVELS else "A1"


@web.route("/eleve/exercices", methods=["GET", "POST"])
def pupil_practice():
    return _home("practice")


@web.route("/eleve/examen-blanc", methods=["GET", "POST"])
def pupil_mock():
    return _home("mock")


def _home(kind):
    st, resp = P._need()
    if resp:
        return resp
    error = None
    with connect() as c:
        if request.method == "POST":
            U.check_csrf()
            level = request.form.get("level")
            section = request.form.get("section") or None
            if level not in LEVELS or (section and section not in SECTIONS) or (kind == "mock" and section):
                abort(400)
            qid = _new_quiz(c, st, kind, level, section)
            if qid:
                return redirect(url_for("pupil_quiz", qid=qid), code=303)
            error = tx()["no_items"]
        hist = _history(c, st, kind)
    return P._page("pupil/practice.html", s=st, kind=kind, hist=hist, levels=LEVELS, sections=SECTIONS,
                   level=_default_level(st), error=error, mock_minutes=MOCK_MINUTES)


def _grade(c, q, items, form):
    """Note la copie : la réponse envoyée est la position affichée, convertie avec l'ordre mélangé de l'essai."""
    answers, by_sec, score = {}, {}, 0
    for it in items:
        perm = q["perms"][str(it["id"])]
        raw = form.get(f"q{it['id']}")
        a = perm[int(raw)] if raw is not None and raw.isdigit() and int(raw) < len(perm) else None
        answers[str(it["id"])] = a
        ok = a == it["answer"]
        score += ok
        s = by_sec.setdefault(it["section"], [0, 0])
        s[0] += ok
        s[1] += 1
    late = bool(q["deadline"] and datetime.now(timezone.utc) > q["deadline"] + timedelta(minutes=2))
    c.execute("""UPDATE pupil_quizzes SET answers=%s, score=%s, by_section=%s, finished_at=now(), late=%s WHERE id=%s""",
              (Jsonb(answers), score, Jsonb(by_sec), late, q["id"]))


@web.route("/eleve/exercices/<int:qid>", methods=["GET", "POST"])
def pupil_quiz(qid):
    st, resp = P._need()
    if resp:
        return resp
    from placement import AUDIO_DIR  # noqa: F401  (les audios passent par placement_audio)
    with connect() as c:
        q = c.execute("SELECT * FROM pupil_quizzes WHERE id=%s AND student_id=%s", (qid, st["id"])).fetchone()
        if not q:
            abort(404)
        rows = {r["id"]: r for r in c.execute("SELECT * FROM placement_items WHERE id = ANY(%s)", (list(q["item_ids"]),)).fetchall()}
        items = [rows[i] for i in q["item_ids"] if i in rows]
        if request.method == "POST" and q["finished_at"] is None:
            U.check_csrf()
            _grade(c, q, items, request.form)
            return redirect(url_for("pupil_quiz", qid=qid), code=303)
    view, seen = [], set()
    for it in items:
        perm = q["perms"][str(it["id"])]
        mine = (q["answers"] or {}).get(str(it["id"])) if q["finished_at"] else None
        view.append(dict(it, choices=[(k, perm[k], it["options"][perm[k]]) for k in range(len(perm))], mine=mine,
                         audio=url_for("placement_audio", name=it["audio_file"]) if it["audio_file"] else None,
                         show_passage=bool(it["passage"]) and it["passage"] not in seen))
        if it["passage"]:
            seen.add(it["passage"])
    left = None
    if q["deadline"] and q["finished_at"] is None:
        left = max(0, int((q["deadline"] - datetime.now(timezone.utc)).total_seconds()))
    return P._page("pupil/quiz.html", s=st, q=q, items=view, left=left, sections=SECTIONS)


def practice_stats(c, st):
    """Statistiques des exercices et examens blancs terminés : totaux, réussite par rubrique et par niveau, suite des examens blancs."""
    rows = c.execute("""SELECT * FROM pupil_quizzes WHERE student_id=%s AND finished_at IS NOT NULL ORDER BY finished_at""", (st["id"],)).fetchall()
    pct = lambda a, b: round(100 * a / b) if b else None
    out = {"n": len(rows), "kinds": {}, "skills": [], "levels": [], "mocks": [], "weak": None, "month": 0}
    by_skill, by_level = {}, {}
    month0 = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for r in rows:
        k = out["kinds"].setdefault(r["kind"], {"n": 0, "good": 0, "total": 0, "best": None})
        k["n"] += 1
        k["good"] += r["score"]
        k["total"] += r["total"]
        p = pct(r["score"], r["total"])
        k["best"] = p if k["best"] is None else max(k["best"], p)
        out["month"] += r["finished_at"] >= month0
        for sec, (g_, t_) in (r["by_section"] or {}).items():
            a = by_skill.setdefault(sec, [0, 0])
            a[0] += g_
            a[1] += t_
        lv = by_level.setdefault(r["level"], {"level": r["level"], "practice": 0, "good": 0, "total": 0, "mock_best": None, "mock_n": 0})
        lv["good"] += r["score"]
        lv["total"] += r["total"]
        if r["kind"] == "mock":
            lv["mock_n"] += 1
            lv["mock_best"] = p if lv["mock_best"] is None else max(lv["mock_best"], p)
            out["mocks"].append({"date": r["finished_at"], "level": r["level"], "pct": p, "late": r["late"]})
        else:
            lv["practice"] += 1
    for k in out["kinds"].values():
        k["pct"] = pct(k["good"], k["total"])
    out["skills"] = [{"sec": sec, "good": by_skill[sec][0], "total": by_skill[sec][1], "pct": pct(*by_skill[sec])} for sec in SECTIONS if sec in by_skill]
    enough = [x for x in out["skills"] if x["total"] >= 5]
    if len(enough) >= 2:
        out["weak"] = min(enough, key=lambda x: x["pct"])["sec"]
    out["levels"] = [dict(v, pct=pct(v["good"], v["total"])) for lv in LEVELS for v in [by_level.get(lv)] if v]
    out["mocks"] = out["mocks"][-10:]
    if len(out["mocks"]) >= 2:
        out["trend"] = out["mocks"][-1]["pct"] - out["mocks"][-2]["pct"]
    return out
