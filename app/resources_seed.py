"""Ressources officielles gratuites du 教材库 : des liens vers les sites des organismes publics, rien n'est copié ni hébergé chez nous.

Lancé à la main (pas par deploy.sh, pour qu'une ressource retirée dans l'admin ne revienne pas) :
    sudo -u maisondufrancais sh -c 'set -a; . ../.env; set +a; ./venv/bin/python resources_seed.py'
Une ressource est reconnue par son lien : rien n'est écrasé si elle existe déjà (même dépubliée ou modifiée).
Liens relevés le 2026-10-26 (sites protégés contre les robots : vérifiés par recherche, pas par une visite automatique).
"""
from db import connect

FEI = "France Éducation international（法国教育部下属机构，DELF/DALF 官方出题方）"
FEI_FR = "France Éducation international (opérateur du ministère de l'Éducation nationale, conçoit le DELF et le DALF)"
LICENSE = "Lien vers la page officielle, contenu non copié ni hébergé (pas d'autorisation nécessaire pour un lien)."

# (titre zh, titre fr, desc zh, desc fr, niveau, compétence, âge min, âge max, visibilité, source, lien, publié)
ITEMS = [
    ("DELF Prim A1.1 官方样题", "DELF Prim A1.1 : exemples de sujets officiels",
     "法国官方 DELF Prim（小学生法语考试）A1.1 级样题：听力、阅读、写作、口语，含音频和评分表。适合 7–12 岁、刚开始学法语的孩子。",
     "Sujets d'exemple officiels du DELF Prim A1.1 (compréhension de l'oral et des écrits, production écrite et orale), avec audios et grilles d'évaluation. Pour les 7–12 ans qui débutent.",
     "A1", "mixte", 7, 12, "public", FEI, "https://www.france-education-international.fr/diplome/delf-prim/exemples-sujets-a1-1", True),
    ("DELF Prim A1 官方样题", "DELF Prim A1 : exemples de sujets officiels",
     "DELF Prim A1 级官方样题，含听力音频、考官口语手册和评分表。", "Sujets d'exemple officiels du DELF Prim A1 : audios, livret de l'examinateur pour l'oral, grilles d'évaluation.",
     "A1", "mixte", 7, 12, "public", FEI, "https://www.france-education-international.fr/diplome/delf-prim/exemples-sujets-a1", True),
    ("DELF Prim A2 官方样题", "DELF Prim A2 : exemples de sujets officiels",
     "DELF Prim A2 级官方样题，含听力音频、考官口语手册和评分表。", "Sujets d'exemple officiels du DELF Prim A2 : audios, livret de l'examinateur pour l'oral, grilles d'évaluation.",
     "A2", "mixte", 7, 12, "public", FEI, "https://www.france-education-international.fr/diplome/delf-prim/exemples-sujets-a2", True),
    ("DELF Junior A1 官方样题", "DELF junior A1 : exemples de sujets officiels",
     "DELF Junior（12–17 岁中学生版）A1 级官方样题：两套笔试样卷、听力音频、写作和口语评分表。",
     "Sujets d'exemple officiels du DELF junior/scolaire A1 (12–17 ans) : 2 exemples d'épreuves collectives, audios, grilles de production écrite et orale.",
     "A1", "mixte", 12, 17, "public", FEI, "https://www.france-education-international.fr/diplome/delf-junior-scolaire/exemples-sujets-a1", True),
    ("DELF Junior A2 官方样题", "DELF junior A2 : exemples de sujets officiels",
     "DELF Junior A2 级官方样题：两套笔试样卷、听力音频、评分表。", "Sujets d'exemple officiels du DELF junior/scolaire A2 : 2 exemples d'épreuves collectives, audios, grilles d'évaluation.",
     "A2", "mixte", 12, 17, "public", FEI, "https://www.france-education-international.fr/diplome/delf-junior-scolaire/exemples-sujets-a2", True),
    ("DELF Junior B1 官方样题", "DELF junior B1 : exemples de sujets officiels",
     "DELF Junior B1 级官方样题：两种题型的笔试样卷、分题和完整听力音频、评分表及评分标准说明。",
     "Sujets d'exemple officiels du DELF junior/scolaire B1 : les 2 formats d'épreuves de compréhension, audios par exercice et complets, grilles et explication des critères.",
     "B1", "mixte", 12, 17, "public", FEI, "https://www.france-education-international.fr/diplome/delf-junior-scolaire/exemples-sujets-b1", True),
    ("DELF Junior B2 官方样题", "DELF junior B2 : exemples de sujets officiels",
     "DELF Junior B2 级官方样题：两种题型的笔试样卷、听力音频、评分表及评分标准说明。",
     "Sujets d'exemple officiels du DELF junior/scolaire B2 : les 2 formats d'épreuves de compréhension, audios, grilles et explication des critères.",
     "B2", "mixte", 12, 17, "public", FEI, "https://www.france-education-international.fr/diplome/delf-junior-scolaire/exemples-sujets-b2", True),
    ("TV5MONDE 学法语（A1–B2 视频练习）", "Apprendre le français avec TV5MONDE (A1 à B2)",
     "法国国际电视台 TV5MONDE 的免费学习网站：3000 多个基于真实电视节目的视频练习，分 A1、A2、B1、B2 四级，有字幕和文字稿，还有在线水平小测。官方说明主要面向 16 岁以上；年龄小的孩子请在家长或老师陪同下使用。",
     "Site gratuit de TV5MONDE : plus de 3 000 exercices à partir de vidéos de la chaîne, classés A1, A2, B1, B2, avec sous-titres et transcriptions, et un test de niveau en ligne. Prévu surtout pour les plus de 16 ans ; les plus jeunes l'utilisent avec un parent ou un professeur.",
     None, "co", 15, None, "public", "TV5MONDE（法语国际电视台，法国等法语国家政府共同出资）", "https://apprendre.tv5monde.com/fr", True),
    ("TV5MONDE 法语教学资源（教师用）", "Enseigner le français avec TV5MONDE (professeurs)",
     "TV5MONDE 为法语老师提供的免费教案和练习，其中有儿童频道 TiVi5MONDE 节目的配套材料，可用于儿童课堂。",
     "Fiches pédagogiques et exercices gratuits de TV5MONDE pour les professeurs, dont des ressources pour utiliser les programmes jeunesse de TiVi5MONDE en classe d'enfants.",
     None, "mixte", None, None, "teachers", "TV5MONDE", "https://enseigner.tv5monde.com", True),
    ("欧洲语言共同参考框架（CECR）补充卷", "CECR : volume complémentaire (Conseil de l'Europe)",
     "欧洲委员会发布的 CECR 官方文件（法语版，2021），A1–C2 各级能力描述的标准依据。供老师备课和评估使用。",
     "Texte officiel du Conseil de l'Europe (version française, 2021) : les descripteurs de référence de A1 à C2. Pour préparer les cours et évaluer.",
     None, "mixte", None, None, "teachers", "Conseil de l'Europe（欧洲委员会）",
     "https://rm.coe.int/cadre-europeen-commun-de-reference-pour-les-langues-apprendre-enseigne/1680a4e270", True),
    ("法兰西学院：Dire, ne pas dire（正确用法）", "Académie française : « Dire, ne pas dire »",
     "法兰西学院的官方专栏，讲解常见用词错误和正确说法。适合 B2 以上、准备 DELF B2 写作的学生。",
     "La rubrique de l'Académie française sur les fautes courantes et le bon usage. Pour les élèves de niveau B2 qui préparent la production écrite.",
     "B2", "ee", 15, None, "public", "Académie française（法兰西学院）", "https://www.academie-francaise.fr/dire-ne-pas-dire", True),
    ("法兰西学院词典（在线免费）", "Dictionnaire de l'Académie française (en ligne)",
     "法兰西学院官方词典第 9 版，免费在线查询，释义和例句权威。适合高年级学生和老师。",
     "La 9e édition du dictionnaire de l'Académie française, gratuite en ligne : définitions et exemples de référence. Pour les grands élèves et les professeurs.",
     "B2", "mixte", 15, None, "public", "Académie française（法兰西学院）", "https://www.dictionnaire-academie.fr/", True),
    ("RFI 简易法语新闻（Journal en français facile）", "RFI : Journal en français facile",
     "法国国际广播电台每天 10 分钟的慢速法语新闻，附文字稿，适合 B1 以上。注意：RFI 网站在中国大陆可能无法访问，未确认前不公开。",
     "Le journal quotidien de RFI en français simple et plus lent (10 minutes), avec transcription. Niveau B1 et plus. Attention : le site de RFI est probablement inaccessible en Chine continentale ; non publié tant que ce n'est pas vérifié.",
     "B1", "co", 15, None, "public", "RFI（法国国际广播电台，France Médias Monde）", "https://francaisfacile.rfi.fr/fr/", False),
]


def seed():
    added = 0
    with connect() as c:
        for i, (tzh, tfr, dzh, dfr, lv, sk, amin, amax, vis, src, url, pub) in enumerate(ITEMS):
            if c.execute("SELECT 1 FROM resources WHERE url=%s", (url,)).fetchone():
                continue
            c.execute("""INSERT INTO resources (title_zh, title_fr, desc_zh, desc_fr, level, skill, ages_min, ages_max, visibility, origin,
                                                tp_source, tp_license, url, file_kind, published, sort)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'tiers',%s,%s,%s,'link',%s,%s)""",
                      (tzh, tfr, dzh, dfr, lv, sk, amin, amax, vis, src, LICENSE, url, pub, 10 + i))
            added += 1
    print(f"ressources officielles : {added} ajoutée(s), {len(ITEMS) - added} déjà présente(s)")


if __name__ == "__main__":
    seed()
