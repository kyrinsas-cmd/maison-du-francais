"""Comptes élèves (enfants) : créés par le parent depuis « 我的孩子 », connexion avec un identifiant généré par le site + mot de passe.

Décidé le 2026-11-09 :
- identifiant unique « MF » + 6 chiffres tirés au hasard (pas de numéro qui se suive), aucun e-mail pour l'enfant ;
- mot de passe choisi par le parent (7 caractères au moins, comme les autres comptes), qu'il peut changer ; il peut aussi désactiver le compte ;
- l'élève se connecte sur /eleve/connexion (session « student_sid », séparée des comptes adultes) ;
- son espace : ses prochains cours et l'entrée en classe ; les devoirs s'y ajouteront (rendus par l'élève seulement, note sur 20).
Les élèves de 15 ans et plus qui ont leur propre compte (rôle « eleve », e-mail) ne sont pas concernés.
"""
import secrets

from flask import abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import users as U
import web
from db import connect

MIN_PW = 7

TX = {
    "zh": {"login_h": "学生登录", "login_lead": "用父母在「我的孩子」里为你创建的学生编号和密码登录。", "id": "学生编号", "pw": "密码", "login": "登录",
           "err": "学生编号或密码不正确。", "too_many": "尝试次数过多，请15分钟后再试。", "parent_link": "家长或老师？用电子邮箱登录",
           "space": "学生空间", "hello": "{n}，你好！", "next": "我的课程", "none": "还没有安排课程。", "enter": "进入教室", "opens": "课前15分钟可以进入教室。",
           "logout": "退出登录", "bj": "北京时间", "acc_h": "学生账户", "acc_lead": "给孩子创建自己的账户：他用学生编号和密码登录，自己进教室，以后还要用它交作业。",
           "acc_create": "创建学生账户", "acc_pw": "设置密码（至少7个字符）", "acc_pw2": "再输入一次密码", "acc_id": "学生编号", "acc_last": "上次登录",
           "acc_never": "还没有登录过", "acc_reset": "修改密码", "acc_off": "停用账户", "acc_on": "启用账户", "acc_disabled": "账户已停用：孩子暂时不能登录。",
           "acc_created": "学生账户已创建。请把学生编号和密码告诉孩子。", "acc_changed": "密码已修改。", "acc_err_pw": "密码至少需要7个字符。",
           "acc_err_pw2": "两次输入的密码不一样。", "acc_where": "登录地址", "acc_toggled": "已保存。",
           "nav_home": "首页", "nav_class": "我的班级", "nav_hw": "我的作业", "nav_tests": "我的测试", "nav_stats": "学习统计", "nav_cal": "课表",
           "class_none": "你还没有分班。老师评估你的水平以后，会为你推荐班级。", "teacher": "老师", "schedule": "上课时间", "classmates": "同学",
           "trial": "试听", "hw_lead": "老师布置的作业会显示在这里：你可以在这里交作业，看到老师的批改和分数（满分20分）。", "hw_none": "现在还没有作业。",
           "tests_none": "还没有水平测试。测试由爸爸妈妈在他们的账户里安排。", "test_wait": "等待老师评估", "test_doing": "进行中",
           "final": "建议级别", "writing": "写作", "oral": "口语", "qcm": "选择题", "score": "得分", "level": "级别",
           "st_courses": "上过的课", "st_rate": "出勤率", "st_present": "出勤", "st_late": "迟到", "st_absent": "缺席", "st_excused": "请假",
           "st_hw": "作业平均分", "st_hw_none": "还没有批改的作业", "st_level": "现在的级别", "st_none": "上完第一节课以后，这里会显示你的统计。",
           "st_month": "本月上课", "cal_today": "今天", "cal_none": "这个月没有课。", "cal_list": "接下来的课",
           "weekdays": ["一", "二", "三", "四", "五", "六", "日"], "month_fmt": "{y}年{m}月",
           "hw_due": "截止", "hw_todo": "待完成", "hw_done": "已提交", "hw_late": "已过截止时间", "hw_instr": "要求", "hw_attach": "附件", "hw_open": "打开",
           "hw_result": "老师批改", "hw_grade": "分数（满分20）", "hw_your": "我的作业", "hw_sent": "提交时间", "hw_answer": "我的答案（可以直接写在这里）",
           "hw_file": "上传文件（照片、PDF、录音，最大20MB）", "hw_submit": "提交作业", "hw_resubmit": "重新提交", "hw_saved": "作业已提交，老师会批改。",
           "hw_edit_note": "老师批改之前，你可以修改。", "hw_err_size": "文件太大（最大20MB）。", "hw_err_format": "文件格式不支持：请上传照片（JPG、PNG）、PDF、录音（MP3、M4A）、Word 或 PowerPoint。",
           "hw_err_empty": "请写下答案或上传一个文件。"},
    "fr": {"login_h": "Connexion élève", "login_lead": "Connecte-toi avec le numéro d'élève et le mot de passe que tes parents ont créés pour toi.",
           "id": "Numéro d'élève", "pw": "Mot de passe", "login": "Se connecter", "err": "Numéro d'élève ou mot de passe incorrect.",
           "too_many": "Trop de tentatives. Réessaie dans 15 minutes.", "parent_link": "Parent ou professeur ? Connexion avec l'e-mail",
           "space": "Espace élève", "hello": "Bonjour {n} !", "next": "Mes cours", "none": "Pas encore de cours programmé.", "enter": "Entrer en classe",
           "opens": "La salle ouvre 15 minutes avant le cours.", "logout": "Se déconnecter", "bj": "Pékin", "acc_h": "Compte élève",
           "acc_lead": "Créez un compte pour votre enfant : il se connecte avec son numéro d'élève et son mot de passe, entre seul en classe et rendra ses devoirs avec.",
           "acc_create": "Créer le compte élève", "acc_pw": "Mot de passe (7 caractères au moins)", "acc_pw2": "Confirmer le mot de passe", "acc_id": "Numéro d'élève",
           "acc_last": "Dernière connexion", "acc_never": "Jamais connecté", "acc_reset": "Changer le mot de passe", "acc_off": "Désactiver le compte",
           "acc_on": "Réactiver le compte", "acc_disabled": "Compte désactivé : l'enfant ne peut plus se connecter pour l'instant.",
           "acc_created": "Compte élève créé. Donnez le numéro d'élève et le mot de passe à votre enfant.", "acc_changed": "Mot de passe modifié.",
           "acc_err_pw": "Le mot de passe doit comporter au moins 7 caractères.", "acc_err_pw2": "Les deux mots de passe sont différents.",
           "acc_where": "Adresse de connexion", "acc_toggled": "Enregistré.",
           "nav_home": "Accueil", "nav_class": "Ma classe", "nav_hw": "Mes devoirs", "nav_tests": "Mes tests", "nav_stats": "Statistiques", "nav_cal": "Calendrier",
           "class_none": "Tu n'as pas encore de classe : ton professeur en proposera une après ton test de niveau.", "teacher": "Professeur",
           "schedule": "Horaires", "classmates": "Élèves de la classe", "trial": "essai",
           "hw_lead": "Les devoirs donnés par ton professeur apparaîtront ici : tu pourras les rendre, puis voir la correction et la note sur 20.",
           "hw_none": "Pas de devoir pour l'instant.", "tests_none": "Pas encore de test de niveau. Ce sont tes parents qui le lancent depuis leur compte.",
           "test_wait": "En attente d'évaluation", "test_doing": "En cours", "final": "Niveau conseillé", "writing": "Écrit", "oral": "Oral", "qcm": "QCM",
           "score": "Score", "level": "Niveau", "st_courses": "Cours suivis", "st_rate": "Présence", "st_present": "Présent", "st_late": "En retard",
           "st_absent": "Absent", "st_excused": "Absence signalée", "st_hw": "Moyenne des devoirs", "st_hw_none": "Pas encore de devoir noté",
           "st_level": "Niveau actuel", "st_none": "Tes statistiques apparaîtront après ton premier cours.", "st_month": "Cours ce mois-ci",
           "cal_today": "Aujourd'hui", "cal_none": "Pas de cours ce mois-ci.", "cal_list": "Prochains cours",
           "weekdays": ["L", "M", "M", "J", "V", "S", "D"], "month_fmt": "{m}/{y}",
           "hw_due": "À rendre pour", "hw_todo": "À faire", "hw_done": "Rendu", "hw_late": "En retard", "hw_instr": "Consigne", "hw_attach": "Pièce jointe",
           "hw_open": "Ouvrir", "hw_result": "Correction", "hw_grade": "Note sur 20", "hw_your": "Mon devoir", "hw_sent": "Rendu le",
           "hw_answer": "Ma réponse (tu peux l'écrire ici)", "hw_file": "Envoyer un fichier (photo, PDF, enregistrement audio, 20 Mo au plus)",
           "hw_submit": "Rendre le devoir", "hw_resubmit": "Rendre à nouveau", "hw_saved": "Devoir rendu : ton professeur va le corriger.",
           "hw_edit_note": "Tu peux le modifier tant qu'il n'est pas corrigé.", "hw_err_size": "Fichier trop lourd (20 Mo au plus).",
           "hw_err_format": "Format refusé : photo (JPG, PNG), PDF, audio (MP3, M4A), Word ou PowerPoint.", "hw_err_empty": "Écris ta réponse ou envoie un fichier."},
}


