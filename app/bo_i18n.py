"""Langue des espaces connectés (2026-11-12).
- Familles et élèves : pages déjà bilingues par l'adresse (/ et /fr) ; le choix est enregistré (users.ui_lang, students.ui_lang)
  et sert à l'arrivée après connexion.
- Administration et espace professeur : gabarits en français, traduits en chinois à l'affichage (dictionnaire bo_zh.ZH)
  quand le compte a choisi le chinois. Le contenu marqué lang="fr" (questions du test, textes saisis en français),
  les champs de saisie et les scripts ne sont jamais traduits."""
import re
from flask import g, redirect, request, session, url_for
import web
from db import connect
from bo_zh import ZH, PATTERNS

_ZH = {" ".join(k.split()): v for k, v in ZH.items()}
_LONG = sorted((k for k in _ZH if len(k) >= 14), key=len, reverse=True)
_PAT = [(re.compile(p), r) for p, r in PATTERNS]
_TOKEN = re.compile(r"(<!--.*?-->|<[^>]*>)", re.S)
_TAG = re.compile(r"<\s*(/?)\s*([a-zA-Z0-9]+)")
_ATTR = re.compile(r'\b(placeholder|title|aria-label|alt)="([^"]*)"')
_CONFIRM = re.compile(r"confirm\('((?:[^'\\]|\\.)*)'\)")
_SKIP = {"textarea", "script", "style", "pre"}
_VOID = {"input", "br", "img", "meta", "link", "hr", "source", "area", "col", "wbr", "base", "track", "embed"}


def tr(s):
    """Traduit un texte affiché (ou le rend tel quel)."""
    core = " ".join(s.split())
    if not core:
        return s
    out = _ZH.get(core)
    if out is None:
        out = core
        for rx, rep in _PAT:
            out = rx.sub(rep, out)
        for k in _LONG:
            if k in out:
                out = out.replace(k, _ZH[k])
        if out == core:
            return s
    lead = s[:len(s) - len(s.lstrip())]
    trail = s[len(s.rstrip()):]
    return lead + out + trail


def _unescape_tr(s):
    """Les textes passent par l'échappement de Jinja (&#39; …) : on traduit la forme lisible."""
    plain = s.replace("&#39;", "'").replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")
    out = tr(plain)
    if out is plain:
        return s
    return out.replace("&", "&amp;").replace('"', "&#34;").replace("'", "&#39;")


def translate_html(html):
    parts = _TOKEN.split(html)
    skip_tag, depth = None, 0
    for i, p in enumerate(parts):
        if not p:
            continue
        if p.startswith("<"):
            if p.startswith("<!--"):
                continue
            m = _TAG.match(p)
            if not m:
                continue
            closing, name = m.group(1) == "/", m.group(2).lower()
            if skip_tag:
                if name == skip_tag:
                    depth += -1 if closing else (0 if p.endswith("/>") else 1)
                    if depth == 0:
                        skip_tag = None
                continue
            if closing:
                continue
            if name == "html":
                parts[i] = p.replace('lang="fr"', 'lang="zh-Hans"', 1)
                continue
            if (name in _SKIP or ' lang="fr"' in p or "notranslate" in p) and name not in _VOID and not p.endswith("/>"):
                skip_tag, depth = name, 1
            if name in _SKIP:
                continue
            p = _ATTR.sub(lambda a: f'{a.group(1)}="{_unescape_tr(a.group(2))}"', p)
            p = _CONFIRM.sub(lambda a: "confirm('" + tr(a.group(1).replace("\\'", "'")).replace("'", "\\'") + "')", p)
            parts[i] = p
        elif not skip_tag and p.strip():
            parts[i] = _unescape_tr(p)
    return "".join(parts)


# ---------- choix de la langue ----------

def bo_lang():
    """Langue de l'administration et de l'espace professeur : français sauf choix du chinois."""
    if "bo_lang" not in g:
        import users
        u = users.current()
        g.bo_lang = "zh" if u and u.get("ui_lang") == "zh" else "fr"
    return g.bo_lang


@web.app.context_processor
def bo_ctx():
    return {"bo_lang": bo_lang}


def _safe_next(n, fallback):
    n = n or ""
    if not n.startswith("/") or n.startswith("//") or "\\" in n or "\n" in n or "\r" in n:
        return fallback
    return n


@web.app.route("/langue/<any(zh,fr):l>", methods=["POST"])
def set_lang(l):
    import users
    import pupil
    users.check_csrf()
    u = users.current()
    st = None if u else pupil.current_student()
    with connect() as c:
        if u:
            c.execute("UPDATE users SET ui_lang=%s WHERE id=%s", (l, u["id"]))
        elif st:
            c.execute("UPDATE students SET ui_lang=%s WHERE id=%s", (l, st["id"]))
    return redirect(_safe_next(request.form.get("next"), "/" if l == "zh" else "/fr/"), code=303)


TRANSLATED_ENDPOINTS = {"account_password"}


@web.app.after_request
def translate_bo(resp):
    bp = request.blueprint
    if bp not in ("admin", "espace") and request.endpoint not in TRANSLATED_ENDPOINTS:
        return resp
    if resp.status_code != 200 or resp.direct_passthrough or not (resp.mimetype or "").startswith("text/html"):
        return resp
    import users
    u = users.current()
    if not u or bo_lang() != "zh":
        return resp
    if bp is None and not (u["role"] in users.STAFF or u["role"] == "professeur"):
        return resp       # page famille : déjà dans la langue de l'adresse
    resp.set_data(translate_html(resp.get_data(as_text=True)))
    return resp
