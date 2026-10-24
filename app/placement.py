"""Test de niveau 水平测试 (cahier des charges §5, §8) : /test-de-niveau (zh) et /fr/test-de-niveau ; correction dans /admin/tests.

Parcours (comptes connectés : parent pour son enfant, ou élève de 15 ans et plus) :
  1. informations : pseudo et âge de l'enfant (compte parent) ;
  2. QCM par niveau A1 → B2 (vocabulaire, grammaire, compréhension écrite, et écoute si l'audio existe) ; on passe au niveau
     suivant avec 60 % de bonnes réponses, sinon le QCM s'arrête. Réponses mélangées à l'affichage (ordre fixe par test) ;
  3. rédaction courte au niveau atteint ;
  4. oral : enregistrement dans le navigateur (3 réponses d'1 minute au plus) avec consentement explicite du parent,
     OU entretien en direct avec un professeur (rien n'est enregistré) ;
  5. l'équipe corrige (niveaux écrit / oral / final, classe proposée, message à la famille) → e-mail + « Mon compte ».
Enregistrements : écoutés seulement par l'équipe dans l'admin ; supprimés 30 jours après la notation, 60 jours au plus
(purge_recordings, appelée par le minuteur maisondufrancais-purge et à l'ouverture de l'admin) ; le parent peut les supprimer.
"""
import os
import random
import re
import secrets

from flask import abort, g, redirect, render_template, request, send_from_directory, url_for
from psycopg.types.json import Jsonb

import users as U
import web
from admin import _check_csrf, bp
from db import connect
from i18n import texts

LEVELS = ("A1", "A2", "B1", "B2")
PASS = 0.6
BASE = os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads")
REC_DIR, AUDIO_DIR = os.path.join(BASE, "placement"), os.path.join(BASE, "placement-audio")
REC_MAX = 6 * 1024 * 1024
KEEP_AFTER_EVAL, KEEP_MAX = "30 days", "60 days"

WRITING = {  # sujet de rédaction selon le niveau atteint
    "A1.1": ("Présente-toi : ton prénom, ton âge, ce que tu aimes. (2 ou 3 phrases)", "用法语介绍自己：名字、年龄、喜欢什么（2–3句话）。"),
    "A1": ("Présente-toi : ton prénom, ton âge, ta famille, ce que tu aimes. (3 à 5 phrases)", "用法语介绍自己：名字、年龄、家人、喜欢什么（3–5句话）。"),
    "A2": ("Raconte ton dernier week-end : où es-tu allé(e) ? avec qui ? qu'est-ce que tu as fait ? (5 à 8 phrases)", "讲讲你上个周末：去了哪里？和谁？做了什么？（5–8句话）"),
    "B1": ("Écris un message à un(e) ami(e) pour lui raconter un voyage ou une sortie, et dis ce que tu en as pensé. (80 à 120 mots)", "给朋友写一段话，讲一次旅行或出游，并说说你的感受（80–120词）。"),
    "B2": ("Faut-il apprendre une langue étrangère dès l'école primaire ? Donne ton avis avec des arguments et des exemples. (150 à 200 mots)", "是否应该从小学开始学外语？请给出你的观点、理由和例子（150–200词）。"),
}
ORAL_READ = {
    "A1.1": "J'ai un chat. Il est noir.", "A1": "J'ai un chat noir. Il s'appelle Minou. Il aime dormir sur mon lit.",
    "A2": "Le week-end, je vais au parc avec mes amis. Nous jouons au ballon et nous mangeons une glace.",
    "B1": "L'année prochaine, j'aimerais partir en France pour améliorer mon français et découvrir une autre culture.",
    "B2": "Apprendre une langue étrangère, ce n'est pas seulement retenir des mots : c'est aussi comprendre une autre façon de voir le monde.",
}
ORAL_QUESTION = {
    "A1.1": "Quelle est ta couleur préférée ?", "A1": "Qu'est-ce que tu aimes manger ?",
    "A2": "Raconte ce que tu as fait le week-end dernier.", "B1": "Quel pays aimerais-tu visiter, et pourquoi ?",
    "B2": "Les écrans sont-ils une bonne chose pour les enfants ? Donne ton avis.",
}

