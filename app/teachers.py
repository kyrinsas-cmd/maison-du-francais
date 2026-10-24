"""Fiches professeurs : gérées par l'équipe dans /admin/professeurs, publiées sur le site (accueil + /professeurs/<slug>).

Règles (cahier des charges §6–7, NOTES.md) :
- aucune fiche publiée sans l'accord écrit du professeur (date + référence obligatoires) ;
- la vidéo de présentation n'est affichée qu'une fois validée (statut « approved ») ;
- photos ré-encodées en JPEG sans EXIF ; vidéos MP4/WebM stockées telles quelles (pas de ffmpeg sur le serveur).
"""
import os
import re
import secrets
import unicodedata

from flask import abort, g, redirect, render_template, request, url_for

import web
from admin import _check_csrf, bp
from db import connect

UPLOADS = os.path.join(os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads"), "teachers")
LEVELS = ("A1", "A2", "B1", "B2")
VIDEO_STATUSES = {"none": "Aucune vidéo", "pending": "En attente de validation", "approved": "Validée", "changes": "À modifier"}
PHOTO_MAX = 15 * 1024 * 1024
VIDEO_MAX = 150 * 1024 * 1024
UPLOAD_MAX = PHOTO_MAX + VIDEO_MAX + 1024 * 1024


# ---------- affichage ----------

def display_name(t):
    return t["first_name"] + (f" {t['last_initial'].rstrip('.')}." if t.get("last_initial") else "")


def ages_label(t, lang):
    a, b = t.get("ages_min"), t.get("ages_max")
    if not a and not b:
        return None
    span = f"{a}–{b}" if a and b else f"{a or b}"
    return f"{span} 岁" if lang == "zh" else f"{span} ans"


def lines(text):
    return [x.strip() for x in (text or "").splitlines() if x.strip()]


def public_view(t, lang):
    return {
        "slug": t["slug"],
        "name": display_name(t),
        "diplomas": t["diplomas"],
        "levels": " · ".join(t["levels"] or []),
        "ages": ages_label(t, lang),
        "bio": (t["bio_zh"] if lang == "zh" else t["bio_fr"]) or "",
        "courses": lines(t["courses_zh"] if lang == "zh" else t["courses_fr"]),
        "photo": f"/uploads/teachers/{t['photo_file']}" if t["photo_file"] else None,
        "video": f"/uploads/teachers/{t['video_file']}" if t["video_file"] and t["video_status"] == "approved" else None,
        "video_type": "video/webm" if (t["video_file"] or "").endswith(".webm") else "video/mp4",
    }


def published(lang):
    with connect() as c:
        rows = c.execute("SELECT * FROM teachers WHERE published ORDER BY sort, id").fetchall()
    return [public_view(t, lang) for t in rows]


def publish_problems(t):
    """Ce qui manque pour pouvoir publier la fiche."""
    p = []
    if not t["consent_at"] or not (t["consent_ref"] or "").strip():
        p.append("l'accord écrit du professeur (date et référence)")
    if not t["photo_file"]:
        p.append("une photo")
    if not (t["bio_zh"] or "").strip():
        p.append("la présentation en chinois")
    if not (t["bio_fr"] or "").strip():
        p.append("la présentation en français")
    if not (t["diplomas"] or "").strip():
        p.append("les diplômes")
    return p


# ---------- pages publiques ----------

@web.app.context_processor
def teachers_ctx():
    return {"published_teachers": lambda: published(web.current_lang())}


@web.route("/professeurs")
def teachers_page():
    return render_template("teachers_list.html", teachers=published(g.lang))


@web.route("/professeurs/<slug>")
def teacher_page(slug):
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE slug=%s AND published", (slug,)).fetchone()
    if not t:
        abort(404)
    import reviews
    rs, rlist = reviews.for_teacher(slug, g.lang)
    return render_template("teacher.html", tp=public_view(t, g.lang), rsum=rs, rlist=rlist)


@web.app.route("/uploads/teachers/<name>")
def teacher_file(name):
    """Photos et vidéos des professeurs (noms aléatoires, requêtes partielles gérées pour les vidéos)."""
    from flask import send_from_directory
    if not re.fullmatch(r"t\d+-[0-9a-f]{12}\.(jpg|mp4|webm)", name):
        abort(404)
    resp = send_from_directory(UPLOADS, name, conditional=True, max_age=7 * 24 * 3600)
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


def sitemap_paths():
    with connect() as c:
        return [f"/professeurs/{r['slug']}" for r in c.execute("SELECT slug FROM teachers WHERE published").fetchall()]


# ---------- fichiers ----------

def _slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "prof"


def _remove(name):
    if name and re.fullmatch(r"[a-z0-9-]+\.(jpg|mp4|webm)", name):
        try:
            os.remove(os.path.join(UPLOADS, name))
        except FileNotFoundError:
            pass


def _save_photo(tid, f):
    from PIL import Image, ImageOps
    data = f.read(PHOTO_MAX + 1)
    if len(data) > PHOTO_MAX:
        raise ValueError("Photo trop lourde (15 Mo au plus).")
    import io
    try:
        im = Image.open(io.BytesIO(data))
        im.verify()
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    except Exception:
        raise ValueError("La photo n'est pas une image valide (JPEG, PNG ou WebP).")
    im.thumbnail((1200, 1200))
    name = f"t{tid}-{secrets.token_hex(6)}.jpg"
    os.makedirs(UPLOADS, exist_ok=True)
    im.save(os.path.join(UPLOADS, name), "JPEG", quality=85, optimize=True, progressive=True)
    return name


def _save_video(tid, f):
    head = f.stream.read(12)
    if len(head) >= 8 and head[4:8] == b"ftyp":
        ext = "mp4"
    elif head[:4] == b"\x1a\x45\xdf\xa3":
        ext = "webm"
    else:
        raise ValueError("La vidéo doit être au format MP4 (H.264 conseillé) ou WebM.")
    name = f"t{tid}-{secrets.token_hex(6)}.{ext}"
    os.makedirs(UPLOADS, exist_ok=True)
    path = os.path.join(UPLOADS, name)
    size = len(head)
    with open(path, "wb") as out:
        out.write(head)
        while chunk := f.stream.read(1024 * 1024):
            size += len(chunk)
            if size > VIDEO_MAX:
                out.close()
                os.remove(path)
                raise ValueError("Vidéo trop lourde (150 Mo au plus).")
            out.write(chunk)
    return name


# ---------- admin ----------

@bp.before_request
def bigger_uploads():
    if request.endpoint in ("admin.teacher", "admin.teacher_new"):
        request.max_content_length = UPLOAD_MAX


@bp.route("/professeurs")
def teachers_list():
    with connect() as c:
        rows = c.execute("SELECT * FROM teachers ORDER BY published DESC, sort, id").fetchall()
    return render_template("admin/teachers.html", rows=rows, display_name=display_name, vstatus=VIDEO_STATUSES)


@bp.route("/professeurs/nouveau", methods=["GET", "POST"])
def teacher_new():
    if request.method == "POST":
        _check_csrf()
        first = (request.form.get("first_name") or "").strip()[:60]
        if not first:
            return render_template("admin/teacher_new.html", error="Indiquez au moins le prénom.", app_id=request.form.get("application_id")), 422
        app_id = request.form.get("application_id")
        app_id = int(app_id) if app_id and app_id.isdigit() else None
        with connect() as c:
            diplomas = None
            if app_id:
                a = c.execute("SELECT diploma FROM teacher_applications WHERE id=%s", (app_id,)).fetchone()
                diplomas = a["diploma"] if a else None
            tid = c.execute("""INSERT INTO teachers (first_name, last_initial, slug, diplomas, application_id)
                               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                            (first, (request.form.get("last_initial") or "").strip()[:3] or None,
                             f"tmp-{secrets.token_hex(8)}", diplomas, app_id)).fetchone()["id"]
            c.execute("UPDATE teachers SET slug=%s WHERE id=%s", (f"{_slugify(first)}-{tid}", tid))
        return redirect(url_for("admin.teacher", tid=tid))
    pre = {}
    aid = request.args.get("candidature")
    if aid and aid.isdigit():
        with connect() as c:
            a = c.execute("SELECT id, full_name FROM teacher_applications WHERE id=%s", (int(aid),)).fetchone()
        if a:
            parts = a["full_name"].split()
            pre = {"first_name": parts[0], "last_initial": parts[-1][:1].upper() if len(parts) > 1 else "", "application_id": a["id"]}
    return render_template("admin/teacher_new.html", pre=pre)


@bp.route("/professeurs/<int:tid>", methods=["GET", "POST"])
def teacher(tid):
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
    if not t:
        abort(404)
    errors = []
    if request.method == "POST":
        _check_csrf()
        f = request.form
        if f.get("action") == "delete":
            with connect() as c:
                c.execute("DELETE FROM teachers WHERE id=%s", (tid,))
            for name in (t["photo_file"], t["video_file"], (t["pending"] or {}).get("photo_file"), (t["pending"] or {}).get("video_file")):
                _remove(name)
            return redirect(url_for("admin.teachers_list", supprime=1))

        def num(k):
            v = (f.get(k) or "").strip()
            return int(v) if v.isdigit() and 0 < int(v) < 100 else None
        vals = {
            "first_name": (f.get("first_name") or "").strip()[:60] or t["first_name"],
            "last_initial": (f.get("last_initial") or "").strip()[:3] or None,
            "diplomas": (f.get("diplomas") or "").strip()[:300] or None,
            "ages_min": num("ages_min"), "ages_max": num("ages_max"),
            "levels": [lv for lv in LEVELS if f.get(f"level_{lv}")],
            "bio_zh": (f.get("bio_zh") or "").strip()[:4000] or None,
            "bio_fr": (f.get("bio_fr") or "").strip()[:4000] or None,
            "courses_zh": (f.get("courses_zh") or "").strip()[:2000] or None,
            "courses_fr": (f.get("courses_fr") or "").strip()[:2000] or None,
            "consent_at": (f.get("consent_at") or None),
            "consent_ref": (f.get("consent_ref") or "").strip()[:300] or None,
            "sort": int(f.get("sort")) if (f.get("sort") or "").lstrip("-").isdigit() else 0,
            "video_status": f.get("video_status") if f.get("video_status") in VIDEO_STATUSES else t["video_status"],
            "video_feedback": (f.get("video_feedback") or "").strip()[:2000] or None,
            "photo_file": t["photo_file"], "video_file": t["video_file"],
        }
        if vals["consent_at"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", vals["consent_at"]):
            vals["consent_at"] = None
        old_files = []
        try:
            ph = request.files.get("photo")
            if f.get("remove_photo"):
                old_files.append(vals["photo_file"]); vals["photo_file"] = None
            if ph and ph.filename:
                old_files.append(vals["photo_file"]); vals["photo_file"] = _save_photo(tid, ph)
            vd = request.files.get("video")
            if f.get("remove_video"):
                old_files.append(vals["video_file"]); vals["video_file"] = None; vals["video_status"] = "none"
            if vd and vd.filename:
                old_files.append(vals["video_file"]); vals["video_file"] = _save_video(tid, vd); vals["video_status"] = "pending"
        except ValueError as e:
            errors.append(str(e))
        if not vals["video_file"]:
            vals["video_status"] = "none"
        want_publish = bool(f.get("published"))
        merged = dict(t, **vals)
        problems = publish_problems(merged)
        if want_publish and problems:
            errors.append("Impossible de publier : il manque " + ", ".join(problems) + ".")
            want_publish = False
        vals["published"] = want_publish
        with connect() as c:
            c.execute("""UPDATE teachers SET first_name=%(first_name)s, last_initial=%(last_initial)s, diplomas=%(diplomas)s,
                           ages_min=%(ages_min)s, ages_max=%(ages_max)s, levels=%(levels)s, bio_zh=%(bio_zh)s, bio_fr=%(bio_fr)s,
                           courses_zh=%(courses_zh)s, courses_fr=%(courses_fr)s, consent_at=%(consent_at)s, consent_ref=%(consent_ref)s,
                           sort=%(sort)s, video_status=%(video_status)s, video_feedback=%(video_feedback)s,
                           photo_file=%(photo_file)s, video_file=%(video_file)s, published=%(published)s, updated_at=now()
                         WHERE id=%(id)s""", dict(vals, id=tid))
            t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
        for name in old_files:
            if name and name not in (t["photo_file"], t["video_file"]):
                _remove(name)
        if not errors:
            return redirect(url_for("admin.teacher", tid=tid, ok=1))
    return render_teacher_admin(tid, errors=errors, msg=request.args.get("ok") and "Enregistré.")


def render_teacher_admin(tid, errors=None, msg=None, link=None, link_kind=None, link_mailed=None):
    import accounts
    with connect() as c:
        t = c.execute("SELECT * FROM teachers WHERE id=%s", (tid,)).fetchone()
    if not t:
        abort(404)
    return render_template("admin/teacher.html", t=t, levels=LEVELS, vstatus=VIDEO_STATUSES, errors=errors or [], msg=msg,
                           problems=publish_problems(t), display_name=display_name, account=accounts.account_for(tid),
                           pending=accounts.pending_view(t) if t["pending"] else None, default_email=accounts.default_email(t),
                           link=link, link_kind=link_kind, link_mailed=link_mailed)
