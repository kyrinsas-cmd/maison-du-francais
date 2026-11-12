"""作业库 — banque de devoirs par unité du programme (2026-11-12).
- Graine : homework_seed.py (2 devoirs par unité, A1 → B2) ; l'équipe ajoute, modifie, masque (Admin → Contenus → Banque de devoirs).
- Le professeur : sur la page de sa classe, les devoirs de l'unité en cours ; « Utiliser » remplit le formulaire « Donner un devoir »
  (modifiable avant envoi). Page « Banque de devoirs » : tout le niveau, unité par unité. Il peut enregistrer son devoir dans la banque
  (visible des autres professeurs) et retirer ses propres ajouts.
- Pièce jointe d'un devoir type : copiée dans le devoir donné (les élèves y accèdent comme à toute pièce jointe de devoir)."""
import os
import shutil
import secrets

from flask import abort, redirect, render_template, request, send_from_directory, url_for

import users as U
import web
from accounts import bp as espace_bp, current as teacher_current
from admin import _check_csrf, bp as admin_bp
from db import connect
from homework import NAME_RE, UPLOADS, remove_upload, save_upload
from placement import LEVELS

KINDS = {"ecrit": "Écrit", "oral": "Oral (enregistrement)"}


def current_unit(program):
    """Unité en cours : la première marquée « en cours », sinon la première pas terminée."""
    for u in program:
        if u["status"] == "doing":
            return u
    return next((u for u in program if u["status"] != "done"), None)


def items_for_units(c, unit_ids, include_hidden=False):
    rows = c.execute(f"""SELECT b.*, (SELECT count(*) FROM homeworks h WHERE h.bank_id=b.id) AS used, u.name AS author
                         FROM homework_bank b LEFT JOIN users u ON u.id=b.created_by
                         WHERE b.unit_id = ANY(%s) {'' if include_hidden else 'AND b.active'} ORDER BY b.unit_id, b.sort, b.id""",
                     (list(unit_ids),)).fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["unit_id"], []).append(r)
    return out


def prefill(c, bank_id, level):
    """Formulaire « Donner un devoir » rempli d'après un devoir type du bon niveau."""
    b = c.execute("""SELECT b.* FROM homework_bank b JOIN program_units u ON u.id=b.unit_id WHERE b.id=%s AND b.active AND u.level=%s""",
                  (bank_id, level)).fetchone()
    if not b:
        return None
    title = b["title_fr"] + (f" · {b['title_zh']}" if b["title_zh"] else "")
    instr = "\n\n".join(x for x in (b["instr_zh"], b["instr_fr"]) if x)
    return {"id": b["id"], "unit_id": b["unit_id"], "title": title[:200], "instructions": instr[:4000], "file_name": b["file_name"]}


def copy_file(b, hid):
    """Copie la pièce jointe du devoir type pour le devoir donné ; renvoie (nom, type) ou (None, None)."""
    if not b or not b["file_name"] or not NAME_RE.fullmatch(b["file_name"]):
        return None, None
    ext = b["file_name"].rsplit(".", 1)[1]
    name = f"h{hid}-{secrets.token_hex(6)}.{ext}"
    try:
        shutil.copyfile(os.path.join(UPLOADS, b["file_name"]), os.path.join(UPLOADS, name))
    except FileNotFoundError:
        return None, None
    return name, b["file_kind"]