PT = {
    "zh": {
        "title": "免费水平测试", "desc": "法语之家免费法语水平测试：笔试（选择题和写作）和口语，由法国老师评估，给出欧标级别和分班建议。",
        "h1": "免费法语水平测试", "lead": "笔试约20分钟，口语约5分钟。低龄孩子请家长陪同完成。测试结束后，老师会给出欧标级别和分班建议。",
        "how1": "笔试：选择题", "how1_p": "词汇、语法、阅读（和听力），从A1开始，难度逐级提高，答错较多时会自动结束。",
        "how2": "笔试：写作", "how2_p": "根据孩子的水平写几句话或一小段文字。",
        "how3": "口语", "how3_p": "在线录音回答3个问题（每个最多1分钟，需家长同意），或预约与老师的视频面谈。",
        "how4": "结果", "how4_p": "老师评估后，结果会显示在“我的账户”中，并通过邮件通知您。",
        "login_needed": "请先登录家长或学生账户，测试结果会保存在您的账户中。", "start": "开始测试", "continue": "继续测试",
        "who_h": "谁来参加测试？", "child_label": "孩子的昵称（不要填写全名）", "age": "年龄", "me": "我自己（学生账户）",
        "err_child": "请填写孩子的昵称。", "err_age": "请填写正确的年龄。",
        "qcm_h": "第{n}部分 · {lv}", "qcm_lead": "选择正确的答案。不知道的话可以选“我不知道”。", "dunno": "我不知道",
        "listen": "听录音", "read_text": "阅读短文", "next": "下一步", "err_all": "请回答所有问题。",
        "writing_h": "写作", "writing_lead": "请用法语完成下面的写作（不要用翻译软件）。", "words": "词数", "err_writing": "请写几句话。",
        "oral_h": "口语", "oral_lead": "请选择口语测试的方式。",
        "oral_rec": "在线录音", "oral_rec_p": "回答3个问题，每个最多1分钟。录音只用于本次测试，仅我们的老师可听，评估后30天自动删除（最长保存60天）。",
        "oral_live": "与老师视频面谈", "oral_live_p": "不录音：提交笔试后，通过微信和我们预约一次约10分钟的视频面谈。",
        "consent": "我是孩子的家长或监护人（或我本人已满15岁），同意录制孩子（或我）的声音，仅用于本次水平测试。",
        "err_consent": "请勾选同意后再录音，或选择“与老师视频面谈”。",
        "task1": "1. 用法语介绍自己", "task1_p": "说说你的名字、年龄、喜欢做什么。", "task2": "2. 朗读下面的句子", "task3": "3. 回答问题",
        "rec": "开始录音", "stop": "停止", "redo": "重新录", "saved": "已保存", "uploading": "正在上传…", "upload_err": "上传失败，请重试。",
        "no_mic": "您的浏览器无法录音（或没有允许使用麦克风）。请换用手机微信以外的浏览器，或选择“与老师视频面谈”。",
        "submit": "提交测试", "err_rec": "请完成3段录音，或选择“与老师视频面谈”。",
        "done_h": "测试已提交", "done_p": "谢谢！老师会尽快评估，结果会显示在“我的账户”中，并通过邮件通知您。",
        "done_live": "请通过微信联系我们，预约口语视频面谈（二维码在“联系我们”页面）。",
        "my_tests": "水平测试", "status_qcm": "进行中", "status_writing": "进行中", "status_oral": "进行中", "status_submitted": "等待老师评估", "status_evaluated": "已出结果",
        "result_level": "建议级别", "result_class": "建议班级", "result_msg": "老师的话", "del_rec": "删除录音", "rec_deleted": "录音已删除。",
        "new_test": "为另一个孩子测试", "est": "选择题估计级别",
    },
    "fr": {
        "title": "Test de niveau gratuit", "desc": "Test de niveau de français gratuit : écrit (QCM et rédaction) et oral, évalués par un professeur en France, avec un niveau CECRL et un conseil de classe.",
        "h1": "Test de niveau de français gratuit", "lead": "Environ 20 minutes d'écrit et 5 minutes d'oral. Les plus jeunes le passent avec un parent. Un professeur donne ensuite le niveau CECRL et conseille une classe.",
        "how1": "Écrit : QCM", "how1_p": "Vocabulaire, grammaire, lecture (et écoute), de plus en plus difficile à partir de A1 ; le QCM s'arrête quand les erreurs deviennent nombreuses.",
        "how2": "Écrit : rédaction", "how2_p": "Quelques phrases ou un petit texte, selon le niveau.",
        "how3": "Oral", "how3_p": "3 réponses enregistrées en ligne (1 minute au plus chacune, avec l'accord du parent), ou un entretien en visio avec un professeur.",
        "how4": "Résultat", "how4_p": "Après l'évaluation, le résultat apparaît dans « Mon compte » et vous recevez un e-mail.",
        "login_needed": "Connectez-vous avec un compte parent ou élève : le résultat est enregistré dans votre compte.", "start": "Commencer le test", "continue": "Reprendre le test",
        "who_h": "Qui passe le test ?", "child_label": "Pseudo de l'enfant (pas de nom complet)", "age": "Âge", "me": "Moi-même (compte élève)",
        "err_child": "Indiquez le pseudo de l'enfant.", "err_age": "Indiquez un âge valide.",
        "qcm_h": "Partie {n} · {lv}", "qcm_lead": "Choisissez la bonne réponse. Si vous ne savez pas, choisissez « Je ne sais pas ».", "dunno": "Je ne sais pas",
        "listen": "Écouter", "read_text": "Lisez le texte", "next": "Suivant", "err_all": "Répondez à toutes les questions.",
        "writing_h": "Rédaction", "writing_lead": "Écrivez en français (sans traducteur automatique).", "words": "Mots", "err_writing": "Écrivez quelques phrases.",
        "oral_h": "Oral", "oral_lead": "Choisissez comment passer l'oral.",
        "oral_rec": "Enregistrement en ligne", "oral_rec_p": "3 réponses d'1 minute au plus. L'enregistrement ne sert qu'à ce test, seuls nos professeurs l'écoutent, il est supprimé 30 jours après l'évaluation (60 jours au plus).",
        "oral_live": "Entretien avec un professeur", "oral_live_p": "Rien n'est enregistré : après l'écrit, réservez sur WeChat un entretien en visio d'environ 10 minutes.",
        "consent": "Je suis le parent ou le représentant légal de l'enfant (ou j'ai moi-même 15 ans ou plus) et j'accepte l'enregistrement de sa voix (ou de la mienne), uniquement pour ce test de niveau.",
        "err_consent": "Cochez la case d'accord pour enregistrer, ou choisissez l'entretien avec un professeur.",
        "task1": "1. Présente-toi en français", "task1_p": "Ton prénom, ton âge, ce que tu aimes faire.", "task2": "2. Lis cette phrase à voix haute", "task3": "3. Réponds à la question",
        "rec": "Enregistrer", "stop": "Arrêter", "redo": "Recommencer", "saved": "Enregistré", "uploading": "Envoi…", "upload_err": "Échec de l'envoi, réessayez.",
        "no_mic": "Votre navigateur ne peut pas enregistrer (ou le micro n'est pas autorisé). Essayez un autre navigateur, ou choisissez l'entretien avec un professeur.",
        "submit": "Envoyer le test", "err_rec": "Faites les 3 enregistrements, ou choisissez l'entretien avec un professeur.",
        "done_h": "Test envoyé", "done_p": "Merci ! Un professeur l'évalue au plus vite ; le résultat apparaîtra dans « Mon compte » et vous recevrez un e-mail.",
        "done_live": "Contactez-nous sur WeChat pour réserver l'entretien oral en visio (QR code sur la page Contact).",
        "my_tests": "Tests de niveau", "status_qcm": "En cours", "status_writing": "En cours", "status_oral": "En cours", "status_submitted": "En attente d'évaluation", "status_evaluated": "Résultat disponible",
        "result_level": "Niveau conseillé", "result_class": "Classe proposée", "result_msg": "Le mot du professeur", "del_rec": "Supprimer les enregistrements", "rec_deleted": "Enregistrements supprimés.",
        "new_test": "Tester un autre enfant", "est": "Estimation du QCM",
    },
}


