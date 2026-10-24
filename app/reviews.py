"""Notes et avis sur les professeurs (cahier des charges §18) : /avis, section sur chaque page professeur, /admin/avis.

Les familles n'ont pas de compte sur ce serveur (leurs données restent en Chine, §11–12) : l'équipe saisit les avis réels
recueillis auprès d'elles (WeChat, questionnaire), avec leur source et l'accord de publication de l'auteur, puis les modère.
Affichage : du plus récent au plus ancien, sans tri par note ; refus seulement pour les motifs de REJECT_REASONS.
Mention de transparence affichée avec les avis (Code de la consommation, art. L111-7-2 et D111-17).
"""
from datetime import date

from flask import abort, g, redirect, render_template, request, url_for

import teachers as T
import web
from admin import _check_csrf, bp
from db import connect

STATUSES = {"pending": "À modérer", "published": "Publié", "rejected": "Refusé"}
REJECT_REASONS = ["Propos injurieux ou diffamatoires", "Données personnelles (nom, téléphone…)", "Sans rapport avec le cours",
                  "Auteur non vérifié (pas d'élève de ce professeur)", "Accord de publication retiré"]
LOW = 2  # une note ≤ 2 est signalée dans l'admin (§18 : « alerte pour une note basse »)


def stars(r):
    r = round(float(r or 0))
    return "★" * r + "☆" * (5 - r)


def summary(c, teacher_id=None):
    q = "SELECT count(*) AS n, avg(rating) AS avg FROM reviews WHERE status='published'" + (" AND teacher_id=%s" if teacher_id else "")
    row = c.execute(q, (teacher_id,) if teacher_id else ()).fetchone()
    return {"n": row["n"], "avg": round(float(row["avg"]), 1) if row["avg"] is not None else None}


def public_list(c, lang, teacher_id=None, limit=None):
    q = """SELECT r.*, t.first_name, t.last_initial, t.slug FROM reviews r JOIN teachers t ON t.id=r.teacher_id
           WHERE r.status='published' AND t.published""" + (" AND r.teacher_id=%s" if teacher_id else "") + \
        " ORDER BY r.published_at DESC, r.id DESC" + (f" LIMIT {int(limit)}" if limit else "")
    out = []
    for r in c.execute(q, (teacher_id,) if teacher_id else ()).fetchall():
        text, original = (r["comment_zh"], False) if lang == "zh" else ((r["comment_fr"], False) if r["comment_fr"] else (r["comment_zh"], True))
        out.append({"rating": r["rating"], "stars": stars(r["rating"]), "text": text, "original": original and bool(text),
                    "author": r["author_label"], "level": r["level"], "month": r["course_month"],
                    "teacher": T.display_name(r), "slug": r["slug"]})
    return out


def month_label(d, lang):
    if not d:
        return ""
    return f"{d.year}年{d.month}月" if lang == "zh" else f"{('janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre')[d.month - 1]} {d.year}"


@web.app.context_processor
def reviews_ctx():
    def teacher_summary(slug):
        with connect() as c:
            t = c.execute("SELECT id FROM teachers WHERE slug=%s", (slug,)).fetchone()
            return summary(c, t["id"]) if t else {"n": 0, "avg": None}
    def reviews_live():
        with connect() as c:
            return summary(c)["n"] > 0
    return {"teacher_summary": teacher_summary, "reviews_live": reviews_live, "month_label": lambda d: month_label(d, web.current_lang()), "stars": stars}


def for_teacher(slug, lang):
    with connect() as c:
        t = c.execute("SELECT id FROM teachers WHERE slug=%s AND published", (slug,)).fetchone()
        if not t:
            return None, []
        return summary(c, t["id"]), public_list(c, lang, t["id"])


@web.route("/avis")
def reviews_page():
    with connect() as c:
        s = summary(c)
        rows = public_list(c, g.lang)
    return render_template("reviews.html", s=s, rows=rows)


def sitemap_paths():
    with connect() as c:
        return ["/avis"] if summary(c)["n"] else []


# ---------- admin ----------

def _form_values(f):
    errors = []
    try:
        rating = int(f.get("rating", ""))
        assert 1 <= rating <= 5
    except (ValueError, AssertionError):
        rating = None
        errors.append("Choisissez une note de 1 à 5.")
    month = (f.get("course_month") or "").strip()
    try:
        course_month = date.fromisoformat(month + "-01") if month else None
    except ValueError:
        course_month = None
        errors.append("Mois du cours invalide.")
    tid = f.get("teacher_id")
    vals = {
        "teacher_id": int(tid) if tid and tid.isdigit() else None,
        "rating": rating,
        "comment_zh": (f.get("comment_zh") or "").strip()[:3000] or None,
        "comment_fr": (f.get("comment_fr") or "").strip()[:3000] or None,
        "author_label": (f.get("author_label") or "").strip()[:80],
        "level": f.get("level") if f.get("level") in T.LEVELS else None,
        "course_month": course_month,
        "source": (f.get("source") or "").strip()[:300],
        "consent_publish": bool(f.get("consent_publish")),
    }
    if not vals["teacher_id"]:
        errors.append("Choisissez le professeur.")
    if not vals["author_label"]:
        errors.append("Indiquez l'auteur (sans nom complet : « Léo 的妈妈 », « parent d'élève A1 »…).")
    if not vals["source"]:
        errors.append("Indiquez d'où vient l'avis (message WeChat du…, questionnaire du…) : un avis sans source ne peut pas être enregistré.")
    return vals, errors