def tx():
    return TX[getattr(g, "lang", "zh")]


def new_login_id(c):
    """« MF » + 6 chiffres au hasard, unique."""
    while True:
        lid = "MF" + "".join(secrets.choice("0123456789") for _ in range(6))
        if not c.execute("SELECT 1 FROM students WHERE login_id=%s", (lid,)).fetchone():
            return lid


def current_student():
    """Élève connecté avec son numéro (session séparée des comptes adultes), relu à chaque requête."""
    if "pupil" not in g:
        g.pupil = None
        sid = session.get("student_sid")
        if sid:
            with connect() as c:
                g.pupil = c.execute("""SELECT s.* FROM students s JOIN users u ON u.id=s.user_id
                                       WHERE s.id=%s AND s.status='active' AND s.login_enabled AND s.password_hash IS NOT NULL AND u.active""",
                                    (sid,)).fetchone()
            if not g.pupil:
                session.pop("student_sid", None)
    return g.pupil


@web.app.context_processor
def pupil_ctx():
    return {"current_student": current_student, "pup": TX.get(getattr(g, "lang", "zh"), TX["zh"])}


def set_password(c, sid, pw, pw2):
    T = tx()
    if len(pw or "") < MIN_PW:
        return T["acc_err_pw"]
    if pw != pw2:
        return T["acc_err_pw2"]
    row = c.execute("SELECT login_id FROM students WHERE id=%s", (sid,)).fetchone()
    lid = row["login_id"] or new_login_id(c)
    c.execute("UPDATE students SET login_id=%s, password_hash=%s, login_enabled=true, updated_at=now() WHERE id=%s",
              (lid, generate_password_hash(pw), sid))
    return None


