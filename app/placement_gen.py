"""Générateur de questions du test de niveau : 250 par niveau (100 vocabulaire, 100 grammaire, 25 textes × 2 questions).

Questions construites à partir de listes et de tables de conjugaison écrites à la main (pas de texte libre généré) :
chaque question a une seule bonne réponse (la 1re de la liste ; l'ordre est mélangé à l'affichage).
Marquées `generated = true` : à relire par un professeur (filtre « générées » dans /admin/tests/questions).
Relancer = mise à jour par clé (gen-<niveau>-<type>-<n>) ; python placement_gen.py
"""
import json
import random



R = random.Random(20261025)


def pick_wrong(pool, correct, n=3, rnd=R):
    """n réponses fausses distinctes, différentes de la bonne réponse (comparaison sans casse)."""
    c = correct.lower()
    cands = sorted({x for x in pool if x.lower() != c})
    return rnd.sample(cands, n)


def q(key, level, section, question, correct, wrong, passage=None):
    opts = [correct] + list(wrong)
    assert len({o.lower() for o in opts}) == 4, (key, opts)
    return {"key": key, "level": level, "section": section, "passage": passage, "question": question, "options": opts, "answer": 0}


SUBJ = ["je", "tu", "il", "elle", "nous", "vous", "ils", "elles"]
IDX = {"je": 0, "tu": 1, "il": 2, "elle": 2, "nous": 3, "vous": 4, "ils": 5, "elles": 5}
VOWEL = tuple("aeéèêiouyh")


def subj_text(s, verb_form):
    if s == "je" and verb_form[0].lower() in VOWEL:
        return "J'"
    return s.capitalize() + " "


def blank_sentence(s, rest, first):
    """« Je ___ … » ou « J'___ … » (élision devant voyelle)."""
    st = subj_text(s, first)
    return f"{st}___ {rest}" if not st.endswith("'") else f"{st}___ {rest}"


# ======================================================================= A1
A1_CATS = {
    "un animal": ["chat", "chien", "lapin", "cheval", "oiseau", "poisson", "vache", "mouton", "souris", "lion"],
    "une couleur": ["rouge", "bleu", "vert", "jaune", "noir", "blanc", "rose", "gris", "violet"],
    "un fruit": ["pomme", "banane", "fraise", "poire", "cerise", "raisin", "melon", "pêche"],
    "un vêtement": ["pantalon", "robe", "chemise", "jupe", "pull", "manteau", "chapeau", "chaussette"],
    "un objet de l'école": ["stylo", "crayon", "cahier", "gomme", "règle", "trousse", "cartable"],
    "une partie du corps": ["tête", "main", "pied", "bras", "jambe", "nez", "bouche", "oreille"],
    "un membre de la famille": ["mère", "père", "frère", "sœur", "oncle", "tante", "cousin", "grand-mère"],
    "un jour de la semaine": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "une boisson": ["eau", "lait", "thé", "café", "jus de pomme", "limonade"],
}
NUM = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize",
       "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf", "vingt"]
