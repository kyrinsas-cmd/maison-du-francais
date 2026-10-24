"""Bibliothèque de ressources 教材库 (cahier des charges §7, §9) : /ressources (zh) et /fr/ressources, gestion dans /admin/ressources.

- Supports faits par l'équipe (§9, décidé). Élément tiers : source et autorisation obligatoires pour publier.
- Classement : niveau (A1–B2), compétence (听 说 读 写 / 综合), thème, âges.
- Visibilité : public (tout le monde, partie visible par les élèves en essai) ; members (comptes connectés) ;
  teachers (professeurs et équipe). Il n'y a pas encore de classes sur ce serveur : « inscrits » = comptes connectés.
- Statistiques : chaque ouverture est comptée par type de compte (jamais l'identité).
- Fichiers dans uploads/resources/ (noms aléatoires), servis par Flask après contrôle d'accès ; PDF, audio, image, Word/PowerPoint.
"""
import os
import re
import secrets

from flask import abort, g, redirect, render_template, request, send_from_directory, url_for

import teachers as T
import users as U
import web
from admin import _check_csrf, bp
from db import connect

UPLOADS = os.path.join(os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads"), "resources")
FILE_MAX = 60 * 1024 * 1024
SKILLS = ("co", "eo", "ce", "ee", "mixte")
VIS = ("public", "members", "teachers")
KINDS = {"pdf": "PDF", "audio": "Audio", "image": "Image", "doc": "Document"}


def _detect(head, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if head[:4] == b"%PDF":
        return "pdf", "pdf"
    if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio", "mp3"
    if head[4:8] == b"ftyp" and ext in ("m4a", "mp4"):
        return "audio", "m4a"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image", "png"
    if head[:3] == b"\xff\xd8\xff":
        return "image", "jpg"
    if head[:4] == b"PK\x03\x04" and ext in ("docx", "pptx"):
        return "doc", ext
    return None, None


def save_file(rid, f):
    head = f.stream.read(16)
    kind, ext = _detect(head, f.filename or "")
    if not kind:
        raise ValueError("Format non accepté : PDF, MP3/M4A, PNG/JPEG, Word (.docx) ou PowerPoint (.pptx).")
    name = f"r{rid}-{secrets.token_hex(6)}.{ext}"
    os.makedirs(UPLOADS, exist_ok=True)
    path, size = os.path.join(UPLOADS, name), len(head)
    with open(path, "wb") as out:
        out.write(head)
        while chunk := f.stream.read(1024 * 1024):
            size += len(chunk)
            if size > FILE_MAX:
                out.close(); os.remove(path)
                raise ValueError("Fichier trop lourd (60 Mo au plus).")
            out.write(chunk)
    return name, kind, size


def remove_file(name):
    if name and re.fullmatch(r"r\d+-[0-9a-f]{12}\.(pdf|mp3|m4a|png|jpg|docx|pptx)", name):
        try:
            os.remove(os.path.join(UPLOADS, name))
        except FileNotFoundError:
            pass


def can_see(vis):
    r = U.role()
    return vis == "public" or (vis == "members" and r is not None) or (vis == "teachers" and r in ("professeur", "moderateur", "admin"))


def size_label(n):
    return f"{n / 1024 / 1024:.1f} Mo" if n and n >= 1024 * 1024 else (f"{round((n or 0) / 1024)} Ko")


# ---------- public ----------

@web.route("/ressources")
def resources_page():
    lv = request.args.get("niveau") if request.args.get("niveau") in T.LEVELS else None
    sk = request.args.get("competence") if request.args.get("competence") in SKILLS else None
    where, args = ["published"], []
    if lv:
        where.append("(level=%s OR level IS NULL)"); args.append(lv)
    if sk:
        where.append("skill=%s"); args.append(sk)
    with connect() as c:
        rows = c.execute(f"SELECT * FROM resources WHERE {' AND '.join(where)} ORDER BY sort, created_at DESC", args).fetchall()
    items = []
    for r in rows:
        title = (r["title_fr"] if g.lang == "fr" and r["title_fr"] else r["title_zh"])
        desc = (r["desc_fr"] if g.lang == "fr" and r["desc_fr"] else r["desc_zh"])
        items.append(dict(r, title=title, desc=desc, allowed=can_see(r["visibility"]), size=size_label(r["file_size"])))
    return render_template("resources.html", items=items, lv=lv, sk=sk, levels=T.LEVELS, skills=SKILLS, logged=U.current() is not None)


@web.route("/ressources/<int:rid>/fichier")
def resource_file(rid):
    with connect() as c:
        r = c.execute("SELECT * FROM resources WHERE id=%s AND published", (rid,)).fetchone()
        if not r or not r["file_name"]:
            abort(404)
        if not can_see(r["visibility"]):
            return redirect(url_for("account_login", next=request.path))
        if request.headers.get("Range", "bytes=0-").startswith("bytes=0-"):  # ne compte pas chaque morceau d'un audio
            c.execute("UPDATE resources SET downloads=downloads+1 WHERE id=%s", (rid,))
            c.execute("INSERT INTO resource_hits (resource_id, role) VALUES (%s,%s)", (rid, U.role() or "visiteur"))
    resp = send_from_directory(UPLOADS, r["file_name"], conditional=True, max_age=0,
                               as_attachment=r["file_kind"] == "doc",
                               download_name=re.sub(r"[^\w\- .]", "", (r["title_fr"] or r["title_zh"]))[:60] + "." + r["file_name"].rsplit(".", 1)[1])
    resp.headers["Cache-Control"] = "private, no-store" if r["visibility"] != "public" else "public, max-age=3600"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


def sitemap_paths():
    with connect() as c:
        return ["/ressources"] if c.execute("SELECT 1 FROM resources WHERE published LIMIT 1").fetchone() else []


# ---------- admin ----------

@bp.before_request
def bigger_files():
    if request.endpoint in ("admin.resource", "admin.resource_new"):
        request.max_content_length = FILE_MAX + 1024 * 1024


def _values(f):
    errors = []
    num = lambda k: int(f[k]) if (f.get(k) or "").isdigit() and 0 < int(f[k]) < 100 else None
    v = {
        "title_zh": (f.get("title_zh") or "").strip()[:200],
        "title_fr": (f.get("title_fr") or "").strip()[:200] or None,
        "desc_zh": (f.get("desc_zh") or "").strip()[:2000] or None,
        "desc_fr": (f.get("desc_fr") or "").strip()[:2000] or None,
        "level": f.get("level") if f.get("level") in T.LEVELS else None,
        "skill": f.get("skill") if f.get("skill") in SKILLS else "mixte",
        "theme": (f.get("theme") or "").strip()[:100] or None,
        "ages_min": num("ages_min"), "ages_max": num("ages_max"),
        "visibility": f.get("visibility") if f.get("visibility") in VIS else "members",
        "origin": "tiers" if f.get("origin") == "tiers" else "maison",
        "tp_source": (f.get("tp_source") or "").strip()[:300] or None,
        "tp_license": (f.get("tp_license") or "").strip()[:300] or None,
        "sort": int(f["sort"]) if (f.get("sort") or "").lstrip("-").isdigit() else 0,
        "published": bool(f.get("published")),
    }
    if not v["title_zh"]:
        errors.append("Indiquez le titre en chinois.")
    return v, errors


def _publish_problems(v, file_name):
    p = []
    if not file_name:
        p.append("le fichier")
    if v["origin"] == "tiers" and not (v["tp_source"] and v["tp_license"]):
        p.append("la source et l'autorisation de l'élément tiers (§9)")
    return p


@bp.route("/ressources")
def resources_admin():
    with connect() as c:
        rows = c.execute("SELECT * FROM resources ORDER BY published DESC, sort, created_at DESC").fetchall()
        stats = {r["resource_id"]: r for r in c.execute("""SELECT resource_id, count(*) AS n,
                     count(*) FILTER (WHERE at > now() - interval '30 days') AS n30,
                     count(*) FILTER (WHERE role='visiteur') AS visiteur, count(*) FILTER (WHERE role='eleve') AS eleve,
                     count(*) FILTER (WHERE role='parent') AS parent, count(*) FILTER (WHERE role='professeur') AS professeur
                     FROM resource_hits GROUP BY resource_id""").fetchall()}
    return render_template("admin/resources.html", rows=rows, stats=stats, kinds=KINDS, size_label=size_label)


@bp.route("/ressources/nouvelle", methods=["GET", "POST"])
def resource_new():
    return resource(None)


@bp.route("/ressources/<int:rid>", methods=["GET", "POST"])
def resource(rid):
    r = None
    if rid:
        with connect() as c:
            r = c.execute("SELECT * FROM resources WHERE id=%s", (rid,)).fetchone()
        if not r:
            abort(404)
    errors, v = [], dict(r) if r else {"skill": "mixte", "visibility": "members", "origin": "maison", "sort": 0}
    if request.method == "POST":
        _check_csrf()
        if r and request.form.get("action") == "delete":
            from admin import require_admin
            require_admin()
            with connect() as c:
                c.execute("DELETE FROM resources WHERE id=%s", (rid,))
            remove_file(r["file_name"])
            return redirect(url_for("admin.resources_admin", supprimee=1))
        v, errors = _values(request.form)
        if not errors:
            with connect() as c:
                if not r:
                    r = c.execute("INSERT INTO resources (title_zh) VALUES (%s) RETURNING *", (v["title_zh"],)).fetchone()
                    rid = r["id"]
                file_name, kind, size, old = r["file_name"], r["file_kind"], r["file_size"], None
                up = request.files.get("file")
                if up and up.filename:
                    try:
                        old = file_name
                        file_name, kind, size = save_file(rid, up)
                    except ValueError as e:
                        errors.append(str(e)); old = None
                problems = _publish_problems(v, file_name)
                if v["published"] and problems:
                    errors.append("Impossible de publier : il manque " + ", ".join(problems) + ".")
                    v["published"] = False
                c.execute("""UPDATE resources SET title_zh=%(title_zh)s, title_fr=%(title_fr)s, desc_zh=%(desc_zh)s, desc_fr=%(desc_fr)s,
                               level=%(level)s, skill=%(skill)s, theme=%(theme)s, ages_min=%(ages_min)s, ages_max=%(ages_max)s,
                               visibility=%(visibility)s, origin=%(origin)s, tp_source=%(tp_source)s, tp_license=%(tp_license)s,
                               sort=%(sort)s, published=%(published)s, file_name=%(fn)s, file_kind=%(kind)s, file_size=%(size)s, updated_at=now()
                             WHERE id=%(id)s""", dict(v, fn=file_name, kind=kind, size=size, id=rid))
            if old:
                remove_file(old)
            if not errors:
                return redirect(url_for("admin.resource", rid=rid, ok=1))
            with connect() as c:
                r = c.execute("SELECT * FROM resources WHERE id=%s", (rid,)).fetchone()
            v.update(file_name=r["file_name"], file_kind=r["file_kind"], file_size=r["file_size"], id=rid)
    return render_template("admin/resource.html", r=r, v=v, errors=errors, levels=T.LEVELS, msg=request.args.get("ok") and "Enregistré.",
                           kinds=KINDS, size_label=size_label, problems=_publish_problems(v, v.get("file_name")) if r else None)