# ---------- connexion élève ----------

@web.route("/eleve/connexion", methods=["GET", "POST"])
def pupil_login():
    T = tx()
    if current_student():
        return redirect(url_for("pupil_home"))
    error, lid = None, ""
    if request.method == "POST":
        U.check_csrf()
        lid = (request.form.get("login_id") or "").strip().upper().replace(" ", "")[:12]
        with connect() as c:
            limited, h = U._limited(c, "pupil", 5, "15 minutes")
            s = c.execute("""SELECT s.* FROM students s JOIN users u ON u.id=s.user_id WHERE s.login_id=%s AND s.status='active'
                             AND s.login_enabled AND s.password_hash IS NOT NULL AND u.active""", (lid,)).fetchone()
            if limited:
                error = T["too_many"]
            elif s and check_password_hash(s["password_hash"], request.form.get("password", "")):
                c.execute("DELETE FROM admin_login_failures WHERE scope='pupil' AND ip_hash=%s", (h,))
                c.execute("UPDATE students SET last_login_at=now() WHERE id=%s", (s["id"],))
                session.pop("user_id", None)                  # un seul compte à la fois sur l'appareil
                session["student_sid"] = s["id"]
                session["csrf"] = secrets.token_urlsafe(24)
                session.permanent = True
                return redirect(url_for("pupil_home", lang=s["ui_lang"] or g.lang))
            else:
                U._fail(c, "pupil", h)
                error = T["err"]
    resp = web.app.make_response(render_template("pupil/login.html", error=error, lid=lid))
    resp.headers["Cache-Control"] = "no-store"
    return resp, (401 if error else 200)