DAYS = A1_CATS["un jour de la semaine"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
USES = [("On écrit avec un ___.", "stylo"), ("On lit un ___.", "livre"), ("On dort dans un ___.", "lit"), ("On s'assoit sur une ___.", "chaise"),
        ("On boit dans un ___.", "verre"), ("On mange avec une ___.", "fourchette"), ("On regarde l'heure sur une ___.", "montre"),
        ("On ouvre la porte avec une ___.", "clé"), ("On se lave les mains avec du ___.", "savon"), ("On coupe le pain avec un ___.", "couteau")]
USE_POOL = [u for _, u in USES] + ["chaussure", "fenêtre", "ballon", "nuage"]


def a1_vocab():
    out, n = [], 0
    stems = ["Quel mot est {c} ?", "Lequel de ces mots est {c} ?", "Trouve {c} :"]
    cats = list(A1_CATS)
    for ci, cat in enumerate(cats):
        words = A1_CATS[cat]
        for k in range(6):
            correct = words[k % len(words)]
            others = R.sample([c for c in cats if c != cat], 3)
            wrong = [R.choice(A1_CATS[o]) for o in others]
            n += 1
            out.append(q(f"gen-a1-v-{n}", "A1", "vocab", stems[k % 3].format(c=cat), correct, wrong))
    for a, b in [(1, 2), (2, 3), (3, 4), (2, 5), (4, 4), (5, 3), (6, 2), (1, 6), (3, 5), (7, 2), (4, 5), (6, 4), (5, 5), (8, 3), (7, 4), (6, 6), (9, 2), (8, 5), (7, 7), (9, 6)]:
        s = a + b
        wrong = [NUM[x] for x in (s - 1, s + 1, s + 2 if s + 2 <= 20 else s - 2)]
        n += 1
        out.append(q(f"gen-a1-v-{n}", "A1", "vocab", f"Combien font {NUM[a]} et {NUM[b]} ?", NUM[s], wrong))
    for i, d in enumerate(DAYS):
        n += 1
        out.append(q(f"gen-a1-v-{n}", "A1", "vocab", f"Après {d}, c'est ___.", DAYS[(i + 1) % 7], pick_wrong(DAYS, DAYS[(i + 1) % 7])))
        n += 1
        out.append(q(f"gen-a1-v-{n}", "A1", "vocab", f"Avant {d}, c'est ___.", DAYS[(i - 1) % 7], pick_wrong(DAYS, DAYS[(i - 1) % 7])))
    for i, m in enumerate(MONTHS):
        n += 1
        out.append(q(f"gen-a1-v-{n}", "A1", "vocab", f"Après {m}, c'est ___.", MONTHS[(i + 1) % 12], pick_wrong(MONTHS, MONTHS[(i + 1) % 12])))
    for stem, ans in USES:
        n += 1
        out.append(q(f"gen-a1-v-{n}", "A1", "vocab", stem, ans, pick_wrong(USE_POOL, ans)))
    return out


ETRE = ["suis", "es", "est", "sommes", "êtes", "sont"]
AVOIR = ["ai", "as", "a", "avons", "avez", "ont"]
ER = [("parler", "français."), ("jouer", "au football."), ("aimer", "le chocolat."), ("habiter", "à Lyon."), ("regarder", "la télévision."),
      ("chanter", "une chanson."), ("danser", "à la fête."), ("écouter", "de la musique."), ("travailler", "beaucoup.")]
ER_END = ["e", "es", "e", "ons", "ez", "ent"]
NOUNS_M = ["chat", "chien", "livre", "vélo", "crayon", "stylo", "gâteau", "sac", "ballon"]
NOUNS_F = ["maison", "voiture", "table", "pomme", "fleur", "chaise", "robe", "porte"]


def conj_items(prefix, level, forms, frames, subjects, start):
    out, n = [], start
    for rest in frames:
        for s in subjects:
            correct = forms[IDX[s]]
            n += 1
            out.append(q(f"{prefix}-{n}", level, "grammar", blank_sentence(s, rest, correct), correct, pick_wrong(forms, correct)))
    return out, n


def a1_grammar():
    out, n = [], 0
    items, n = conj_items("gen-a1-g", "A1", ETRE, ["à la maison.", "à l'école."], SUBJ, n); out += items
    items, n = conj_items("gen-a1-g", "A1", AVOIR, ["un chien.", "faim."], SUBJ, n); out += items
    for vi, (verb, rest) in enumerate(ER):
        stem = verb[:-2]
        forms = [stem + e for e in ER_END]
        for s in [SUBJ[(vi * 3 + k) % 8] for k in range(5)]:
            correct = forms[IDX[s]]
            n += 1
            out.append(q(f"gen-a1-g-{n}", "A1", "grammar", blank_sentence(s, rest, correct), correct, pick_wrong(forms, correct)))
    for nm in NOUNS_M:
        n += 1
        out.append(q(f"gen-a1-g-{n}", "A1", "grammar", f"C'est ___ {nm}.", "un", ["une", "des", "les"]))
    for nf in NOUNS_F:
        n += 1
        out.append(q(f"gen-a1-g-{n}", "A1", "grammar", f"C'est ___ {nf}.", "une", ["un", "des", "les"]))
    for nm in NOUNS_M[:5]:
        n += 1
        out.append(q(f"gen-a1-g-{n}", "A1", "grammar", f"C'est ___ {nm} (à moi).", "mon", ["ma", "mes", "me"]))
    for nf in ["maison", "voiture", "robe", "chaise", "table"]:
        n += 1
        out.append(q(f"gen-a1-g-{n}", "A1", "grammar", f"C'est ___ {nf} (à moi).", "ma", ["mon", "mes", "me"]))
    return out


NAMES = ["Léa", "Hugo", "Emma", "Tom", "Lina", "Sami", "Chloé", "Nathan", "Inès", "Lucas", "Jade", "Adam", "Zoé", "Louis", "Rose",
         "Paul", "Alice", "Noah", "Lou", "Jules", "Mia", "Gabriel", "Camille", "Arthur", "Manon"]
CITIES = ["Paris", "Lyon", "Marseille", "Nice", "Lille", "Bordeaux", "Nantes", "Toulouse", "Pékin", "Shanghai", "Canton"]
ACTS = ["le football", "la danse", "la natation", "le dessin", "la musique", "le vélo", "la lecture", "le judo"]
FOODS = ["le chocolat", "les pommes", "les pâtes", "le riz", "les fraises", "le fromage", "les bananes"]
PETS = ["chat", "chien", "lapin", "poisson", "hamster"]
PETN = ["Minou", "Rex", "Pompon", "Bulle", "Caramel", "Filou", "Choupi", "Noisette"]


def a1_reading():
    out = []
    for i, name in enumerate(NAMES):
        age, city, act, food, pet, pn = 6 + i % 7, CITIES[i % len(CITIES)], ACTS[i % len(ACTS)], FOODS[(i * 3) % len(FOODS)], PETS[i % len(PETS)], PETN[(i * 5) % len(PETN)]
        text = f"Je m'appelle {name}. J'ai {NUM[age]} ans. J'habite à {city}. J'aime {act} et {food}. J'ai un {pet} : il s'appelle {pn}."
        qs = [
            (f"Quel âge a {name} ?", f"{NUM[age].capitalize()} ans", [f"{NUM[x].capitalize()} ans" for x in R.sample([y for y in range(5, 14) if y != age], 3)]),
            (f"Où habite {name} ?", f"À {city}", [f"À {c}" for c in pick_wrong(CITIES, city)]),
            (f"Quel sport ou quelle activité aime {name} ?", act.capitalize(), [a.capitalize() for a in pick_wrong(ACTS, act)]),
            (f"Quel animal a {name} ?", f"Un {pet}", [f"Un {p}" for p in pick_wrong(PETS, pet)]),
            (f"Comment s'appelle l'animal de {name} ?", pn, pick_wrong(PETN, pn)),
        ]
        for k, (qq, c, w) in enumerate([qs[i % 5], qs[(i + 2) % 5]]):
            out.append(q(f"gen-a1-r-{i + 1}-{k + 1}", "A1", "reading", qq, c, w, passage=text))
    return out


# ======================================================================= A2
PLACES = [("On achète du pain ___.", "à la boulangerie"), ("On achète des médicaments ___.", "à la pharmacie"),
          ("On envoie une lettre ___.", "à la poste"), ("On emprunte des livres ___.", "à la bibliothèque"),
          ("On prend le train ___.", "à la gare"), ("On prend l'avion ___.", "à l'aéroport"), ("On nage ___.", "à la piscine"),
          ("On regarde un film ___.", "au cinéma"), ("On achète de la viande ___.", "à la boucherie"), ("On retire de l'argent ___.", "à la banque"),
          ("On achète des livres ___.", "à la librairie"), ("On soigne les malades ___.", "à l'hôpital"), ("On voit des tableaux ___.", "au musée"),
          ("On fait du sport ___.", "au gymnase"), ("On attend le bus ___.", "à l'arrêt de bus")]
PLACE_POOL = [p for _, p in PLACES]
PLACE_ACTS = ["acheter du pain", "acheter des médicaments", "envoyer une lettre", "emprunter des livres", "prendre le train", "prendre l'avion", "nager",
              "regarder un film", "acheter de la viande", "retirer de l'argent", "acheter des livres", "me faire soigner", "voir des tableaux",
              "faire du sport", "attendre le bus"]
JOBS = [("Il soigne les malades : il est ___.", "médecin"), ("Elle fait le pain : elle est ___.", "boulangère"),
        ("Il éteint les incendies : il est ___.", "pompier"), ("Elle apporte le courrier : elle est ___.", "factrice"),
        ("Il prépare les repas au restaurant : il est ___.", "cuisinier"), ("Elle coupe les cheveux : elle est ___.", "coiffeuse"),
        ("Il pilote les avions : il est ___.", "pilote"), ("Elle soigne les dents : elle est ___.", "dentiste"),
        ("Il cultive la terre : il est ___.", "agriculteur"), ("Elle enseigne aux élèves : elle est ___.", "professeure"),
        ("Il vend des fruits au marché : il est ___.", "marchand"), ("Elle répare les voitures : elle est ___.", "mécanicienne")]
JOB_POOL = ["médecin", "boulangère", "pompier", "factrice", "cuisinier", "coiffeuse", "pilote", "dentiste", "agriculteur", "professeure", "marchand", "mécanicienne", "chanteur", "journaliste"]
OPP = [("grand", "petit"), ("chaud", "froid"), ("facile", "difficile"), ("jeune", "vieux"), ("rapide", "lent"), ("ouvert", "fermé"),
       ("propre", "sale"), ("plein", "vide"), ("long", "court"), ("heureux", "triste"), ("lourd", "léger"), ("tôt", "tard"),
       ("cher", "bon marché"), ("fort", "faible"), ("riche", "pauvre")]
OPP_POOL = sorted({w for p in OPP for w in p})
TIMEQ = [("Une heure, c'est ___ minutes.", "soixante", ["trente", "cent", "quarante"]), ("Une semaine, c'est ___ jours.", "sept", ["cinq", "dix", "six"]),
         ("Un an, c'est ___ mois.", "douze", ["dix", "onze", "quatorze"]), ("Un jour, c'est ___ heures.", "vingt-quatre", ["douze", "vingt", "trente"]),
         ("Une demi-heure, c'est ___ minutes.", "trente", ["quinze", "soixante", "quarante-cinq"]), ("Un quart d'heure, c'est ___ minutes.", "quinze", ["dix", "trente", "vingt"]),
         ("Un siècle, c'est ___ ans.", "cent", ["dix", "mille", "cinquante"]), ("Le mois qui vient après juin, c'est ___.", "juillet", ["mai", "août", "septembre"])]
TRANS = [("Pour traverser la mer, on peut prendre le ___.", "bateau", ["vélo", "métro", "tramway"]), ("On voyage dans le ciel en ___.", "avion", ["train", "bus", "bateau"]),
         ("Sous la ville, on peut prendre le ___.", "métro", ["avion", "bateau", "hélicoptère"]), ("On pédale pour avancer à ___.", "vélo", ["voiture", "moto", "train"])]
WEATHER = [("Il fait froid : je mets mon ___.", "manteau", ["maillot de bain", "short", "tee-shirt"]), ("Il pleut : je prends mon ___.", "parapluie", ["maillot de bain", "ballon", "short"]),
           ("Il fait très chaud : je mets un ___.", "short", ["manteau", "bonnet", "pull"]), ("Il neige : je mets des ___.", "gants", ["sandales", "lunettes de soleil", "shorts"]),
           ("Il y a du soleil : je mets mes ___.", "lunettes de soleil", ["gants", "bottes de pluie", "écharpe"])]


def a2_vocab():
    out, n = [], 0
    for (stem, ans), act in zip(PLACES, PLACE_ACTS):
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", stem, ans, pick_wrong(PLACE_POOL, ans)))
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", f"Pour {act}, je vais ___.", ans, pick_wrong(PLACE_POOL, ans)))
    masc = ["médecin", "pompier", "cuisinier", "pilote", "agriculteur", "marchand", "chanteur", "journaliste", "dentiste", "boulanger"]
    fem = ["boulangère", "factrice", "coiffeuse", "dentiste", "professeure", "mécanicienne", "journaliste", "vendeuse", "infirmière", "chanteuse"]
    health = {"médecin", "dentiste", "infirmière"}
    for stem, ans in JOBS:
        is_f = stem.startswith("Elle")
        pool = [w for w in (fem if is_f else masc) if not (ans in health and w in health)]
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", stem, ans, pick_wrong(pool, ans)))
        action = stem.split(" ", 1)[1].split(" :")[0]
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", f"{'Une' if is_f else 'Un'} ___ {action}.", ans, pick_wrong(pool, ans)))
    for a, b in OPP:
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", f"Le contraire de « {a} », c'est « ___ ».", b, pick_wrong([w for w in OPP_POOL if w != a], b)))
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", f"Le contraire de « {b} », c'est « ___ ».", a, pick_wrong([w for w in OPP_POOL if w != b], a)))
    for stem, ans, wrong in TIMEQ + TRANS + WEATHER:
        n += 1
        out.append(q(f"gen-a2-v-{n}", "A2", "vocab", stem, ans, wrong))
    return out


PC_AVOIR = [  # (objet, participe, infinitif, présent « je », imparfait « je »)
    ("une pomme", "mangé", "manger", "mange", "mangeais"), ("mes devoirs", "fini", "finir", "finis", "finissais"),
    ("le bus", "pris", "prendre", "prends", "prenais"), ("un gâteau", "fait", "faire", "fais", "faisais"),
    ("un film", "vu", "voir", "vois", "voyais"), ("un jus d'orange", "bu", "boire", "bois", "buvais"),
    ("un livre", "lu", "lire", "lis", "lisais"), ("une lettre", "écrit", "écrire", "écris", "écrivais"),
    ("la télévision", "regardé", "regarder", "regarde", "regardais"), ("du pain", "acheté", "acheter", "achète", "achetais")]
PC_ETRE = [("aller", "allé"), ("partir", "parti"), ("arriver", "arrivé"), ("rester", "resté"), ("rentrer", "rentré"), ("sortir", "sorti"), ("venir", "venu"), ("tomber", "tombé")]
ALLER = ["vais", "vas", "va", "allons", "allez", "vont"]
COUNTRIES_F = ["France", "Chine", "Italie", "Espagne", "Allemagne", "Belgique", "Suisse"]
COUNTRIES_M = ["Japon", "Canada", "Portugal", "Brésil", "Mexique", "Maroc"]
CITIES2 = ["Paris", "Pékin", "Londres", "Rome", "Madrid"]


def a2_grammar():
    out, n = [], 0
    for obj, pp, inf, pres, imp in PC_AVOIR:
        for sent in (f"Hier, j'ai ___ {obj}.", f"Hier, nous avons ___ {obj.replace('mes ', 'nos ')}."):
            n += 1
            out.append(q(f"gen-a2-g-{n}", "A2", "grammar", sent, pp, [inf, pres, imp]))
    for verb, pp in PC_ETRE:
        for subj, aux, agr, wrong in (("Elle", "est", "e", ["a", "ont", "avons"]), ("Ils", "sont", "s", ["ont", "a", "avez"])):
            end = "à la maison" if verb == "rester" else "à huit heures"
            n += 1
            out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"Hier, {subj.lower()} ___ {pp}{agr} {end}.".capitalize().replace("Hier, elle", "Hier, elle"), aux, wrong))
    for s in SUBJ:
        correct = ALLER[IDX[s]]
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"Demain, {s} ___ visiter le musée.", correct, pick_wrong(ALLER, correct)))
    for noun, pron in (("Marie", "la"), ("Paul", "le"), ("tes amis", "les"), ("la voiture", "la"), ("le film", "le"), ("les photos", "les")):
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"Tu vois {noun} ? — Oui, je ___ vois.", pron, pick_wrong(["le", "la", "les", "lui", "leur"], pron)))
    for qq in (("Tu vas à Paris ? — Oui, j'___ vais.", "y", ["en", "le", "la"]), ("Tu veux du pain ? — Oui, j'___ veux.", "en", ["y", "le", "la"]),
               ("Tu habites à Lyon ? — Oui, j'___ habite.", "y", ["en", "le", "lui"]), ("Tu as des frères ? — Oui, j'___ ai deux.", "en", ["y", "les", "leur"]),
               ("Vous allez au cinéma ? — Oui, nous ___ allons.", "y", ["en", "le", "lui"]), ("Il boit du café ? — Oui, il ___ boit.", "en", ["y", "le", "lui"])):
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", qq[0], qq[1], qq[2]))
    for sent, ans in (("Le garçon ___ parle est mon frère.", "qui"), ("Le livre ___ je lis est intéressant.", "que"), ("La fille ___ chante s'appelle Léa.", "qui"),
                      ("Le film ___ nous regardons est drôle.", "que"), ("C'est l'ami ___ habite à Paris.", "qui"), ("C'est la robe ___ j'ai achetée.", "que"),
                      ("Le chat ___ dort est à moi.", "qui"), ("Les gâteaux ___ tu fais sont bons.", "que")):
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", sent, ans, [x for x in ("qui", "que", "dont", "où") if x != ans]))
    for c in COUNTRIES_F:
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"J'habite ___ {c}.", "en", ["au", "aux", "à"]))
    for c in COUNTRIES_M:
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"J'habite ___ {c}.", "au", ["en", "aux", "à"]))
    n += 1
    out.append(q(f"gen-a2-g-{n}", "A2", "grammar", "J'habite ___ États-Unis.", "aux", ["en", "au", "à"]))
    for c in CITIES2:
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"J'habite ___ {c}.", "à", ["en", "au", "aux"]))
    for a, b, adj in (("Paul", "Marc", "grand"), ("le train", "le bus", "rapide"), ("ma sœur", "moi", "jeune"), ("cette robe", "l'autre", "chère"),
                      ("Pékin", "Lyon", "grand"), ("le chocolat", "le café", "sucré")):
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"{a[0].upper() + a[1:]} est ___ {adj} que {b}.", "plus", ["très", "beaucoup", "trop"]))
    for inf, tu, vous, rest in (("fermer", "Ferme", "Fermez", "la porte, s'il te plaît !"), ("ouvrir", "Ouvre", "Ouvrez", "la fenêtre, s'il te plaît !"),
                                ("écouter", "Écoute", "Écoutez", "bien la question !"), ("regarder", "Regarde", "Regardez", "le tableau !"),
                                ("venir", "Viens", "Venez", "ici, s'il te plaît !"), ("prendre", "Prends", "Prenez", "ton cahier !"), ("faire", "Fais", "Faites", "attention !")):
        n += 1
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"(À un ami) ___ {rest} [{inf}]", tu, [vous, inf.capitalize(), {"Ferme": "Fermes", "Ouvre": "Ouvres", "Écoute": "Écoutes", "Regarde": "Regardes", "Viens": "Vient", "Prends": "Prend", "Fais": "Fait"}[tu]]))
        n += 1
        wrong_v = {"Fermez": "Fermons", "Ouvrez": "Ouvrons", "Écoutez": "Écoutons", "Regardez": "Regardons", "Venez": "Venons", "Prenez": "Prenons", "Faites": "Faisons"}[vous]
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"(À la classe) ___ {rest.replace('te plaît', 'vous plaît').replace('ton cahier', 'votre cahier')} [{inf}]", vous, [tu, inf.capitalize(), wrong_v]))
    for subj, pron in (("Je", "me"), ("Tu", "te"), ("Il", "se"), ("Nous", "nous"), ("Vous", "vous"), ("Ils", "se")):
        n += 1
        verb = {"Je": "lève", "Tu": "lèves", "Il": "lève", "Nous": "levons", "Vous": "levez", "Ils": "lèvent"}[subj]
        out.append(q(f"gen-a2-g-{n}", "A2", "grammar", f"{subj} ___ {verb} à sept heures.", pron, pick_wrong(["me", "te", "se", "nous", "vous"], pron)))
    return out


