"""Leçons pilotes (2026-11-14) : A1, unité 1 « Se présenter et saluer », 6 leçons de 45 min.
Rédigées par Claude comme base de travail : arrivent « en relecture » ; un professeur de FLE relit avant toute publication.
Guide du professeur en français, fiche de l'élève expliquée en chinois (élèves en Chine).
Lancé par deploy.sh : ajoute les leçons absentes (clé) ; met à jour une leçon de la graine tant qu'elle n'est ni publiée ni modifiée par l'équipe."""
from psycopg.types.json import Jsonb

from db import connect
from lesson_content import validate


def V(w, py, m):
    return {"w": w, "py": py, "m": m}


def E(t, py="", m=""):
    return {"t": t, "py": py, "m": m}


def S(mn, phase, title, do, say="", tip=""):
    return {"min": mn, "phase": phase, "title": title, "do": do, "say": say, "tip": tip}


def Q(q, choices, explain="", audio=None):          # la bonne réponse est la 1re (les choix sont mélangés à l'affichage)
    d = {"type": "qcm", "q": q, "choices": choices, "answer": 0, "explain": explain}
    if audio:
        d["audio"] = audio
    return d


def F(q, choices, explain=""):
    return {"type": "fill", "q": q, "choices": choices, "answer": 0, "explain": explain}


def TF(q, answer, explain="", audio=None):
    d = {"type": "tf", "q": q, "answer": answer, "explain": explain}
    if audio:
        d["audio"] = audio
    return d


def M(q, pairs):
    return {"type": "match", "q": q, "pairs": pairs}


def A(id_, label, script):
    return {"id": id_, "label": label, "script": script}