@web.route("/eleve/deconnexion", methods=["POST"])
def pupil_logout():
    U.check_csrf()
    session.pop("student_sid", None)
    return redirect(url_for("pupil_login"))


@web.route("/eleve/")
def pupil_home():
    s = me_student()
    if not s:
        return redirect(url_for("pupil_login"))
    import classroom
    with connect() as c:
        stats = stats_for(c, s)
        classes = my_classes(c, s)
    return _page("pupil/home.html", s=s, sessions=classroom.student_sessions(s, 3), st=stats, classes=classes)


# ---------- espace élève : ma classe, mes devoirs, mes tests, statistiques, calendrier ----------
# Valable pour un enfant connecté avec son numéro (session student_sid) et pour un élève de 15 ans et plus avec son compte e-mail.

def me_student():
    st = current_student()
    if st:
        return st
    u = U.current()
    if u and u["role"] == "eleve":
        import students as ST
        with connect() as c:
            sid = ST.ensure_student(c, u["id"], u["name"])
            return c.execute("SELECT * FROM students WHERE id=%s", (sid,)).fetchone()
    return None


def _page(tpl, **kw):
    resp = web.app.make_response(render_template(tpl, **kw))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


def _need():
    st = me_student()
    if not st:
        return None, redirect(url_for("pupil_login"))
    return st, None


def my_classes(c, st):
    return c.execute("""SELECT l.*, m.kind, t.first_name AS t_first, t.last_initial AS t_last, t.slug AS t_slug, t.published AS t_pub,
                          (SELECT json_agg(m2.child_label ORDER BY m2.child_label) FROM class_members m2
                            WHERE m2.class_id=l.id AND m2.status='active' AND m2.kind='student' AND m2.student_id <> %(s)s) AS mates
                        FROM class_members m JOIN live_classes l ON l.id=m.class_id LEFT JOIN teachers t ON t.id=l.teacher_id
                        WHERE m.student_id=%(s)s AND m.status='active' ORDER BY l.level""", {"s": st["id"]}).fetchall()


@web.route("/eleve/classe")
def pupil_class():
    st, resp = _need()
    if resp:
        return resp
    import classroom
    with connect() as c:
        classes = my_classes(c, st)
    return _page("pupil/class.html", s=st, classes=classes, sessions=classroom.student_sessions(st, 6))


@web.route("/eleve/devoirs")
def pupil_homework():
    st, resp = _need()
    if resp:
        return resp
    import homework as HW
    with connect() as c:
        hws = HW.homeworks_for_student(c, st)
    return _page("pupil/homework.html", s=st, hws=hws)


@web.route("/eleve/tests")
def pupil_tests():
    st, resp = _need()
    if resp:
        return resp
    import placement
    with connect() as c:
        tests = c.execute("SELECT * FROM placement_tests WHERE student_id=%s ORDER BY created_at DESC", (st["id"],)).fetchall()
    tests = [dict(t, qcm=placement.qcm_total(t)) for t in tests]
    return _page("pupil/tests.html", s=st, tests=tests, levels=placement.LEVELS)


def stats_for(c, st):
    att = {r["status"]: r["n"] for r in c.execute("""SELECT r.status, count(*) AS n FROM session_reports r JOIN class_members m ON m.id=r.member_id
                                                       WHERE m.student_id=%s GROUP BY 1""", (st["id"],)).fetchall()}
    done = sum(att.values())
    came = att.get("present", 0) + att.get("late", 0)
    month = c.execute("""SELECT count(*) AS n FROM session_reports r JOIN class_members m ON m.id=r.member_id JOIN class_sessions x ON x.id=r.session_id
                         WHERE m.student_id=%s AND r.status IN ('present','late') AND x.starts_at >= date_trunc('month', now())""", (st["id"],)).fetchone()["n"]
    avg = c.execute("SELECT round(avg(grade), 1) AS a, count(grade) AS n FROM homework_submissions WHERE student_id=%s AND grade IS NOT NULL",
                    (st["id"],)).fetchone()
    return {"att": att, "done": done, "came": came, "rate": round(100 * came / done) if done else None, "month": month,
            "hw_avg": avg["a"], "hw_n": avg["n"]}