def pt(lang):
    return {**PT["fr"], **PT.get(lang, {})}


# ---------- outils ----------

def purge_recordings():
    """Supprime les enregistrements : 30 jours après l'évaluation, 60 jours au plus (garde-fou de conservation)."""
    with connect() as c:
        rows = c.execute(f"""SELECT r.id, r.file_name FROM placement_recordings r JOIN placement_tests t ON t.id=r.test_id
                             WHERE (t.evaluated_at IS NOT NULL AND t.evaluated_at < now() - interval '{KEEP_AFTER_EVAL}')
                                OR r.created_at < now() - interval '{KEEP_MAX}'""").fetchall()
        for r in rows:
            _rm(REC_DIR, r["file_name"])
            c.execute("DELETE FROM placement_recordings WHERE id=%s", (r["id"],))
    return len(rows)


def _rm(d, name):
    if name and re.fullmatch(r"[pa]\d+-[0-9a-f]{12}\.(webm|ogg|m4a|mp3)", name):
        try:
            os.remove(os.path.join(d, name))
        except FileNotFoundError:
            pass


def delete_recordings(test_id):
    with connect() as c:
        for r in c.execute("SELECT id, file_name FROM placement_recordings WHERE test_id=%s", (test_id,)).fetchall():
            _rm(REC_DIR, r["file_name"])
        c.execute("DELETE FROM placement_recordings WHERE test_id=%s", (test_id,))