A2_TEXTS = [
    ("postcard", "Chloé", "Lina", "à la mer", "visité un vieux château", "lundi"), ("postcard", "Hugo", "Sami", "à la montagne", "fait une grande promenade", "samedi"),
    ("postcard", "Emma", "Jade", "à la campagne", "cueilli des fraises", "dimanche"), ("postcard", "Tom", "Paul", "à Paris", "vu la tour Eiffel", "mardi"),
    ("postcard", "Inès", "Rose", "en Bretagne", "mangé des crêpes", "vendredi"), ("postcard", "Lucas", "Noah", "à Nice", "fait du bateau", "jeudi"),
    ("postcard", "Manon", "Zoé", "à Lyon", "visité un musée", "mercredi"), ("postcard", "Arthur", "Louis", "au Canada", "vu des ours", "lundi"),
]
CLUBS = [("théâtre", "le jeudi", "17 h", "18 h 30", "gratuite", "salle 12"), ("musique", "le mardi", "16 h", "17 h", "de 10 euros", "salle 5"),
         ("échecs", "le mercredi", "14 h", "16 h", "gratuite", "la bibliothèque"), ("danse", "le vendredi", "17 h 30", "19 h", "de 15 euros", "le gymnase"),
         ("cuisine", "le samedi", "10 h", "12 h", "de 20 euros", "la cantine"), ("dessin", "le lundi", "16 h 30", "18 h", "gratuite", "salle 3"),
         ("photo", "le jeudi", "15 h", "16 h 30", "de 5 euros", "salle 8"), ("robotique", "le mercredi", "10 h", "11 h 30", "de 12 euros", "salle 20")]
MEETS = [("Léo", "devant le cinéma", "18 h", "ton billet"), ("Mia", "à la gare", "9 h", "ton sac à dos"), ("Nathan", "devant l'école", "8 h", "ton vélo"),
         ("Alice", "au parc", "14 h", "un ballon"), ("Gabriel", "à la piscine", "16 h", "ton maillot de bain"), ("Lou", "devant la bibliothèque", "10 h", "ta carte"),
         ("Jules", "au café", "17 h", "tes photos"), ("Camille", "à l'arrêt de bus", "7 h 30", "ton parapluie"), ("Adam", "devant le musée", "11 h", "ton appareil photo")]
DAYS_ANS = ["le lundi", "le mardi", "le mercredi", "le jeudi", "le vendredi", "le samedi", "le dimanche"]
PLACES_MEET = [m[1] for m in MEETS]
HOURS = [m[2] for m in MEETS] + ["12 h", "19 h"]
OBJS = [m[3] for m in MEETS]


def a2_reading():
    out, i = [], 0
    for _, who, to, where, did, back in A2_TEXTS:
        i += 1
        text = f"Bonjour {to}, je suis en vacances {where} avec ma famille. Il fait beau. Hier, nous avons {did}. Je rentre {back} prochain. Bises, {who}"
        wheres = [t[3] for t in A2_TEXTS]
        dids = [t[4] for t in A2_TEXTS]
        out.append(q(f"gen-a2-r-{i}-1", "A2", "reading", f"Où est {who} ?", where[0].upper() + where[1:], [w[0].upper() + w[1:] for w in pick_wrong(wheres, where)], passage=text))
        out.append(q(f"gen-a2-r-{i}-2", "A2", "reading", f"Qu'est-ce {'qu' + chr(39) if who[0] in 'AEÉIOUH' else 'que '}{who} et sa famille ont fait hier ?", f"Ils ont {did}", [f"Ils ont {d}" for d in pick_wrong(dids, did)], passage=text))
    for club, day, h1, h2, price, room in CLUBS:
        i += 1
        text = f"Le club {'d' + chr(39) if club[0] in 'aeéiou' else 'de '}{club} du collège cherche de nouveaux élèves. Les séances ont lieu {day} de {h1} à {h2}. L'inscription est {price}. Rendez-vous {room if room.startswith('salle') is False else 'en ' + room} pour en savoir plus."
        text = text.replace("Rendez-vous la", "Rendez-vous à la").replace("Rendez-vous le gymnase", "Rendez-vous au gymnase")
        out.append(q(f"gen-a2-r-{i}-1", "A2", "reading", "Quand ont lieu les séances ?", day[0].upper() + day[1:], [d[0].upper() + d[1:] for d in pick_wrong(DAYS_ANS, day)], passage=text))
        prices = sorted({c[4] for c in CLUBS})
        lab = lambda p: "Elle est gratuite" if p == "gratuite" else f"Elle coûte {p[3:]}"
        out.append(q(f"gen-a2-r-{i}-2", "A2", "reading", "Combien coûte l'inscription ?", lab(price), [lab(p) for p in pick_wrong(prices, price)], passage=text))
    for who, where, hour, obj in MEETS:
        i += 1
        text = f"Salut ! C'est {who}. Samedi, on se retrouve {where} à {hour}. N'oublie pas d'apporter {obj}. À samedi !"
        out.append(q(f"gen-a2-r-{i}-1", "A2", "reading", "Où est le rendez-vous ?", where[0].upper() + where[1:], [w[0].upper() + w[1:] for w in pick_wrong(PLACES_MEET, where)], passage=text))
        out.append(q(f"gen-a2-r-{i}-2", "A2", "reading", "Qu'est-ce qu'il faut apporter ?", obj[0].upper() + obj[1:], [o[0].upper() + o[1:] for o in pick_wrong(OBJS, obj)], passage=text))
    return out


# ======================================================================= B1
COLLOC = [("J'ai ___ une décision importante.", "pris", ["fait", "mis", "donné"]), ("Le samedi, je ___ les courses au marché.", "fais", ["prends", "mets", "donne"]),
          ("Est-ce que je peux ___ une question ?", "poser", ["faire", "mettre", "donner"]), ("Demain, je vais ___ visite à ma grand-mère.", "rendre", ["faire", "donner", "prendre"]),
          ("Il faut ___ attention en traversant la rue.", "faire", ["prendre", "mettre", "donner"]), ("J'ai ___ rendez-vous chez le dentiste.", "pris", ["fait", "mis", "posé"]),
          ("Avant le dîner, peux-tu ___ la table ?", "mettre", ["faire", "poser", "prendre"]), ("Après le repas, je ___ la vaisselle.", "fais", ["mets", "prends", "donne"]),
          ("Il a ___ sa promesse.", "tenu", ["fait", "pris", "mis"]), ("Pendant le cours, je ___ des notes.", "prends", ["fais", "mets", "donne"]),
          ("Mon professeur m'a ___ un bon conseil.", "donné", ["fait", "mis", "pris"]), ("Elle a ___ sa candidature pour ce poste.", "posé", ["fait", "donné", "pris"]),
          ("Dans le magasin, il faut ___ la queue.", "faire", ["prendre", "mettre", "donner"]), ("J'ai ___ beaucoup de temps dans les embouteillages.", "perdu", ["fait", "tenu", "posé"]),
          ("Il a ___ l'examen du permis de conduire.", "passé", ["fait", "pris", "mis"]), ("Ce travail me permet de ___ de l'argent.", "gagner", ["tenir", "poser", "rendre"]),
          ("Nous avons ___ la connaissance de nos voisins.", "fait", ["pris", "mis", "donné"]), ("Il faut ___ la vérité.", "dire", ["parler", "répondre", "faire"]),
          ("Ils ont ___ du bruit toute la nuit.", "fait", ["mis", "pris", "donné"])]
