"""Données de démonstration (is_demo = true) pour voir le rendu de 直播课, 老师 et 教材库. Demandées par l'utilisateur, temporaires.

  python demo.py add      → 4 professeurs fictifs, 6 classes, 6 ressources (badge « 示例 / Exemple » partout)
  python demo.py remove   → supprime tout ce qui est is_demo, fichiers compris

Avatars à initiales (aucune photo de personne réelle), fichiers PDF/PNG générés. Ne jamais laisser au lancement du site.
"""
import os
import secrets
import sys
from datetime import date, time

from PIL import Image, ImageDraw, ImageFont

import web  # noqa: F401  (charge toute l'application dans le bon ordre)
import resources as R
import teachers as T
from db import connect

TEACHERS = [
    ("Camille", "L", "Master FLE, habilitation DELF", 6, 10, ["A1", "A2"], "#063372",
     "Camille 老师在巴黎教授少儿法语多年，课堂上用游戏和歌曲帮助孩子开口。（示例）", "Camille enseigne le FLE aux enfants à Paris ; elle fait parler les élèves avec des jeux et des chansons. (exemple)",
     "少儿A1\n少儿A2", "Enfants A1\nEnfants A2"),
    ("Julien", "M", "Master FLE, DAEFLE", 9, 14, ["A2", "B1"], "#DF333A",
     "Julien 老师擅长口语和语音教学，注重让每个学生都有发言机会。（示例）", "Julien travaille surtout l'oral et la phonétique ; chaque élève prend la parole à chaque séance. (exemple)",
     "A2 口语\nB1 综合", "Oral A2\nB1 complet"),
    ("Sophie", "R", "Master FLE, examinatrice DELF", 13, 17, ["B1", "B2"], "#1F7A5A",
     "Sophie 老师是 DELF 考官，带青少年备考 B1、B2。（示例）", "Sophie est examinatrice DELF et prépare les adolescents au B1 et au B2. (exemple)",
     "DELF B1 冲刺\nDELF B2 冲刺", "Préparation DELF B1\nPréparation DELF B2"),
    ("Thomas", "D", "Licence FLE", 6, 8, ["A1"], "#B8860B",
     "Thomas 老师专门教 6–8 岁零基础的孩子。（示例）", "Thomas s'occupe des débutants de 6 à 8 ans. (exemple)",
     "零基础启蒙", "Éveil débutants"),
]
# (niveau, âges, index du professeur, jours, heure Pékin, date de début, places occupées, statut)
CLASSES = [
    ("A1", 6, 8, 3, [2, 4, 6], time(17, 0), date(2026, 11, 3), 3, "open"),
    ("A1", 6, 9, 0, [1, 3, 5], time(19, 30), date(2026, 11, 2), 5, "full"),
    ("A2", 9, 12, 1, [2, 4, 6], time(16, 0), date(2026, 11, 10), 2, "open"),
    ("B1", 12, 15, 1, [6, 7], time(10, 0), date(2026, 11, 7), 4, "open"),
    ("B1", 13, 17, 2, [1, 3], time(20, 30), date(2026, 12, 1), 0, "soon"),
    ("B2", 14, 17, 2, [2, 5], time(20, 0), date(2026, 11, 13), 1, "open"),
]
# (titre zh, titre fr, niveau, compétence, type, visibilité)
RESOURCES = [
    ("颜色与数字", "Les couleurs et les nombres", "A1", "mixte", "pdf", "public"),
    ("自我介绍句型", "Se présenter", "A1", "eo", "image", "public"),
    ("我的家庭", "Ma famille", "A2", "ce", "pdf", "members"),
    ("阅读：巴黎的一天", "Lecture : une journée à Paris", "B1", "ce", "pdf", "members"),
    ("DELF B2 写作范文", "DELF B2 : modèle de production écrite", "B2", "ee", "pdf", "teachers"),
    ("法语发音表", "Tableau des sons du français", None, "co", "image", "public"),
]


def _font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)  # accents (é, ç) ; la police par défaut ne les a pas
    return ImageFont.load_default(size=size)


def avatar(initials, color):
    im = Image.new("RGB", (800, 1000), color)
    d = ImageDraw.Draw(im)
    f = _font(300)
    w = d.textlength(initials, font=f)
    d.text(((800 - w) / 2, 330), initials, fill="#FFFFFF", font=f)
    d.text((40, 930), "EXEMPLE / DEMO", fill="#FFFFFF", font=_font(40))
    return im