LESSONS = [
# ------------------------------------------------------------------ 1
{"key": "a1-u1-l1", "level": "A1", "unit": 1, "sort": 1, "title_fr": "Bonjour ! Saluer et dire au revoir", "title_zh": "你好！打招呼和告别",
 "content": {
  "objectives": ["Saluer et prendre congé selon le moment de la journée (bonjour, bonsoir, salut, au revoir, à demain, bonne nuit)",
                 "Demander et dire comment ça va (Ça va ? Ça va bien, merci. Et toi ?)", "Choisir tu ou vous (copain ou adulte)",
                 "Poser une question par l'intonation montante"],
  "can_do": ["用法语打招呼和告别（早上、晚上、睡觉前）", "问别人“你好吗？”，也会回答", "知道什么时候说 tu，什么时候说 vous"],
  "skills": ["co", "eo"],
  "exam": "DELF Prim A1 — production orale, entretien dirigé : saluer l'examinateur et répondre poliment ; compréhension de l'oral : salutations du quotidien.",
  "materials": ["Images : soleil (matin), lune (soir), lit (nuit)", "Une marionnette ou une peluche", "Deux cartes « tu » et « vous »"],
  "vocab": [V("bonjour", "", "你好（白天）"), V("salut", "", "你好／再见（朋友之间）"), V("bonsoir", "", "晚上好"), V("au revoir", "", "再见"),
            V("à demain", "", "明天见"), V("bonne nuit", "", "晚安"), V("Ça va ?", "", "你好吗？"), V("Ça va bien, merci.", "", "我很好，谢谢。"),
            V("Et toi ?", "", "你呢？"), V("madame", "", "女士（称呼女老师）"), V("monsieur", "", "先生（称呼男老师）")],
  "grammar": [
   {"title": "tu 还是 vous ?", "explain": "tu = 你：用于朋友、同学、家人和小朋友。\nvous = 您：用于老师和不熟悉的大人；同时跟好几个人说话时也用 vous（你们）。\n跟老师说话要用 vous！",
    "examples": [E("Salut Léo, ça va ?", "", "你好，Léo，你好吗？（朋友）"), E("Bonjour madame, vous allez bien ?", "", "老师好，您好吗？（老师）")]},
   {"title": "用语调提问", "explain": "汉语用“吗”提问，法语口语常常只靠语调：句尾声音往上扬 ↗ 就是问题，往下降 ↘ 就是回答。",
    "examples": [E("Ça va ? ↗", "", "你好吗？"), E("Ça va. ↘", "", "我很好。")]},
  ],
  "text": {"title": "À l'école", "audio": "dialogue", "lines": [
   {"who": "Madame Martin", "t": "Bonjour, les enfants !", "py": "", "m": "孩子们好！"},
   {"who": "Les enfants", "t": "Bonjour, madame !", "py": "", "m": "老师好！"},
   {"who": "Léo", "t": "Salut, Lili ! Ça va ?", "py": "", "m": "你好，丽丽！你好吗？"},
   {"who": "Lili", "t": "Ça va bien, merci. Et toi ?", "py": "", "m": "我很好，谢谢。你呢？"},
   {"who": "Léo", "t": "Ça va !", "py": "", "m": "我也很好！"},
   {"who": "Lili", "t": "Au revoir, madame ! À demain !", "py": "", "m": "老师再见！明天见！"}]},
  "steps": [
   S(5, "warmup", "Bonjour à chacun", "Saluer chaque élève par son prénom avec un geste de la main (« Bonjour Xiaoming ! »). Les élèves répondent « Bonjour madame ! » ou « Bonjour monsieur ! ». Demander à chacun s'il a un prénom français ; sinon, on garde le prénom chinois.",
     say="Bonjour Lili ! — Bonjour madame !", tip="Commencer par l'élève le plus à l'aise ; le plus timide parle en dernier, quand il a entendu les autres."),
   S(12, "present", "Bonjour, bonsoir, bonne nuit", "Montrer les images soleil / lune / lit : bonjour, bonsoir, bonne nuit. Salut entre copains. Écouter (ou lire) le dialogue, puis travailler « Ça va ? » avec la main qui monte, « Ça va. » avec la main qui descend. Présenter les cartes tu / vous.",
     say="Ça va ? ↗ — Ça va bien, merci. Et toi ?"),
   S(13, "practice", "Jeu des images et chaîne", "1) Le professeur montre une image, les élèves disent la bonne salutation. 2) Chaîne : chaque élève salue le suivant (« Salut X, ça va ? » — « Ça va bien, merci. Et toi ? »). 3) Prononciation : le son [u] (bonjour), le r (bonsoir, au revoir) au fond de la gorge.",
     tip="En visio, chacun dit le prénom de celui à qui il parle : tout le monde sait à qui c'est le tour."),
   S(10, "produce", "Jeu de rôle : à l'école", "Arriver à l'école le matin (saluer le professeur avec « vous », les copains avec « tu »), puis partir le soir (« Au revoir, madame ! À demain ! »). Chaque élève joue au moins deux fois, une fois le professeur."),
   S(5, "wrapup", "Bilan", "Relire « À la fin de la leçon, je sais… » : chaque élève dit une phrase. Présenter la tâche à faire après le cours. Finir par « Au revoir, les enfants ! À demain ! »."),
  ],
  "mistakes": ["« tu » au professeur : en chinois, 你 s'emploie beaucoup plus que 您 ; rappeler que vous ≈ 您.",
               "Le r prononcé à l'anglaise ou comme le r du pinyin : le faire sentir au fond de la gorge, comme un léger gargarisme.",
               "« bonjour » prononcé avec un n (« bon-n-jour ») : la voyelle nasale [ɔ̃] n'a pas de n.",
               "Questions dites avec une intonation plate : en chinois, c'est 吗 qui marque la question, en français c'est la voix qui monte."],
  "diff": {"young": "Une marionnette dit bonjour à chaque enfant et se trompe exprès (« Bonne nuit ! » le matin) : les enfants la corrigent.",
           "teen": "Comparer avec 你好 / 您好 ; ajouter « Comment allez-vous ? » et « Bonne journée ! »."},
  "culture": {"title": "法国人怎么打招呼？", "text": "在法国，进商店、上公交车、见到邻居都要说 Bonjour。朋友和家人之间常常贴脸颊（la bise），跟老师和不认识的大人一般握手，或者说 Bonjour madame / Bonjour monsieur。只说 Bonjour 而不加 madame / monsieur，有时会显得不够礼貌。"},
  "exercises": [
   Q("早上见到老师，你说：", ["Bonjour, madame !", "Bonne nuit, madame !", "Salut !"]),
   Q("晚上睡觉前，你对妈妈说：", ["Bonne nuit !", "Bonjour !", "À demain !"]),
   Q("朋友问你 « Ça va ? »，你回答：", ["Ça va bien, merci. Et toi ?", "Au revoir !", "Bonsoir !"]),
   Q("跟老师说话，你用：", ["vous", "tu"]),
   TF("« Salut » 可以对朋友说。", True),
   TF("« Bonsoir » 是早上用的。", False, explain="Bonsoir 是晚上用的；早上和白天说 Bonjour。"),
   F("___ demain !（明天见！）", ["À", "Au", "Et"]),
   M("把法语和中文意思连起来。", [["Bonjour", "你好（白天）"], ["Au revoir", "再见"], ["Bonne nuit", "晚安"], ["Merci", "谢谢"]]),
   Q("听录音。这是什么时候？", ["晚上", "早上", "睡觉前"], audio="s1"),
   Q("听录音。Léo 怎么样？", ["很好", "不太好", "很累"], audio="s2"),
  ],
  "task": {"kind": "oral", "title": "Bonjour, ça va ?", "instr": "用法语跟三个人打招呼（家人、朋友或玩偶都可以）：Bonjour ! Ça va ? … Au revoir ! 跟大人说 vous，跟朋友说 tu。录下来上传。",
           "instr_guide": "Vérifier : bonjour / bonsoir selon le moment, l'intonation montante de « Ça va ? », tu ou vous."},
  "audio": [A("dialogue", "Dialogue : À l'école", "Bonjour, les enfants !\nBonjour, madame !\nSalut, Lili ! Ça va ?\nÇa va bien, merci. Et toi ?\nÇa va !\nAu revoir, madame ! À demain !"),
            A("s1", "Écoute : quel moment ?", "Bonsoir, madame ! … Bonsoir, Lili !"),
            A("s2", "Écoute : Léo", "Salut, Léo ! Ça va ? … Ça va bien, merci !")],
 }},
# ------------------------------------------------------------------ 2
{"key": "a1-u1-l2", "level": "A1", "unit": 1, "sort": 2, "title_fr": "Je m'appelle…", "title_zh": "我叫……",
 "content": {
  "objectives": ["Demander et dire son prénom (Comment tu t'appelles ? Je m'appelle… Et toi ?)", "Présenter quelqu'un (C'est… Il s'appelle… / Elle s'appelle…)",
                 "Conjuguer s'appeler au singulier", "Distinguer il et elle"],
  "can_do": ["问别人叫什么名字，说出自己的名字", "介绍一个男孩或女孩叫什么名字", "分清 il（他）和 elle（她）"],
  "skills": ["co", "eo"],
  "exam": "DELF Prim A1 — entretien dirigé : « Comment tu t'appelles ? » est la première question de l'examinateur ; compréhension de l'oral : repérer un prénom.",
  "materials": ["Une balle (ou un objet à « lancer » en visio)", "Photos d'un garçon et d'une fille", "Badges à dessiner"],
  "vocab": [V("Comment tu t'appelles ?", "", "你叫什么名字？"), V("Je m'appelle…", "", "我叫……"), V("Il s'appelle…", "", "他叫……"), V("Elle s'appelle…", "", "她叫……"),
            V("C'est…", "", "这是……"), V("il", "", "他"), V("elle", "", "她"), V("un garçon", "", "男孩"), V("une fille", "", "女孩"),
            V("un copain / une copine", "", "朋友（男／女）"), V("oui", "", "是，对"), V("non", "", "不，不是")],
  "grammar": [
   {"title": "动词 s'appeler（叫……）", "explain": "je m'appelle（我叫）、tu t'appelles（你叫）、il / elle s'appelle（他／她叫）。\nappelle 有两个 l，词尾的 e 和 es 都不发音：三种形式读音一样 [apɛl]。",
    "examples": [E("Je m'appelle Lili.", "", "我叫丽丽。"), E("Tu t'appelles Léo ?", "", "你叫 Léo 吗？"), E("Elle s'appelle Chloé.", "", "她叫 Chloé。")]},
   {"title": "问名字的三种说法", "explain": "Comment tu t'appelles ?（最常用）\nTu t'appelles comment ?（更口语）\nComment vous vous appelez ?（对老师和大人，更礼貌）",
    "examples": [E("Comment tu t'appelles ?", "", "你叫什么名字？"), E("Comment vous vous appelez ?", "", "您叫什么名字？")]},
   {"title": "il 还是 elle ?", "explain": "汉语口语里“他”和“她”读音一样（tā），法语却不一样：il = 他（男），elle = 她（女）。",
    "examples": [E("C'est Léo. Il s'appelle Léo.", "", "这是 Léo。他叫 Léo。"), E("C'est Lili. Elle s'appelle Lili.", "", "这是丽丽。她叫丽丽。")]},
  ],
  "text": {"title": "Comment tu t'appelles ?", "audio": "dialogue", "lines": [
   {"who": "Léo", "t": "Bonjour ! Je m'appelle Léo. Et toi, comment tu t'appelles ?", "py": "", "m": "你好！我叫 Léo。你呢，你叫什么名字？"},
   {"who": "Xiaoming", "t": "Je m'appelle Xiaoming.", "py": "", "m": "我叫小明。"},
   {"who": "Léo", "t": "Et elle, comment elle s'appelle ?", "py": "", "m": "她呢，她叫什么名字？"},
   {"who": "Xiaoming", "t": "C'est ma copine. Elle s'appelle Lili.", "py": "", "m": "这是我的朋友。她叫丽丽。"},
   {"who": "Lili", "t": "Bonjour, Léo !", "py": "", "m": "你好，Léo！"},
   {"who": "Léo", "t": "Salut, Lili !", "py": "", "m": "你好，丽丽！"}]},
  "steps": [
   S(5, "warmup", "Bonjour, ça va ?", "Révision de la leçon 1 : la balle passe d'un élève à l'autre, celui qui la reçoit répond « Ça va bien, merci. Et toi ? » et la relance."),
   S(12, "present", "Je m'appelle…", "Le professeur se présente (« Je m'appelle… »), puis écoute du dialogue. Faire répéter « Je m'appelle » en frappant les syllabes (je-m'a-ppelle : 3 temps). Présenter il / elle avec les photos garçon / fille.",
     say="Je m'appelle Madame Martin. Et toi, comment tu t'appelles ?"),
   S(13, "practice", "La chaîne des prénoms", "1) Chaîne : « Je m'appelle X. Et toi ? ». 2) Le professeur montre un élève de la classe : « Il / Elle s'appelle comment ? » — « Il s'appelle… ». 3) Variante polie : chacun pose la question au professeur avec « vous ».",
     tip="Avec 5 élèves, chacun présente aussi son voisin : tout le monde utilise il et elle."),
   S(10, "produce", "Mon badge", "Chaque élève dessine un badge avec son prénom, se présente, puis présente une personne de sa famille ou un personnage qu'il aime (« C'est… Il / Elle s'appelle… »)."),
   S(5, "wrapup", "Bilan", "Tour rapide : chaque élève dit le prénom de deux camarades (« Il s'appelle…, elle s'appelle… »). Présenter la tâche."),
  ],
  "mistakes": ["il / elle confondus : en chinois oral, 他 et 她 se disent tous les deux tā. Travailler avec des photos.",
               "« Je m'appelle » prononcé avec le e final (« ma-pe-lé ») : le e final ne se prononce pas.", "Oubli du pronom : « Je appelle… » ; rappeler « je m'appelle »."],
  "diff": {"young": "Jeu de la marionnette qui oublie les prénoms : les enfants lui répondent « Non ! Il s'appelle… ».",
           "teen": "Ajouter le nom de famille : « Je m'appelle Lili Wang. Mon prénom, c'est Lili. »"},
  "culture": {"title": "名字的顺序", "text": "法国人先说名（prénom），再说姓（nom）：Léo Martin，Martin 是姓。很多学法语的中国孩子会起一个法语名字（Léo、Chloé……），也可以直接用自己的中文名字。"},
  "exercises": [
   Q("« Comment tu t'appelles ? » 是什么意思？", ["你叫什么名字？", "你好吗？", "你几岁？"]),
   Q("介绍一个女孩，要说：", ["Elle s'appelle Lili.", "Il s'appelle Lili.", "Je s'appelle Lili."]),
   F("Je m'___ Xiaoming.", ["appelle", "appelles", "appeler"]),
   F("Tu t'___ comment ?", ["appelles", "appelle", "appelez"]),
   TF("« il » 的意思是“她”。", False, explain="il = 他，elle = 她。"),
   Q("问老师叫什么名字，礼貌的说法是：", ["Comment vous vous appelez ?", "Tu t'appelles comment ?", "Et toi ?"]),
   M("把法语和中文意思连起来。", [["Je m'appelle", "我叫"], ["il", "他"], ["elle", "她"], ["un garçon", "男孩"]]),
   Q("听录音。男孩叫什么名字？", ["Hugo", "Léo", "Lili"], audio="n1"),
   Q("听录音。她叫什么名字？", ["Chloé", "Zoé", "Léa"], audio="n2"),
  ],
  "task": {"kind": "oral", "title": "Je me présente", "instr": "录一段自我介绍：Bonjour ! Je m'appelle … 然后介绍一个家人或朋友：C'est … Il / Elle s'appelle … 上传录音。",
           "instr_guide": "Vérifier : « je m'appelle » sans e final prononcé ; il / elle selon la personne présentée."},
  "audio": [A("dialogue", "Dialogue : Comment tu t'appelles ?", "Bonjour ! Je m'appelle Léo. Et toi, comment tu t'appelles ?\nJe m'appelle Xiaoming.\nEt elle, comment elle s'appelle ?\nC'est ma copine. Elle s'appelle Lili.\nBonjour, Léo !\nSalut, Lili !"),
            A("n1", "Écoute : le prénom du garçon", "Bonjour ! Comment tu t'appelles ? … Je m'appelle Hugo."),
            A("n2", "Écoute : le prénom de la fille", "C'est ma copine. Elle s'appelle Chloé.")],
 }},
# ------------------------------------------------------------------ 3
{"key": "a1-u1-l3", "level": "A1", "unit": 1, "sort": 3, "title_fr": "L'alphabet : épeler son prénom", "title_zh": "字母表：拼写名字",
 "content": {
  "objectives": ["Dire l'alphabet", "Épeler son prénom et des mots courts", "Reconnaître les lettres difficiles pour un élève chinois (E / I, G / J, U, R, H, W, Y)",
                 "Connaître les accents é, è, ê et la cédille ç"],
  "can_do": ["用法语念字母表", "拼写自己的名字", "听懂别人拼写的名字"],
  "skills": ["co", "eo", "ce"],
  "exam": "DELF Prim A1 — compréhension de l'oral : noter un prénom épelé ; production orale : épeler son prénom.",
  "materials": ["Cartes des 26 lettres", "Tableau blanc partagé (pour écrire les mots épelés)"],
  "vocab": [V("l'alphabet", "", "字母表"), V("une lettre", "", "字母"), V("épeler", "", "拼写（一个一个字母说）"), V("Comment ça s'écrit ?", "", "怎么写？"),
            V("un accent", "", "字母上的符号"), V("une majuscule", "", "大写字母"), V("une minuscule", "", "小写字母"), V("deux L", "", "两个 L")],
  "grammar": [
   {"title": "最容易读错的字母", "explain": "法语字母和汉语拼音长得一样，读法却不一样：\nE 读 [ə]，嘴唇微圆；I 读 [i]，像“衣”。\nU 读 [y]：就是拼音里的 ü！\nG 读 [ʒe]，J 读 [ʒi]：开头的音一样，区别在后面的 e 和 i。[ʒ] 有点像拼音 r，但舌头不卷，嘴唇往前突。\nH 读 [aʃ]，在单词里一般不发音（hôtel）。\nR 读 [ɛʁ]：r 在喉咙后面。\nW 读 double vé，Y 读 i grec。",
    "examples": [E("U — tu, salut", "", "U 像拼音 ü"), E("G — Gérard", "", "G 读 [ʒe]"), E("J — Julie", "", "J 读 [ʒi]"), E("H — hôtel", "", "H 不发音")]},
   {"title": "字母上的符号", "explain": "é（accent aigu）读 [e]；è（accent grave）和 ê（accent circonflexe）读 [ɛ]；ç（cédille）读 [s]。\n拼写时要把符号说出来：E accent aigu。",
    "examples": [E("Chloé : C - H - L - O - E accent aigu", "", "Chloé 的拼写"), E("François : F - R - A - N - C cédille - O - I - S", "", "François 的拼写")]},
  ],
  "text": {"title": "Comment ça s'écrit ?", "audio": "dialogue", "lines": [
   {"who": "Madame Martin", "t": "Comment tu t'appelles ?", "py": "", "m": "你叫什么名字？"},
   {"who": "Xiaoming", "t": "Je m'appelle Xiaoming.", "py": "", "m": "我叫小明。"},
   {"who": "Madame Martin", "t": "Comment ça s'écrit ?", "py": "", "m": "怎么写？"},
   {"who": "Xiaoming", "t": "X - I - A - O - M - I - N - G.", "py": "", "m": "X、I、A、O、M、I、N、G。"},
   {"who": "Madame Martin", "t": "Merci, Xiaoming ! Et toi, Chloé ?", "py": "", "m": "谢谢，小明！Chloé，你呢？"},
   {"who": "Chloé", "t": "C - H - L - O - E accent aigu.", "py": "", "m": "C、H、L、O、E 加 accent aigu。"}]},
  "steps": [
   S(5, "warmup", "Les prénoms", "Révision : « Comment tu t'appelles ? » — « Il / Elle s'appelle… » avec les prénoms de la classe."),
   S(12, "present", "L'alphabet", "Dire l'alphabet par groupes de lettres (A–G, H–N, O–U, V–Z) en rythme ; les élèves répètent. Insister sur E / I, G / J, U, R, H. Présenter les accents avec des prénoms (Chloé, Hélène, François).",
     say="A, B, C, D, E, F, G… — Comment ça s'écrit ?", tip="Écrire les lettres au tableau partagé pendant qu'on les dit : les élèves associent son et forme."),
   S(13, "practice", "Dictée de lettres et devinettes", "1) Le professeur dit une lettre, les élèves l'écrivent et la montrent à la caméra. 2) Le professeur épelle un mot connu (salut, merci, Léo), les élèves le devinent. 3) Les élèves épellent à leur tour un mot pour les autres."),
   S(10, "produce", "J'épelle mon prénom", "Chaque élève épelle son prénom (chinois ou français) ; les autres l'écrivent sur le tableau partagé. On vérifie ensemble. Puis épeler le prénom d'un membre de sa famille."),
   S(5, "wrapup", "Bilan", "Réciter l'alphabet tous ensemble une dernière fois ; rappeler les 3 lettres les plus difficiles du jour ; présenter la tâche."),
  ],
  "mistakes": ["E et I confondus : E [ə] / I [i].", "G et J inversés : G [ʒe] / J [ʒi].", "U prononcé [u] : c'est le ü du pinyin.",
               "Lettres du pinyin lues à la chinoise (X lu comme 西, Q comme 七) : en français, X se dit [iks] et Q [ky].", "W dit « double you » à l'anglaise : en français, « double vé »."],
  "diff": {"young": "Chanter l'alphabet sur un air connu de tous (comme « Ah ! vous dirai-je, maman »), puis jouer au « jeu du pendu » avec des mots très courts.",
           "teen": "Épeler une adresse e-mail (arobase, point, tiret) : utile pour les formulaires."},
  "culture": {"title": "拼音和法语字母", "text": "法语字母表和汉语拼音用的都是拉丁字母，但读法不一样：拼音的 x 在法语里读 [iks]，拼音的 q 在法语里读 [ky]。用法语拼写中文名字时，要用法语字母的读法：Xiaoming = X [iks]、I、A、O、M、I、N、G。"},
  "exercises": [
   Q("法语字母 U 的发音像拼音里的：", ["ü", "u", "i"]),
   Q("哪个字母读 [ʒi]？", ["J", "G", "I"]),
   TF("字母 H 在单词 hôtel 里不发音。", True),
   Q("« Comment ça s'écrit ? » 是什么意思？", ["怎么写？", "你叫什么名字？", "这是什么？"]),
   Q("é 上面的符号叫：", ["accent aigu", "accent grave", "cédille"]),
   F("C - H - L - O - E accent ___", ["aigu", "grave", "cédille"]),
   M("字母和它的读法。", [["W", "double vé"], ["Y", "i grec"], ["H", "ache"], ["G", "gé"]]),
   TF("用法语拼写 Xiaoming 时，X 读“西”。", False, explain="法语字母 X 读 [iks]。"),
   Q("听录音。拼的是哪个名字？", ["Zoé", "Léa", "Chloé"], audio="a1"),
   Q("听录音。是哪个字母？", ["J", "G", "I"], audio="a2"),
  ],
  "task": {"kind": "oral", "title": "Mon prénom, lettre par lettre", "instr": "录音：用法语拼写你的中文名字和你的法语名字（如果有），再拼写一个家人的名字。上传录音。",
           "instr_guide": "Vérifier : E / I, G / J, U ; les lettres du pinyin dites à la française (X [iks], Q [ky])."},
  "audio": [A("dialogue", "Dialogue : Comment ça s'écrit ?", "Comment tu t'appelles ?\nJe m'appelle Xiaoming.\nComment ça s'écrit ?\nX, I, A, O, M, I, N, G.\nMerci, Xiaoming ! Et toi, Chloé ?\nC, H, L, O, E accent aigu."),
            A("a1", "Écoute : un prénom épelé", "Z, O, E accent aigu. Zoé."), A("a2", "Écoute : une lettre", "J. … J.")],
 }},
# ------------------------------------------------------------------ 4
{"key": "a1-u1-l4", "level": "A1", "unit": 1, "sort": 4, "title_fr": "Les nombres de 0 à 20 et l'âge", "title_zh": "0到20的数字和年龄",
 "content": {
  "objectives": ["Compter de 0 à 20", "Demander et dire son âge (Tu as quel âge ? J'ai 9 ans.)", "Conjuguer avoir au singulier", "Faire la liaison avec « ans » (deux‿ans, six‿ans, neuf‿ans)"],
  "can_do": ["用法语从0数到20", "问别人几岁，说出自己的年龄"],
  "skills": ["co", "eo"],
  "exam": "DELF Prim A1 — entretien dirigé : « Tu as quel âge ? » ; compréhension de l'oral : repérer un nombre.",
  "materials": ["Cartes des nombres 0–20", "Grilles de loto (bingo) de 0 à 20"],
  "vocab": [V("zéro, un, deux, trois, quatre, cinq", "", "0、1、2、3、4、5"), V("six, sept, huit, neuf, dix", "", "6、7、8、9、10"),
            V("onze, douze, treize, quatorze, quinze, seize", "", "11、12、13、14、15、16"), V("dix-sept, dix-huit, dix-neuf, vingt", "", "17、18、19、20"),
            V("Tu as quel âge ?", "", "你几岁？"), V("J'ai … ans.", "", "我……岁。"), V("un an", "", "一岁，一年"), V("avoir", "", "有")],
  "grammar": [
   {"title": "说年龄用 avoir（有）", "explain": "汉语说“我九岁”，法语说“我有九年”：J'ai neuf ans。\nj'ai（我有）、tu as（你有）、il / elle a（他／她有）。\n不能说 « Je suis neuf ans »！",
    "examples": [E("J'ai neuf ans.", "", "我九岁。"), E("Tu as quel âge ?", "", "你几岁？"), E("Il a onze ans.", "", "他十一岁。")]},
   {"title": "数字和 ans 连读", "explain": "数字后面跟 ans 时，数字最后的音要和 ans 连起来读（liaison）：\ndeux ans [døzɑ̃]、trois ans [tʁwazɑ̃]、six ans [sizɑ̃]、dix ans [dizɑ̃]、neuf ans [nœvɑ̃]、un an [œ̃nɑ̃]。",
    "examples": [E("J'ai six ans.", "", "我六岁。six‿ans 读 [sizɑ̃]"), E("Elle a neuf ans.", "", "她九岁。neuf‿ans 读 [nœvɑ̃]")]},
   {"title": "17、18、19", "explain": "dix-sept = 10 + 7，dix-huit = 10 + 8，dix-neuf = 10 + 9。11 到 16 要单独记。",
    "examples": [E("dix-sept", "", "17"), E("dix-huit", "", "18"), E("dix-neuf", "", "19")]},
  ],
  "text": {"title": "Tu as quel âge ?", "audio": "dialogue", "lines": [
   {"who": "Madame Martin", "t": "Lili, tu as quel âge ?", "py": "", "m": "丽丽，你几岁？"},
   {"who": "Lili", "t": "J'ai neuf ans.", "py": "", "m": "我九岁。"},
   {"who": "Madame Martin", "t": "Et toi, Xiaoming ?", "py": "", "m": "小明，你呢？"},
   {"who": "Xiaoming", "t": "J'ai onze ans. Et vous, madame ?", "py": "", "m": "我十一岁。老师，您呢？"},
   {"who": "Madame Martin", "t": "Ah ! C'est un secret !", "py": "", "m": "啊！这是秘密！"},
   {"who": "Léo", "t": "Moi, j'ai dix ans !", "py": "", "m": "我十岁！"}]},
  "steps": [
   S(5, "warmup", "Prénoms et lettres", "Révision rapide : chaque élève épelle le prénom d'un camarade, les autres devinent de qui il s'agit."),
   S(12, "present", "Compter jusqu'à 20", "Compter de 0 à 10 avec les doigts (à la française : on commence par le pouce), puis de 11 à 20. Écouter le dialogue ; présenter « Tu as quel âge ? — J'ai… ans » et la liaison avec « ans ».",
     say="Un, deux, trois… — Tu as quel âge ? — J'ai dix ans."),
   S(13, "practice", "Loto et « Bzz »", "1) Loto : le professeur tire des nombres, les élèves cochent leur grille. 2) « Bzz » : on compte chacun son tour ; à chaque multiple de 5, on dit « Bzz ! » à la place du nombre. 3) Répéter les âges avec les liaisons (deux‿ans, six‿ans, neuf‿ans).",
     tip="Laisser chaque élève tirer à son tour les nombres du loto : il parle, les autres écoutent."),
   S(10, "produce", "L'âge de ma famille", "Chaque élève demande l'âge d'un camarade, puis présente sa famille : « Mon frère a … ans. Ma mère a … ans. » (accepter « Maman a … ans »)."),
   S(5, "wrapup", "Bilan", "Compter de 20 à 0 tous ensemble ; rappeler « J'ai … ans » (pas « je suis ») ; présenter la tâche."),
  ],
  "mistakes": ["« Je suis neuf ans » : calque de 我是九岁 ; rappeler « J'ai neuf ans ».", "douze / treize / seize confondus : les faire entendre côte à côte.",
               "Pas de liaison (« deux / ans ») : faire entendre le [z] de deux‿ans, trois‿ans, six‿ans, dix‿ans.", "« quatre » prononcé avec un e final (« ka-tre ») : le e final est muet."],
  "diff": {"young": "Compter en sautant, en tapant dans les mains, avec des objets de la maison montrés à la caméra.",
           "teen": "Ajouter « Tu as quel âge ? / Quel âge as-tu ? » (registre plus soutenu) et les dates d'anniversaire."},
  "culture": {"title": "法国人怎么用手指数数？", "text": "法国人数数从大拇指开始：大拇指是 1，大拇指加食指是 2。另外，在中国有人说“虚岁”，在法国只说实际年龄（周岁）。"},
  "exercises": [
   Q("« quinze » 是几？", ["15", "5", "50"]),
   Q("« J'ai douze ans. » 他几岁？", ["12", "2", "20"]),
   F("J'___ dix ans.", ["ai", "as", "a"]),
   F("Tu ___ quel âge ?", ["as", "ai", "es"]),
   TF("说“我九岁”可以说 « Je suis neuf ans. »", False, explain="法语说年龄用 avoir：J'ai neuf ans."),
   Q("dix-sept =", ["17", "7", "70"]),
   M("把数字连起来。", [["treize", "13"], ["seize", "16"], ["onze", "11"], ["vingt", "20"]]),
   Q("听录音。Léo 几岁？", ["8岁", "18岁", "6岁"], audio="m1"),
   Q("听录音。是哪个数字？", ["14", "4", "40"], audio="m2"),
  ],
  "task": {"kind": "oral", "title": "Je compte et je dis mon âge", "instr": "录音：用法语从0数到20，然后说你和两个家人的年龄（J'ai … ans. Mon père a … ans.）。上传录音。",
           "instr_guide": "Vérifier : liaisons avec « ans », douze / treize / seize, avoir (et non « je suis »)."},
  "audio": [A("dialogue", "Dialogue : Tu as quel âge ?", "Lili, tu as quel âge ?\nJ'ai neuf ans.\nEt toi, Xiaoming ?\nJ'ai onze ans. Et vous, madame ?\nAh ! C'est un secret !\nMoi, j'ai dix ans !"),
            A("m1", "Écoute : l'âge de Léo", "Léo, tu as quel âge ? … J'ai huit ans."), A("m2", "Écoute : un nombre", "quatorze … quatorze")],
 }},
# ------------------------------------------------------------------ 5
{"key": "a1-u1-l5", "level": "A1", "unit": 1, "sort": 5, "title_fr": "Je suis chinois, j'habite à…", "title_zh": "我是中国人，我住在……",
 "content": {
  "objectives": ["Dire sa nationalité (Je suis chinois / chinoise)", "Dire où on habite (J'habite à Shanghai, en Chine)", "Accorder la nationalité au féminin (chinois → chinoise)",
                 "Conjuguer être au singulier ; à + ville, en + pays"],
  "can_do": ["说自己是哪国人", "说自己住在哪个城市、哪个国家", "分清 chinois（男）和 chinoise（女）"],
  "skills": ["co", "eo", "ce"],
  "exam": "DELF Prim A1 — entretien dirigé : « Tu habites où ? » ; compréhension écrite : fiche d'identité simple.",
  "materials": ["Carte du monde ou de la Chine et de la France", "Drapeaux", "Fiche d'identité vierge"],
  "vocab": [V("la Chine", "", "中国"), V("la France", "", "法国"), V("chinois / chinoise", "", "中国人（男／女）"), V("français / française", "", "法国人（男／女）"),
            V("je suis", "", "我是"), V("j'habite à…", "", "我住在……（城市）"), V("en Chine, en France", "", "在中国，在法国"),
            V("Tu habites où ?", "", "你住在哪里？"), V("Pékin", "", "北京"), V("moi aussi", "", "我也是")],
  "grammar": [
   {"title": "动词 être（是）", "explain": "je suis（我是）、tu es（你是）、il / elle est（他／她是）。",
    "examples": [E("Je suis chinoise.", "", "我是中国人。（女孩）"), E("Tu es français ?", "", "你是法国人吗？"), E("Il est chinois.", "", "他是中国人。")]},
   {"title": "女孩加 e", "explain": "说女孩的国籍时，词尾加 e，前面不发音的辅音就要读出来：\nchinois [ʃinwa] → chinoise [ʃinwaz]\nfrançais [fʁɑ̃sɛ] → française [fʁɑ̃sɛz]",
    "examples": [E("Léo est français.", "", "Léo 是法国人。"), E("Chloé est française.", "", "Chloé 是法国人。（读出最后的 [z]）")]},
   {"title": "à 还是 en ?", "explain": "城市前面用 à：J'habite à Pékin.\nla Chine、la France 这样的国家前面用 en：J'habite en Chine.",
    "examples": [E("J'habite à Shanghai, en Chine.", "", "我住在中国上海。"), E("Léo habite à Paris, en France.", "", "Léo 住在法国巴黎。")]},
  ],
  "text": {"title": "Bonjour la Chine !", "audio": "dialogue", "lines": [
   {"who": "Léo", "t": "Xiaoming, tu es chinois ?", "py": "", "m": "小明，你是中国人吗？"},
   {"who": "Xiaoming", "t": "Oui, je suis chinois. J'habite à Shanghai. Et toi ?", "py": "", "m": "是的，我是中国人。我住在上海。你呢？"},
   {"who": "Léo", "t": "Moi, je suis français. J'habite à Paris, en France.", "py": "", "m": "我是法国人。我住在法国巴黎。"},
   {"who": "Lili", "t": "Moi, je suis chinoise. J'habite à Pékin.", "py": "", "m": "我是中国人。我住在北京。"},
   {"who": "Léo", "t": "Super ! Bonjour la Chine !", "py": "", "m": "太好了！你好，中国！"}]},
  "steps": [
   S(5, "warmup", "Les nombres", "Révision : « Tu as quel âge ? » et un tour de « Bzz » de 0 à 20."),
   S(12, "present", "Nationalités et villes", "Carte du monde : la Chine, la France, quelques villes. Écouter le dialogue. Présenter je suis / tu es / il est, puis chinois / chinoise, français / française (faire entendre le [z] du féminin), puis à + ville, en + pays.",
     say="Je suis chinois. Elle est chinoise. J'habite à Pékin, en Chine."),
   S(13, "practice", "Le tour du monde", "1) Le professeur montre un drapeau et un personnage (garçon ou fille) : les élèves disent « Il est chinois » / « Elle est française ». 2) Questions en chaîne : « Tu habites où ? » — « J'habite à… »."),
   S(10, "produce", "Ma fiche d'identité", "Chaque élève remplit une fiche (prénom, âge, nationalité, ville) puis se présente à l'oral en 4 phrases. Les autres posent une question."),
   S(5, "wrapup", "Bilan", "Lire ensemble deux fiches d'identité ; rappeler chinois / chinoise et à / en ; présenter la tâche."),
  ],
  "mistakes": ["« chinoise » prononcé comme « chinois » : faire entendre la consonne finale [z].", "« J'habite à Chine » ou « dans Chine » : en Chine.",
               "« Je habite » : on dit « j'habite » (élision devant voyelle et h muet).", "« Je suis Chine » : confusion du pays et de la nationalité (中国 / 中国人)."],
  "diff": {"young": "Jeu des drapeaux à colorier ; les enfants présentent leur peluche : « Il s'appelle… Il est français. »",
           "teen": "Ajouter d'autres nationalités (anglais / anglaise, américain / américaine) et « Je parle chinois et un peu français. »"},
  "culture": {"title": "法国的中文", "text": "巴黎13区有一个很大的亚洲街区，法国的很多中学和大学也开设中文课。在法国，有时你会听到法国人用中文跟你打招呼：« Ni hao ! »"},
  "exercises": [
   F("Je suis ___.（女孩，中国人）", ["chinoise", "chinois", "Chine"]),
   F("J'habite ___ France.", ["en", "à", "au"]),
   F("J'habite ___ Paris.", ["à", "en", "au"]),
   Q("« Il est français. » 是什么意思？", ["他是法国人。", "他住在法国。", "她是法国人。"]),
   TF("chinoise 最后的 s 要读出来 [z]。", True),
   F("Tu ___ chinois ?", ["es", "est", "suis"]),
   M("把法语和中文意思连起来。", [["la Chine", "中国"], ["la France", "法国"], ["Pékin", "北京"], ["je suis", "我是"]]),
   Q("听录音。Chloé 住在哪里？", ["巴黎", "北京", "上海"], audio="p1"),
   Q("听录音。这句话说的是男孩还是女孩？", ["女孩", "男孩"], audio="p2"),
  ],
  "task": {"kind": "ecrit", "title": "Ma fiche d'identité", "instr": "写一张自己的法语身份卡：Je m'appelle… J'ai … ans. Je suis … J'habite à …, en … 可以加一张画或照片。拍照上传。",
           "instr_guide": "Vérifier : accord chinois / chinoise, j'habite à + ville, en + pays, j'ai … ans."},
  "audio": [A("dialogue", "Dialogue : Bonjour la Chine !", "Xiaoming, tu es chinois ?\nOui, je suis chinois. J'habite à Shanghai. Et toi ?\nMoi, je suis français. J'habite à Paris, en France.\nMoi, je suis chinoise. J'habite à Pékin.\nSuper ! Bonjour la Chine !"),
            A("p1", "Écoute : la ville de Chloé", "Chloé, tu habites où ? … J'habite à Paris."), A("p2", "Écoute : garçon ou fille ?", "Je suis française.")],
 }},
# ------------------------------------------------------------------ 6
{"key": "a1-u1-l6", "level": "A1", "unit": 1, "sort": 6, "title_fr": "Révision : je me présente", "title_zh": "复习：自我介绍",
 "content": {
  "objectives": ["Réviser l'unité 1 (saluer, prénom, âge, nationalité, ville)", "Se présenter en cinq phrases", "Répondre aux questions de l'entretien dirigé du DELF Prim A1",
                 "Mini-test (oral et exercices en ligne) et auto-évaluation"],
  "can_do": ["用五句话介绍自己", "回答老师的问题：叫什么名字、几岁、哪国人、住在哪里"],
  "skills": ["co", "eo", "ce"],
  "exam": "DELF Prim A1 — production orale, 1re partie « entretien dirigé » : répondre à des questions simples sur soi ; compréhension de l'oral : informations personnelles.",
  "materials": ["Cartes-questions de l'entretien", "Grille d'auto-évaluation (smileys)"],
  "vocab": [V("Comment tu t'appelles ?", "", "你叫什么名字？"), V("Tu as quel âge ?", "", "你几岁？"), V("Tu es chinois ?", "", "你是中国人吗？"),
            V("Tu habites où ?", "", "你住在哪里？"), V("Je me présente.", "", "我来介绍一下自己。")],
  "grammar": [
   {"title": "复习：四个动词", "explain": "s'appeler：je m'appelle\navoir：j'ai … ans\nêtre：je suis chinois / chinoise\nhabiter：j'habite à … , en …",
    "examples": [E("Je m'appelle Lili.", "", "我叫丽丽。"), E("J'ai neuf ans.", "", "我九岁。"), E("Je suis chinoise.", "", "我是中国人。"), E("J'habite à Pékin, en Chine.", "", "我住在中国北京。")]},
  ],
  "text": {"title": "L'entretien", "audio": "dialogue", "lines": [
   {"who": "Madame Martin", "t": "Bonjour ! Comment tu t'appelles ?", "py": "", "m": "你好！你叫什么名字？"},
   {"who": "Xiaoming", "t": "Bonjour, madame ! Je m'appelle Xiaoming.", "py": "", "m": "老师好！我叫小明。"},
   {"who": "Madame Martin", "t": "Tu as quel âge ?", "py": "", "m": "你几岁？"},
   {"who": "Xiaoming", "t": "J'ai onze ans.", "py": "", "m": "我十一岁。"},
   {"who": "Madame Martin", "t": "Tu habites où ?", "py": "", "m": "你住在哪里？"},
   {"who": "Xiaoming", "t": "J'habite à Shanghai, en Chine.", "py": "", "m": "我住在中国上海。"},
   {"who": "Madame Martin", "t": "Merci, Xiaoming. Au revoir !", "py": "", "m": "谢谢，小明。再见！"},
   {"who": "Xiaoming", "t": "Au revoir, madame !", "py": "", "m": "老师再见！"}]},
  "steps": [
   S(5, "warmup", "La balle aux questions", "Le professeur lance une question (« Tu as quel âge ? ») avec la balle ; l'élève répond et pose une autre question au suivant."),
   S(10, "practice", "Ateliers rapides", "1) Questions-réponses en paires (prénom, âge, ville). 2) Épeler son prénom. 3) Compter de 0 à 20 à l'envers."),
   S(15, "produce", "Mini-test : l'entretien", "Entretien individuel d'1 à 2 minutes, comme au DELF Prim A1 : saluer, prénom, âge, nationalité, ville, prendre congé. Pendant ce temps, les autres font les exercices en ligne de la leçon (les écoutes s'affichent quand les audios sont envoyés).",
     tip="Noter pour chaque élève : compréhension des questions, prononciation, structures (j'ai / je suis), politesse (vous)."),
   S(10, "produce", "Je me présente", "Chaque élève prépare et dit sa présentation en cinq phrases devant la classe ; les autres posent une question de plus."),
   S(5, "wrapup", "Auto-évaluation", "Chaque élève colorie les smileys de « À la fin de la leçon, je sais… ». Le professeur note un mot pour les parents dans l'appel et bilan."),
  ],
  "mistakes": ["Revoir les erreurs fréquentes de l'unité : « je suis neuf ans », il / elle, chinois / chinoise, « tu » au professeur."],
  "diff": {"young": "Mini-test sous forme de jeu de l'oie : chaque case est une question.", "teen": "Enregistrer une courte vidéo de présentation (30 secondes) à partager avec la classe."},
  "culture": {"title": "DELF Prim 是什么？", "text": "DELF Prim 是给小学生（大约7到12岁）的法语官方证书，有 A1.1、A1、A2 三个级别。口语考试的第一部分叫“entretien dirigé”：考官会问你的名字、年龄、住在哪里——就是这一单元学的内容！"},
  "exercises": [
   TF("听录音。这个孩子十岁。", False, audio="r1", explain="他说 J'ai douze ans：十二岁。"),
   TF("听录音。她住在法国。", True, audio="r2"),
   Q("老师问：« Tu habites où ? »，你回答：", ["J'habite à Pékin.", "J'ai dix ans.", "Je m'appelle Lili."]),
   Q("老师问：« Tu as quel âge ? »，你回答：", ["J'ai neuf ans.", "Je suis chinois.", "Ça va bien."]),
   Q("哪句是对的？", ["Je suis chinoise et j'ai dix ans.", "Je suis dix ans.", "J'ai chinoise."]),
   F("Elle ___ française.", ["est", "a", "es"]),
   F("Il ___ onze ans.", ["a", "est", "ai"]),
   M("把问题和意思连起来。", [["Comment tu t'appelles ?", "你叫什么名字？"], ["Tu as quel âge ?", "你几岁？"], ["Tu habites où ?", "你住在哪里？"], ["Ça va ?", "你好吗？"]]),
   TF("跟老师说话应该用 vous。", True),
   Q("« dix-neuf » =", ["19", "9", "90"]),
  ],
  "task": {"kind": "oral", "title": "Ma présentation", "instr": "录一段30秒左右的自我介绍（录音或视频）：打招呼、名字、年龄、国籍、城市、告别。上传。",
           "instr_guide": "Tâche bilan de l'unité : écrire un court retour à chaque élève (prononciation, aisance, structures) et indiquer aux parents les points à revoir avant l'unité 2."},
  "audio": [A("dialogue", "Dialogue : L'entretien", "Bonjour ! Comment tu t'appelles ?\nBonjour, madame ! Je m'appelle Xiaoming.\nTu as quel âge ?\nJ'ai onze ans.\nTu habites où ?\nJ'habite à Shanghai, en Chine.\nMerci, Xiaoming. Au revoir !\nAu revoir, madame !"),
            A("r1", "Test : l'âge", "Je m'appelle Hugo. J'ai douze ans."), A("r2", "Test : le pays", "Je m'appelle Léa. J'habite à Lyon, en France.")],
 }},
]

