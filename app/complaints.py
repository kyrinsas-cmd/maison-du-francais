"""Réclamations (cahier des charges §18) : tickets internes dans /admin/reclamations, suivi public par numéro sur /suivi.

- Visibles par l'équipe seulement (ni les professeurs ni le public n'y ont accès).
- L'équipe enregistre la réclamation reçue (WeChat, e-mail…), donne le numéro de suivi à la famille,
  et écrit le « message à la famille » affiché sur /suivi avec le statut. Rien d'autre n'y est affiché.
- Catégorie « sécurité des enfants » = gravité « grave » d'office ; toute réclamation grave ouverte s'affiche en bandeau
  rouge sur toutes les pages de l'admin (alerte immédiate, §18). Pas encore d'alerte par e-mail (Resend non configuré).
"""
import secrets

from flask import abort, g, redirect, render_template, request, url_for

import teachers as T
import web
from admin import _check_csrf, bp
from db import connect

CATEGORIES = {"safety": "Sécurité des enfants", "teacher": "Professeur", "teaching": "Pédagogie / contenu",
              "technical": "Technique / connexion", "schedule": "Planning / absence / rattrapage",
              "billing": "Facturation / remboursement", "other": "Autre"}
SEVERITIES = {"normal": "Normale", "high": "Haute", "grave": "Grave"}
STATUSES = {"new": "Nouvelle", "in_progress": "En cours", "waiting": "En attente de la famille", "resolved": "Résolue", "closed": "Close"}
OPEN = ("new", "in_progress", "waiting")
CHANNELS = {"wechat": "WeChat", "email": "E-mail", "phone": "Téléphone", "other": "Autre"}
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sans 0/O ni 1/I
LOOKUP_MAX = 20                                   # recherches de suivi infructueuses par heure et par empreinte IP


def new_code():
    s = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"R-{s[:4]}-{s[4:]}"


def norm_code(s):
    s = "".join(ch for ch in (s or "").upper() if ch in ALPHABET)
    return f"R-{s[-8:-4]}-{s[-4:]}" if len(s) >= 8 else None


@bp.app_context_processor
def complaints_ctx():
    def grave_open():
        if request.blueprint != "admin":
            return 0
        with connect() as c:
            return c.execute("SELECT count(*) AS n FROM complaints WHERE severity='grave' AND status = ANY(%s)", (list(OPEN),)).fetchone()["n"]
    return {"grave_open": grave_open}


# ---------- suivi public ----------

@web.route("/suivi", methods=["GET", "POST"])
def tracking():
    result, error, code = None, None, ""
    if request.method == "POST":
        _check_csrf()
        code = (request.form.get("code") or "").strip()[:20]
        h = web.ip_hash()
        with connect() as c:
            n = c.execute("SELECT count(*) AS n FROM admin_login_failures WHERE scope='suivi' AND ip_hash=%s AND at > now() - interval '1 hour'", (h,)).fetchone()["n"]
            k = norm_code(code)
            row = c.execute("SELECT code, status, public_message, updated_at FROM complaints WHERE code=%s", (k,)).fetchone() if k and n < LOOKUP_MAX else None
            if n >= LOOKUP_MAX:
                error = "rate"
            elif not row:
                c.execute("INSERT INTO admin_login_failures (ip_hash, scope) VALUES (%s, 'suivi')", (h,))
                error = "notfound"
            else:
                result = row
    return render_template("tracking.html", result=result, error=error, code=code)


# ---------- admin ----------

def _log(c, cid, text):
    c.execute("INSERT INTO complaint_events (complaint_id, text) VALUES (%s, %s)", (cid, text))


@bp.route("/reclamations")
def complaints_admin():
    status = request.args.get("statut", "ouvertes")
    cat = request.args.get("categorie")
    where, args = [], []
    if status == "ouvertes":
        where.append("c.status = ANY(%s)"); args.append(list(OPEN))
    elif status in STATUSES:
        where.append("c.status = %s"); args.append(status)
    if cat in CATEGORIES:
        where.append("c.category = %s"); args.append(cat)
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    with connect() as c:
        rows = c.execute(f"""SELECT c.*, t.first_name, t.last_initial FROM complaints c LEFT JOIN teachers t ON t.id=c.teacher_id {sql_where}
                             ORDER BY (c.severity='grave' AND c.status = ANY(%s)) DESC, c.created_at DESC LIMIT 300""", args + [list(OPEN)]).fetchall()
        counts = {r["status"]: r["n"] for r in c.execute("SELECT status, count(*) AS n FROM complaints GROUP BY status").fetchall()}
    return render_template("admin/complaints.html", rows=rows, counts=counts, status=status, cat=cat, statuses=STATUSES,
                           categories=CATEGORIES, severities=SEVERITIES, open_n=sum(counts.get(s, 0) for s in OPEN),
                           display_name=T.display_name)