SYN = [("commencer", "débuter"), ("terminer", "finir"), ("content", "heureux"), ("habiter", "vivre"), ("maintenant", "en ce moment"),
       ("souvent", "fréquemment"), ("utiliser", "se servir de"), ("aider", "donner un coup de main"), ("se dépêcher", "se presser"),
       ("bâtir", "construire"), ("un logement", "un lieu où l'on habite"), ("rapidement", "vite")]
SYN_POOL = ["débuter", "finir", "heureux", "vivre", "en ce moment", "fréquemment", "se servir de", "donner un coup de main", "se presser", "construire",
            "un lieu où l'on habite", "vite", "oublier", "dormir", "triste", "rarement", "lentement"]
DEFS = [("Personne qui écrit des livres :", "un écrivain"), ("Personne qui traduit d'une langue à une autre :", "un traducteur"), ("Personne qui dessine les plans des maisons :", "un architecte"),
        ("Personne qui soigne les animaux :", "un vétérinaire"), ("Personne qui répare les tuyaux et les robinets :", "un plombier"), ("Personne qui installe l'électricité :", "un électricien"),
        ("Personne qui fait des recherches scientifiques :", "un chercheur"), ("Personne qui fait visiter une ville :", "un guide"), ("Personne qui répare les voitures :", "un mécanicien"),
        ("Personne qui travaille dans un hôpital et aide le médecin :", "un infirmier"), ("Personne qui écrit des articles dans un journal :", "un journaliste"), ("Personne qui juge au tribunal :", "un juge"),
        ("Personne qui vend des livres :", "un libraire"), ("Personne qui fait les comptes d'une entreprise :", "un comptable"), ("Personne qui conduit un taxi :", "un chauffeur")]
DEF_POOL = [d for _, d in DEFS] + ["un boulanger", "un facteur"]
FAMILY = [("décider", "la décision"), ("choisir", "le choix"), ("partir", "le départ"), ("arriver", "l'arrivée"), ("construire", "la construction"), ("développer", "le développement"),
          ("vendre", "la vente"), ("payer", "le paiement"), ("envoyer", "l'envoi"), ("connaître", "la connaissance"), ("réussir", "la réussite"), ("expliquer", "l'explication"),
          ("proposer", "la proposition"), ("sortir", "la sortie"), ("voyager", "le voyage"), ("répondre", "la réponse"), ("inviter", "l'invitation"), ("protéger", "la protection")]
FAM_POOL = [f for _, f in FAMILY]
CONNECT = [("Il pleut, ___ je reste à la maison.", "donc", ["mais", "pourtant", "car"]), ("Je suis fatigué ___ j'ai mal dormi.", "parce que", ["donc", "pourtant", "alors"]),
           ("Il est riche, ___ il n'est pas heureux.", "mais", ["donc", "car", "alors"]), ("J'ai beaucoup travaillé ; ___, j'ai réussi l'examen.", "par conséquent", ["pourtant", "cependant", "en revanche"]),
           ("Elle n'a pas étudié ; ___, elle a eu une bonne note.", "pourtant", ["donc", "alors", "par conséquent"]), ("Je prends un parapluie ___ il va pleuvoir.", "car", ["donc", "mais", "pourtant"]),
           ("D'abord je me lève, ___ je prends mon petit-déjeuner.", "ensuite", ["pourtant", "car", "mais"]), ("J'aime le thé ; mon frère, ___, préfère le café.", "en revanche", ["donc", "car", "ainsi"]),
           ("Il est malade, c'est ___ il ne vient pas à l'école.", "pourquoi", ["pourtant", "car", "mais"]), ("Il sort sans manteau ___ le froid.", "malgré", ["grâce à", "à cause du", "pour"]),
           ("Je n'ai pas pu venir à cause ___ la grève des transports.", "de", ["à", "par", "pour"]), ("___ ton aide, j'ai fini à temps.", "Grâce à", ["Malgré", "À cause de", "Sans"])]


def b1_vocab():
    out, n = [], 0
    for stem, ans, wrong in COLLOC:
        n += 1
        out.append(q(f"gen-b1-v-{n}", "B1", "vocab", stem, ans, wrong))
    for a, b in SYN:
        for k in range(2):
            n += 1
            out.append(q(f"gen-b1-v-{n}", "B1", "vocab", f"« {a} » veut dire à peu près :" if k == 0 else f"Quel est le synonyme {'d' + chr(39) if a[0] in 'aeéiouh' else 'de '}« {a} » ?", b, pick_wrong(SYN_POOL, b)))
    for stem, ans in DEFS:
        for k in range(2):
            n += 1
            out.append(q(f"gen-b1-v-{n}", "B1", "vocab", stem if k == 0 else stem.replace("Personne qui", "Comment appelle-t-on la personne qui").rstrip(" :") + " ?", ans, pick_wrong(DEF_POOL, ans)))
    for verb, noun in FAMILY:
        n += 1
        out.append(q(f"gen-b1-v-{n}", "B1", "vocab", f"Le nom qui correspond au verbe « {verb} », c'est :", noun, pick_wrong(FAM_POOL, noun)))
    for stem, ans, wrong in CONNECT:
        n += 1
        out.append(q(f"gen-b1-v-{n}", "B1", "vocab", stem, ans, wrong))
    return out


COND = {"faire": ["ferais", "ferais", "ferait", "ferions", "feriez", "feraient"], "aller": ["irais", "irais", "irait", "irions", "iriez", "iraient"],
        "acheter": ["achèterais", "achèterais", "achèterait", "achèterions", "achèteriez", "achèteraient"], "être": ["serais", "serais", "serait", "serions", "seriez", "seraient"],
        "avoir": ["aurais", "aurais", "aurait", "aurions", "auriez", "auraient"], "pouvoir": ["pourrais", "pourrais", "pourrait", "pourrions", "pourriez", "pourraient"]}
COND_OTHER = {"faire": ["fais", "ferai", "faisais"], "aller": ["vais", "irai", "allais"], "acheter": ["achète", "achèterai", "achetais"], "être": ["suis", "serai", "étais"],
              "avoir": ["ai", "aurai", "avais"], "pouvoir": ["peux", "pourrai", "pouvais"]}
COND_FRAMES = {"faire": "un grand voyage", "aller": "au Japon", "acheter": "une maison", "être": "très heureux", "avoir": "un chien", "pouvoir": "t'aider"}
SUBJ_PRES = {"être": ["sois", "sois", "soit", "soyons", "soyez", "soient"], "avoir": ["aie", "aies", "ait", "ayons", "ayez", "aient"],
             "faire": ["fasse", "fasses", "fasse", "fassions", "fassiez", "fassent"], "aller": ["aille", "ailles", "aille", "allions", "alliez", "aillent"],
             "venir": ["vienne", "viennes", "vienne", "venions", "veniez", "viennent"], "prendre": ["prenne", "prennes", "prenne", "prenions", "preniez", "prennent"],
             "finir": ["finisse", "finisses", "finisse", "finissions", "finissiez", "finissent"], "partir": ["parte", "partes", "parte", "partions", "partiez", "partent"]}
SUBJ_WRONG = {"être": ["es", "seras", "étais"], "avoir": ["as", "auras", "avais"], "faire": ["fais", "feras", "faisais"], "aller": ["vas", "iras", "allais"],
              "venir": ["viens", "viendras", "venais"], "prendre": ["prends", "prendras", "prenais"], "finir": ["finis", "finiras", "finissais"], "partir": ["pars", "partiras", "partais"]}
SUBJ_FRAMES = {"être": "à l'heure", "avoir": "les billets", "faire": "les courses", "aller": "chez le médecin", "venir": "à la réunion", "prendre": "le train de 8 h",
               "finir": "ce travail avant ce soir", "partir": "tôt demain"}
GER = [("écouter de la musique", "travaillant", "travailler"), ("parler", "mangeant", "manger"), ("chanter", "marchant", "marcher"), ("apprendre", "jouant", "jouer"),
       ("se blesser", "tombant", "tomber"), ("sourire", "disant", "dire"), ("trouver la solution", "réfléchissant", "réfléchir"), ("progresser", "lisant", "lire"),
       ("économiser", "prenant", "prendre"), ("rencontrer des gens", "voyageant", "voyager")]
REL = [("La ville ___ je suis né est petite.", "où", ["dont", "que", "qui"]), ("Le livre ___ tu m'as parlé est passionnant.", "dont", ["que", "où", "qui"]),
       ("C'est le jour ___ nous nous sommes rencontrés.", "où", ["dont", "que", "qui"]), ("La personne ___ j'ai besoin n'est pas là.", "dont", ["que", "où", "qui"]),
       ("Le restaurant ___ nous dînons est excellent.", "où", ["dont", "qui", "que"]), ("Voici l'ami ___ je t'ai présenté.", "que", ["dont", "où", "qui"]),
       ("C'est un projet ___ je suis fier.", "dont", ["que", "où", "qui"]), ("La maison ___ ils habitent est ancienne.", "où", ["dont", "que", "qui"]),
       ("Le film ___ tout le monde parle sort demain.", "dont", ["que", "où", "qui"]), ("L'élève ___ a gagné le prix s'appelle Lina.", "qui", ["que", "dont", "où"]),
       ("Les vacances ___ je rêve sont au bord de la mer.", "dont", ["que", "où", "qui"]), ("La chanson ___ tu écoutes est belle.", "que", ["dont", "où", "qui"])]