def doc_image(title_fr, level):
    im = Image.new("RGB", (1240, 1754), "#FFFFFF")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1240, 160], fill="#063372")
    d.text((60, 50), "Maison du français", fill="#FFFFFF", font=_font(60))
    d.text((60, 240), title_fr, fill="#063372", font=_font(64))
    d.text((60, 340), f"Niveau : {level or 'tous'}", fill="#33476E", font=_font(40))
    d.text((60, 1640), "EXEMPLE - document de démonstration", fill="#C8242B", font=_font(36))
    return im


def add():
    os.makedirs(T.UPLOADS, exist_ok=True)
    os.makedirs(R.UPLOADS, exist_ok=True)
    tids = []
    with connect() as c:
        for i, (first, last, dipl, amin, amax, levels, color, bio_zh, bio_fr, co_zh, co_fr) in enumerate(TEACHERS):
            tid = c.execute("""INSERT INTO teachers (first_name, last_initial, slug, diplomas, ages_min, ages_max, levels, bio_zh, bio_fr, courses_zh, courses_fr,
                                                     consent_at, consent_ref, published, sort, is_demo)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, CURRENT_DATE, 'Données de démonstration', true, %s, true) RETURNING id""",
                            (first, last, f"demo-{secrets.token_hex(3)}", dipl, amin, amax, levels, bio_zh, bio_fr, co_zh, co_fr, 100 + i)).fetchone()["id"]
            name = f"t{tid}-{secrets.token_hex(6)}.jpg"
            avatar(first[0] + last, color).save(os.path.join(T.UPLOADS, name), "JPEG", quality=85)
            c.execute("UPDATE teachers SET slug=%s, photo_file=%s WHERE id=%s", (f"{T._slugify(first)}-{tid}", name, tid))
            tids.append(tid)
        for i, (lv, amin, amax, ti, days, start, d0, taken, status) in enumerate(CLASSES):
            c.execute("""INSERT INTO live_classes (level, ages_min, ages_max, teacher_id, days, start_bj, start_date, capacity, seats_taken, status,
                                                   note_zh, note_fr, published, sort, is_demo)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,5,%s,%s,'示例班级','Classe d''exemple',true,%s,true)""",
                      (lv, amin, amax, tids[ti], days, start, d0, taken, status, 100 + i))
        for i, (tzh, tfr, lv, sk, kind, vis) in enumerate(RESOURCES):
            rid = c.execute("""INSERT INTO resources (title_zh, title_fr, desc_zh, desc_fr, level, skill, visibility, origin, published, sort, is_demo)
                               VALUES (%s,%s,'示例教材，仅用于展示效果。','Ressource d''exemple, pour voir le rendu.',%s,%s,%s,'maison',true,%s,true) RETURNING id""",
                            (tzh, tfr, lv, sk, vis, 100 + i)).fetchone()["id"]
            ext = "pdf" if kind == "pdf" else "png"
            name = f"r{rid}-{secrets.token_hex(6)}.{ext}"
            path = os.path.join(R.UPLOADS, name)
            doc_image(tfr, lv).save(path, "PDF" if ext == "pdf" else "PNG")
            c.execute("UPDATE resources SET file_name=%s, file_kind=%s, file_size=%s WHERE id=%s", (name, kind, os.path.getsize(path), rid))
    print(f"ajouté : {len(TEACHERS)} professeurs, {len(CLASSES)} classes, {len(RESOURCES)} ressources (toutes marquées « exemple »)")


def remove():
    with connect() as c:
        files_t = [v for r in c.execute("SELECT photo_file, video_file FROM teachers WHERE is_demo").fetchall() for v in r.values() if v]
        files_r = [r["file_name"] for r in c.execute("SELECT file_name FROM resources WHERE is_demo AND file_name IS NOT NULL").fetchall()]
        n = (c.execute("DELETE FROM live_classes WHERE is_demo").rowcount, c.execute("DELETE FROM resources WHERE is_demo").rowcount,
             c.execute("DELETE FROM teachers WHERE is_demo").rowcount)
    for f in files_t:
        T._remove(f)
    for f in files_r:
        R.remove_file(f)
    print(f"supprimé : {n[2]} professeurs, {n[0]} classes, {n[1]} ressources, {len(files_t) + len(files_r)} fichiers")


if __name__ == "__main__":
    {"add": add, "remove": remove}.get((sys.argv[1:] or [""])[0], lambda: print("Usage : python demo.py add | remove"))()
