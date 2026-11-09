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
           "acc_err_pw2": "两次输入的密码不一样。", "acc_where": "登录地址", "acc_toggled": "已保存。"},
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
           "acc_where": "Adresse de connexion", "acc_toggled": "Enregistré."},
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
                return redirect(url_for("pupil_home"))
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
    s = current_student()
    if not s:
        return redirect(url_for("pupil_login"))
    import classroom
    sess = classroom.student_sessions(s)
    resp = web.app.make_response(render_template("pupil/home.html", s=s, sessions=sess))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


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