PRON = [("Tu as parlé à tes parents ? — Oui, je ___ ai parlé.", "leur", ["les", "lui", "y"]), ("Tu as téléphoné à Marie ? — Oui, je ___ ai téléphoné.", "lui", ["la", "leur", "y"]),
        ("Tu penses à ton examen ? — Oui, j'___ pense.", "y", ["en", "lui", "le"]), ("Tu as besoin de ce livre ? — Oui, j'___ ai besoin.", "en", ["y", "le", "lui"]),
        ("Tu as écrit à tes amis ? — Oui, je ___ ai écrit.", "leur", ["les", "lui", "y"]), ("Vous avez vu le directeur ? — Oui, nous ___ avons vu.", "l'", ["lui", "leur", "y"]),
        ("Tu as répondu au professeur ? — Oui, je ___ ai répondu.", "lui", ["le", "leur", "en"]), ("Tu parles de ton voyage ? — Oui, j'___ parle souvent.", "en", ["y", "le", "lui"]),
        ("Tu crois à cette histoire ? — Non, je n'___ crois pas.", "y", ["en", "la", "lui"]), ("Tu as offert des fleurs à ta mère ? — Oui, je ___ en ai offert.", "lui", ["la", "leur", "y"])]
REPORT = [("Il dit qu'il ___ demain.", "viendra", ["viendrait", "venait", "viendras"]), ("Elle dit qu'elle ___ fatiguée aujourd'hui.", "est", ["était", "serait", "soit"]),
          ("Ils disent qu'ils ___ partis hier.", "sont", ["seront", "seraient", "soient"]), ("Je te dis que je ___ d'accord.", "suis", ["sois", "serais", "étais"]),
          ("Tu dis que tu ___ faim maintenant.", "as", ["aies", "aurais", "auras"])]


COND_FORMS = {  # (je/tu, il, nous, ils) au conditionnel / présent / futur / imparfait
    "faire": {"cond": ["ferais", "ferait", "ferions", "feraient"], "pres": ["fais", "fait", "faisons", "font"], "fut": ["ferai", "fera", "ferons", "feront"], "imp": ["faisais", "faisait", "faisions", "faisaient"]},
    "aller": {"cond": ["irais", "irait", "irions", "iraient"], "pres": ["vais", "va", "allons", "vont"], "fut": ["irai", "ira", "irons", "iront"], "imp": ["allais", "allait", "allions", "allaient"]},
    "acheter": {"cond": ["achèterais", "achèterait", "achèterions", "achèteraient"], "pres": ["achète", "achète", "achetons", "achètent"], "fut": ["achèterai", "achètera", "achèterons", "achèteront"], "imp": ["achetais", "achetait", "achetions", "achetaient"]},
    "être": {"cond": ["serais", "serait", "serions", "seraient"], "pres": ["suis", "est", "sommes", "sont"], "fut": ["serai", "sera", "serons", "seront"], "imp": ["étais", "était", "étions", "étaient"]},
    "avoir": {"cond": ["aurais", "aurait", "aurions", "auraient"], "pres": ["ai", "a", "avons", "ont"], "fut": ["aurai", "aura", "aurons", "auront"], "imp": ["avais", "avait", "avions", "avaient"]},
    "pouvoir": {"cond": ["pourrais", "pourrait", "pourrions", "pourraient"], "pres": ["peux", "peut", "pouvons", "peuvent"], "fut": ["pourrai", "pourra", "pourrons", "pourront"], "imp": ["pouvais", "pouvait", "pouvions", "pouvaient"]},
}
COND_SUBJ = [("je", "j'avais", 0), ("il", "il avait", 1), ("nous", "nous avions", 2), ("ils", "ils avaient", 3)]
GER = [("écouter de la musique en", "travaillant", ["travailler", "travaillé", "travaille"]), ("parler en", "mangeant", ["manger", "mangé", "mange"]),
       ("chanter en", "marchant", ["marcher", "marché", "marche"]), ("apprendre en", "jouant", ["jouer", "joué", "joue"]),
       ("se blesser en", "tombant", ["tomber", "tombé", "tombe"]), ("trouver la solution en", "réfléchissant", ["réfléchir", "réfléchi", "réfléchit"]),
       ("progresser en", "lisant", ["lire", "lu", "lit"]), ("se reposer en", "dormant", ["dormir", "dormi", "dort"]),
       ("rencontrer des gens en", "voyageant", ["voyager", "voyagé", "voyage"]), ("se détendre en", "écoutant", ["écouter", "écouté", "écoute"])]


def b1_grammar():
    out, n = [], 0
    for verb, f in COND_FORMS.items():
        for subj, cond_si, k in COND_SUBJ:
            correct = f["cond"][k]
            start = "j'" if subj == "je" and correct[0] in VOWEL else (subj + " ")
            n += 1
            si = "S'" + cond_si if cond_si.startswith("il") else "Si " + cond_si
            out.append(q(f"gen-b1-g-{n}", "B1", "grammar", f"{si} le temps, {start}___ {COND_FRAMES[verb]}.".replace("j' ___", "j'___"),
                         correct, [f["pres"][k], f["fut"][k], f["imp"][k]]))
    for verb, forms in SUBJ_PRES.items():
        for subj in ("tu", "nous", "vous"):
            correct = forms[IDX[subj]]
            wrong = {"tu": SUBJ_WRONG[verb], "nous": [x for x in SUBJ_WRONG_NOUS[verb]], "vous": [x for x in SUBJ_WRONG_VOUS[verb]]}[subj]
            n += 1
            out.append(q(f"gen-b1-g-{n}", "B1", "grammar", f"Il faut que {subj} ___ {SUBJ_FRAMES[verb]}.", correct, wrong))
    for goal, ger, wrong in GER:
        n += 1
        out.append(q(f"gen-b1-g-{n}", "B1", "grammar", f"On peut {goal} ___.", ger, wrong))
    fut_frames = {"faire": "une promenade", "aller": "au marché", "acheter": "du pain", "être": "à Paris", "avoir": "le temps", "pouvoir": "venir"}
    for verb, f in COND_FORMS.items():
        for subj, k in (("je", 0), ("il", 1), ("nous", 2), ("ils", 3)):
            correct = f["fut"][k]
            start = "j'" if subj == "je" and correct[0] in VOWEL else subj + " "
            n += 1
            out.append(q(f"gen-b1-g-{n}", "B1", "grammar", f"Demain, {start}___ {fut_frames[verb]}.", correct, [f["cond"][k], f["imp"][k], f["pres"][k]]))
    for sent, ans, wrong in REL + PRON + REPORT:
        n += 1
        out.append(q(f"gen-b1-g-{n}", "B1", "grammar", sent, ans, wrong))
    return out


SUBJ_WRONG_NOUS = {"être": ["sommes", "serons", "serions"], "avoir": ["avons", "aurons", "aurions"], "faire": ["faisons", "ferons", "ferions"], "aller": ["allons", "irons", "irions"],
                   "venir": ["venons", "viendrons", "viendrions"], "prendre": ["prenons", "prendrons", "prendrions"], "finir": ["finissons", "finirons", "finirions"], "partir": ["partons", "partirons", "partirions"]}
SUBJ_WRONG_VOUS = {"être": ["êtes", "serez", "seriez"], "avoir": ["avez", "aurez", "auriez"], "faire": ["faites", "ferez", "feriez"], "aller": ["allez", "irez", "iriez"],
                   "venir": ["venez", "viendrez", "viendriez"], "prendre": ["prenez", "prendrez", "prendriez"], "finir": ["finissez", "finirez", "finiriez"], "partir": ["partez", "partirez", "partiriez"]}


B1_SERVICES = [("le prêt gratuit de vélos", "Il suffit de présenter une carte d'habitant", "gratuit"), ("des cours de cuisine pour les jeunes", "Les cours ont lieu le mercredi après-midi", "5 euros par séance"),
               ("une navette pour les personnes âgées", "Il faut réserver la veille", "gratuit"), ("un atelier de réparation d'objets", "Des bénévoles aident les habitants à réparer leurs appareils", "2 euros"),
               ("des visites guidées du vieux quartier", "Les visites durent une heure et demie", "8 euros"), ("le prêt de jeux de société", "Chaque famille peut emprunter deux jeux", "gratuit"),
               ("des cours de natation pour adultes", "Les cours ont lieu le samedi matin", "10 euros par séance"), ("un jardin partagé", "Chaque habitant peut cultiver un petit carré de terre", "15 euros par an")]
PRICES_B1 = sorted({s[2] for s in B1_SERVICES} | {"20 euros", "1 euro"})
EMAILS = [("je suis malade", "venir au cours de jeudi", "recevoir les exercices par e-mail"), ("mon train a été annulé", "être là lundi matin", "déplacer le rendez-vous à mardi"),
          ("j'ai déménagé", "recevoir le courrier à l'ancienne adresse", "changer mon adresse"), ("ma fille a un examen", "participer à la réunion de vendredi", "avoir le compte rendu"),
          ("je pars en voyage", "rendre le livre à temps", "garder le livre une semaine de plus"), ("mon ordinateur est en panne", "envoyer le dossier aujourd'hui", "avoir deux jours de plus"),
          ("j'ai un rendez-vous chez le médecin", "venir à l'entretien de mercredi", "venir jeudi à la place")]
STORIES = [  # (prénom, il/elle, durée, lieu, but, difficulté (infinitif), aide, résultat)
    ("Thomas", "il", "un an", "en Espagne", "ses études", "comprendre ses professeurs", "ses colocataires", "il parle couramment espagnol"),
    ("Sarah", "elle", "six mois", "au Canada", "un stage", "se faire des amis", "une association d'étudiants", "elle a beaucoup d'amis"),
    ("Kevin", "il", "trois mois", "en Allemagne", "un projet de recherche", "parler allemand", "un cours du soir", "il peut travailler en allemand"),
    ("Julie", "elle", "deux ans", "au Japon", "son travail", "s'orienter dans la ville", "ses collègues", "elle se déplace sans problème"),
    ("Marc", "il", "un semestre", "en Italie", "ses études d'art", "payer ses dépenses", "une bourse de l'université", "il visite de nombreux musées"),
    ("Laura", "elle", "un an", "en Chine", "apprendre le chinois", "lire les caractères", "son professeur particulier", "elle lit le journal"),
    ("Hugo", "il", "quatre mois", "en Irlande", "un échange scolaire", "parler devant les autres", "sa famille d'accueil", "il ose parler en public"),
    ("Nadia", "elle", "un an", "en Suisse", "un emploi", "trouver un logement", "une collègue", "elle a un appartement près du travail"),
    ("Paul", "il", "six mois", "au Portugal", "son stage", "comprendre l'accent", "une application de langue", "il comprend presque tout"),
    ("Inès", "elle", "un an", "en Angleterre", "ses études", "parler sans avoir peur des erreurs", "un club de conversation", "elle parle anglais avec assurance")]


