"""Page Tarifs (/tarifs, /fr/tarifs) pilotée depuis /admin/tarifs.

Le prix n'est pas fixé dans le cahier des charges (§19 : « prix final à décider », suggestion 130–150 ¥ par séance et par élève) :
rien n'est affiché tant que l'équipe n'a pas saisi un prix et publié la page. Les montants sont en yuans (encaissement en Chine, §8).
Facturation : 1 séance = 1 heure (45 min de cours + 15 min de devoirs et questions), par élève.
"""
from flask import abort, redirect, render_template, request, session, url_for
from psycopg.types.json import Jsonb

import web
from admin import _check_csrf, bp
from db import connect

KEY = "pricing"
DEFAULT = {"price_session": None, "block_sessions": 36, "private_hourly": None, "published": False}


def get():
    with connect() as c:
        r = c.execute("SELECT value FROM settings WHERE key=%s", (KEY,)).fetchone()
    return dict(DEFAULT, **(r["value"] if r else {}))


def is_live():
    p = get()
    return bool(p["published"] and p["price_session"])


def fmt(n):
    return f"{n:,}".replace(",", " ")


@web.app.context_processor
def pricing_ctx():
    return {"pricing_live": is_live}


@web.route("/tarifs")
def prices():
    p = get()
    import staff
    preview = staff.is_admin() and request.args.get("apercu") == "1"
    if not (p["published"] and p["price_session"]) and not (preview and p["price_session"]):
        abort(404)
    price = p["price_session"]
    block = p["block_sessions"] or 36
    rows = [dict(l, total=fmt(l["sessions"] * price)) for l in web.LEVELS]
    return render_template("prices.html", p=p, price=fmt(price), block=block, block_weeks=round(block / 3),
                           block_total=fmt(block * price), private=fmt(p["private_hourly"]) if p["private_hourly"] else None,
                           rows=rows, preview=preview and not p["published"])


def sitemap_paths():
    return ["/tarifs"] if is_live() else []


@bp.route("/tarifs", methods=["GET", "POST"])
def pricing_admin():
    p = get()
    errors = []
    if request.method == "POST":
        _check_csrf()
        f = request.form

        def num(k, lo, hi):
            v = (f.get(k) or "").strip()
            if not v:
                return None
            if not v.isdigit() or not lo <= int(v) <= hi:
                errors.append(f"Valeur invalide pour « {LABELS[k]} » (entre {lo} et {hi}).")
                return p.get(k)
            return int(v)
        new = {
            "price_session": num("price_session", 1, 10000),
            "block_sessions": num("block_sessions", 1, 500) or 36,
            "private_hourly": num("private_hourly", 1, 10000),
            "published": bool(f.get("published")),
        }
        if new["published"] and not new["price_session"]:
            errors.append("Pour publier la page, indiquez le prix d'une séance.")
            new["published"] = False
        with connect() as c:
            c.execute("""INSERT INTO settings (key, value) VALUES (%s, %s)
                         ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=now()""", (KEY, Jsonb(new)))
        if not errors:
            return redirect(url_for("admin.pricing_admin", ok=1))
        p = new
    return render_template("admin/pricing.html", p=p, errors=errors, msg=request.args.get("ok") and "Enregistré.")


LABELS = {"price_session": "Prix d'une séance", "block_sessions": "Séances par forfait", "private_hourly": "Cours particulier"}