PICK = {"vocab": 2, "grammar": 2, "listening": 1}  # + 1 texte de lecture avec toutes ses questions


def items_for(c, level, test_id):
    """Questions d'un niveau pour un test : tirées au hasard dans la banque (toujours les mêmes pour un test donné)."""
    pool = c.execute("""SELECT * FROM placement_items WHERE level=%s AND active AND (section <> 'listening' OR audio_file IS NOT NULL)
                        ORDER BY sort, id""", (level,)).fetchall()
    rnd = random.Random(f"tirage-{test_id}-{level}")
    chosen = []
    for sec, n in PICK.items():
        items = [it for it in pool if it["section"] == sec]
        chosen += rnd.sample(items, min(n, len(items)))
    passages = sorted({it["passage"] for it in pool if it["section"] == "reading" and it["passage"]})
    if passages:
        p = rnd.choice(passages)
        chosen += [it for it in pool if it["section"] == "reading" and it["passage"] == p]
    order = {"vocab": 0, "grammar": 1, "reading": 2, "listening": 3}
    return sorted(chosen, key=lambda it: (order[it["section"]], it["sort"], it["id"]))


def shuffled(test_id, item):
    """Réponses dans un ordre mélangé, toujours le même pour un test donné : [(index d'origine, texte)]."""
    opts = list(enumerate(item["options"]))
    random.Random(f"{test_id}-{item['id']}").shuffle(opts)
    return opts


def estimate(scores):
    est = "A1.1"
    for lv in LEVELS:
        good, total = scores.get(lv, [0, 0])
        if total and good / total >= PASS:
            est = lv
        else:
            break
    return est


def _own_test(tid):
    u = U.current()
    if not u:
        abort(403)
    with connect() as c:
        t = c.execute("SELECT * FROM placement_tests WHERE id=%s AND user_id=%s", (tid, u["id"])).fetchone()
    if not t:
        abort(404)
    return t


def can_take(u):
    return u and u["role"] in ("parent", "eleve")


def _nocache(html):
    resp = web.app.make_response(html)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


# ---------- parcours ----------

@web.app.before_request
def bigger_recordings():
    if request.endpoint == "placement_record":
        request.max_content_length = REC_MAX + 256 * 1024