@bp.route("/avis")
def reviews_admin():
    status = request.args.get("statut")
    status = status if status in STATUSES else None
    with connect() as c:
        counts = {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) AS n FROM reviews GROUP BY status").fetchall()}
        rows = c.execute("""SELECT r.*, t.first_name, t.last_initial FROM reviews r JOIN teachers t ON t.id=r.teacher_id
                            """ + ("WHERE r.status=%s " if status else "") + "ORDER BY r.created_at DESC LIMIT 200",
                         (status,) if status else ()).fetchall()
        per_teacher = c.execute("""SELECT t.id, t.first_name, t.last_initial, count(r.id) AS n, round(avg(r.rating), 1) AS avg,
                                          count(*) FILTER (WHERE r.rating <= %s) AS low
                                   FROM teachers t JOIN reviews r ON r.teacher_id=t.id AND r.status='published'
                                   GROUP BY t.id ORDER BY t.first_name""", (LOW,)).fetchall()
    return render_template("admin/reviews.html", rows=rows, counts=counts, status=status, statuses=STATUSES,
                           per_teacher=per_teacher, display_name=T.display_name, low=LOW)


@bp.route("/avis/nouveau", methods=["GET", "POST"])
def review_new():
    with connect() as c:
        teachers = c.execute("SELECT id, first_name, last_initial FROM teachers ORDER BY first_name").fetchall()
    errors, vals = [], {"teacher_id": request.args.get("professeur", type=int)}
    if request.method == "POST":
        _check_csrf()
        vals, errors = _form_values(request.form)
        if not errors:
            with connect() as c:
                rid = c.execute("""INSERT INTO reviews (teacher_id, rating, comment_zh, comment_fr, author_label, level, course_month, source, consent_publish)
                                   VALUES (%(teacher_id)s,%(rating)s,%(comment_zh)s,%(comment_fr)s,%(author_label)s,%(level)s,%(course_month)s,%(source)s,%(consent_publish)s)
                                   RETURNING id""", vals).fetchone()["id"]
            return redirect(url_for("admin.review", rid=rid, ok=1))
    return render_template("admin/review.html", r=None, v=vals, teachers=teachers, errors=errors, levels=T.LEVELS,
                           display_name=T.display_name, reasons=REJECT_REASONS, statuses=STATUSES)


@bp.route("/avis/<int:rid>", methods=["GET", "POST"])
def review(rid):
    with connect() as c:
        r = c.execute("SELECT * FROM reviews WHERE id=%s", (rid,)).fetchone()
        teachers = c.execute("SELECT id, first_name, last_initial FROM teachers ORDER BY first_name").fetchall()
    if not r:
        abort(404)
    errors, msg = [], request.args.get("ok") and "Enregistré."
    v = dict(r)
    if request.method == "POST":
        _check_csrf()
        action = request.form.get("action")
        if action == "delete":
            with connect() as c:
                c.execute("DELETE FROM reviews WHERE id=%s", (rid,))
            return redirect(url_for("admin.reviews_admin", supprime=1))
        v, errors = _form_values(request.form)
        status, reason = r["status"], r["reject_reason"]
        if action == "publish":
            if not v["consent_publish"]:
                errors.append("Impossible de publier sans l'accord de l'auteur.")
            else:
                status, reason = "published", None
        elif action == "reject":
            reason = request.form.get("reject_reason")
            if reason not in REJECT_REASONS:
                errors.append("Choisissez le motif du refus.")
            else:
                status = "rejected"
        elif action == "pending":
            status, reason = "pending", None
        if status == "published" and not v["consent_publish"]:
            status = "pending"  # accord retiré : l'avis quitte le site
        if not errors:
            with connect() as c:
                c.execute("""UPDATE reviews SET teacher_id=%(teacher_id)s, rating=%(rating)s, comment_zh=%(comment_zh)s, comment_fr=%(comment_fr)s,
                               author_label=%(author_label)s, level=%(level)s, course_month=%(course_month)s, source=%(source)s,
                               consent_publish=%(consent_publish)s, status=%(status)s, reject_reason=%(reason)s, updated_at=now(),
                               published_at=CASE WHEN %(status)s='published' THEN COALESCE(published_at, now()) ELSE NULL END
                             WHERE id=%(id)s""", dict(v, status=status, reason=reason, id=rid))
            return redirect(url_for("admin.review", rid=rid, ok=1))
        v.update(status=r["status"], id=rid)
    return render_template("admin/review.html", r=r, v=v, teachers=teachers, errors=errors, msg=msg, levels=T.LEVELS,
                           display_name=T.display_name, reasons=REJECT_REASONS, statuses=STATUSES)