@web.route("/eleve/statistiques")
def pupil_stats():
    st, resp = _need()
    if resp:
        return resp
    with connect() as c:
        stats = stats_for(c, st)
        import practice
        ps = practice.practice_stats(c, st)
        levels = c.execute("""SELECT final_level, evaluated_at FROM placement_tests WHERE student_id=%s AND step='evaluated' ORDER BY evaluated_at""",
                           (st["id"],)).fetchall()
    return _page("pupil/stats.html", s=st, st=stats, levels=levels, ps=ps)


@web.route("/eleve/calendrier")
def pupil_calendar():
    """Calendrier du mois (heure de Pékin) : les jours de cours sont marqués ; ?m=AAAA-MM pour un autre mois."""
    import calendar as cal
    from datetime import date, datetime, timezone
    from liveclasses import BJ
    st, resp = _need()
    if resp:
        return resp
    today = datetime.now(BJ).date()
    try:
        y, m = (int(x) for x in request.args.get("m", "").split("-"))
        first = date(y, m, 1)
    except ValueError:
        first = today.replace(day=1)
    last = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    with connect() as c:
        rows = c.execute("""SELECT s.*, l.level, CASE WHEN m.kind='trial' THEN 'trial' ELSE 'student' END AS my_role FROM class_sessions s
                            JOIN live_classes l ON l.id=s.class_id JOIN class_members m ON m.class_id=s.class_id AND m.student_id=%s AND m.status='active'
                            WHERE s.status <> 'cancelled' AND s.starts_at >= %s AND s.starts_at < %s ORDER BY s.starts_at""",
                         (st["id"], datetime.combine(first, datetime.min.time(), BJ), datetime.combine(last, datetime.min.time(), BJ))).fetchall()
    import classroom
    now = datetime.now(timezone.utc)
    by_day = {}
    for r in rows:
        r = dict(r, bj=r["starts_at"].astimezone(BJ), open=classroom.is_open(r, r["my_role"], now), past=r["starts_at"] < now)
        by_day.setdefault(r["bj"].date(), []).append(r)
    weeks = cal.Calendar(firstweekday=0).monthdatescalendar(first.year, first.month)
    prev_m = (first.replace(day=1) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m")
    return _page("pupil/calendar.html", s=st, weeks=weeks, by_day=by_day, first=first, today=today, prev_m=prev_m, next_m=last.strftime("%Y-%m"),
                 upcoming=classroom.student_sessions(st, 8))


# ---------- côté parent : créer et gérer le compte de l'enfant (page de l'enfant, family.py) ----------

@web.route("/compte/enfants/<int:sid>/compte-eleve", methods=["POST"])
def pupil_account(sid):
    T = tx()
    u = U.current()
    if not u or u["role"] != "parent":
        abort(403)
    U.check_csrf()
    with connect() as c:
        s = c.execute("SELECT * FROM students WHERE id=%s AND user_id=%s AND status='active'", (sid, u["id"])).fetchone()
        if not s:
            abort(404)
        act = request.form.get("action")
        if act in ("create", "password"):
            err = set_password(c, sid, request.form.get("password", ""), request.form.get("password2", ""))
            if err:   # un code, jamais le texte : l'adresse ne doit pas pouvoir afficher n'importe quel message
                return redirect(url_for("family_kid", sid=sid, pw_err="court" if err == T["acc_err_pw"] else "different") + "#compte-eleve")
            return redirect(url_for("family_kid", sid=sid, ok="pupil_created" if act == "create" else "pupil_changed") + "#compte-eleve")
        if act in ("disable", "enable"):
            c.execute("UPDATE students SET login_enabled=%s, updated_at=now() WHERE id=%s", (act == "enable", sid))
            return redirect(url_for("family_kid", sid=sid, ok="pupil_toggled") + "#compte-eleve")
    abort(400)