@web.route("/test-de-niveau", methods=["GET", "POST"])
def placement_home():
    p, u = pt(g.lang), U.current()
    errors, form = [], {}
    tests = []
    if u:
        with connect() as c:
            tests = c.execute("SELECT * FROM placement_tests WHERE user_id=%s ORDER BY created_at DESC", (u["id"],)).fetchall()
    if request.method == "POST":
        U.check_csrf()
        if not can_take(u):
            abort(403)
        form = {"child_label": (request.form.get("child_label") or "").strip()[:40], "age": (request.form.get("age") or "").strip()}
        age = int(form["age"]) if form["age"].isdigit() and 3 <= int(form["age"]) <= 99 else None
        if u["role"] == "parent" and not form["child_label"]:
            errors.append(p["err_child"])
        if form["age"] and not age:
            errors.append(p["err_age"])
        if not errors:
            with connect() as c:
                tid = c.execute("INSERT INTO placement_tests (user_id, child_label, age) VALUES (%s,%s,%s) RETURNING id",
                                (u["id"], form["child_label"] if u["role"] == "parent" else None, age)).fetchone()["id"]
            return redirect(url_for("placement_step", tid=tid))
    return _nocache(render_template("placement/home.html", p=p, u=u, tests=tests, errors=errors, form=form, can_take=can_take(u)))


@web.route("/test-de-niveau/<int:tid>", methods=["GET", "POST"])
def placement_step(tid):
    p, t = pt(g.lang), _own_test(tid)
    if t["step"] in ("submitted", "evaluated"):
        return redirect(url_for("placement_done", tid=tid))
    errors = []
    with connect() as c:
        if t["step"] == "qcm":
            lv = LEVELS[t["qcm_level_idx"]]
            items = items_for(c, lv, tid)
            if request.method == "POST":
                U.check_csrf()
                answers, good = dict(t["answers"] or {}), 0
                for it in items:
                    v = request.form.get(f"q{it['id']}")
                    if v is None or not (v == "-1" or v.isdigit()):
                        errors.append(p["err_all"]); break
                    answers[str(it["id"])] = int(v)
                    good += int(v) == it["answer"]
                if not errors:
                    scores = dict(t["scores"] or {}); scores[lv] = [good, len(items)]
                    ok = items and good / len(items) >= PASS
                    nxt = t["qcm_level_idx"] + 1
                    if ok and nxt < len(LEVELS):
                        c.execute("UPDATE placement_tests SET answers=%s, scores=%s, qcm_level_idx=%s, updated_at=now() WHERE id=%s",
                                  (Jsonb(answers), Jsonb(scores), nxt, tid))
                    else:
                        c.execute("UPDATE placement_tests SET answers=%s, scores=%s, est_level=%s, step='writing', updated_at=now() WHERE id=%s",
                                  (Jsonb(answers), Jsonb(scores), estimate(scores), tid))
                    return redirect(url_for("placement_step", tid=tid))
            view = [dict(it, choices=shuffled(tid, it), audio=url_for("placement_audio", name=it["audio_file"]) if it["audio_file"] else None) for it in items]
            passages = []
            for it in view:  # un texte de lecture n'est affiché qu'une fois, avant sa première question
                it["show_passage"] = bool(it["passage"]) and it["passage"] not in passages
                if it["passage"]:
                    passages.append(it["passage"])
            return _nocache(render_template("placement/qcm.html", p=p, t=t, lv=lv, n=t["qcm_level_idx"] + 1, items=view, errors=errors))
        if t["step"] == "writing":
            prompt = WRITING[t["est_level"] or "A1.1"]
            if request.method == "POST":
                U.check_csrf()
                txt = (request.form.get("writing") or "").strip()[:4000]
                if len(txt) < 5:
                    errors.append(p["err_writing"])
                else:
                    c.execute("UPDATE placement_tests SET writing_text=%s, step='oral', updated_at=now() WHERE id=%s", (txt, tid))
                    return redirect(url_for("placement_step", tid=tid))
            return _nocache(render_template("placement/writing.html", p=p, t=t, prompt=prompt, errors=errors, text=request.form.get("writing", "")))
        # oral
        recs = {r["task"]: r for r in c.execute("SELECT * FROM placement_recordings WHERE test_id=%s", (tid,)).fetchall()}
        lv = t["est_level"] or "A1.1"
        if request.method == "POST":
            U.check_csrf()
            mode = request.form.get("mode")
            if mode == "live":
                c.execute("UPDATE placement_tests SET oral_mode='live', step='submitted', submitted_at=now(), updated_at=now() WHERE id=%s", (tid,))
            elif mode == "record":
                if not t["oral_consent_at"]:
                    errors.append(p["err_consent"])
                elif len(recs) < 3:
                    errors.append(p["err_rec"])
                else:
                    c.execute("UPDATE placement_tests SET oral_mode='record', step='submitted', submitted_at=now(), updated_at=now() WHERE id=%s", (tid,))
            if not errors and mode in ("live", "record"):
                import mailer
                mailer.notify_team("Nouveau test de niveau à évaluer", f"Un test de niveau vient d'être envoyé (estimation du QCM : {t['est_level']}).\n{web.SITE_URL}/admin/tests/{tid}" + mailer.SIGN)
                return redirect(url_for("placement_done", tid=tid))
        return _nocache(render_template("placement/oral.html", p=p, t=t, recs=recs, read=ORAL_READ[lv], question=ORAL_QUESTION[lv], errors=errors))