def _values(f):
    errors = []
    v = {
        "category": f.get("category") if f.get("category") in CATEGORIES else None,
        "severity": f.get("severity") if f.get("severity") in SEVERITIES else "normal",
        "teacher_id": int(f["teacher_id"]) if (f.get("teacher_id") or "").isdigit() else None,
        "complainant_label": (f.get("complainant_label") or "").strip()[:80],
        "complainant_role": f.get("complainant_role") if f.get("complainant_role") in ("parent", "eleve") else "parent",
        "channel": f.get("channel") if f.get("channel") in CHANNELS else None,
        "channel_ref": (f.get("channel_ref") or "").strip()[:200] or None,
        "description": (f.get("description") or "").strip()[:6000],
    }
    if not v["category"]:
        errors.append("Choisissez une catégorie.")
    if not v["channel"]:
        errors.append("Indiquez par où la réclamation est arrivée.")
    if not v["complainant_label"]:
        errors.append("Indiquez l'auteur (sans nom complet : « Léo 的妈妈 »).")
    if not v["description"]:
        errors.append("Décrivez la réclamation.")
    if v["category"] == "safety":
        v["severity"] = "grave"
    return v, errors


@bp.route("/reclamations/nouvelle", methods=["GET", "POST"])
def complaint_new():
    with connect() as c:
        teachers = c.execute("SELECT id, first_name, last_initial FROM teachers ORDER BY first_name").fetchall()
    v, errors = {"teacher_id": request.args.get("professeur", type=int)}, []
    if request.method == "POST":
        _check_csrf()
        v, errors = _values(request.form)
        if not errors:
            with connect() as c:
                for _ in range(5):
                    code = new_code()
                    if not c.execute("SELECT 1 FROM complaints WHERE code=%s", (code,)).fetchone():
                        break
                cid = c.execute("""INSERT INTO complaints (code, category, severity, teacher_id, complainant_label, complainant_role, channel, channel_ref, description)
                                   VALUES (%(code)s,%(category)s,%(severity)s,%(teacher_id)s,%(complainant_label)s,%(complainant_role)s,%(channel)s,%(channel_ref)s,%(description)s)
                                   RETURNING id""", dict(v, code=code)).fetchone()["id"]
                _log(c, cid, f"Réclamation enregistrée ({CATEGORIES[v['category']]}, gravité {SEVERITIES[v['severity']].lower()}).")
            return redirect(url_for("admin.complaint", cid=cid, nouveau=1))
    return render_template("admin/complaint.html", c=None, v=v, teachers=teachers, errors=errors, categories=CATEGORIES,
                           severities=SEVERITIES, statuses=STATUSES, channels=CHANNELS, display_name=T.display_name)


@bp.route("/reclamations/<int:cid>", methods=["GET", "POST"])
def complaint(cid):
    with connect() as c:
        row = c.execute("SELECT * FROM complaints WHERE id=%s", (cid,)).fetchone()
        teachers = c.execute("SELECT id, first_name, last_initial FROM teachers ORDER BY first_name").fetchall()
    if not row:
        abort(404)
    errors, v = [], dict(row)
    if request.method == "POST":
        _check_csrf()
        f = request.form
        if f.get("action") == "delete":
            with connect() as c:
                c.execute("DELETE FROM complaints WHERE id=%s", (cid,))
            return redirect(url_for("admin.complaints_admin", supprimee=1))
        v, errors = _values(f)
        status = f.get("status") if f.get("status") in STATUSES else row["status"]
        upd = dict(v, status=status, assignee=(f.get("assignee") or "").strip()[:80] or None,
                   resolution=(f.get("resolution") or "").strip()[:6000] or None,
                   public_message=(f.get("public_message") or "").strip()[:2000] or None, id=cid)
        if status in ("resolved", "closed") and not upd["resolution"]:
            errors.append("Indiquez le résultat avant de marquer la réclamation résolue ou close.")
        note = (f.get("note") or "").strip()[:3000]
        if not errors:
            with connect() as c:
                c.execute("""UPDATE complaints SET category=%(category)s, severity=%(severity)s, teacher_id=%(teacher_id)s,
                               complainant_label=%(complainant_label)s, complainant_role=%(complainant_role)s, channel=%(channel)s,
                               channel_ref=%(channel_ref)s, description=%(description)s, status=%(status)s, assignee=%(assignee)s,
                               resolution=%(resolution)s, public_message=%(public_message)s, updated_at=now(),
                               closed_at=CASE WHEN %(status)s IN ('resolved','closed') THEN COALESCE(closed_at, now()) ELSE NULL END
                             WHERE id=%(id)s""", upd)
                changes = []
                for k, label, names in (("status", "Statut", STATUSES), ("severity", "Gravité", SEVERITIES), ("category", "Catégorie", CATEGORIES)):
                    if upd[k] != row[k]:
                        changes.append(f"{label} : {names[row[k]]} → {names[upd[k]]}")
                if upd["assignee"] != row["assignee"]:
                    changes.append(f"Responsable : {upd['assignee'] or '—'}")
                if upd["public_message"] != row["public_message"]:
                    changes.append("Message à la famille mis à jour")
                if upd["resolution"] != row["resolution"]:
                    changes.append("Résultat mis à jour")
                if changes:
                    _log(c, cid, " · ".join(changes))
                if note:
                    _log(c, cid, "Note : " + note)
            return redirect(url_for("admin.complaint", cid=cid, ok=1))
        v.update(upd)
    with connect() as c:
        events = c.execute("SELECT * FROM complaint_events WHERE complaint_id=%s ORDER BY at DESC, id DESC", (cid,)).fetchall()
    return render_template("admin/complaint.html", c=row, v=v, teachers=teachers, errors=errors, events=events,
                           categories=CATEGORIES, severities=SEVERITIES, statuses=STATUSES, channels=CHANNELS,
                           display_name=T.display_name, created=request.args.get("nouveau"), msg=request.args.get("ok") and "Enregistré.")
