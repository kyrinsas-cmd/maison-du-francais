"""作业库 : devoirs types par unité du programme (program_seed.py), 2 par unité, rédigés le 2026-11-12 comme base de travail.
À relire par un professeur de FLE. Lancé par deploy.sh : n'ajoute que les devoirs absents (clé), ne modifie jamais un devoir existant.
Chaque devoir : (type, titre fr, titre zh, consigne fr, consigne zh). Types : ecrit (rendu écrit ou photo du cahier), oral (enregistrement audio)."""
from db import connect

BANK = {
    "A1": [
        [("oral", "Ma présentation", "我的自我介绍", "Enregistre-toi (1 minute) : dis bonjour, ton prénom, ton âge, ta nationalité et ta ville.", "录一段1分钟的音频：打招呼，说出你的名字、年龄、国籍和城市。"),
         ("ecrit", "L'alphabet de mon prénom", "用字母拼我的名字", "Écris ton prénom et le prénom de 3 personnes de ta famille, puis épelle-les en français (ex. : M-A-X → « ème, a, ixe »).", "写下你和3个家人的名字，再用法语字母读法拼出来（例如 M-A-X → « ème, a, ixe »）。")],
        [("ecrit", "Mon arbre généalogique", "我的家谱", "Dessine ton arbre généalogique et écris 6 phrases : « Voici mon père, il s'appelle… Il a … ans. »", "画出你的家谱，写6句话：« Voici mon père, il s'appelle… Il a … ans. »"),
         ("oral", "Les nombres", "数字", "Enregistre-toi : compte de 0 à 30, puis lis ces nombres : 45, 58, 63, 71, 86, 99, 100.", "录音：从0数到30，再读这些数字：45、58、63、71、86、99、100。")],
        [("ecrit", "Ma trousse et mon cartable", "我的文具盒和书包", "Fais une liste de 10 objets de ton cartable avec l'article (un / une) et dessine-les.", "列出书包里的10样东西，加上冠词（un / une），并画出来。"),
         ("oral", "Ma semaine à l'école", "我在学校的一周", "Enregistre-toi : dis les jours de la semaine et ce que tu as à l'école chaque jour (« Le lundi, j'ai maths. »).", "录音：说出一周七天，以及每天在学校上什么课（« Le lundi, j'ai maths. »）。")],
        [("ecrit", "J'aime, je n'aime pas", "我喜欢，我不喜欢", "Écris 5 choses que tu aimes et 5 choses que tu n'aimes pas. Utilise : j'aime, j'adore, je n'aime pas, je déteste.", "写5样你喜欢的和5样你不喜欢的东西。用上：j'aime、j'adore、je n'aime pas、je déteste。"),
         ("ecrit", "Conjugaison : verbes en -er", "动词变位：-er 动词", "Conjugue au présent : parler, jouer, regarder, danser (je, tu, il/elle, nous, vous, ils/elles). Puis écris une phrase avec chaque verbe.", "把 parler、jouer、regarder、danser 变位到现在时（所有人称），每个动词再造一个句子。")],
        [("ecrit", "Ma chambre", "我的房间", "Dessine ta chambre et décris-la en 6 phrases avec « il y a » et sur, sous, à côté de, devant, derrière.", "画出你的房间，用 « il y a » 和 sur、sous、à côté de、devant、derrière 写6句话描述它。"),
         ("oral", "Visite de ma maison", "参观我的家", "Enregistre-toi (1 minute) : présente les pièces de ta maison comme pour une visite.", "录一段1分钟的音频：像带人参观一样介绍你家的房间。")],
        [("ecrit", "Mon menu préféré", "我最喜欢的菜单", "Écris ton menu idéal (entrée, plat, dessert, boisson) avec du, de la, des. Exemple : « Je mange du riz. »", "写出你理想的菜单（前菜、主菜、甜点、饮料），用上 du、de la、des。例如：« Je mange du riz. »"),
         ("oral", "Au restaurant", "在餐厅", "Enregistre un petit dialogue au restaurant (avec un parent ou seul) : commander un plat et une boisson, demander l'addition.", "录一段在餐厅的小对话（可以和家人一起）：点一道菜和一杯饮料，然后结账。")],
        [("ecrit", "Ma journée", "我的一天", "Raconte ta journée en 8 phrases avec l'heure : « Je me lève à 7 heures. »", "用8句话写你的一天，要写时间：« Je me lève à 7 heures. »"),
         ("ecrit", "Quelle heure est-il ?", "现在几点？", "Dessine 6 horloges avec des heures différentes et écris l'heure en lettres sous chaque horloge.", "画6个钟表，时间各不相同，在每个钟表下面用法语写出时间。")],
        [("ecrit", "Le plan de mon quartier", "我家附近的地图", "Dessine le plan de ton quartier et écris le chemin de ta maison à l'école (tout droit, à gauche, à droite…).", "画出你家附近的地图，写出从家到学校怎么走（tout droit、à gauche、à droite……）。"),
         ("oral", "Demander son chemin", "问路", "Enregistre-toi : demande le chemin pour aller à la gare, puis explique le chemin pour aller à la poste.", "录音：问去火车站怎么走，再说明去邮局怎么走。")],
        [("ecrit", "Ma tenue préférée", "我最喜欢的衣服", "Décris en 5 phrases les vêtements que tu portes aujourd'hui et leurs couleurs (attention aux accords).", "用5句话描述你今天穿的衣服和颜色（注意性数配合）。"),
         ("oral", "La météo", "天气预报", "Présente la météo de 3 villes (Pékin, Paris et ta ville) comme à la télévision.", "像电视上一样，播报3个城市的天气：北京、巴黎和你的城市。")],
        [("ecrit", "Mon anniversaire", "我的生日", "Écris une invitation pour ta fête d'anniversaire : date, heure, lieu, ce qu'on va faire.", "写一张生日会邀请卡：日期、时间、地点、要做什么。"),
         ("ecrit", "Les fêtes de l'année", "一年里的节日", "Écris 6 fêtes françaises ou chinoises avec leur date ou leur mois (ex. : Le Nouvel An chinois est en janvier ou en février.).", "写出6个法国或中国的节日和日期或月份（例如：Le Nouvel An chinois est en janvier ou en février.）。")],
    ],
    "A2": [
        [("ecrit", "Mon week-end", "我的周末", "Raconte ton dernier week-end en 8 phrases au passé composé.", "用复合过去时写8句话，讲讲你上个周末。"),
         ("ecrit", "Avoir ou être ?", "用 avoir 还是 être？", "Écris 10 phrases au passé composé : 5 avec avoir, 5 avec être (aller, venir, partir, arriver, rester).", "写10个复合过去时的句子：5个用 avoir，5个用 être（aller、venir、partir、arriver、rester）。")],
        [("ecrit", "Portrait d'un ami", "描写一个朋友", "Fais le portrait de ton meilleur ami (physique et caractère) en 8 phrases.", "用8句话描写你最好的朋友（外貌和性格）。"),
         ("ecrit", "Comparaisons", "比较", "Compare deux personnes de ta famille avec plus… que, moins… que, aussi… que (6 phrases).", "用 plus… que、moins… que、aussi… que 比较两个家人（6句话）。")],
        [("ecrit", "Carte postale de vacances", "假期明信片", "Écris une carte postale (80 mots) à un ami : où tu es, le transport, l'hôtel, ce que tu vas faire demain.", "给朋友写一张明信片（80词左右）：你在哪里、怎么去的、住在哪里、明天要做什么。"),
         ("oral", "Réserver une chambre", "预订房间", "Enregistre un dialogue : tu téléphones à un hôtel pour réserver une chambre (dates, prix, petit-déjeuner).", "录一段对话：给酒店打电话订房（日期、价格、早餐）。")],
        [("ecrit", "Quand j'étais petit", "我小时候", "Raconte en 8 phrases ta vie quand tu avais 5 ans (où tu habitais, ce que tu aimais…) à l'imparfait.", "用未完成过去时写8句话，讲讲你5岁时的生活（住在哪里、喜欢什么……）。"),
         ("ecrit", "Imparfait ou passé composé ?", "未完成过去时还是复合过去时？", "Raconte un souvenir (un jour spécial) en mélangeant l'imparfait (description) et le passé composé (actions).", "讲一段回忆（特别的一天），描写用未完成过去时，动作用复合过去时。")],
        [("oral", "Au marché", "在市场", "Enregistre un dialogue au marché : demander le prix, la quantité (un kilo de, une bouteille de…), payer.", "录一段在市场的对话：问价格、说数量（un kilo de、une bouteille de……）、付钱。"),
         ("ecrit", "Les pronoms COD", "直接宾语代词", "Réponds à 10 questions en remplaçant le nom par le, la, l' ou les (ex. : Tu regardes la télé ? — Oui, je la regarde.).", "回答10个问题，用 le、la、l'、les 代替名词（例如：Tu regardes la télé ? — Oui, je la regarde.）。")],
        [("oral", "Chez le médecin", "看医生", "Enregistre un dialogue chez le médecin : dire où tu as mal, comprendre les conseils.", "录一段看医生的对话：说哪里疼，听懂医生的建议。"),
         ("ecrit", "Conseils pour être en forme", "保持健康的建议", "Écris 8 conseils pour être en bonne santé avec « il faut », « tu dois » et l'impératif.", "用 « il faut »、« tu dois » 和命令式写8条保持健康的建议。")],
        [("ecrit", "Petite annonce", "租房广告", "Écris une petite annonce pour louer ton appartement idéal (pièces, prix, quartier).", "写一则出租你理想公寓的广告（房间、价格、街区）。"),
         ("ecrit", "Y et en", "代词 y 和 en", "Réponds à 10 questions avec y ou en (ex. : Tu vas à la piscine ? — Oui, j'y vais.).", "用 y 或 en 回答10个问题（例如：Tu vas à la piscine ? — Oui, j'y vais.）。")],
        [("ecrit", "Mon émission préférée", "我最喜欢的节目", "Présente ton émission ou ta vidéo préférée et donne ton avis en 80 mots.", "介绍你最喜欢的节目或视频，并发表看法（80词左右）。"),
         ("oral", "Internet et moi", "我和网络", "Enregistre-toi (1 minute) : combien de temps tu passes sur Internet et pour faire quoi.", "录一段1分钟的音频：你每天上网多长时间，做什么。")],
        [("ecrit", "Dans 10 ans", "十年以后", "Imagine ta vie dans 10 ans en 8 phrases au futur simple.", "用简单将来时写8句话，想象十年以后的你。"),
         ("oral", "Mes projets de vacances", "我的假期计划", "Enregistre-toi : présente tes projets pour les prochaines vacances (futur proche et futur simple).", "录音：介绍下一个假期的计划（用最近将来时和简单将来时）。")],
        [("ecrit", "Une région de France", "法国的一个地区", "Choisis une région de France et présente-la en 100 mots (ville, spécialités, fête).", "选一个法国的地区，用100词左右介绍（城市、特产、节日）。"),
         ("ecrit", "Courriel à un correspondant", "给笔友写邮件", "Écris un courriel à un correspondant français pour lui présenter une fête chinoise.", "给一个法国笔友写邮件，介绍一个中国节日。")],
    ],
    "B1": [
        [("ecrit", "Pour ou contre l'uniforme ?", "赞成还是反对校服？", "Donne ton opinion sur l'uniforme scolaire en 150 mots avec des connecteurs (d'abord, ensuite, cependant, enfin).", "就校服问题发表看法（150词左右），用上连接词（d'abord、ensuite、cependant、enfin）。"),
         ("oral", "Je suis d'accord, je ne suis pas d'accord", "同意和反对", "Enregistre-toi (2 minutes) : réagis à la phrase « Les devoirs sont inutiles. »", "录一段2分钟的音频：对 « Les devoirs sont inutiles. » 这句话发表看法。")],
        [("ecrit", "Si j'étais…", "如果我是……", "Écris 8 phrases au conditionnel : « Si j'étais ministre de l'Éducation, je… »", "用条件式写8句话：« Si j'étais ministre de l'Éducation, je… »"),
         ("ecrit", "Mes études", "我的学业", "Présente en 150 mots les études que tu voudrais faire plus tard et pourquoi.", "用150词左右介绍你以后想学的专业以及原因。")],
        [("ecrit", "Mon CV", "我的简历", "Rédige ton CV en français pour un petit job d'été (formation, langues, qualités).", "用法语写一份暑期兼职简历（学历、语言、优点）。"),
         ("ecrit", "Qui, que, où, dont", "关系代词", "Écris 10 phrases pour définir des métiers avec qui, que, où, dont (ex. : Un boulanger est une personne qui…).", "用 qui、que、où、dont 写10个句子来解释职业（例如：Un boulanger est une personne qui…）。")],
        [("ecrit", "Il était une fois", "从前……", "Écris un conte de 200 mots au passé (imparfait, passé composé, plus-que-parfait).", "用过去时写一个200词左右的童话（未完成过去时、复合过去时、愈过去时）。"),
         ("oral", "Raconter un film", "讲一部电影", "Enregistre-toi (2 minutes) : raconte l'histoire d'un film que tu as vu.", "录一段2分钟的音频：讲你看过的一部电影的故事。")],
        [("ecrit", "Journal intime", "日记", "Écris une page de journal (150 mots) sur une journée pleine d'émotions.", "写一篇日记（150词左右），记录一个情绪起伏的日子。"),
         ("ecrit", "Le subjonctif", "虚拟式", "Complète 10 phrases avec le subjonctif après « je veux que », « il faut que », « j'ai peur que ».", "在 « je veux que »、« il faut que »、« j'ai peur que » 之后用虚拟式完成10个句子。")],
        [("ecrit", "Sauver la planète", "拯救地球", "Écris un article de 150 mots : 5 gestes pour protéger l'environnement, avec causes et conséquences.", "写一篇150词左右的短文：保护环境的5个做法，说明原因和结果。"),
         ("oral", "Exposé : un problème écologique", "演讲：一个环境问题", "Enregistre un exposé de 2 minutes sur un problème écologique dans ta ville.", "录一段2分钟的演讲，介绍你所在城市的一个环境问题。")],
        [("ecrit", "Critique de livre", "书评", "Écris la critique d'un livre (résumé et avis) en 150 mots.", "写一篇书评（概要和看法），150词左右。"),
         ("oral", "Ma chanson française", "我的法语歌", "Choisis une chanson française, présente-la et explique pourquoi tu l'aimes (2 minutes).", "选一首法语歌，介绍它并说明你为什么喜欢（2分钟）。")],
        [("ecrit", "Le règlement de la classe", "班级规则", "Rédige 10 règles pour la classe idéale : obligations et interdictions (il est interdit de, on doit…).", "为理想的班级写10条规则：义务和禁止（il est interdit de、on doit……）。"),
         ("ecrit", "Droits des enfants", "儿童权利", "Présente 5 droits des enfants et explique pourquoi ils sont importants (150 mots).", "介绍5项儿童权利，说明它们为什么重要（150词左右）。")],
        [("ecrit", "Il a dit que…", "他说……", "Transforme un dialogue de 10 répliques au discours rapporté au passé.", "把一段10句的对话改写成过去时的间接引语。"),
         ("oral", "Rapporter une interview", "转述采访", "Interroge un membre de ta famille (3 questions), puis rapporte ses réponses au discours indirect.", "采访一个家人（3个问题），再用间接引语转述他的回答。")],
        [("ecrit", "DELF B1 : production écrite", "DELF B1：写作", "Sujet type DELF B1 : écris un courriel de 160 mots pour raconter une expérience et donner ton avis.", "DELF B1 写作题型：写一封160词左右的邮件，讲述一次经历并发表看法。"),
         ("oral", "DELF B1 : monologue suivi", "DELF B1：连续独白", "Prépare 10 minutes puis enregistre 3 minutes sur le sujet : « Le sport est-il important pour les jeunes ? »", "准备10分钟，然后就 « Le sport est-il important pour les jeunes ? » 录3分钟。")],
    ],
    "B2": [
        [("ecrit", "Essai argumenté", "议论文", "Rédige un texte argumenté de 250 mots : « Faut-il interdire les téléphones à l'école ? »", "写一篇250词左右的议论文：« Faut-il interdire les téléphones à l'école ? »"),
         ("oral", "Débat", "辩论", "Enregistre 3 minutes : défends une opinion, puis réfute l'opinion contraire.", "录3分钟：先为一个观点辩护，再反驳相反的观点。")],
        [("ecrit", "Analyse d'article", "文章分析", "Choisis un article de presse français récent, résume-le et sépare les faits des opinions (200 mots).", "选一篇最近的法语新闻文章，概括内容并区分事实和观点（200词左右）。"),
         ("ecrit", "Une fausse information", "假新闻", "Explique comment reconnaître une fausse information, avec un exemple (200 mots).", "说明如何识别假新闻，并举一个例子（200词左右）。")],
        [("ecrit", "L'IA à l'école", "学校里的人工智能", "Avantages et dangers de l'intelligence artificielle pour les élèves : 250 mots.", "人工智能对学生的好处和危险：250词左右。"),
         ("oral", "Une invention", "一项发明", "Présente une invention qui a changé notre vie (3 minutes).", "介绍一项改变了我们生活的发明（3分钟）。")],
        [("ecrit", "Bien que, même si", "让步表达", "Écris 10 phrases de concession avec bien que (+ subjonctif), même si, pourtant, malgré.", "用 bien que（+虚拟式）、même si、pourtant、malgré 写10个表示让步的句子。"),
         ("ecrit", "Nuancer son opinion", "表达细微差别", "Réécris un texte d'opinion très tranché pour le rendre plus nuancé (200 mots).", "把一篇观点很绝对的短文改写得更有分寸（200词左右）。")],
        [("ecrit", "Lettre de motivation", "求职信", "Rédige une lettre de motivation pour un stage dans une entreprise française (registre soutenu).", "给一家法国公司写一封实习求职信（正式语体）。"),
         ("oral", "Entretien d'embauche", "求职面试", "Enregistre tes réponses à 5 questions d'entretien : qualités, défauts, projets, motivation.", "录下你对5个面试问题的回答：优点、缺点、计划、动机。")],
        [("ecrit", "La voix passive", "被动语态", "Transforme 10 titres de presse à la voix passive, puis écris un court article sur l'un d'eux.", "把10个新闻标题改成被动语态，再就其中一个写一篇短文。"),
         ("oral", "Un débat de société", "社会话题辩论", "Présente les deux points de vue sur un débat de société de ton choix (3 minutes).", "介绍一个你选择的社会话题的正反两方观点（3分钟）。")],
        [("ecrit", "Le français dans le monde", "世界上的法语", "Présente un pays francophone hors d'Europe : langue, culture, particularités du français (200 mots).", "介绍一个欧洲以外的法语国家：语言、文化、法语的特点（200词左右）。"),
         ("ecrit", "Changer de registre", "转换语体", "Réécris un même message en trois registres : familier, courant, soutenu.", "把同一条信息用三种语体改写：通俗、日常、正式。")],
        [("ecrit", "Plan d'essai", "议论文提纲", "Fais le plan détaillé (introduction, 2 parties, conclusion) d'un essai sur « Les voyages forment-ils la jeunesse ? »", "为 « Les voyages forment-ils la jeunesse ? » 写一份详细提纲（引言、两部分、结论）。"),
         ("ecrit", "Essai complet", "完整的议论文", "Rédige l'essai complet (250 mots) à partir de ton plan.", "根据你的提纲写出完整的议论文（250词左右）。")],
        [("ecrit", "Compte rendu de podcast", "播客听后报告", "Écoute un podcast français (10 minutes) et écris un compte rendu de 200 mots.", "听一期法语播客（10分钟），写一篇200词左右的听后报告。"),
         ("oral", "Résumé oral", "口头概述", "Résume oralement un reportage français que tu as regardé (2 minutes).", "口头概述你看过的一个法语报道（2分钟）。")],
        [("ecrit", "DELF B2 : production écrite", "DELF B2：写作", "Sujet type DELF B2 : lettre formelle argumentée de 250 mots adressée au maire de ta ville.", "DELF B2 写作题型：给你所在城市的市长写一封250词左右的正式议论信。"),
         ("oral", "DELF B2 : exposé", "DELF B2：口头陈述", "Prépare 30 minutes puis enregistre un exposé de 5 minutes à partir d'un court article.", "准备30分钟，然后根据一篇短文录5分钟的陈述。")],
    ],
}


def main():
    n = 0
    with connect() as c:
        units = {(r["level"], r["sort"]): r["id"] for r in c.execute("SELECT id, level, sort FROM program_units").fetchall()}
        for level, per_unit in BANK.items():
            for i, items in enumerate(per_unit, 1):
                uid = units.get((level, i))
                if not uid:
                    continue
                for j, (kind, tfr, tzh, ifr, izh) in enumerate(items, 1):
                    n += c.execute("""INSERT INTO homework_bank (key, unit_id, kind, title_fr, title_zh, instr_fr, instr_zh, sort, source)
                                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'seed') ON CONFLICT (key) DO NOTHING""",
                                   (f"{level}-{i:02d}-{j}", uid, kind, tfr, tzh, ifr, izh, j)).rowcount
    print(f"作业库 : {n} devoir(s) ajouté(s)")


if __name__ == "__main__":
    main()