@web.route("/test-de-niveau/<int:tid>/consentement", methods=["POST"])
def placement_consent(tid):
    t = _own_test(tid)
    U.check_csrf()
    if t["step"] == "oral" and request.form.get("consent"):
        with connect() as c:
            c.execute("UPDATE placement_tests SET oral_consent_at=COALESCE(oral_consent_at, now()) WHERE id=%s", (tid,))
    return redirect(url_for("placement_step", tid=tid))


@web.route("/test-de-niveau/<int:tid>/enregistrement/<int:task>", methods=["POST"])
def placement_record(tid, task):
    t = _own_test(tid)
    U.check_csrf()
    if t["step"] != "oral" or not t["oral_consent_at"] or task not in (1, 2, 3):
        abort(400)
    f = request.files.get("audio")
    if not f:
        abort(400)
    data = f.read(REC_MAX + 1)
    if len(data) > REC_MAX or len(data) < 200:
        abort(413 if len(data) > REC_MAX else 400)
    if data[:4] == b"\x1a\x45\xdf\xa3":
        ext = "webm"
    elif data[:4] == b"OggS":
        ext = "ogg"
    elif data[4:8] == b"ftyp":
        ext = "m4a"
    else:
        abort(415)
    os.makedirs(REC_DIR, exist_ok=True)
    name = f"p{tid}-{secrets.token_hex(6)}.{ext}"
    with open(os.path.join(REC_DIR, name), "wb") as out:
        out.write(data)
    with connect() as c:
        old = c.execute("SELECT file_name FROM placement_recordings WHERE test_id=%s AND task=%s", (tid, task)).fetchone()
        c.execute("""INSERT INTO placement_recordings (test_id, task, file_name) VALUES (%s,%s,%s)
                     ON CONFLICT (test_id, task) DO UPDATE SET file_name=EXCLUDED.file_name, created_at=now()""", (tid, task, name))
    if old:
        _rm(REC_DIR, old["file_name"])
    return {"ok": True}


@web.route("/test-de-niveau/<int:tid>/termine")
def placement_done(tid):
    t = _own_test(tid)
    return _nocache(render_template("placement/done.html", p=pt(g.lang), t=t))


@web.route("/test-de-niveau/<int:tid>/supprimer-enregistrements", methods=["POST"])
def placement_delete_recordings(tid):
    _own_test(tid)
    U.check_csrf()
    delete_recordings(tid)
    return redirect(url_for("account_home", enregistrements="supprimes"))


@web.app.route("/test-de-niveau/audio/<name>")
def placement_audio(name):
    """Audios des questions d'écoute (enregistrés par l'équipe) : pour les comptes connectés."""
    if not U.current() or not re.fullmatch(r"a\d+-[0-9a-f]{12}\.(mp3|m4a|ogg|webm)", name):
        abort(404)
    return send_from_directory(AUDIO_DIR, name, conditional=True, max_age=3600)