def b1_reading():
    out, i = [], 0
    svcs = [s[0] for s in B1_SERVICES]
    for city, (svc, cond, price) in zip(["Rennes", "Lille", "Nantes", "Dijon", "Tours", "Metz", "Brest", "Annecy"], B1_SERVICES):
        i += 1
        text = (f"Depuis septembre, la ville {"d" + chr(39) if city[0] in "AEIOU" else "de "}{city} propose {svc}. {cond}. Ce service est {price if price == 'gratuit' else 'proposé au prix de ' + price}. "
                "Selon la mairie, de nombreux habitants l'ont déjà utilisé.")
        out.append(q(f"gen-b1-r-{i}-1", "B1", "reading", "Que propose la ville ?", svc[0].upper() + svc[1:], [x[0].upper() + x[1:] for x in pick_wrong(svcs, svc)], passage=text))
        lab = lambda p: "Rien, c'est gratuit" if p == "gratuit" else p[0].upper() + p[1:]
        out.append(q(f"gen-b1-r-{i}-2", "B1", "reading", "Combien coûte ce service ?", lab(price), [lab(p) for p in pick_wrong(PRICES_B1, price)], passage=text))
    reasons = [e[0] for e in EMAILS]
    asks = [e[2] for e in EMAILS]
    for name, (why, cannot, ask) in zip(["Lucie", "Karim", "Anne", "Yann", "Sophie", "Malik", "Claire"], EMAILS):
        i += 1
        text = f"Bonjour Madame Martin, je vous écris parce que {why}. Je ne pourrai pas {cannot}. Est-ce que je pourrais {ask} ? Merci d'avance. {name}"
        out.append(q(f"gen-b1-r-{i}-1", "B1", "reading", f"Quelle raison {name} donne-t-{'il' if name in ('Karim', 'Yann', 'Malik') else 'elle'} dans son message ?",
                     f"« Parce que {why}. »", [f"« Parce que {r}. »" for r in pick_wrong(reasons, why)], passage=text))
        out.append(q(f"gen-b1-r-{i}-2", "B1", "reading", f"Que demande {name} ?", f"« Est-ce que je pourrais {ask} ? »", [f"« Est-ce que je pourrais {a} ? »" for a in pick_wrong(asks, ask)], passage=text))
    diffs = [s[5] for s in STORIES]
    helps = [s[6] for s in STORIES]
    for name, pron, dur, where, why, diff, help_, res in STORIES:
        i += 1
        text = f"{name} a passé {dur} {where} pour {why}. Au début, {pron} avait du mal à {diff}. Mais grâce à {help_}, les choses ont changé : aujourd'hui, {res}."
        text = text.replace("grâce à ses", "grâce à ses").replace("grâce à le", "grâce au")
        cap = lambda x: x[0].upper() + x[1:]
        out.append(q(f"gen-b1-r-{i}-1", "B1", "reading", f"Qu'est-ce qui était difficile pour {name} au début ?",
                     cap(diff), [cap(d) for d in pick_wrong(diffs, diff)], passage=text))
        out.append(q(f"gen-b1-r-{i}-2", "B1", "reading", f"Qu'est-ce qui a aidé {name} ?", cap(help_), [cap(h) for h in pick_wrong(helps, help_)], passage=text))
    return out


# ======================================================================= B2
B2_COLLOC = [("Le chercheur a ___ une hypothèse audacieuse.", "émis", ["porté", "rendu", "tiré"]), ("Il faut ___ en compte l'avis des habitants.", "prendre", ["mettre", "porter", "tirer"]),
             ("Le gouvernement va ___ en œuvre cette réforme.", "mettre", ["prendre", "porter", "tenir"]), ("Quelle conclusion peut-on ___ de cette expérience ?", "tirer", ["porter", "mettre", "rendre"]),
             ("La victime a ___ plainte auprès de la police.", "porté", ["mis", "fait", "tiré"]), ("L'entreprise doit ___ face à une forte concurrence.", "faire", ["mettre", "tenir", "porter"]),
             ("La police a ___ une enquête approfondie.", "mené", ["porté", "rendu", "tiré"]), ("Cette découverte ___ en question nos certitudes.", "remet", ["porte", "rend", "tire"]),
             ("Il faut ___ compte des contraintes budgétaires.", "tenir", ["porter", "mettre", "tirer"]), ("Le journaliste doit ___ compte des faits avec précision.", "rendre", ["tenir", "porter", "mettre"]),
             ("Les parents ___ un rôle essentiel dans l'éducation.", "jouent", ["portent", "rendent", "tirent"]), ("Les autorités ont ___ des mesures urgentes.", "pris", ["porté", "tiré", "rendu"]),
             ("L'association a ___ un nouveau projet.", "lancé", ["porté", "rendu", "tenu"]), ("En fin d'année, il faut ___ le bilan de nos actions.", "dresser", ["porter", "rendre", "tenir"]),
             ("Ce débat a ___ de nombreuses questions.", "soulevé", ["porté", "rendu", "tenu"]), ("L'équipe a ___ le défi avec succès.", "relevé", ["porté", "rendu", "tenu"]),
             ("Cette mesure vise à ___ un manque de logements.", "combler", ["porter", "rendre", "tenir"]), ("L'entreprise a ___ tous ses objectifs.", "atteint", ["porté", "rendu", "tenu"]),
             ("Ce film a ___ un vif intérêt chez les jeunes.", "suscité", ["porté", "rendu", "tenu"]), ("Il ne faut pas ___ trop d'importance à ces rumeurs.", "accorder", ["porter", "rendre", "tenir"])]
B2_CONN = [("___ ses efforts, il a échoué.", "Malgré", ["Grâce à", "Afin de", "Pour"]), ("Il a réussi ___ son travail acharné.", "grâce à", ["malgré", "au lieu de", "afin de"]),
           ("Elle travaille beaucoup ___ réussir son concours.", "afin de", ["malgré", "grâce à", "bien que"]), ("Le projet est intéressant ; ___, il coûte trop cher.", "néanmoins", ["par conséquent", "ainsi", "donc"]),
           ("Les prix ont augmenté ; ___, les ventes ont baissé.", "par conséquent", ["néanmoins", "pourtant", "en revanche"]), ("Paul aime la ville ; sa sœur, ___, préfère la campagne.", "en revanche", ["par conséquent", "ainsi", "donc"]),
           ("Il parle lentement ___ tout le monde le comprenne.", "de sorte que", ["bien que", "malgré", "grâce à"]), ("___ pleuve, le concert aura lieu.", "Bien qu'il", ["Parce qu'il", "Puisqu'il", "Comme il"]),
           ("Je partirai tôt ___ éviter les embouteillages.", "pour", ["malgré", "bien que", "grâce à"]), ("Il est resté calme ___ la situation était grave.", "alors que", ["afin que", "pour que", "grâce à"]),
           ("___ de partir, vérifie que tu as tes clés.", "Avant", ["Après", "Malgré", "Pendant"]), ("Le match est annulé ___ de la tempête.", "en raison", ["grâce", "malgré", "afin"]),
           ("Tu peux venir ___ tu préviennes avant.", "à condition que", ["bien que", "parce que", "alors que"]), ("Nous accepterons ___ le prix soit raisonnable.", "pourvu que", ["bien que", "parce que", "puisque"]),
           ("___ soit tard, il continue à travailler.", "Quoiqu'il", ["Parce qu'il", "Puisqu'il", "Comme il"]), ("Elle n'a rien dit, ___ elle était d'accord.", "comme si", ["afin que", "pour que", "de sorte que"]),
           ("Les résultats sont bons ; ___, nous devons rester prudents.", "toutefois", ["donc", "ainsi", "par conséquent"]), ("La réunion est reportée ___ nouvel ordre.", "jusqu'à", ["malgré", "grâce à", "afin de"]),
           ("Il a démissionné ___ protester contre la décision.", "pour", ["malgré", "bien que", "grâce à"]), ("___ le mauvais temps, la fête a eu du succès.", "En dépit du", ["Grâce au", "À cause du", "Au lieu du"])]
B2_SYN = [("pallier", "remédier à"), ("entraver", "gêner"), ("accroître", "augmenter"), ("éphémère", "de courte durée"), ("pérenne", "durable"), ("révolu", "terminé"),
          ("inéluctable", "inévitable"), ("préconiser", "recommander"), ("déplorer", "regretter"), ("étayer", "appuyer par des preuves"), ("un enjeu", "ce qu'on peut gagner ou perdre"),
          ("une lacune", "un manque"), ("un essor", "un développement rapide"), ("une divergence", "un désaccord"), ("corroborer", "confirmer"), ("atténuer", "diminuer"),
          ("fustiger", "critiquer vivement"), ("vétuste", "vieux et en mauvais état"), ("pertinent", "adapté et approprié"), ("anodin", "sans importance")]
B2_SYN_POOL = [b for _, b in B2_SYN]
B2_REG = [("argent", "fric"), ("travail", "boulot"), ("voiture", "bagnole"), ("livre", "bouquin"), ("vêtements", "fringues"), ("chaussures", "godasses"), ("nourriture", "bouffe"), ("rire", "rigoler")]
B2_REG_POOL = [b for _, b in B2_REG]
B2_ANT = [("légal", "illégal"), ("possible", "impossible"), ("lisible", "illisible"), ("responsable", "irresponsable"), ("honnête", "malhonnête"), ("connu", "inconnu"),
          ("un accord", "un désaccord"), ("régulier", "irrégulier"), ("habile", "maladroit"), ("prudent", "imprudent"), ("croyable", "incroyable"), ("patient", "impatient")]
B2_ANT_POOL = [b for _, b in B2_ANT] + ["déloyal", "anormal"]