def run():
    for L in LESSONS:
        errs = validate(L["content"])
        assert not errs, (L["key"], errs)
    added = updated = 0
    with connect() as c:
        units = {(r["level"], r["sort"]): r["id"] for r in c.execute("SELECT id, level, sort FROM program_units").fetchall()}
        for L in LESSONS:
            uid = units.get((L["level"], L["unit"]))
            if not uid:
                continue
            row = c.execute("SELECT id, edited, status FROM lessons WHERE key=%s", (L["key"],)).fetchone()
            if not row:
                c.execute("""INSERT INTO lessons (key, unit_id, sort, title_fr, title_zh, content, status) VALUES (%s,%s,%s,%s,%s,%s,'review')""",
                          (L["key"], uid, L["sort"], L["title_fr"], L["title_zh"], Jsonb(L["content"])))
                added += 1
            elif not row["edited"] and row["status"] != "published":
                n = c.execute("""UPDATE lessons SET title_fr=%s, title_zh=%s, content=%s, updated_at=now() WHERE id=%s
                                 AND (content IS DISTINCT FROM %s OR title_fr IS DISTINCT FROM %s OR title_zh IS DISTINCT FROM %s)""",
                              (L["title_fr"], L["title_zh"], Jsonb(L["content"]), row["id"], Jsonb(L["content"]), L["title_fr"], L["title_zh"])).rowcount
                updated += n
    print(f"leçons : {added} ajoutée(s), {updated} mise(s) à jour")


if __name__ == "__main__":
    run()
