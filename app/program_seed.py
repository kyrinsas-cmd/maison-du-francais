"""Programme indicatif par niveau (A1 → B2), en unités de communication, d'après les descripteurs du CECRL.
Rédigé le 2026-11-11 comme base de travail : l'équipe pédagogique le modifie (table program_units).
Lancé par deploy.sh : n'ajoute que les unités absentes (niveau + numéro), ne touche jamais aux unités existantes."""
from db import connect

UNITS = {
    "A1": [
        ("Se présenter et saluer", "打招呼和自我介绍", "Saluer, dire son nom, son âge, sa nationalité ; l'alphabet.", "问候，说出姓名、年龄、国籍；字母表。"),
        ("Ma famille et mes amis", "我的家人和朋友", "Présenter sa famille ; les possessifs ; les nombres jusqu'à 100.", "介绍家人；物主形容词；100以内的数字。"),
        ("L'école et la classe", "学校和教室", "Les objets de la classe, les consignes, les jours de la semaine.", "教室用品、课堂指令、星期。"),
        ("Mes goûts et mes loisirs", "我的爱好", "Dire ce qu'on aime ou pas ; les verbes en -er au présent.", "表达喜欢和不喜欢；-er 动词现在时。"),
        ("La maison", "我的家", "Décrire sa maison et sa chambre ; il y a ; les prépositions de lieu.", "描述房子和房间；il y a；方位介词。"),
        ("La nourriture et les repas", "食物和三餐", "Les aliments, les articles partitifs ; commander simplement.", "食物名称、部分冠词；简单点餐。"),
        ("Ma journée", "我的一天", "Dire l'heure ; les verbes pronominaux ; la routine quotidienne.", "说时间；代词式动词；日常作息。"),
        ("La ville et les directions", "城市和问路", "Les lieux de la ville ; demander et indiquer un chemin.", "城市里的地点；问路和指路。"),
        ("Les vêtements et la météo", "衣服和天气", "Décrire une tenue, les couleurs ; parler du temps qu'il fait.", "描述穿着和颜色；谈论天气。"),
        ("Les fêtes et le calendrier", "节日和日历", "Les mois, les saisons, les dates ; inviter, accepter, refuser.", "月份、季节、日期；邀请、接受、拒绝。"),
    ],
    "A2": [
        ("Raconter un événement passé", "讲述过去的事", "Le passé composé avec avoir et être ; les marqueurs de temps.", "复合过去时（avoir 和 être）；时间标志词。"),
        ("Décrire une personne", "描述一个人", "Le physique et le caractère ; les comparatifs.", "外貌和性格；比较级。"),
        ("Les vacances et les voyages", "假期和旅行", "Les transports, réserver, l'hébergement ; le futur proche.", "交通、预订、住宿；最近将来时。"),
        ("Les souvenirs d'enfance", "童年回忆", "L'imparfait pour décrire le passé ; imparfait et passé composé.", "用未完成过去时描述过去；与复合过去时的区别。"),
        ("Faire des achats", "购物", "Les magasins, les prix, les quantités ; les pronoms COD.", "商店、价格、数量；直接宾语代词。"),
        ("La santé et le corps", "健康和身体", "Les parties du corps, chez le médecin, donner des conseils.", "身体部位、看医生、提建议。"),
        ("Le logement", "住房", "Chercher un logement, lire une petite annonce ; les pronoms y et en.", "找房子、读租房广告；代词 y 和 en。"),
        ("Les médias et Internet", "媒体和网络", "Les réseaux, les émissions, donner son avis simplement.", "社交网络、节目，简单表达观点。"),
        ("Les projets et l'avenir", "计划和未来", "Le futur simple ; exprimer des projets et des souhaits.", "简单将来时；表达计划和愿望。"),
        ("La culture française", "法国文化", "Fêtes, régions et traditions ; écrire une carte ou un courriel.", "节日、地区和传统；写明信片或邮件。"),
    ],
    "B1": [
        ("Exprimer son opinion", "表达观点", "Argumenter, être d'accord ou pas ; les connecteurs logiques.", "论证、同意或反对；逻辑连接词。"),
        ("Les études et l'orientation", "学业和升学", "Le système scolaire, les choix d'études ; le conditionnel présent.", "学校体系、专业选择；条件式现在时。"),
        ("Le monde du travail", "职场", "Les métiers, le CV, l'entretien ; les pronoms relatifs.", "职业、简历、面试；关系代词。"),
        ("Raconter une histoire", "讲故事", "Le récit au passé, le plus-que-parfait, la chronologie.", "过去时叙事、愈过去时、时间顺序。"),
        ("Les sentiments et les émotions", "情感", "Exprimer la joie, la peur, la surprise ; le subjonctif (introduction).", "表达喜悦、害怕、惊讶；虚拟式（入门）。"),
        ("L'environnement", "环境", "Les enjeux écologiques ; la cause et la conséquence.", "生态问题；原因和结果。"),
        ("Les loisirs culturels", "文化生活", "Cinéma, livres, musique : résumer et critiquer une œuvre.", "电影、书籍、音乐：概括和评论作品。"),
        ("La vie en société", "社会生活", "Les règles, les droits et devoirs ; l'obligation et l'interdiction.", "规则、权利和义务；表达义务和禁止。"),
        ("Le discours rapporté", "间接引语", "Rapporter des paroles au présent et au passé.", "转述现在和过去的话。"),
        ("Préparer le DELF B1", "备考 DELF B1", "Les quatre épreuves du DELF B1, entraînement et méthodes.", "DELF B1 四项考试的训练和方法。"),
    ],
    "B2": [
        ("Débattre et convaincre", "辩论和说服", "Structurer une argumentation, réfuter, nuancer.", "组织论证、反驳、表达细微差别。"),
        ("Les médias et l'information", "媒体和信息", "Analyser un article, distinguer faits et opinions.", "分析文章，区分事实和观点。"),
        ("Science et technologie", "科学和技术", "Le numérique, l'intelligence artificielle : enjeux et débats.", "数字化、人工智能：问题和争论。"),
        ("La concession et l'opposition", "让步和对立", "Bien que, même si, pourtant ; le subjonctif approfondi.", "bien que、même si、pourtant；虚拟式进阶。"),
        ("Le monde du travail (suite)", "职场（进阶）", "La lettre de motivation, le registre soutenu.", "求职信、正式语体。"),
        ("Société et citoyenneté", "社会和公民", "Les grands débats de société ; la voix passive.", "社会热点问题；被动语态。"),
        ("La langue et la francophonie", "法语和法语国家", "Les variétés du français, les registres de langue.", "法语的地区差异、语言语体。"),
        ("Écrire un essai argumenté", "写议论文", "Plan, introduction, conclusion ; la production écrite du DELF B2.", "提纲、引言、结论；DELF B2 写作。"),
        ("Comprendre l'oral authentique", "理解真实语料", "Podcasts, reportages, conférences : stratégies d'écoute.", "播客、报道、讲座：听力策略。"),
        ("Préparer le DELF B2", "备考 DELF B2", "Les quatre épreuves du DELF B2, examens blancs.", "DELF B2 四项考试，模拟考试。"),
    ],
}


def main():
    n = 0
    with connect() as c:
        for level, units in UNITS.items():
            for i, (tfr, tzh, gfr, gzh) in enumerate(units, 1):
                n += c.execute("""INSERT INTO program_units (level, sort, title_fr, title_zh, goals_fr, goals_zh) VALUES (%s,%s,%s,%s,%s,%s)
                                  ON CONFLICT (level, sort) DO NOTHING""", (level, i, tfr, tzh, gfr, gzh)).rowcount
    print(f"programme : {n} unité(s) ajoutée(s)")


if __name__ == "__main__":
    main()
