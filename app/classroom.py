"""Salle de classe en direct (直播教室) : notre propre outil de visio, sur le moteur LiveKit installé sur ce serveur.

- Moteur : service systemd « livekit » (/etc/livekit/livekit.yaml), signalisation via nginx sur wss://maisondufrancais.fr/livekit.
  Clés dans .env : LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET.
- Une séance (class_sessions) = un cours d'une classe (live_classes) à une date ; une salle LiveKit par séance.
  Les séances sont générées depuis le planning de la classe (/admin/classes/<id>).
- Qui entre (comptes du site uniquement, cahier des charges §9) :
  · le professeur de la classe (rôle « professeur » relié à la fiche) → teacher ;
  · un élève inscrit (class_members, compte parent ou élève) → student (caméra + micro) ou trial (essai : rien d'activé,
    le professeur peut l'inviter à parler) ; le même compte peut entrer en « parent » (旁听 : ni caméra ni micro) ;
  · l'équipe (admin, modérateur) → observer, ou teacher pour un administrateur qui remplace / teste.
- Ouverture de la salle : 15 min avant (30 min pour le professeur), fermeture 30 min après la fin prévue.
- Le professeur agit sur les autres par le serveur (couper un micro, inviter un essai à parler, exclure, terminer) :
  l'API de LiveKit n'est appelée que d'ici, jamais avec une clé dans le navigateur.
- Présence : enregistrée à chaque entrée (session_attendance). Pas d'enregistrement vidéo pour l'instant (accord des parents
  et durée de conservation à prévoir avant, §9 et §17). Pas de message privé : le chat de la salle est public et non conservé.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import date, datetime, timedelta, timezone

import httpx
import psycopg
from flask import abort, g, jsonify, redirect, render_template, request, url_for

import users as U
import web
from admin import _check_csrf, bp as admin_bp
from db import connect
from liveclasses import BJ, PARIS

LK_URL = os.environ.get("LIVEKIT_URL", "wss://maisondufrancais.fr/livekit")
LK_KEY = os.environ.get("LIVEKIT_API_KEY", "")
LK_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
LK_API = os.environ.get("LIVEKIT_API", "http://127.0.0.1:7880")
OPEN_BEFORE, OPEN_BEFORE_TEACHER, CLOSE_AFTER = timedelta(minutes=15), timedelta(minutes=30), timedelta(minutes=30)
SESSION_MIN = 60                     # 45 min de cours + 15 min de devoirs et questions (§16)
ABSENCE_NOTICE = timedelta(hours=24)  # absence signalée au moins 24 h avant : accès au replay quand il existera (§17)
LATE_AFTER = timedelta(minutes=5)     # entrée plus de 5 min après le début : « en retard » proposé à l'appel
REPORT_STATUSES = {"present": ("Présent", "出勤"), "late": ("En retard", "迟到"), "absent": ("Absent", "缺席"), "excused": ("Absence signalée", "已请假")}
ROLES = ("teacher", "student", "trial", "parent", "observer")

# Textes de la salle (zh pour les familles, fr pour les professeurs et l'équipe ; la langue suit l'adresse /fr/)
CR = {
    "zh": {"title": "直播教室", "enter": "进入教室", "enter_parent": "以家长身份旁听", "enter_child": "孩子上课", "not_open": "教室将于北京时间 {t} 开放（课前15分钟）。",
           "closed": "本节课已结束。", "cancelled": "本节课已取消。", "check": "进入前请检查摄像头和麦克风。", "mic": "麦克风", "cam": "摄像头",
           "no_device": "没有找到摄像头或麦克风，或浏览器没有获得权限。可以先进入教室，在浏览器设置里允许后再打开。",
           "mic_on": "关闭麦克风", "mic_off": "打开麦克风", "cam_on": "关闭摄像头", "cam_off": "打开摄像头", "hand_up": "举手", "hand_down": "放下手",
           "share": "共享屏幕", "share_stop": "停止共享", "leave": "离开教室", "end": "结束课程", "end_confirm": "结束这节课？所有人都会离开教室。",
           "people": "成员", "chat": "聊天", "chat_ph": "发消息给全班…", "send": "发送", "teacher": "老师", "student": "学生", "trial": "试听",
           "parent": "家长旁听", "observer": "教务", "you": "我", "raised": "举手了", "mute": "静音", "allow": "请他发言", "revoke": "停止发言",
           "remove": "移出", "remove_confirm": "把 {n} 移出教室？", "connecting": "正在连接…", "reconnecting": "网络不稳定，正在重新连接…",
           "connected": "已连接", "left": "你已离开教室。", "rejoin": "重新进入", "removed": "你已被老师移出教室。", "ended": "本节课已结束，谢谢！",
           "error": "无法连接教室，请检查网络后重试。", "audio_blocked": "点这里打开声音", "allowed": "老师请你发言了：可以打开麦克风和摄像头。",
           "revoked": "老师结束了你的发言。", "waiting_teacher": "老师还没有进入教室，请稍等。", "time_left": "距下课 {m} 分钟", "homework": "作业与答疑时间",
           "starts_in": "{m} 分钟后开始上课", "quality": {"excellent": "网络很好", "good": "网络一般", "poor": "网络较差", "lost": "网络中断"},
           "back": "返回我的账户", "listen_only": "旁听模式：你可以看和听，但不能发言。", "trial_note": "试听模式：老师请你发言后，才能打开麦克风和摄像头。",
           "safety": "课堂内不能私聊，聊天内容不会保存。", "board": "白板", "board_close": "关闭白板", "pen": "笔", "eraser": "橡皮", "clear_all": "清空",
           "board_allow": "允许学生写", "board_forbid": "禁止学生写", "board_can": "老师允许你在白板上写字了。", "board_cannot": "现在只有老师可以写。"},
    "fr": {"title": "Salle de classe", "enter": "Entrer en classe", "enter_parent": "Assister en tant que parent", "enter_child": "Mon enfant suit le cours",
           "not_open": "La salle ouvre à {t} (heure de Paris), 30 minutes avant le cours.", "closed": "Ce cours est terminé.", "cancelled": "Ce cours est annulé.",
           "check": "Vérifiez votre caméra et votre micro avant d'entrer.", "mic": "Micro", "cam": "Caméra",
           "no_device": "Aucune caméra ou aucun micro trouvé, ou le navigateur n'a pas l'autorisation. Vous pouvez entrer et les activer ensuite dans les réglages du navigateur.",
           "mic_on": "Couper le micro", "mic_off": "Activer le micro", "cam_on": "Couper la caméra", "cam_off": "Activer la caméra", "hand_up": "Lever la main",
           "hand_down": "Baisser la main", "share": "Partager l'écran", "share_stop": "Arrêter le partage", "leave": "Quitter", "end": "Terminer le cours",
           "end_confirm": "Terminer le cours ? Tout le monde sortira de la salle.", "people": "Participants", "chat": "Discussion", "chat_ph": "Message à toute la classe…",
           "send": "Envoyer", "teacher": "Professeur", "student": "Élève", "trial": "Essai", "parent": "Parent (écoute)", "observer": "Équipe", "you": "moi",
           "raised": "lève la main", "mute": "Couper le micro", "allow": "Donner la parole", "revoke": "Retirer la parole", "remove": "Exclure",
           "remove_confirm": "Exclure {n} de la salle ?", "connecting": "Connexion…", "reconnecting": "Réseau instable, reconnexion en cours…", "connected": "Connecté",
           "left": "Vous avez quitté la salle.", "rejoin": "Revenir", "removed": "Vous avez été exclu de la salle.", "ended": "Le cours est terminé. Merci !",
           "error": "Connexion impossible. Vérifiez le réseau et réessayez.", "audio_blocked": "Cliquez ici pour activer le son",
           "allowed": "Le professeur vous donne la parole : vous pouvez activer micro et caméra.", "revoked": "Le professeur vous a retiré la parole.",
           "waiting_teacher": "Le professeur n'est pas encore arrivé.", "time_left": "Fin du cours dans {m} min", "homework": "Temps des devoirs et des questions",
           "starts_in": "Le cours commence dans {m} min", "quality": {"excellent": "Très bonne connexion", "good": "Connexion moyenne", "poor": "Connexion faible", "lost": "Connexion perdue"},
           "back": "Retour à mon espace", "listen_only": "Mode écoute : vous voyez et entendez, sans prendre la parole.",
           "trial_note": "Cours d'essai : micro et caméra s'activent quand le professeur vous donne la parole.",
           "safety": "Pas de message privé dans la salle ; la discussion n'est pas conservée.", "board": "Tableau", "board_close": "Fermer le tableau",
           "pen": "Stylo", "eraser": "Gomme", "clear_all": "Effacer tout", "board_allow": "Les élèves peuvent écrire", "board_forbid": "Seul le professeur écrit",
           "board_can": "Le professeur vous laisse écrire au tableau.", "board_cannot": "Seul le professeur écrit au tableau."},
}


# ---------- jetons et API LiveKit ----------

def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def token(identity, name, grants, metadata=None, ttl=3 * 3600):
    """Jeton d'accès LiveKit (JWT HS256) signé avec la clé du serveur."""
    now = int(time.time())
    claims = {"iss": LK_KEY, "sub": identity, "nbf": now - 10, "exp": now + ttl, "name": name, "video": grants}
    if metadata is not None:
        claims["metadata"] = json.dumps(metadata, ensure_ascii=False)
    head = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(json.dumps(claims, ensure_ascii=False).encode())
    sig = _b64(hmac.new(LK_SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


def api(method, room, **payload):
    """Appel à l'API serveur de LiveKit (RoomService) pour une salle."""
    tok = token("maisondufrancais-server", "server", {"roomAdmin": True, "roomCreate": True, "room": room}, ttl=60)  # roomCreate : nécessaire pour DeleteRoom
    r = httpx.post(f"{LK_API}/twirp/livekit.RoomService/{method}", json=dict(payload, room=room),
                   headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    if r.status_code >= 400:
        raise RuntimeError(f"LiveKit {method} : {r.status_code} {r.text[:200]}")
    return r.json() if r.content else {}


SPEAK = {"canPublish": True, "canSubscribe": True, "canPublishData": True, "canPublishSources": ["CAMERA", "MICROPHONE"]}
SILENT = {"canPublish": False, "canSubscribe": True, "canPublishData": True}


def grants_for(role, room):
    g_ = {"room": room, "roomJoin": True, "canSubscribe": True, "canPublishData": role in ("teacher", "student", "trial")}
    if role == "teacher":
        g_.update(canPublish=True, canPublishSources=["camera", "microphone", "screen_share", "screen_share_audio"])
    elif role == "student":
        g_.update(canPublish=True, canPublishSources=["camera", "microphone"])
    else:                       # essai (invité à parler par le professeur), parent, équipe
        g_.update(canPublish=False)
    return g_


# ---------- séances ----------

def room_name(session_id):
    return f"mdf-s{session_id}"


def window(s, role):
    start = s["starts_at"]
    opens = start - (OPEN_BEFORE_TEACHER if role == "teacher" else OPEN_BEFORE)
    closes = start + timedelta(minutes=s["duration_min"]) + CLOSE_AFTER
    return opens, closes


def is_open(s, role, now=None):
    now = now or datetime.now(timezone.utc)
    opens, closes = window(s, role)
    return s["status"] == "scheduled" and opens <= now <= closes


def generate_sessions(c, cls, weeks):
    """Crée les séances des `weeks` prochaines semaines d'après le planning (jours + heure de Pékin). Ne touche pas aux existantes."""
    if not cls["days"] or not cls["start_bj"]:
        return 0
    first = max(cls["start_date"] or date.today(), datetime.now(BJ).date())
    made = 0
    for i in range(weeks * 7):
        d = first + timedelta(days=i)
        if d.isoweekday() not in cls["days"]:
            continue
        starts = datetime.combine(d, cls["start_bj"], BJ)
        if starts < datetime.now(timezone.utc):
            continue
        row = c.execute("""INSERT INTO class_sessions (class_id, starts_at, duration_min) VALUES (%s,%s,%s)
                           ON CONFLICT (class_id, starts_at) DO NOTHING RETURNING id""", (cls["id"], starts, SESSION_MIN)).fetchone()
        made += bool(row)
    return made


def access(c, s, u, wanted=None):
    """Rôle de l'utilisateur dans la séance, ou None. `wanted` : « parent » pour entrer en 旁听, « teacher » pour un admin."""
    if not u:
        return None, None
    cls = c.execute("SELECT * FROM live_classes WHERE id=%s", (s["class_id"],)).fetchone()
    if u["role"] == "professeur" and u["teacher_id"] and cls and u["teacher_id"] == cls["teacher_id"]:
        return "teacher", None
    if u["role"] in ("parent", "eleve"):
        m = c.execute("SELECT * FROM class_members WHERE class_id=%s AND user_id=%s AND status='active' ORDER BY id LIMIT 1",
                      (s["class_id"], u["id"])).fetchone()
        if m:
            if wanted == "parent":
                return "parent", m
            return ("trial" if m["kind"] == "trial" else "student"), m
        return None, None
    if u["role"] in U.STAFF:
        return ("teacher" if wanted == "teacher" and u["role"] == "admin" else "observer"), None
    return None, None


def access_pupil(c, s, st):
    """Élève connecté avec son numéro (pupil.py) : élève inscrit ou essai de la classe de la séance."""
    m = c.execute("SELECT * FROM class_members WHERE class_id=%s AND student_id=%s AND status='active'", (s["class_id"], st["id"])).fetchone()
    if not m:
        return None, None
    return ("trial" if m["kind"] == "trial" else "student"), m


def viewer():
    """(compte adulte, élève connecté avec son numéro) : l'un des deux, ou aucun."""
    u = U.current()
    if u:
        return u, None
    import pupil
    return None, pupil.current_student()


def student_sessions(st, limit=12):
    """Prochains cours d'un élève connecté avec son numéro."""
    now = datetime.now(timezone.utc)
    with connect() as c:
        rows = c.execute("""SELECT s.*, l.level, CASE WHEN m.kind='trial' THEN 'trial' ELSE 'student' END AS my_role
                            FROM class_sessions s JOIN live_classes l ON l.id=s.class_id
                            JOIN class_members m ON m.class_id=s.class_id AND m.student_id=%s AND m.status='active'
                            WHERE s.status='scheduled' AND s.starts_at + make_interval(mins => s.duration_min) + interval '30 minutes' > %s
                            ORDER BY s.starts_at LIMIT %s""", (st["id"], now, limit)).fetchall()
    return [dict(r, open=is_open(r, r["my_role"], now), bj=r["starts_at"].astimezone(BJ), paris=r["starts_at"].astimezone(PARIS)) for r in rows]


def display(role, u, m, teacher_name):
    lang = getattr(g, "lang", "zh")
    if role == "teacher":
        return teacher_name or u["name"]
    child = (m and m["child_label"]) or u["name"]
    if role == "parent":
        return f"家长 · {child}" if lang == "zh" else f"Parent · {child}"
    if role == "observer":
        return "教务老师" if lang == "zh" else "Équipe pédagogique"
    return child


def my_sessions(u, limit=8, student_id=None):
    """Prochaines séances d'un compte (famille, élève ou professeur), pour « Mon compte » et l'espace professeur."""
    if not u:
        return []
    now = datetime.now(timezone.utc)
    with connect() as c:
        if u["role"] == "professeur" and u["teacher_id"]:
            rows = c.execute("""SELECT s.*, l.level, l.teacher_id, 'teacher' AS my_role, NULL AS child_label FROM class_sessions s
                                JOIN live_classes l ON l.id=s.class_id WHERE l.teacher_id=%s AND s.status='scheduled'
                                AND s.starts_at + make_interval(mins => s.duration_min) + interval '30 minutes' > %s
                                ORDER BY s.starts_at LIMIT %s""", (u["teacher_id"], now, limit)).fetchall()
        elif u["role"] in ("parent", "eleve"):
            rows = c.execute("""SELECT s.*, l.level, l.teacher_id, CASE WHEN m.kind='trial' THEN 'trial' ELSE 'student' END AS my_role, m.child_label, m.student_id,
                                m.id AS member_id, EXISTS (SELECT 1 FROM session_absences a WHERE a.session_id=s.id AND a.member_id=m.id) AS absent
                                FROM class_sessions s JOIN live_classes l ON l.id=s.class_id
                                JOIN class_members m ON m.class_id=s.class_id AND m.user_id=%s AND m.status='active'
                                WHERE s.status='scheduled' AND s.starts_at + make_interval(mins => s.duration_min) + interval '30 minutes' > %s
                                ORDER BY s.starts_at LIMIT %s""", (u["id"], now, limit)).fetchall()
        else:
            return []
    return [dict(r, open=is_open(r, r["my_role"], now), bj=r["starts_at"].astimezone(BJ), paris=r["starts_at"].astimezone(PARIS),
                 can_excuse=r["starts_at"] - now >= ABSENCE_NOTICE) for r in rows if student_id is None or r.get("student_id") == student_id]


def my_reports(u, limit=6, student_id=None):
    """Bilans des derniers cours d'une famille ou d'un élève (appel + mot du professeur)."""
    if not u or u["role"] not in ("parent", "eleve"):
        return []
    with connect() as c:
        rows = c.execute("""SELECT s.starts_at, l.level, m.child_label, m.student_id, r.status, r.comment FROM session_reports r
                            JOIN class_sessions s ON s.id=r.session_id JOIN live_classes l ON l.id=s.class_id
                            JOIN class_members m ON m.id=r.member_id WHERE m.user_id=%s ORDER BY s.starts_at DESC LIMIT %s""", (u["id"], limit)).fetchall()
    return [dict(r, bj=r["starts_at"].astimezone(BJ)) for r in rows if student_id is None or r["student_id"] == student_id]


def teacher_reports_todo(u):
    """Cours passés du professeur dont l'appel n'est pas fait (30 derniers jours)."""
    if not u or u["role"] != "professeur" or not u["teacher_id"]:
        return []
    with connect() as c:
        rows = c.execute("""SELECT s.*, l.level FROM class_sessions s JOIN live_classes l ON l.id=s.class_id
                            WHERE l.teacher_id=%s AND s.status <> 'cancelled' AND s.starts_at < now() AND s.starts_at > now() - interval '30 days'
                            AND EXISTS (SELECT 1 FROM class_members m WHERE m.class_id=s.class_id AND m.status='active')
                            AND NOT EXISTS (SELECT 1 FROM session_reports r WHERE r.session_id=s.id)
                            ORDER BY s.starts_at DESC""", (u["teacher_id"],)).fetchall()
    return [dict(r, paris=r["starts_at"].astimezone(PARIS)) for r in rows]


@web.app.context_processor
def classroom_ctx():
    return {"my_sessions": my_sessions, "my_reports": my_reports, "teacher_reports_todo": teacher_reports_todo, "is_admin": U.is_admin}


# ---------- salle (pages publiques, comptes connectés) ----------

def _session(c, sid):
    s = c.execute("SELECT * FROM class_sessions WHERE id=%s", (sid,)).fetchone()
    if not s:
        abort(404)
    return s


@web.route("/classe/<int:sid>")
def classroom(sid):
    u, st = viewer()
    if not u and not st:
        return redirect(url_for("account_login", next=request.path))
    with connect() as c:
        s = _session(c, sid)
        role, m = access_pupil(c, s, st) if st else access(c, s, u, request.args.get("as"))
        if not role:
            abort(403)
        cls = c.execute("""SELECT l.*, t.first_name, t.last_initial FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id
                           WHERE l.id=%s""", (s["class_id"],)).fetchone()
        can_parent = role in ("student", "trial") and not st
    opens, closes = window(s, role)
    resp = web.app.make_response(render_template(
        "classroom.html", s=s, cls=cls, role=role, x=CR[g.lang], open=is_open(s, role), opens_bj=opens.astimezone(BJ), opens_paris=opens.astimezone(PARIS),
        starts_bj=s["starts_at"].astimezone(BJ), starts_paris=s["starts_at"].astimezone(PARIS), closed=datetime.now(timezone.utc) > closes,
        can_parent=can_parent, as_parent=request.args.get("as") == "parent"))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    # micro et caméra autorisés sur cette page seulement
    resp.headers["Permissions-Policy"] = "camera=(self), microphone=(self), display-capture=(self)"
    return resp


@web.route("/classe/<int:sid>/jeton", methods=["POST"])
def classroom_token(sid):
    u, st = viewer()
    if not u and not st:
        abort(403)
    U.check_csrf()
    with connect() as c:
        s = _session(c, sid)
        role, m = access_pupil(c, s, st) if st else access(c, s, u, request.form.get("as"))
        if not role:
            abort(403)
        if not is_open(s, role):
            return jsonify(error="closed"), 409
        cls = c.execute("SELECT l.*, t.first_name FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id WHERE l.id=%s",
                        (s["class_id"],)).fetchone()
        room = room_name(sid)
        if st:   # élève avec son propre numéro : identité distincte de celle du parent
            identity, name, owner = f"{role}-s{st['id']}-m{m['id']}", st["first_name"], st["user_id"]
        else:
            identity, name, owner = f"{role}-{u['id']}" + (f"-m{m['id']}" if m else ""), display(role, u, m, cls["first_name"]), u["id"]
        c.execute("""INSERT INTO session_attendance (session_id, user_id, member_id, role) VALUES (%s,%s,%s,%s)
                     ON CONFLICT (session_id, user_id, role) DO UPDATE SET last_join=now(), joins=session_attendance.joins+1""",
                  (sid, owner, m["id"] if m else None, role))
        if role == "teacher" and not s["started_at"]:
            c.execute("UPDATE class_sessions SET started_at=now() WHERE id=%s", (sid,))
    tok = token(identity, name, grants_for(role, room), metadata={"role": role})
    return jsonify(url=LK_URL, token=tok, identity=identity, role=role, name=name)


@web.route("/classe/<int:sid>/action", methods=["POST"])
def classroom_action(sid):
    """Actions du professeur (ou d'un administrateur) sur la salle."""
    u = U.current()
    if not u:
        abort(403)
    U.check_csrf()
    with connect() as c:
        s = _session(c, sid)
        role, _ = access(c, s, u, request.form.get("as"))
        if role != "teacher":
            abort(403)
        room, act, who = room_name(sid), request.form.get("action"), (request.form.get("identity") or "")[:80]
        if who and not who.split("-")[0] in ROLES or who.startswith("teacher-"):
            abort(400)
        try:
            if act == "mute":
                api("MutePublishedTrack", room, identity=who, track_sid=request.form.get("track", "")[:40], muted=True)
            elif act == "allow":           # inviter un élève en essai à parler (caméra + micro)
                api("UpdateParticipant", room, identity=who, permission=SPEAK)
            elif act == "revoke":
                api("UpdateParticipant", room, identity=who, permission=SILENT)
            elif act == "remove":
                api("RemoveParticipant", room, identity=who)
            elif act == "end":
                try:
                    api("DeleteRoom", room)
                finally:
                    c.execute("UPDATE class_sessions SET status='done', ended_at=now() WHERE id=%s AND status='scheduled'", (sid,))
            else:
                abort(400)
        except RuntimeError as e:
            web.app.logger.warning("classroom action %s: %s", act, e)
            return jsonify(ok=False), 502
    return jsonify(ok=True)


@web.route("/classe/<int:sid>/absence", methods=["POST"])
def classroom_absence(sid):
    """La famille signale une absence, au moins 24 h avant le cours."""
    u = U.current()
    if not u:
        abort(403)
    U.check_csrf()
    with connect() as c:
        s = _session(c, sid)
        m = c.execute("SELECT * FROM class_members WHERE class_id=%s AND user_id=%s AND status='active'", (s["class_id"], u["id"])).fetchone()
        if not m or s["status"] != "scheduled" or s["starts_at"] - datetime.now(timezone.utc) < ABSENCE_NOTICE:
            abort(403)
        c.execute("INSERT INTO session_absences (session_id, member_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (sid, m["id"]))
    return redirect(url_for("account_home", ok="absence"))


def report_rows(c, s):
    """Élèves de la séance avec l'état proposé : bilan déjà fait, sinon absence signalée, sinon présence d'après l'entrée en salle."""
    rows = c.execute("""SELECT m.*, r.status AS r_status, r.comment AS r_comment,
                               EXISTS (SELECT 1 FROM session_absences a WHERE a.session_id=%(s)s AND a.member_id=m.id) AS excused,
                               (SELECT min(first_join) FROM session_attendance t WHERE t.session_id=%(s)s AND t.member_id=m.id AND t.role IN ('student','trial')) AS joined
                        FROM class_members m LEFT JOIN session_reports r ON r.session_id=%(s)s AND r.member_id=m.id
                        WHERE m.class_id=%(c)s AND (m.status='active' OR r.status IS NOT NULL) ORDER BY m.kind, m.child_label""",
                     {"s": s["id"], "c": s["class_id"]}).fetchall()
    out = []
    for m in rows:
        guess = m["r_status"] or ("excused" if m["excused"] else ("late" if m["joined"] and m["joined"] > s["starts_at"] + LATE_AFTER
                                                                   else "present" if m["joined"] else "absent"))
        out.append(dict(m, status=guess, joined_paris=m["joined"].astimezone(PARIS) if m["joined"] else None))
    return out


def _teacher_session(c, sid):
    import accounts
    u = accounts.current()
    s = _session(c, sid)
    cls = c.execute("SELECT * FROM live_classes WHERE id=%s", (s["class_id"],)).fetchone()
    if not u or not cls or cls["teacher_id"] != u["teacher_id"]:
        abort(404)
    return s, cls


def _espace_routes():
    from accounts import bp as espace_bp

    @espace_bp.route("/seance/<int:sid>", methods=["GET", "POST"])
    def session_report(sid):
        with connect() as c:
            s, cls = _teacher_session(c, sid)
            if request.method == "POST":
                U.check_csrf()
                if s["starts_at"] > datetime.now(timezone.utc):
                    abort(400)
                unit = request.form.get("unit_id", type=int)
                c.execute("UPDATE class_sessions SET unit_id=%s, topic=%s WHERE id=%s",
                          (unit if unit and c.execute("SELECT 1 FROM program_units WHERE id=%s AND level=%s", (unit, cls["level"])).fetchone() else None,
                           (request.form.get("topic") or "").strip()[:1000] or None, sid))
                if request.form.get("unit_done") and unit:
                    c.execute("""INSERT INTO class_progress (class_id, unit_id, status) VALUES (%s,%s,'done')
                                 ON CONFLICT (class_id, unit_id) DO UPDATE SET status='done', updated_at=now()""", (cls["id"], unit))
                elif unit:
                    c.execute("""INSERT INTO class_progress (class_id, unit_id, status) VALUES (%s,%s,'doing')
                                 ON CONFLICT (class_id, unit_id) DO NOTHING""", (cls["id"], unit))
                for m in report_rows(c, s):
                    st = request.form.get(f"st{m['id']}")
                    if st not in REPORT_STATUSES:
                        continue
                    c.execute("""INSERT INTO session_reports (session_id, member_id, status, comment) VALUES (%s,%s,%s,%s)
                                 ON CONFLICT (session_id, member_id) DO UPDATE SET status=EXCLUDED.status, comment=EXCLUDED.comment, updated_at=now()""",
                              (sid, m["id"], st, (request.form.get(f"cm{m['id']}") or "").strip()[:600] or None))
                return redirect(url_for("espace.session_report", sid=sid, ok=1))
            rows = report_rows(c, s)
            units = c.execute("SELECT * FROM program_units WHERE level=%s ORDER BY sort", (cls["level"],)).fetchall()
        return render_template("espace/session.html", s=s, cls=cls, rows=rows, units=units, statuses=REPORT_STATUSES, ok=request.args.get("ok"),
                               paris=s["starts_at"].astimezone(PARIS), bj=s["starts_at"].astimezone(BJ),
                               future=s["starts_at"] > datetime.now(timezone.utc))


    @espace_bp.route("/classes")
    def my_classes():
        import accounts
        u = accounts.current()
        with connect() as c:
            rows = c.execute("""SELECT l.*, (SELECT count(*) FROM class_members m WHERE m.class_id=l.id AND m.status='active' AND m.kind='student') AS n,
                                  (SELECT count(*) FROM class_members m WHERE m.class_id=l.id AND m.status='active' AND m.kind='trial') AS trials,
                                  (SELECT min(starts_at) FROM class_sessions s WHERE s.class_id=l.id AND s.status='scheduled' AND s.starts_at > now()) AS next_at
                                FROM live_classes l WHERE l.teacher_id=%s AND l.status <> 'closed' ORDER BY l.level, l.start_bj""", (u["teacher_id"],)).fetchall()
        return render_template("espace/classes.html", rows=[dict(r, next_paris=r["next_at"].astimezone(PARIS) if r["next_at"] else None) for r in rows],
                               days={1: "lundi", 2: "mardi", 3: "mercredi", 4: "jeudi", 5: "vendredi", 6: "samedi", 7: "dimanche"})

    @espace_bp.route("/classes/<int:cid>")
    def my_class(cid):
        """Lecture seule : élèves de la classe (gérés par l'équipe), présence, dernier bilan, séances."""
        import accounts
        u = accounts.current()
        with connect() as c:
            cls = c.execute("SELECT * FROM live_classes WHERE id=%s AND teacher_id=%s", (cid, u["teacher_id"])).fetchone()
            if not cls:
                abort(404)
            members = c.execute("""SELECT m.*, s.age, s.level AS s_level,
                       (SELECT count(*) FILTER (WHERE r.status IN ('present','late')) FROM session_reports r WHERE r.member_id=m.id) AS came,
                       (SELECT count(*) FROM session_reports r WHERE r.member_id=m.id) AS done,
                       (SELECT r.comment FROM session_reports r JOIN class_sessions x ON x.id=r.session_id WHERE r.member_id=m.id AND r.comment IS NOT NULL
                          ORDER BY x.starts_at DESC LIMIT 1) AS last_comment
                       FROM class_members m LEFT JOIN students s ON s.id=m.student_id
                       WHERE m.class_id=%s AND m.status='active' ORDER BY m.kind, m.child_label""", (cid,)).fetchall()
            sessions = c.execute("""SELECT s.*, (SELECT count(*) FROM session_reports r WHERE r.session_id=s.id) AS reported,
                                      (SELECT count(*) FROM session_absences a WHERE a.session_id=s.id) AS excused
                                    FROM class_sessions s WHERE s.class_id=%s AND s.status <> 'cancelled'
                                    AND s.starts_at > now() - interval '30 days' ORDER BY s.starts_at LIMIT 40""", (cid,)).fetchall()
            import homework as HW
            program, done, pct = HW.program_for(c, cls)
            homeworks = HW.homeworks_for_class(c, cls)
            next_at = HW.next_session_at(c, cid)
            import bank
            cur_unit = bank.current_unit(program)
            bank_items = bank.items_for_units(c, [cur_unit["id"]]).get(cur_unit["id"], []) if cur_unit else []
            tpl = bank.prefill(c, request.args.get("modele", type=int), cls["level"]) if request.args.get("modele") else None
        now = datetime.now(timezone.utc)
        sessions = [dict(s, paris=s["starts_at"].astimezone(PARIS), bj=s["starts_at"].astimezone(BJ), past=s["starts_at"] < now,
                         open=is_open(s, "teacher", now)) for s in sessions]
        return render_template("espace/class.html", cls=cls, members=members, sessions=sessions, program=program, done=done, pct=pct,
                               homeworks=homeworks, cur_unit=cur_unit, bank_items=bank_items, tpl=tpl, open_now=next((s for s in sessions if s["open"]), None),
                               next_due=(next_at.astimezone(PARIS).strftime("%Y-%m-%dT%H:%M") if next_at else ""),
                               ok=request.args.get("ok"), err=request.args.get("err"))


_espace_routes()


# ---------- administration : élèves de la classe et séances ----------

@admin_bp.route("/classes/<int:cid>/salle", methods=["GET", "POST"])
def class_room_admin(cid):
    msg, errors = request.args.get("ok"), []
    with connect() as c:
        cls = c.execute("""SELECT l.*, t.first_name, t.last_initial FROM live_classes l LEFT JOIN teachers t ON t.id=l.teacher_id
                           WHERE l.id=%s""", (cid,)).fetchone()
        if not cls:
            abort(404)
        if request.method == "POST":
            _check_csrf()
            act = request.form.get("action")
            if act == "add":                       # inscrire un élève existant (fiche élève, gestion des élèves)
                import students as ST
                sid_ = request.form.get("student_id", type=int)
                err = ST.enroll(c, sid_, cid, "trial" if request.form.get("kind") == "trial" else "student") if sid_ else "Choisissez un élève."
                if err:
                    errors.append(err)
                else:
                    return redirect(url_for("admin.class_room_admin", cid=cid, ok="Élève inscrit."))
            elif act == "remove":
                import students as ST
                c.execute("UPDATE class_members SET status='ended' WHERE id=%s AND class_id=%s", (request.form.get("member", type=int), cid))
                ST.sync_seats(c, cid)
                return redirect(url_for("admin.class_room_admin", cid=cid, ok="Élève retiré de la classe."))
            elif act == "move_session":             # déplacer une séance (nouvelle date et heure de Pékin)
                try:
                    starts = datetime.strptime(request.form.get("starts_bj", ""), "%Y-%m-%dT%H:%M").replace(tzinfo=BJ)
                    with c.transaction():           # point de sauvegarde : un doublon d'horaire n'interrompt pas la page
                        moved = c.execute("UPDATE class_sessions SET starts_at=%s WHERE id=%s AND class_id=%s AND status='scheduled'",
                                          (starts, request.form.get("session", type=int), cid)).rowcount
                    if not moved:
                        raise LookupError
                    return redirect(url_for("admin.class_room_admin", cid=cid, ok="Séance déplacée. Pensez à prévenir les familles (WeChat) : la nouvelle heure s'affiche déjà dans leur compte."))
                except ValueError:
                    errors.append("Date et heure invalides.")
                except psycopg.errors.UniqueViolation:
                    errors.append("Il y a déjà une séance à cette heure-là.")
                except LookupError:
                    errors.append("Seule une séance prévue (ni terminée ni annulée) peut être déplacée.")
            elif act == "generate":
                n = generate_sessions(c, cls, max(1, min(12, request.form.get("weeks", 4, type=int) or 4)))
                return redirect(url_for("admin.class_room_admin", cid=cid, ok=f"{n} séance(s) créée(s)."))
            elif act == "add_session":
                try:
                    starts = datetime.strptime(request.form.get("starts_bj", ""), "%Y-%m-%dT%H:%M").replace(tzinfo=BJ)
                    c.execute("""INSERT INTO class_sessions (class_id, starts_at, duration_min) VALUES (%s,%s,%s)
                                 ON CONFLICT (class_id, starts_at) DO NOTHING""", (cid, starts, SESSION_MIN))
                    return redirect(url_for("admin.class_room_admin", cid=cid, ok="Séance ajoutée."))
                except ValueError:
                    errors.append("Date et heure invalides.")
            elif act == "start_now":                # séance immédiate (test, rattrapage) : salle ouverte tout de suite, 90 min
                starts = datetime.now(timezone.utc).replace(second=0, microsecond=0)
                c.execute("""INSERT INTO class_sessions (class_id, starts_at, duration_min) VALUES (%s,%s,%s)
                             ON CONFLICT (class_id, starts_at) DO NOTHING""", (cid, starts, SESSION_MIN))
                return redirect(url_for("admin.class_room_admin", cid=cid, ok="Séance créée : la salle est ouverte dès maintenant, jusqu'à 1 h 30 après le début."))
            elif act == "cancel":
                c.execute("UPDATE class_sessions SET status='cancelled' WHERE id=%s AND class_id=%s AND status='scheduled'",
                          (request.form.get("session", type=int), cid))
                return redirect(url_for("admin.class_room_admin", cid=cid, ok="Séance annulée."))
        members = c.execute("""SELECT m.*, u.email, u.name, u.role AS account_role, s.age, s.level AS s_level FROM class_members m JOIN users u ON u.id=m.user_id
                               LEFT JOIN students s ON s.id=m.student_id WHERE m.class_id=%s ORDER BY m.status, m.kind, m.child_label""", (cid,)).fetchall()
        candidates = c.execute("""SELECT s.id, s.first_name, s.age, s.level, u.name AS account_name FROM students s JOIN users u ON u.id=s.user_id
                                  WHERE s.status='active' AND NOT EXISTS (SELECT 1 FROM class_members m WHERE m.student_id=s.id AND m.class_id=%s AND m.status='active')
                                  ORDER BY (s.level = %s) DESC NULLS LAST, s.first_name""", (cid, cls["level"])).fetchall()
        sessions = c.execute("""SELECT s.*, (SELECT count(*) FROM session_attendance a WHERE a.session_id=s.id AND a.role IN ('student','trial')) AS present,
                                (SELECT count(*) FROM session_reports r WHERE r.session_id=s.id) AS reported,
                                (SELECT count(*) FROM session_absences a WHERE a.session_id=s.id) AS excused
                                FROM class_sessions s WHERE class_id=%s ORDER BY starts_at DESC LIMIT 60""", (cid,)).fetchall()
    now = datetime.now(timezone.utc)
    sessions = [dict(s, bj=s["starts_at"].astimezone(BJ), paris=s["starts_at"].astimezone(PARIS), open=is_open(s, "teacher", now)) for s in sessions]
    return render_template("admin/class_room.html", cls=cls, members=members, sessions=sessions, msg=msg, errors=errors, now_utc=now, candidates=candidates,
                           active=sum(1 for m in members if m["status"] == "active" and m["kind"] == "student"))
