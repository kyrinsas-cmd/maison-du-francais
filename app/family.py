"""Espace famille : « 我的孩子 / Mes enfants » (/compte/enfants) — décidé le 2026-11-09.

- Un compte parent déclare ses enfants une fois (prénom ou pseudo, âge) ; le test de niveau part ensuite d'un enfant de la liste
  (plus de prénom retapé, plus de doublons). Le niveau et les classes sont fixés par l'équipe (lecture seule ici).
- Un compte élève (15 ans et plus) n'a qu'une fiche : la sienne (« 我的学习 / Mon apprentissage »).
- Page d'un enfant : niveau, classes, prochains cours (entrer, signaler une absence), bilans, tests de niveau.
"""
from flask import abort, g, redirect, render_template, request, url_for

import users as U
import web
from db import connect

TX = {
    "zh": {"kids": "我的孩子", "me": "我的学习", "add": "添加孩子", "name": "孩子的昵称（不要填写全名）", "age": "年龄", "save": "保存",
           "added": "已添加。现在可以为孩子参加水平测试。", "saved": "已保存。", "dup": "已经有一个孩子用这个名字。", "err_name": "请填写孩子的昵称。",
           "err_age": "请填写正确的年龄（3–99）。", "empty": "还没有添加孩子。添加以后，可以为每个孩子参加水平测试，查看他的课程和课后报告。",
           "level": "级别", "level_none": "等待老师评估", "classes": "班级", "no_class": "还没有分班，老师评估水平以后会推荐班级。",
           "trial": "试听", "next": "下一节课", "courses": "直播课", "reports": "课后报告", "tests": "水平测试", "no_tests": "还没有参加水平测试。",
           "take_test": "参加水平测试", "view": "查看", "edit": "修改资料", "back": "我的孩子", "age_unit": "{a}岁",
           "remove": "删除", "remove_confirm": "确定删除这个孩子吗？", "removed": "已删除。", "cant_remove": "这个孩子已经有测试或课程，不能删除。如需修改，请联系我们。",
           "bj": "北京时间"},
    "fr": {"kids": "Mes enfants", "me": "Mon apprentissage", "add": "Ajouter un enfant", "name": "Prénom ou pseudo de l'enfant (pas de nom complet)", "age": "Âge",
           "save": "Enregistrer", "added": "Enfant ajouté. Vous pouvez maintenant lui faire passer le test de niveau.", "saved": "Enregistré.",
           "dup": "Un enfant porte déjà ce prénom.", "err_name": "Indiquez le prénom ou le pseudo de l'enfant.", "err_age": "Indiquez un âge valide (3 à 99).",
           "empty": "Aucun enfant pour l'instant. Ajoutez-en un pour lui faire passer le test de niveau et suivre ses cours et ses bilans.",
           "level": "Niveau", "level_none": "En attente d'évaluation", "classes": "Classes", "no_class": "Pas encore de classe : le professeur en proposera une après le test de niveau.",
           "trial": "essai", "next": "Prochain cours", "courses": "Cours en direct", "reports": "Bilans des cours", "tests": "Tests de niveau",
           "no_tests": "Pas encore de test de niveau.", "take_test": "Passer le test de niveau", "view": "Voir", "edit": "Modifier", "back": "Mes enfants",
           "age_unit": "{a} ans", "remove": "Supprimer", "remove_confirm": "Supprimer cet enfant ?", "removed": "Supprimé.",
           "cant_remove": "Cet enfant a déjà des tests ou des cours : il ne peut pas être supprimé. Écrivez-nous pour toute correction.", "bj": "Pékin"},
}


def _nostore(html):
    resp = web.app.make_response(html)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


def tx():
    return TX[g.lang]


def kids_of(u):
    """Enfants (compte parent) ou fiche personnelle (compte élève, créée au besoin), avec niveau et classes."""
    import students as ST
    with connect() as c:
        if u["role"] == "eleve":
            ST.ensure_student(c, u["id"], u["name"])
        rows = c.execute("""SELECT s.*,
                  (SELECT json_agg(json_build_object('level', l.level, 'kind', m.kind, 'teacher', t.first_name, 'start', to_char(l.start_bj, 'HH24:MI'), 'days', l.days)
                                   ORDER BY l.level)
                     FROM class_members m JOIN live_classes l ON l.id=m.class_id LEFT JOIN teachers t ON t.id=l.teacher_id
                    WHERE m.student_id=s.id AND m.status='active') AS classes
                  FROM students s WHERE s.user_id=%s AND s.status='active' ORDER BY s.created_at""", (u["id"],)).fetchall()
    return rows