def b2_vocab():
    out, n = [], 0
    for stem, ans, wrong in B2_COLLOC + B2_CONN:
        n += 1
        out.append(q(f"gen-b2-v-{n}", "B2", "vocab", stem, ans, wrong))
    for a, b in B2_SYN:
        for k in range(2):
            n += 1
            out.append(q(f"gen-b2-v-{n}", "B2", "vocab", f"« {a} » signifie :" if k == 0 else f"Quel est le sens {'d' + chr(39) if a[0] in 'aeéiouh' else 'de '}« {a} » ?", b, pick_wrong(B2_SYN_POOL, b)))
    for a, b in B2_REG:
        n += 1
        out.append(q(f"gen-b2-v-{n}", "B2", "vocab", f"Quel est le mot familier pour « {a} » ?", b, pick_wrong(B2_REG_POOL, b)))
    for a, b in B2_ANT:
        n += 1
        out.append(q(f"gen-b2-v-{n}", "B2", "vocab", f"Le contraire de « {a} », c'est :", b, pick_wrong(B2_ANT_POOL, b)))
    return out


B2_SUBJ = [("bien que", "il ___ malade, il est venu.", "soit", ["est", "sera", "était"]), ("pour que", "Je t'explique pour que tu ___ comprendre.", "puisses", ["peux", "pourras", "pouvais"]),
           ("avant que", "Rentre avant qu'il ne ___ nuit.", "fasse", ["fait", "fera", "faisait"]), ("à moins que", "Je viendrai, à moins qu'il ne ___ trop tard.", "soit", ["est", "sera", "était"]),
           ("sans que", "Il est parti sans que nous le ___.", "sachions", ["savons", "saurons", "savions"]), ("jusqu'à ce que", "Attends ici jusqu'à ce que je ___.", "revienne", ["reviens", "reviendrai", "revenais"]),
           ("bien que", "Bien qu'elle ___ raison, personne ne l'écoute.", "ait", ["a", "aura", "avait"]), ("pour que", "Parle fort pour qu'on t'___.", "entende", ["entend", "entendra", "entendait"]),
           ("il est possible que", "Il est possible qu'il ___ demain.", "pleuve", ["pleut", "pleuvra", "pleuvait"]), ("je doute que", "Je doute qu'il ___ la vérité.", "dise", ["dit", "dira", "disait"]),
           ("je souhaite que", "Je souhaite que vous ___ un bon séjour.", "passiez", ["passez", "passerez", "passeriez"]), ("il faut que", "Il faut que nous ___ une solution.", "trouvions", ["trouvons", "trouverons", "trouverions"]),
           ("bien que", "Bien que nous ___ fatigués, nous continuons.", "soyons", ["sommes", "serons", "étions"]), ("à condition que", "Je te prête ma voiture à condition que tu ___ prudent.", "sois", ["es", "seras", "étais"]),
           ("avant que", "Finis ton travail avant que le directeur n'___.", "arrive", ["arrivera", "arrivait", "est arrivé"]), ("bien que", "Bien qu'ils ___ peu de temps, ils nous ont aidés.", "aient", ["ont", "auront", "avaient"]),
           ("je ne pense pas que", "Je ne pense pas qu'elle ___ venir.", "puisse", ["peut", "pourra", "pouvait"]), ("il est important que", "Il est important que tu ___ à l'heure.", "arrives", ["arriveras", "arrivais", "arriverais"]),
           ("pour que", "Je ferme la fenêtre pour que le bébé ___.", "dorme", ["dort", "dormira", "dormait"]), ("quoique", "Quoiqu'il ___ beaucoup, il ne grossit pas.", "mange", ["mangera", "mangeait", "a mangé"])]
B2_COND = [("Si tu m'avais prévenu, je ___ venu.", "serais", ["suis", "serai", "étais"]), ("Si elle avait su, elle ___ accepté.", "aurait", ["a", "aura", "avait"]),
           ("S'il avait plu, nous ___ restés à la maison.", "serions", ["sommes", "serons", "étions"]), ("Si j'avais eu le temps, j'___ fini.", "aurais", ["ai", "aurai", "avais"]),
           ("Si vous étiez partis plus tôt, vous ___ arrivés à l'heure.", "seriez", ["êtes", "serez", "étiez"]), ("S'ils avaient travaillé, ils ___ réussi.", "auraient", ["ont", "auront", "avaient"]),
           ("Si nous avions su, nous ___ réservé.", "aurions", ["avons", "aurons", "avions"]), ("Si tu avais écouté, tu ___ compris.", "aurais", ["as", "auras", "avais"]),
           ("Si elle était venue, elle ___ rencontré Paul.", "aurait", ["a", "aura", "avait"]), ("S'il avait fait beau, ils ___ sortis.", "seraient", ["sont", "seront", "étaient"]),
           ("Si tu étais venu, tu te ___ amusé.", "serais", ["es", "seras", "étais"]), ("Si j'avais vu ce film, je te l'___ dit.", "aurais", ["ai", "aurai", "avais"])]
B2_REL = [("C'est le projet ___ je travaille depuis un an.", "sur lequel", ["auquel", "duquel", "dont"]), ("C'est une idée ___ je n'avais pas pensé.", "à laquelle", ["laquelle", "dont", "de laquelle"]),
          ("Voici les collègues avec ___ je travaille.", "lesquels", ["auxquels", "dont", "duquel"]), ("Le parc près ___ j'habite est immense.", "duquel", ["auquel", "lequel", "dont"]),
          ("C'est la raison pour ___ il est parti.", "laquelle", ["lequel", "qui", "quoi"]), ("Le concours ___ elle participe est difficile.", "auquel", ["duquel", "lequel", "dont"]),
          ("Les amis ___ je pense sont loin.", "auxquels", ["desquels", "lesquels", "dont"]), ("La table sur ___ j'ai posé le livre est en bois.", "laquelle", ["lequel", "qui", "dont"]),
          ("Le stylo avec ___ j'écris est neuf.", "lequel", ["laquelle", "qui", "dont"]), ("Je ne sais pas ___ il a besoin.", "ce dont", ["ce que", "ce qui", "dont"]),
          ("Dis-moi ___ te fait peur.", "ce qui", ["ce que", "ce dont", "qui"]), ("Fais ___ tu veux.", "ce que", ["ce qui", "ce dont", "que"]),
          ("___ m'étonne, c'est son calme.", "Ce qui", ["Ce que", "Ce dont", "Qui"]), ("___ je me souviens, c'est de son sourire.", "Ce dont", ["Ce que", "Ce qui", "Dont"])]
B2_AGR = [("Les lettres qu'il a ___ sont arrivées.", "écrites", ["écrit", "écrits", "écrite"]), ("La robe que j'ai ___ est rouge.", "achetée", ["acheté", "achetés", "achetées"]),
          ("Les fleurs que tu m'as ___ sont belles.", "offertes", ["offert", "offerts", "offerte"]), ("Les films que nous avons ___ étaient longs.", "vus", ["vu", "vue", "vues"]),
          ("Ces chansons, je les ai ___ cent fois.", "écoutées", ["écouté", "écoutés", "écoutée"]), ("La décision qu'elle a ___ est courageuse.", "prise", ["pris", "prises", "prit"]),
          ("Elles se sont ___ à six heures.", "levées", ["levé", "levés", "levée"]), ("Les clés que j'ai ___ étaient dans ma poche.", "cherchées", ["cherché", "cherchés", "cherchée"]),
          ("Les photos qu'ils ont ___ sont magnifiques.", "prises", ["pris", "prise", "prit"]), ("Les erreurs que tu as ___ sont légères.", "faites", ["fait", "faits", "faite"])]
B2_REPORT = [("Il a dit qu'il ___ le lendemain.", "viendrait", ["viendra", "vienne", "viendrai"]), ("Elle m'a demandé si j'___ fini.", "avais", ["ai", "aurai", "aie"]),
             ("Ils ont annoncé qu'ils ___ déménager.", "allaient", ["vont", "iront", "aillent"]), ("Tu m'as dit que tu ___ malade la veille.", "avais été", ["as été", "seras", "sois"]),
             ("Il m'a promis qu'il m'___ dès son arrivée.", "appellerait", ["appellera", "appelle", "appelait"]), ("Elle a expliqué qu'elle ___ en retard à cause du train.", "était", ["est", "sera", "soit"])]


B2_BIENQUE = [  # (phrase, subjonctif, [indicatif présent, futur, imparfait])
    ("Bien qu'il ___ tard, il continue à travailler.", "soit", ["est", "sera", "était"]),
    ("Bien qu'il ___ peu de temps, il nous aide.", "ait", ["a", "aura", "avait"]),
    ("Bien qu'il ___ froid, nous sortons nous promener.", "fasse", ["fait", "fera", "faisait"]),
    ("Bien qu'il ___ mieux, il reste prudent.", "aille", ["va", "ira", "allait"]),
    ("Bien qu'il ___ souvent nous voir, il ne reste jamais longtemps.", "vienne", ["vient", "viendra", "venait"]),
    ("Bien qu'il ___ le bus de 7 h, il arrive en retard.", "prenne", ["prend", "prendra", "prenait"]),
    ("Bien qu'il ___ son travail tôt, il reste au bureau.", "finisse", ["finit", "finira", "finissait"]),
    ("Bien qu'il ___ demain, il n'a pas encore fait sa valise.", "parte", ["part", "partira", "partait"]),
    ("Bien qu'ils ___ fatigués, ils terminent le match.", "soient", ["sont", "seront", "étaient"]),
    ("Bien qu'ils ___ raison, personne ne les écoute.", "aient", ["ont", "auront", "avaient"]),
    ("Bien qu'ils ___ à la plage, ils ne se baignent pas.", "aillent", ["vont", "iront", "allaient"])]
B2_COND2 = [("Sans ton aide, je n'___ pas réussi.", "aurais", ["ai", "aurai", "avais"]), ("À ta place, j'___ accepté cette offre.", "aurais", ["ai", "aurai", "avais"]),
            ("Avec un peu plus de temps, nous ___ fini le projet.", "aurions", ["avons", "aurons", "avions"]), ("Sans la pluie, ils ___ venus à la fête.", "seraient", ["sont", "seront", "étaient"]),
            ("Si tu avais demandé, je t'___ aidé.", "aurais", ["ai", "aurai", "avais"]), ("Si nous étions partis à l'heure, nous ___ arrivés avant la nuit.", "serions", ["sommes", "serons", "étions"]),
            ("Si elle avait eu son permis, elle ___ conduit.", "aurait", ["a", "aura", "avait"]), ("S'il avait été là, il ___ su quoi faire.", "aurait", ["a", "aura", "avait"]),
            ("Si vous aviez lu le texte, vous ___ compris.", "auriez", ["avez", "aurez", "aviez"]), ("Si j'avais su, je ne ___ pas venu.", "serais", ["suis", "serai", "étais"])]
