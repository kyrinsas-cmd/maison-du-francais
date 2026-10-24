"""Textes du site en chinois simplifié (zh, langue principale, à la racine /) et en français (fr, sous /fr/).
Une clé absente en zh retombe sur le français."""

LANGS = ("fr", "zh")
HTML_LANG = {"fr": "fr", "zh": "zh-Hans"}

T = {
    "fr": {
        "title": "Maison du français · 法语之家 — cours de français en direct",
        "description": "École de français en ligne : cours en direct de 5 élèves au maximum avec des professeurs FLE diplômés, basés en France.",
        "skip": "Aller au contenu",
        "home_aria": "Maison du français, accueil",
        "brand_main": "Maison du français", "brand_sub": "法语之家", "brand_sub_lang": "zh-Hans",
        "nav_aria": "Navigation principale",
        "nav_method": "Méthode", "nav_path": "Parcours", "nav_teachers": "Professeurs", "nav_atelier": "Atelier Paris",
        "nav_teach": "Enseigner chez nous", "nav_cta": "Cours d'essai gratuit", "nav_prices": "Tarifs", "nav_contact": "Contact",
        "method_title": "Méthode", "method_desc": "Test de niveau, 3 cours d'essai, classe de 5 élèves au plus et suivi : comment se déroulent les cours de français en direct.",
        "path_title": "Parcours et cours", "path_desc": "Parcours de français A1 à B2 : nombre de séances, durée et examens DELF visés.",
        "teachers_title": "Professeurs", "teachers_desc": "Les professeurs de Maison du français : enseignants FLE diplômés, basés en France.",
        "atelier_title": "Atelier Paris", "atelier_desc": "L'Atelier Paris : des séances de français en direct depuis un café ou un musée parisien, pendant les vacances.",
        "teach_title": "Enseigner chez nous", "teach_desc": "Professeurs de FLE en France : enseignez à de petits groupes de 5 élèves. Envoyez votre candidature.",
        "contact_title": "Contact", "contact_desc": "Réserver un test de niveau gratuit ou un cours d'essai, ou nous écrire.",
        "contact_h1": "Réserver un test ou un cours d'essai",
        "contact_lead": "Le test de niveau et les 3 cours d'essai sont gratuits. Pour les familles en Chine, tout se passe sur WeChat.",
        "contact_s1": "Scannez le QR code WeChat.", "contact_s2": "Indiquez l'âge et le niveau de votre enfant.", "contact_s3": "Nous fixons ensemble le test de niveau.",
        "contact_other_h": "Autres demandes", "contact_partner": "Écoles et partenaires : écrivez-nous.", "contact_teach": "Vous êtes professeur ?",
        "home_more_h2": "Découvrir Maison du français", "more": "En savoir plus", "teachers_all": "Voir tous les professeurs",
        "tz_method": "Test de niveau, cours d'essai, classe de 5 et suivi : comment se passent les cours.",
        "tz_path": "De A1 à B2 : séances, durée et examens DELF visés.",
        "tz_teachers": "Des enseignants FLE diplômés, basés en France.",
        "tz_atelier": "Le français en direct depuis Paris, pendant les vacances.",
        "home_cta_h2": "Prêt pour le premier cours ?",
        "pr_title": "Tarifs", "pr_desc": "Tarifs des cours de français en direct, en classe de 5 élèves au plus : prix par séance, forfaits et estimation par niveau.",
        "pr_eyebrow": "Tarifs", "pr_h1": "Un prix simple : par séance et par élève.",
        "pr_lead": "Chaque séance est facturée une heure : 45 minutes de cours en direct, puis 15 minutes de correction des devoirs et de questions.",
        "pr_preview": "Aperçu : cette page n'est pas encore publiée.",
        "pr_unit": "par séance et par élève", "pr_free": "Test de niveau et 3 cours d'essai offerts",
        "pr_block_h": "Forfait", "pr_block": "{n} séances, soit environ {w} semaines à 3 cours par semaine",
        "pr_private_h": "Cours particulier", "pr_private": "par heure, pour un rattrapage ou un soutien individuel",
        "pr_included_h": "Inclus dans chaque séance",
        "pr_inc1": "Classe de 3 à 5 élèves, professeur FLE diplômé en France", "pr_inc2": "15 minutes de devoirs corrigés et de questions",
        "pr_inc3": "Commentaires du professeur et bilans réguliers", "pr_inc4": "Replay si l'absence est signalée 24 h à l'avance",
        "pr_inc5": "Parents auditeurs, caméra et micro coupés",
        "pr_level_h": "Estimation par niveau", "pr_level_lead": "Nombre de séances estimé à partir des heures de formation indicatives du DELF. Ordre de grandeur, pas un devis.",
        "pr_th_total": "Total estimé", "pr_cny": "¥",
        "pr_note": "Prix en yuans (RMB). L'inscription, le paiement et les conditions de remboursement sont confirmés au moment de l'inscription, sur WeChat.",
        "pr_cta": "Réserver le test de niveau gratuit",
        "switch_label": "中文", "switch_lang": "zh-Hans", "switch_aria": "Voir le site en chinois",

        "hero_pill": "Cours de français en direct · 5 élèves maximum",
        "hero_h1": "Votre enfant ose parler français, avec un professeur en France.",
        "hero_alt": "法国本土持证老师 · 直播小班，每班最多5人", "hero_alt_lang": "zh-Hans",
        "hero_lead": "Des enseignants FLE diplômés, basés en France, animent chaque cours en direct. Dans une classe de cinq, chaque enfant prend la parole à chaque séance, et les parents suivent ses progrès.",
        "hero_cta1": "Test de niveau gratuit", "hero_cta2": "Comment ça marche",
        "hero_note": "3 cours d'essai offerts à chaque élève, sans engagement.",
        "class_live": "En direct · Classe A1", "class_time": "Paris 10:00 · Pékin 17:00",
        "class_caption": "Illustration : pseudonymes uniquement, pas de chat privé.",

        "facts_aria": "L'essentiel",
        "fact1": "élèves au maximum par classe", "fact2": "professeurs diplômés, basés en France",
        "fact3": "minutes de cours, puis devoirs et questions", "fact4": "cours par semaine, horaires fixes",

        "method_eyebrow": "Méthode", "method_h2": "Quatre étapes, du test à la classe.",
        "method_lead": "Les classes sont formées par niveau de français (CECRL), pas par âge, après un test de placement.",
        "step1_h": "Test de niveau", "step1_p": "Gratuit, fait avec un parent. Il situe l'enfant sur l'échelle CECRL et donne un conseil de classe.",
        "step2_h": "3 cours d'essai", "step2_p": "Offerts, dans une vraie classe. L'élève en essai écoute, le professeur l'invite à parler.",
        "step3_h": "Choix de la classe", "step3_p": "Une classe ouvre à partir de 3 élèves et en compte 5 au plus. Chaque demande est validée par l'équipe.",
        "step4_h": "Suivi et bilans", "step4_p": "Commentaires du professeur, devoirs, replay en cas d'absence signalée 24 h à l'avance.",

        "path_eyebrow": "Parcours", "path_h2": "De A1 à B2, au rythme du DELF.",
        "path_lead": "Durées estimées à partir des heures de formation indicatives du DELF, à raison de 3 séances de 45 minutes par semaine. Chiffres arrondis, à confirmer.",
        "th_level": "Niveau", "th_sessions": "Séances (45 min)", "th_duration": "Durée", "th_exam": "Examen visé",
        "weeks": "≈ {n} semaines",

        "teachers_eyebrow": "Professeurs", "teachers_h2": "Des enseignants FLE diplômés, en France.",
        "teachers_lead": "Chaque profil et chaque vidéo de présentation sont vérifiés par l'équipe avant publication.",
        "teachers_empty": "Les premiers professeurs seront présentés ici très bientôt.",
        "teachers_cta": "Vous êtes professeur de FLE ?",
        "tp_profile": "Voir le profil", "tp_levels": "Niveaux", "tp_ages": "Âge des élèves", "tp_diplomas": "Diplômes",
        "tp_courses": "Cours", "tp_video": "Vidéo de présentation", "tp_about": "Présentation",
        "tp_cta": "Demander un cours d'essai", "tp_cta_note": "Les cours d'essai se réservent sur WeChat (QR code en bas de page).",
        "tp_back": "Tous les professeurs", "tp_title": "{name}, professeur de FLE",
        "tp_desc": "{name} enseigne le français en direct, en classe de 5 élèves au plus.",

        "parents_eyebrow": "Pour les parents", "parents_h2": "Une classe sûre, que vous pouvez observer.",
        "par1_h": "Parents auditeurs", "par1_p": "Vous pouvez suivre le cours, caméra et micro coupés.",
        "par2_h": "Pas de contact privé", "par2_p": "Pas de chat privé, pseudonymes uniquement, aucun échange hors de la plateforme.",
        "par3_h": "Replays réservés", "par3_p": "Enregistrement avec votre accord, visible par la seule classe.",
        "par4_h": "Bilans réguliers", "par4_p": "Commentaire du professeur sur l'oral et les devoirs de votre enfant.",

        "atelier_eyebrow": "Atelier Paris", "atelier_h2": "Le français en direct d'un café ou d'un musée parisien.",
        "atelier_p": "Des séances spéciales pendant les vacances scolaires, filmées depuis Paris.",
        "atelier_cta": "Être prévenu des dates",

        "teach_eyebrow": "Enseigner chez nous", "teach_h2": "Vous êtes professeur de FLE en France ?",
        "teach_lead": "Enseignez à de petits groupes de 5 élèves, sur des créneaux adaptés au décalage avec l'Asie. Statut indépendant, supports pédagogiques fournis.",
        "f_name": "Nom et prénom", "f_email": "E-mail", "f_diploma": "Diplôme FLE", "f_diploma_ph": "Master FLE, DAEFLE…",
        "f_message": "Message (facultatif)", "f_message_ph": "Expérience, publics, disponibilités…",
        "f_consent": "J'accepte que mes données soient utilisées pour étudier ma candidature et me recontacter",
        "f_privacy": "confidentialité", "f_submit": "Envoyer ma candidature", "f_website": "Site web",
        "err_name": "Indiquez votre nom et prénom.", "err_email": "Indiquez une adresse e-mail valide.",
        "err_diploma": "Indiquez votre diplôme FLE.", "err_long": "Votre message est trop long (3 000 caractères au plus).",
        "err_consent": "Merci d'accepter le traitement de vos données pour que nous puissions vous répondre.",
        "err_rate": "Trop d'envois depuis cette connexion. Réessayez dans une heure.",
        "done_title": "Candidature envoyée", "done_h1": "Merci, votre candidature est envoyée.",
        "done_p": "Nous l'étudions et nous vous recontactons par e-mail.", "back_home": "Retour à l'accueil",
        "nf_title": "Page introuvable", "nf_h1": "Page introuvable", "nf_p": "Cette page n'existe pas ou a été déplacée.",

        "foot_logo_alt": "Maison du français · 法语之家",
        "foot_tagline": "École de français en ligne, professeurs FLE en France.",
        "foot_parents": "Parents en Chine", "foot_qr": "QR code WeChat bientôt disponible",
        "foot_qr_text": "Le test de niveau et les cours d'essai se réservent sur WeChat.",
        "foot_contact": "Contact", "foot_contact_soon": "Adresse de contact bientôt disponible.",
        "foot_teach": "Devenir professeur", "foot_espace": "Espace professeur", "teach_login": "Déjà professeur chez nous ?", "foot_legal": "Mentions légales", "foot_privacy": "Confidentialité",
        "legal_title": "Mentions légales", "privacy_title": "Confidentialité",
    },
    "zh": {
        "title": "法语之家 Maison du français — 法国老师直播法语小班",
        "description": "在线法语学校：法国本土持证FLE老师直播授课，每班最多5名学生。",
        "skip": "跳到正文",
        "home_aria": "法语之家首页",
        "brand_main": "法语之家", "brand_sub": "Maison du français", "brand_sub_lang": "fr",
        "nav_aria": "主导航",
        "nav_method": "教学方法", "nav_path": "课程体系", "nav_teachers": "老师", "nav_atelier": "巴黎工坊",
        "nav_teach": "教师招聘", "nav_cta": "免费试听", "nav_prices": "收费标准", "nav_contact": "联系我们",
        "method_title": "教学方法", "method_desc": "水平测试、3节免费试听、每班最多5人的小班和学习跟踪：法语直播课的上课方式。",
        "path_title": "课程体系", "path_desc": "A1到B2的法语课程：课数、时长和对应的DELF考试。",
        "teachers_title": "老师", "teachers_desc": "法语之家的老师：身在法国的FLE持证老师。",
        "atelier_title": "巴黎沉浸工坊", "atelier_desc": "巴黎沉浸工坊：寒暑假从巴黎的咖啡馆、博物馆现场直播法语课。",
        "teach_title": "教师招聘", "teach_desc": "在法国的FLE老师：教5人小班，欢迎投递申请。",
        "contact_title": "联系我们", "contact_desc": "预约免费水平测试或试听课，或给我们留言。",
        "contact_h1": "预约水平测试或试听课",
        "contact_lead": "水平测试和3节试听课均免费。中国的家庭请通过微信预约。",
        "contact_s1": "扫描微信二维码。", "contact_s2": "告诉我们孩子的年龄和法语水平。", "contact_s3": "我们和您约定水平测试的时间。",
        "contact_other_h": "其他咨询", "contact_partner": "学校与合作机构：欢迎发邮件联系我们。", "contact_teach": "您是老师？",
        "home_more_h2": "了解法语之家", "more": "了解更多", "teachers_all": "查看全部老师",
        "tz_method": "水平测试、试听、五人小班和学习跟踪：上课流程一览。",
        "tz_path": "从A1到B2：课数、时长和对应的DELF考试。",
        "tz_teachers": "身在法国的FLE持证老师。",
        "tz_atelier": "寒暑假，从巴黎现场直播学法语。",
        "home_cta_h2": "准备好上第一节课了吗？",
        "pr_title": "收费标准", "pr_desc": "法国老师直播法语小班（每班最多5人）的收费标准：每节课单价、课时包和各级别费用估算。",
        "pr_eyebrow": "收费标准", "pr_h1": "价格透明：按节、按人收费。",
        "pr_lead": "每节课按1小时计费：45分钟直播授课，另有15分钟讲解作业和答疑。",
        "pr_preview": "预览：本页尚未发布。",
        "pr_unit": "每人每节", "pr_free": "免费水平测试，赠送3节试听课",
        "pr_block_h": "课时包", "pr_block": "{n}节课，按每周3节约{w}周",
        "pr_private_h": "一对一辅导", "pr_private": "每小时，用于补课或单独辅导",
        "pr_included_h": "每节课包含",
        "pr_inc1": "3–5人小班，法国本土FLE持证老师", "pr_inc2": "15分钟作业讲解与答疑",
        "pr_inc3": "老师评语和定期学习报告", "pr_inc4": "提前24小时请假可看回放",
        "pr_inc5": "家长可旁听（摄像头和麦克风关闭）",
        "pr_level_h": "各级别费用估算", "pr_level_lead": "课数根据DELF官方建议学时估算，仅供参考，不是报价。",
        "pr_th_total": "预估总价", "pr_cny": "¥",
        "pr_note": "价格以人民币计。报名、付款方式和退费规则在报名时通过微信确认。",
        "pr_cta": "预约免费水平测试",
        "switch_label": "Français", "switch_lang": "fr", "switch_aria": "Voir le site en français",

        "hero_pill": "法语直播课 · 每班最多5人",
        "hero_h1": "让孩子开口说法语，老师就在法国。",
        "hero_alt": "Cours de français en direct · professeurs en France", "hero_alt_lang": "fr",
        "hero_lead": "由身在法国的FLE持证老师全程直播授课。五人小班，每个孩子每节课都有开口的机会，家长随时了解孩子的进步。",
        "hero_cta1": "免费水平测试", "hero_cta2": "了解上课流程",
        "hero_note": "每位学员可免费试听3节课，无需任何承诺。",
        "class_live": "直播中 · A1班", "class_time": "巴黎 10:00 · 北京 17:00",
        "class_caption": "示意图：只显示昵称，不能私聊。",

        "facts_aria": "核心信息",
        "fact1": "每班最多学生人数", "fact2": "持证老师，人在法国",
        "fact3": "分钟授课，另有15分钟作业与答疑", "fact4": "每周上课次数，时间固定",

        "method_eyebrow": "教学方法", "method_h2": "从测试到入班，四步完成。",
        "method_lead": "按法语水平（欧标CECRL）分班，而不是按年龄；入班前先做分级测试。",
        "step1_h": "水平测试", "step1_p": "免费，家长陪同完成。确定孩子的欧标等级，并给出分班建议。",
        "step2_h": "3节试听课", "step2_p": "免费，在真实的小班里上课。试听学员先旁听，老师会邀请孩子开口。",
        "step3_h": "选班", "step3_p": "满3人开班，每班最多5人。每份报名申请都由我们人工审核。",
        "step4_h": "跟踪与报告", "step4_p": "老师评语和课后作业；提前24小时请假，可以观看该节课的回放。",

        "path_eyebrow": "课程体系", "path_h2": "从A1到B2，对标DELF考试。",
        "path_lead": "根据DELF官方建议学时估算，按每周3节、每节45分钟计算。数字为约数，以后续确认为准。",
        "th_level": "级别", "th_sessions": "课数（每节45分钟）", "th_duration": "时长", "th_exam": "目标考试",
        "weeks": "约{n}周",

        "teachers_eyebrow": "老师", "teachers_h2": "法国本土的FLE持证老师。",
        "teachers_lead": "每位老师的资料和介绍视频都经过我们审核后才会发布。",
        "teachers_empty": "首批老师即将在这里亮相。",
        "teachers_cta": "您是FLE老师？",
        "tp_profile": "查看老师介绍", "tp_levels": "教授级别", "tp_ages": "学生年龄", "tp_diplomas": "资质",
        "tp_courses": "所授课程", "tp_video": "介绍视频", "tp_about": "老师简介",
        "tp_cta": "预约试听", "tp_cta_note": "试听课通过微信预约（二维码见页面底部）。",
        "tp_back": "全部老师", "tp_title": "{name} · 法语老师（FLE）",
        "tp_desc": "{name}老师直播教授法语，每班最多5名学生。",

        "parents_eyebrow": "家长关心的", "parents_h2": "安全的课堂，家长可以旁听。",
        "par1_h": "家长旁听", "par1_p": "您可以旁听课堂，摄像头和麦克风默认关闭。",
        "par2_h": "不私下联系", "par2_p": "不能私聊，只显示昵称，不在平台之外联系孩子。",
        "par3_h": "回放仅限本班", "par3_p": "经您同意才录制，回放只对本班开放。",
        "par4_h": "定期学习报告", "par4_p": "老师对孩子口语表现和作业的评语。",

        "atelier_eyebrow": "巴黎沉浸工坊", "atelier_h2": "连线巴黎的咖啡馆和博物馆，在现场学法语。",
        "atelier_p": "寒暑假特别班，从巴黎现场直播。",
        "atelier_cta": "获取开课通知",

        "teach_eyebrow": "教师招聘", "teach_h2": "您是在法国的FLE老师吗？",
        "teach_lead": "教5人小班，上课时段照顾与亚洲的时差。以自由职业身份合作，我们提供教材。",
        "f_name": "姓名", "f_email": "电子邮箱", "f_diploma": "FLE文凭", "f_diploma_ph": "例如：FLE硕士、DAEFLE…",
        "f_message": "留言（选填）", "f_message_ph": "教学经验、学生类型、可上课时间…",
        "f_consent": "我同意你们使用我的信息来审核申请并与我联系",
        "f_privacy": "隐私政策", "f_submit": "提交申请", "f_website": "网站",
        "err_name": "请填写姓名。", "err_email": "请填写有效的电子邮箱。",
        "err_diploma": "请填写您的FLE文凭。", "err_long": "留言过长（最多3000字）。",
        "err_consent": "请勾选同意，我们才能回复您。",
        "err_rate": "提交次数过多，请一小时后再试。",
        "done_title": "申请已提交", "done_h1": "谢谢，您的申请已提交。",
        "done_p": "我们会审核您的申请，并通过电子邮件与您联系。", "back_home": "返回首页",
        "nf_title": "页面不存在", "nf_h1": "页面不存在", "nf_p": "该页面不存在或已移动。",

        "foot_logo_alt": "法语之家 · Maison du français",
        "foot_tagline": "在线法语学校，老师在法国。",
        "foot_parents": "中国的家长", "foot_qr": "微信二维码即将上线",
        "foot_qr_text": "水平测试和试听课请通过微信预约。",
        "foot_contact": "联系我们", "foot_contact_soon": "联系邮箱即将公布。",
        "foot_teach": "成为老师", "foot_espace": "Espace professeur（教师登录）", "teach_login": "已经是我们的老师？", "foot_legal": "法律声明", "foot_privacy": "隐私政策",
        "legal_title": "法律声明", "privacy_title": "隐私政策",
    },
}


class Texts(dict):
    """Accès {{ t.cle }} dans les templates ; une clé absente retombe sur le français, puis sur la clé elle-même."""

    def __init__(self, lang):
        super().__init__(T["fr"])
        self.update(T.get(lang, {}))

    def __getattr__(self, k):
        return self.get(k, k)


def texts(lang):
    return Texts(lang)


# Contrôle : toutes les clés françaises existent en chinois (python i18n.py)
if __name__ == "__main__":
    missing = sorted(set(T["fr"]) - set(T["zh"]))
    extra = sorted(set(T["zh"]) - set(T["fr"]))
    print("manquantes en zh :", missing or "aucune")
    print("en trop en zh :", extra or "aucune")