@web.app.context_processor
def family_ctx():
    return {"fam": TX.get(getattr(g, "lang", "zh"), TX["zh"]), "kids_of": kids_of}


def _family_user():
    u = U.current()
    if not u:
        return None, redirect(url_for("account_login", next=request.path))
    if u["role"] not in ("parent", "eleve"):
        return None, redirect(url_for("account_home"))
    return u, None


@web.route("/compte/enfants", methods=["GET", "POST"])
def family_kids():
    u, resp = _family_user()
    if resp:
        return resp
    T = tx()
    kids = kids_of(u)
    if u["role"] == "eleve":                       # un compte élève n'a que sa propre fiche
        return redirect(url_for("family_kid", sid=kids[0]["id"]))
    errors, form = [], {}
    if request.method == "POST":
        U.check_csrf()
        form = {"name": (request.form.get("name") or "").strip()[:40], "age": (request.form.get("age") or "").strip()}
        age = int(form["age"]) if form["age"].isdigit() and 3 <= int(form["age"]) <= 99 else None
        if not form["name"]:
            errors.append(T["err_name"])
        if not age:
            errors.append(T["err_age"])
        if not errors:
            with connect() as c:
                if c.execute("SELECT 1 FROM students WHERE user_id=%s AND lower(first_name)=lower(%s)", (u["id"], form["name"])).fetchone():
                    errors.append(T["dup"])
                else:
                    c.execute("INSERT INTO students (user_id, first_name, age) VALUES (%s,%s,%s)", (u["id"], form["name"], age))
                    return redirect(url_for("family_kids", ok="added"))
    return _nostore(render_template("family/kids.html", u=u, kids=kids, errors=errors, form=form, ok=request.args.get("ok")))


@web.route("/compte/enfants/<int:sid>", methods=["GET", "POST"])
def family_kid(sid):
    u, resp = _family_user()
    if resp:
        return resp
    T = tx()
    errors = []
    with connect() as c:
        s = c.execute("SELECT * FROM students WHERE id=%s AND user_id=%s AND status='active'", (sid, u["id"])).fetchone()
        if not s:
            abort(404)
        used = c.execute("""SELECT EXISTS (SELECT 1 FROM placement_tests WHERE student_id=%(s)s)
                                OR EXISTS (SELECT 1 FROM class_members WHERE student_id=%(s)s) AS used""", {"s": sid}).fetchone()["used"]
        if request.method == "POST":
            U.check_csrf()
            if request.form.get("action") == "remove" and u["role"] == "parent":
                if used:
                    errors.append(T["cant_remove"])
                else:
                    c.execute("DELETE FROM students WHERE id=%s AND user_id=%s", (sid, u["id"]))
                    return redirect(url_for("family_kids", ok="removed"))
            else:
                name = (request.form.get("name") or "").strip()[:40] if u["role"] == "parent" else s["first_name"]
                age_s = (request.form.get("age") or "").strip()
                age = int(age_s) if age_s.isdigit() and 3 <= int(age_s) <= 99 else None
                if not name:
                    errors.append(T["err_name"])
                elif not age:
                    errors.append(T["err_age"])
                elif c.execute("SELECT 1 FROM students WHERE user_id=%s AND lower(first_name)=lower(%s) AND id<>%s", (u["id"], name, sid)).fetchone():
                    errors.append(T["dup"])
                else:
                    c.execute("UPDATE students SET first_name=%s, age=%s, updated_at=now() WHERE id=%s", (name, age, sid))
                    c.execute("UPDATE class_members SET child_label=%s WHERE student_id=%s", (name, sid))
                    return redirect(url_for("family_kid", sid=sid, ok="saved"))
        tests = c.execute("""SELECT t.*, (SELECT count(*) FROM placement_recordings r WHERE r.test_id=t.id) AS n_rec FROM placement_tests t
                             WHERE t.student_id=%s ORDER BY t.created_at DESC""", (sid,)).fetchall()
    import classroom
    kid = next((k for k in kids_of(u) if k["id"] == sid), s)
    import placement
    return _nostore(render_template("family/kid.html", u=u, s=s, kid=kid, p=placement.pt(g.lang), tests=tests, used=used, errors=errors, ok=request.args.get("ok"),
                                        sessions=classroom.my_sessions(u, limit=60, student_id=sid), reports=classroom.my_reports(u, limit=60, student_id=sid)))