B2_PQP = [("Quand je suis arrivé, le film ___ déjà commencé.", "avait", ["a", "aura", "aurait"]), ("Elle était triste parce qu'elle ___ perdu son chat.", "avait", ["a", "aura", "aurait"]),
          ("Nous étions fatigués : nous ___ marché toute la journée.", "avions", ["avons", "aurons", "aurions"]), ("Quand ils sont arrivés, nous ___ déjà partis.", "étions", ["sommes", "serons", "serions"]),
          ("Il a réussi l'examen qu'il ___ raté l'année précédente.", "avait", ["a", "aura", "aurait"]), ("Je ne l'ai pas reconnu : il ___ beaucoup changé.", "avait", ["a", "aura", "aurait"])]
B2_FUTANT = [("Quand tu ___ fini, appelle-moi.", "auras", ["as", "avais", "aurais"]), ("Dès que nous ___ arrivés, nous te préviendrons.", "serons", ["sommes", "étions", "serions"]),
             ("Je partirai quand j'___ terminé ce rapport.", "aurai", ["ai", "avais", "aurais"]), ("Lorsqu'elle ___ reçu ta lettre, elle te répondra.", "aura", ["a", "avait", "aurait"]),
             ("Quand ils ___ rentrés, nous dînerons.", "seront", ["sont", "étaient", "seraient"])]
B2_REPORT2 = [("Il a affirmé qu'il ne ___ jamais ce secret.", "dirait", ["dira", "dise", "dirai"]), ("Elle m'a demandé où j'___ mes vacances.", "avais passé", ["ai passé", "aurai passé", "aie passé"]),
              ("Ils nous ont dit qu'ils ___ partir le lendemain.", "devaient", ["doivent", "devront", "devoir"]), ("Tu m'as demandé si je ___ venir à la réunion.", "pouvais", ["peux", "pourrai", "puisse"]),
              ("Il a expliqué qu'il ___ son train la veille.", "avait raté", ["a raté", "rate", "aura raté"]), ("Elle a annoncé qu'elle ___ en Chine l'année suivante.", "partirait", ["partira", "part", "parte"])]


def b2_grammar():
    out, n = [], 0
    for _, sent, ans, wrong in B2_SUBJ:
        n += 1
        s = sent if sent[0].isupper() else sent[0].upper() + sent[1:]
        if s.startswith("Il ___"):
            s = "Bien qu'" + sent
        out.append(q(f"gen-b2-g-{n}", "B2", "grammar", s, ans, wrong))
    for sent, ans, wrong in B2_COND + B2_REL + B2_AGR + B2_REPORT + B2_BIENQUE + B2_COND2 + B2_PQP + B2_FUTANT + B2_REPORT2:
        n += 1
        out.append(q(f"gen-b2-g-{n}", "B2", "grammar", sent, ans, wrong))
    return out


B2_TOPICS = [
    ("Le télétravail", "le gain de temps sur les trajets", "l'isolement des salariés", "Beaucoup d'entreprises choisissent une formule mixte."),
    ("La semaine de quatre jours", "un meilleur équilibre entre travail et vie privée", "une charge de travail plus lourde chaque jour", "Plusieurs entreprises la testent avant de décider."),
    ("L'uniforme à l'école", "la réduction des inégalités entre élèves", "une atteinte à la liberté d'expression", "Certaines écoles laissent les familles voter."),
    ("La voiture électrique", "la baisse de la pollution en ville", "le prix élevé des batteries", "Les aides publiques jouent un rôle décisif."),
    ("Les devoirs à la maison", "la consolidation des apprentissages", "l'aggravation des inégalités entre familles", "Certains collèges proposent une aide aux devoirs le soir."),
    ("Le tourisme de masse", "les revenus pour l'économie locale", "la dégradation des sites naturels", "Des villes limitent désormais le nombre de visiteurs."),
    ("Les livres numériques", "la possibilité d'emporter des centaines de livres", "la fatigue des yeux", "Les deux supports semblent complémentaires."),
    ("La cantine bio", "une alimentation plus saine pour les enfants", "le coût plus élevé des repas", "Les communes cherchent des producteurs locaux."),
    ("Le vélo en ville", "la réduction des embouteillages", "le manque de pistes sécurisées", "Les villes investissent dans de nouvelles pistes."),
    ("Les réseaux sociaux chez les adolescents", "le maintien du lien avec les amis", "le risque de harcèlement en ligne", "Les écoles organisent des ateliers de prévention."),
    ("L'intelligence artificielle à l'école", "un accompagnement personnalisé des élèves", "le risque de triche", "Les enseignants réfléchissent à de nouveaux exercices."),
    ("Les cours en ligne", "la liberté d'apprendre à son rythme", "le manque de motivation sans professeur", "Les formations mêlent souvent cours en ligne et séances en classe."),
    ("La réduction de l'éclairage public la nuit", "les économies d'énergie", "un sentiment d'insécurité", "Certaines villes éteignent seulement les rues peu fréquentées."),
    ("Le service civique obligatoire", "le renforcement de la cohésion sociale", "le coût pour l'État", "Le débat reste ouvert au Parlement."),
    ("Les zoos", "la protection des espèces menacées", "la captivité des animaux", "Les zoos modernes misent sur de grands espaces."),
    ("La gratuité des transports en commun", "l'accès à la mobilité pour tous", "la perte de recettes pour les villes", "Certaines villes l'appliquent seulement le week-end."),
    ("Le travail des étudiants pendant leurs études", "l'acquisition d'une expérience professionnelle", "la baisse des résultats universitaires", "Les universités adaptent parfois les horaires."),
    ("Les compteurs d'eau intelligents", "la détection rapide des fuites", "la question de la vie privée", "Les fournisseurs promettent de protéger les données."),
    ("La publicité dans les écoles", "le financement de projets scolaires", "l'influence sur les jeunes consommateurs", "La plupart des pays l'encadrent strictement."),
    ("Les jardins sur les toits", "la fraîcheur en été dans les villes", "le coût d'installation", "Des subventions encouragent les immeubles neufs."),
    ("Le vote dès seize ans", "l'engagement plus précoce des jeunes", "le manque de maturité supposé", "Quelques pays l'ont déjà adopté."),
    ("Les trottinettes électriques en libre-service", "des trajets courts plus rapides", "le désordre sur les trottoirs", "Plusieurs villes ont créé des places de stationnement dédiées."),
    ("L'apprentissage d'une deuxième langue dès la maternelle", "une meilleure prononciation", "une surcharge pour les jeunes enfants", "Les spécialistes recommandent des activités ludiques."),
    ("Les petits commerces de centre-ville", "le lien social dans les quartiers", "des prix souvent plus élevés", "Les mairies aident à réduire les loyers commerciaux."),
    ("La limitation de la vitesse à 30 km/h en ville", "la diminution des accidents graves", "l'allongement des temps de trajet", "Les premiers bilans sont plutôt positifs."),
]


def b2_reading():
    out = []
    advs = [t[1] for t in B2_TOPICS]
    cons = [t[2] for t in B2_TOPICS]
    cap = lambda x: x[0].upper() + x[1:]
    for i, (topic, adv, con, concl) in enumerate(B2_TOPICS, 1):
        pl = topic.startswith("Les ")
        de = {"le": "du ", "la": "de la ", "les": "des ", "un": "d'un ", "une": "d'une ", "des": "des "}.get(con.split(" ")[0])
        de_con = de + con.split(" ", 1)[1] if de else ("d'" if con[0] in "aeéiouh" else "de ") + con.removeprefix("l'") if not con.startswith("l'") else "de " + con
        text = (f"{topic} {'font' if pl else 'fait'} débat. {'Leurs' if pl else 'Ses'} partisans mettent en avant {adv}. "
                f"{'Leurs' if pl else 'Ses'} détracteurs, eux, s'inquiètent {de_con}. {concl}")
        out.append(q(f"gen-b2-r-{i}-1", "B2", "reading", "Quel argument avancent les partisans ?", cap(adv), [cap(a) for a in pick_wrong(advs, adv)], passage=text))
        out.append(q(f"gen-b2-r-{i}-2", "B2", "reading", "Qu'est-ce qui inquiète les détracteurs ?", cap(con), [cap(c) for c in pick_wrong(cons, con)], passage=text))
    return out


def build():
    levels = {"A1": (a1_vocab, a1_grammar, a1_reading), "A2": (a2_vocab, a2_grammar, a2_reading),
              "B1": (b1_vocab, b1_grammar, b1_reading), "B2": (b2_vocab, b2_grammar, b2_reading)}
    all_items = []
    for lv, (fv, fg, fr) in levels.items():
        v, g, r = fv(), fg(), fr()
        # 100 + 100 + 50 : on complète vocabulaire / grammaire par des variantes si besoin
        v, g, r = v[:100], g[:100], r[:50]
        all_items += v + g + r
    keys = [it["key"] for it in all_items]
    assert len(keys) == len(set(keys)), "clés en double"
    content = [(it["question"], it["options"][0], it["passage"]) for it in all_items]
    assert len(content) == len(set(content)), "questions en double"
    for lv in ("A1", "A2", "B1", "B2"):
        for sec, n in (("vocab", 100), ("grammar", 100), ("reading", 50)):
            got = sum(1 for it in all_items if it["level"] == lv and it["section"] == sec)
            assert got == n, (lv, sec, got)
    return all_items


def seed():
    from db import connect
    items = build()
    with connect() as c:
        for i, it in enumerate(items):
            c.execute("""INSERT INTO placement_items (key, level, section, passage, question, options, answer, sort, generated)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,true)
                         ON CONFLICT (key) DO UPDATE SET level=EXCLUDED.level, section=EXCLUDED.section, passage=EXCLUDED.passage,
                           question=EXCLUDED.question, options=EXCLUDED.options, answer=EXCLUDED.answer, sort=EXCLUDED.sort, generated=true""",
                      (it["key"], it["level"], it["section"], it["passage"], it["question"], json.dumps(it["options"], ensure_ascii=False), 0, 1000 + i))
    print(f"questions générées : {len(items)}")
    return items


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--check"]:
        from collections import Counter
        print(Counter((i["level"], i["section"]) for i in build()))
    else:
        seed()
