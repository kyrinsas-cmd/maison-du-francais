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
        "nav_teach": "Enseigner chez nous", "nav_cta": "Cours d'essai gratuit",
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
        "foot_teach": "Devenir professeur", "foot_legal": "Mentions légales", "foot_privacy": "Confidentialité",
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
        "nav_teach": "教师招聘", "nav_cta": "免费试听",
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
        "foot_teach": "成为老师", "foot_legal": "法律声明", "foot_privacy": "隐私政策",
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
