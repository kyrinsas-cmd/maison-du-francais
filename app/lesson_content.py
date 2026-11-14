"""Contenu d'une leçon (JSON de lessons.content) : champs attendus et vérification. Sans Flask : utilisé par lessons.py et lessons_seed.py."""
import json
import re

EX_TYPES = ("qcm", "tf", "fill", "match")
SKILLS = ("co", "eo", "ce", "ee")
PHASES = ("warmup", "present", "practice", "produce", "wrapup")


SKELETON = {
    "objectives": [""], "can_do": [""], "skills": ["co", "eo"], "exam": "", "materials": [],
    "vocab": [{"w": "", "py": "", "m": ""}],
    "grammar": [{"title": "", "explain": "", "examples": [{"t": "", "py": "", "m": ""}]}],
    "text": {"title": "", "audio": "", "lines": [{"who": "", "t": "", "py": "", "m": ""}]},
    "steps": [{"min": 5, "phase": "warmup", "title": "", "do": "", "say": "", "tip": ""}],
    "mistakes": [], "diff": {"young": "", "teen": ""}, "culture": {"title": "", "text": ""},
    "exercises": [{"type": "qcm", "q": "", "choices": ["", "", ""], "answer": 0, "explain": ""}],
    "task": {"kind": "oral", "title": "", "instr": "", "instr_guide": ""},
    "audio": [{"id": "dialogue", "label": "", "script": ""}],
}


def _str(x):
    return isinstance(x, str)


def validate(c):
    """Renvoie la liste des problèmes (vide = contenu valable)."""
    e = []
    if not isinstance(c, dict):
        return ["Le contenu doit être un objet JSON { … }."]
    unknown = set(c) - set(SKELETON)
    if unknown:
        e.append("Champs inconnus : " + ", ".join(sorted(unknown)))
    for k in ("objectives", "can_do", "materials", "mistakes"):
        if k in c and not (isinstance(c[k], list) and all(_str(x) for x in c[k])):
            e.append(f"« {k} » : liste de textes attendue.")
    if any(s not in SKILLS for s in c.get("skills", [])):
        e.append("« skills » : co, eo, ce ou ee.")
    for i, v in enumerate(c.get("vocab", [])):
        if not (isinstance(v, dict) and _str(v.get("w")) and _str(v.get("m"))):
            e.append(f"vocab n° {i + 1} : « w » (mot) et « m » (sens) obligatoires.")
    for i, gr in enumerate(c.get("grammar", [])):
        if not (isinstance(gr, dict) and _str(gr.get("title")) and isinstance(gr.get("examples", []), list)):
            e.append(f"grammar n° {i + 1} : « title » et « examples » (liste).")
    t = c.get("text")
    if t is not None and not (isinstance(t, dict) and isinstance(t.get("lines", []), list)):
        e.append("« text » : objet avec « lines » (liste).")
    total = 0
    for i, s in enumerate(c.get("steps", [])):
        if not (isinstance(s, dict) and isinstance(s.get("min"), int) and s.get("phase") in PHASES and _str(s.get("do"))):
            e.append(f"steps n° {i + 1} : « min » (nombre), « phase » ({', '.join(PHASES)}) et « do » obligatoires.")
        else:
            total += s["min"]
    if c.get("steps") and total != 45:
        e.append(f"Le déroulé fait {total} min : il doit faire 45 min.")
    slots = {a.get("id") for a in c.get("audio", []) if isinstance(a, dict)}
    for a in c.get("audio", []):
        if not (isinstance(a, dict) and _str(a.get("id")) and re.fullmatch(r"[a-z0-9]{1,12}", a["id"]) and _str(a.get("script"))):
            e.append("audio : « id » (lettres minuscules et chiffres, 12 au plus) et « script » obligatoires.")
    if len(slots) != len(c.get("audio", [])):
        e.append("audio : deux pistes ont le même « id ».")
    for i, x in enumerate(c.get("exercises", [])):
        n = f"exercice n° {i + 1}"
        if not isinstance(x, dict) or x.get("type") not in EX_TYPES:
            e.append(f"{n} : « type » = {', '.join(EX_TYPES)}.")
            continue
        if x.get("audio") and x["audio"] not in slots:
            e.append(f"{n} : piste audio « {x['audio']} » absente de « audio ».")
        if x["type"] in ("qcm", "fill"):
            ch = x.get("choices")
            if not (_str(x.get("q")) and isinstance(ch, list) and len(ch) >= 2 and all(_str(y) for y in ch)
                    and isinstance(x.get("answer"), int) and 0 <= x["answer"] < len(ch)):
                e.append(f"{n} : « q », « choices » (2 au moins) et « answer » (index de la bonne réponse, à partir de 0).")
            elif len(set(ch)) != len(ch):
                e.append(f"{n} : deux choix identiques.")
            if x["type"] == "fill" and _str(x.get("q")) and "___" not in x["q"]:
                e.append(f"{n} : la phrase doit contenir ___ (le trou).")
        elif x["type"] == "tf":
            if not (_str(x.get("q")) and isinstance(x.get("answer"), bool)):
                e.append(f"{n} : « q » et « answer » (true ou false).")
        elif x["type"] == "match":
            p = x.get("pairs")
            if not (isinstance(p, list) and len(p) >= 2 and all(isinstance(y, list) and len(y) == 2 and all(_str(z) for z in y) for y in p)):
                e.append(f"{n} : « pairs » = liste de paires [gauche, droite], 2 au moins.")
            elif len({y[1] for y in p}) != len(p):
                e.append(f"{n} : deux éléments de droite identiques.")
    tk = c.get("task")
    if tk is not None and not (isinstance(tk, dict) and tk.get("kind") in ("oral", "ecrit") and _str(tk.get("instr"))):
        e.append("« task » : « kind » (oral ou ecrit) et « instr » obligatoires.")
    return e


def dumps(c):
    return json.dumps(c, ensure_ascii=False, indent=1)