def add_item(c, unit_id, kind, title_fr, title_zh, instr_fr, instr_zh, source, uid):
    sort = c.execute("SELECT coalesce(max(sort), 0) + 1 AS s FROM homework_bank WHERE unit_id=%s", (unit_id,)).fetchone()["s"]
    return c.execute("""INSERT INTO homework_bank (unit_id, kind, title_fr, title_zh, instr_fr, instr_zh, sort, source, created_by)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                     (unit_id, kind if kind in KINDS else "ecrit", title_fr[:200], (title_zh or "")[:200] or None,
                      (instr_fr or "")[:4000] or None, (instr_zh or "")[:4000] or None, sort, source, uid)).fetchone()["id"]


@web.app.before_request
def bank_upload_size():
    if request.endpoint in ("admin.bank_item", "admin.bank_new"):
        from homework import FILE_MAX
        request.max_content_length = FILE_MAX + 1024 * 1024


@web.app.route("/devoirs/modele/<int:bid>/fichier")
def bank_file(bid):
    """Pièce jointe d'un devoir type : professeurs et équipe."""
    u = U.current()
    if not u or not (u["role"] in U.STAFF or (u["role"] == "professeur" and u["teacher_id"])):
        abort(404)
    with connect() as c:
        b = c.execute("SELECT file_name FROM homework_bank WHERE id=%s", (bid,)).fetchone()
    if not b or not b["file_name"] or not NAME_RE.fullmatch(b["file_name"]):
        abort(404)
    return send_from_directory(UPLOADS, b["file_name"], as_attachment=False, max_age=0)


# ---------- professeur ----------

@espace_bp.route("/devoirs/banque", methods=["GET", "POST"])
def bank_teacher():
    u = teacher_current()
    with connect() as c:
        classes = c.execute("SELECT id, level, days, start_bj FROM live_classes WHERE teacher_id=%s ORDER BY level, id", (u["teacher_id"],)).fetchall()
        level = request.values.get("niveau")
        if level not in LEVELS:
            level = classes[0]["level"][:2] if classes and classes[0]["level"][:2] in LEVELS else "A1"
        units = c.execute("SELECT * FROM program_units WHERE level=%s ORDER BY sort", (level,)).fetchall()
        ok = request.args.get("ok")
        if request.method == "POST":
            U.check_csrf()
            if request.form.get("action") == "delete":
                c.execute("DELETE FROM homework_bank WHERE id=%s AND created_by=%s AND source='teacher'", (request.form.get("bid"), u["id"]))
                ok = "retire"
            else:
                uid = request.form.get("unit_id", type=int)
                if uid in {x["id"] for x in units} and (request.form.get("title_fr") or "").strip():
                    add_item(c, uid, request.form.get("kind"), request.form["title_fr"].strip(), request.form.get("title_zh", "").strip(),
                             request.form.get("instr_fr", "").strip(), request.form.get("instr_zh", "").strip(), "teacher", u["id"])
                    ok = "ajoute"
            return redirect(url_for("espace.bank_teacher", niveau=level, ok=ok))
        items = items_for_units(c, [x["id"] for x in units])
    mine = [x for x in classes if x["level"][:2] == level]
    days = {1: "Lun", 2: "Mar", 3: "Mer", 4: "Jeu", 5: "Ven", 6: "Sam", 7: "Dim"}
    labels = [" ".join([x["level"]] + [days[d] for d in (x["days"] or []) if d in days] + ([x["start_bj"].strftime("%H:%M")] if x["start_bj"] else []))
              for x in mine]
    mine = [dict(x, label=lab + (f" · n° {x['id']}" if labels.count(lab) > 1 else "")) for x, lab in zip(mine, labels)]
    return render_template("espace/bank.html", level=level, levels=LEVELS, units=units, items=items, me=u, ok=ok, kinds=KINDS, classes=mine)


# ---------- administration ----------

@admin_bp.route("/devoirs")
def bank_admin():
    level = request.args.get("niveau") if request.args.get("niveau") in LEVELS else "A1"
    with connect() as c:
        units = c.execute("SELECT * FROM program_units WHERE level=%s ORDER BY sort", (level,)).fetchall()
        items = items_for_units(c, [x["id"] for x in units], include_hidden=True)
        counts = {r["level"]: r["n"] for r in c.execute("""SELECT u.level, count(*) AS n FROM homework_bank b JOIN program_units u ON u.id=b.unit_id
                                                            WHERE b.active GROUP BY 1""").fetchall()}
    return render_template("admin/bank.html", level=level, levels=LEVELS, units=units, items=items, counts=counts, kinds=KINDS,
                           ok=request.args.get("ok"))


def _save(c, bid, form, files):
    unit_id = form.get("unit_id", type=int)
    if not c.execute("SELECT 1 FROM program_units WHERE id=%s", (unit_id,)).fetchone():
        return None, "Choisissez l'unité."
    if not (form.get("title_fr") or "").strip():
        return None, "Le titre en français est obligatoire."
    if bid is None:
        bid = add_item(c, unit_id, form.get("kind"), form["title_fr"].strip(), form.get("title_zh", "").strip(),
                       form.get("instr_fr", "").strip(), form.get("instr_zh", "").strip(), "team", U.current()["id"])
    else:
        c.execute("""UPDATE homework_bank SET unit_id=%s, kind=%s, title_fr=%s, title_zh=%s, instr_fr=%s, instr_zh=%s, active=%s WHERE id=%s""",
                  (unit_id, form.get("kind") if form.get("kind") in KINDS else "ecrit", form["title_fr"].strip()[:200],
                   form.get("title_zh", "").strip()[:200] or None, form.get("instr_fr", "").strip()[:4000] or None,
                   form.get("instr_zh", "").strip()[:4000] or None, form.get("active") == "1", bid))
    old = c.execute("SELECT file_name FROM homework_bank WHERE id=%s", (bid,)).fetchone()["file_name"]
    f = files.get("file")
    if f and f.filename:
        try:
            name, kind = save_upload(f"b{bid}", f)
        except ValueError as e:
            return bid, "Fichier trop lourd (20 Mo au plus)." if str(e) == "size" else "Fichier refusé : PDF, image (PNG, JPEG), audio (MP3, M4A), Word ou PowerPoint."
        c.execute("UPDATE homework_bank SET file_name=%s, file_kind=%s WHERE id=%s", (name, kind, bid))
        remove_upload(old)
    elif form.get("remove_file") == "1" and old:
        c.execute("UPDATE homework_bank SET file_name=NULL, file_kind=NULL WHERE id=%s", (bid,))
        remove_upload(old)
    return bid, None


def _units_all(c):
    return c.execute("SELECT * FROM program_units ORDER BY level, sort").fetchall()


@admin_bp.route("/devoirs/nouveau", methods=["GET", "POST"])
def bank_new():
    error = None
    with connect() as c:
        if request.method == "POST":
            _check_csrf()
            bid, error = _save(c, None, request.form, request.files)
            if bid and not error:
                return redirect(url_for("admin.bank_item", bid=bid, ok="1"))
        v = dict(request.form) if request.method == "POST" else {"unit_id": request.args.get("unite", type=int), "kind": "ecrit", "active": True}
        return render_template("admin/bank_item.html", v=v, b=None, units=_units_all(c), kinds=KINDS, error=error)


@admin_bp.route("/devoirs/<int:bid>", methods=["GET", "POST"])
def bank_item(bid):
    error = None
    with connect() as c:
        b = c.execute("""SELECT b.*, u.name AS author, (SELECT count(*) FROM homeworks h WHERE h.bank_id=b.id) AS used
                         FROM homework_bank b LEFT JOIN users u ON u.id=b.created_by WHERE b.id=%s""", (bid,)).fetchone()
        if not b:
            abort(404)
        if request.method == "POST":
            _check_csrf()
            if request.form.get("action") == "delete":
                if b["key"]:      # devoir de la graine : masqué (sinon le déploiement suivant le recréerait)
                    c.execute("UPDATE homework_bank SET active=false WHERE id=%s", (bid,))
                else:
                    remove_upload(b["file_name"])
                    c.execute("DELETE FROM homework_bank WHERE id=%s", (bid,))
                level = c.execute("SELECT level FROM program_units WHERE id=%s", (b["unit_id"],)).fetchone()["level"]
                return redirect(url_for("admin.bank_admin", niveau=level, ok="supprime"))
            _, error = _save(c, bid, request.form, request.files)
            if not error:
                return redirect(url_for("admin.bank_item", bid=bid, ok="1"))
        return render_template("admin/bank_item.html", v=b, b=b, units=_units_all(c), kinds=KINDS, error=error, ok=request.args.get("ok"))