def tests_for_account(uid, lang):
    with connect() as c:
        rows = c.execute("""SELECT t.*, l.level AS c_level, l.days AS c_days, l.start_bj AS c_start,
                                   (SELECT count(*) FROM placement_recordings r WHERE r.test_id=t.id) AS n_rec
                            FROM placement_tests t LEFT JOIN live_classes l ON l.id=t.class_id
                            WHERE t.user_id=%s ORDER BY t.created_at DESC""", (uid,)).fetchall()
    return rows


# ---------- admin ----------

@bp.route("/tests")
def tests_admin():
    purge_recordings()
    status = request.args.get("statut", "a-evaluer")
    where = {"a-evaluer": "t.step='submitted'", "evalues": "t.step='evaluated'", "en-cours": "t.step IN ('qcm','writing','oral')"}.get(status, "true")
    with connect() as c:
        rows = c.execute(f"""SELECT t.*, u.name AS u_name, u.role AS u_role, u.lang AS u_lang,
                                    (SELECT count(*) FROM placement_recordings r WHERE r.test_id=t.id) AS n_rec
                             FROM placement_tests t JOIN users u ON u.id=t.user_id WHERE {where} ORDER BY t.submitted_at DESC NULLS LAST, t.created_at DESC LIMIT 300""").fetchall()
        counts = c.execute("""SELECT count(*) FILTER (WHERE step='submitted') AS a, count(*) FILTER (WHERE step='evaluated') AS e,
                                     count(*) FILTER (WHERE step IN ('qcm','writing','oral')) AS c FROM placement_tests""").fetchone()
    return render_template("admin/tests.html", rows=rows, status=status, counts=counts)


@bp.route("/tests/<int:tid>", methods=["GET", "POST"])
def test_admin(tid):
    import liveclasses as L
    with connect() as c:
        t = c.execute("""SELECT t.*, u.name AS u_name, u.email AS u_email, u.role AS u_role, u.lang AS u_lang
                         FROM placement_tests t JOIN users u ON u.id=t.user_id WHERE t.id=%s""", (tid,)).fetchone()
        if not t:
            abort(404)
        classes = c.execute("SELECT * FROM live_classes WHERE status <> 'closed' ORDER BY level, start_bj").fetchall()
    errors = []
    if request.method == "POST":
        _check_csrf()
        f = request.form
        action = f.get("action")
        if action == "delete_recordings":
            delete_recordings(tid)
            return redirect(url_for("admin.test_admin", tid=tid, ok="enregistrements"))
        if action == "delete":
            from admin import require_admin
            require_admin()
            delete_recordings(tid)
            with connect() as c:
                c.execute("DELETE FROM placement_tests WHERE id=%s", (tid,))
            return redirect(url_for("admin.tests_admin"))
        lv_ok = ("A1.1",) + LEVELS + ("C1", "C2")
        v = {k: (f.get(k) if f.get(k) in lv_ok else None) for k in ("writing_level", "oral_level", "final_level")}
        v["class_id"] = int(f["class_id"]) if (f.get("class_id") or "").isdigit() else None
        v["family_msg"] = (f.get("family_msg") or "").strip()[:3000] or None
        v["notes"] = (f.get("notes") or "").strip()[:3000] or None
        if action == "evaluate" and not v["final_level"]:
            errors.append("Indiquez le niveau final avant d'envoyer le résultat.")
        if not errors:
            me = U.current()
            with connect() as c:
                c.execute("""UPDATE placement_tests SET writing_level=%(writing_level)s, oral_level=%(oral_level)s, final_level=%(final_level)s,
                               class_id=%(class_id)s, family_msg=%(family_msg)s, notes=%(notes)s, updated_at=now() WHERE id=%(id)s""", dict(v, id=tid))
                if action == "evaluate":
                    c.execute("UPDATE placement_tests SET step='evaluated', evaluated_at=COALESCE(evaluated_at, now()), evaluated_by=%s WHERE id=%s", (me["id"], tid))
            if action == "evaluate":
                lang = t["u_lang"] or "zh"
                subj = "水平测试结果已出 — 法语之家" if lang == "zh" else "Résultat du test de niveau — Maison du français"
                who = t["child_label"] or t["u_name"]
                body = (f"您好：\n\n{who} 的法语水平测试结果已出：建议级别 {v['final_level']}。\n请登录“我的账户”查看老师的评语和分班建议：\n{U.link('account_home', 'zh')}"
                        if lang == "zh" else
                        f"Bonjour,\n\nLe résultat du test de niveau de {who} est disponible : niveau conseillé {v['final_level']}.\n"
                        f"Le commentaire du professeur et la classe proposée sont dans « Mon compte » :\n{U.link('account_home', 'fr')}")
                import mailer
                mailer.send(t["u_email"], subj, body + mailer.SIGN)
            return redirect(url_for("admin.test_admin", tid=tid, ok=action or "1"))
    with connect() as c:
        items = {str(r["id"]): r for r in c.execute("SELECT * FROM placement_items").fetchall()}
        recs = c.execute("SELECT * FROM placement_recordings WHERE test_id=%s ORDER BY task", (tid,)).fetchall()
    answers = [(items[k], v) for k, v in (t["answers"] or {}).items() if k in items]
    answers.sort(key=lambda a: (LEVELS.index(a[0]["level"]), a[0]["sort"]))
    lv = t["est_level"] or "A1.1"
    return render_template("admin/test.html", t=t, answers=answers, recs=recs, classes=classes, errors=errors, levels=("A1.1",) + LEVELS + ("C1", "C2"),
                           writing_prompt=WRITING[lv][0], read=ORAL_READ[lv], question=ORAL_QUESTION[lv], ok=request.args.get("ok"),
                           paris_time=L.paris_time, keep=KEEP_AFTER_EVAL)


@bp.route("/tests/enregistrement/<name>")
def test_recording(name):
    if not re.fullmatch(r"p\d+-[0-9a-f]{12}\.(webm|ogg|m4a)", name):
        abort(404)
    resp = send_from_directory(REC_DIR, name, conditional=True, max_age=0)
    resp.headers["Cache-Control"] = "private, no-store"
    return resp


@bp.route("/tests/questions", methods=["GET", "POST"])
def test_items():
    msg = None
    if request.method == "POST":
        _check_csrf()
        iid = request.form.get("item_id", type=int)
        with connect() as c:
            it = c.execute("SELECT * FROM placement_items WHERE id=%s", (iid,)).fetchone()
            if not it:
                abort(404)
            if request.form.get("action") == "toggle":
                c.execute("UPDATE placement_items SET active = NOT active WHERE id=%s", (iid,)); msg = "Question mise à jour."
            elif request.form.get("action") == "audio":
                up = request.files.get("audio")
                data = up.read(12 * 1024 * 1024 + 1) if up else b""
                ext = "mp3" if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3") else ("m4a" if data[4:8] == b"ftyp" else ("ogg" if data[:4] == b"OggS" else None))
                if not ext or len(data) > 12 * 1024 * 1024:
                    msg = "Audio refusé : MP3, M4A ou OGG, 12 Mo au plus."
                else:
                    os.makedirs(AUDIO_DIR, exist_ok=True)
                    name = f"a{iid}-{secrets.token_hex(6)}.{ext}"
                    with open(os.path.join(AUDIO_DIR, name), "wb") as out:
                        out.write(data)
                    c.execute("UPDATE placement_items SET audio_file=%s WHERE id=%s", (name, iid))
                    _rm(AUDIO_DIR, it["audio_file"])
                    msg = "Audio enregistré : la question d'écoute est maintenant posée."
    with connect() as c:
        items = c.execute("SELECT * FROM placement_items ORDER BY level, sort").fetchall()
    return render_template("admin/test_items.html", items=items, msg=msg)


@bp.before_request
def bigger_audio():
    if request.endpoint == "admin.test_items":
        request.max_content_length = 13 * 1024 * 1024

