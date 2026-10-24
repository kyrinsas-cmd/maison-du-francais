"""Banque de questions du test de niveau (questions originales, écrites pour Maison du français ; pas d'extraits du DELF).
Relancer = mise à jour par clé (python placement_seed.py) ; n'efface pas les audios déjà envoyés.
Les questions d'écoute (listening) ne sont posées qu'une fois leur audio envoyé dans l'admin (transcription fournie).
"""
import json

from db import connect

L1 = "Je m'appelle Léa. J'ai huit ans. J'habite à Lyon avec mes parents et mon petit frère, Tom. J'aime le chocolat et le football."
L2 = ("Samedi, Paul s'est levé tôt. Il a pris le train pour aller voir sa grand-mère à la campagne. Ils ont fait une tarte aux pommes "
      "ensemble. Paul est rentré dimanche soir, fatigué mais content.")
L3 = ("Au collège de Marie, les élèves ne peuvent plus utiliser leur téléphone pendant la journée. Le directeur pense que cela les aide "
      "à se concentrer. Certains parents ne sont pas d'accord : ils veulent pouvoir joindre leurs enfants en cas de problème.")
L4 = ("De plus en plus de villes européennes limitent la place de la voiture dans leur centre. Les partisans de ces mesures mettent en "
      "avant la baisse de la pollution et le retour des piétons. Leurs opposants craignent que les commerçants perdent des clients venus "
      "de l'extérieur, qui n'ont pas d'autre moyen de transport.")

# (clé, niveau, section, passage, transcription, question, réponses, index de la bonne réponse)
ITEMS = [
    ("a1-v1", "A1", "vocab", None, None, "Le chat est un ___.", ["animal", "fruit", "jour", "couleur"], 0),
    ("a1-v2", "A1", "vocab", None, None, "Lundi, mardi, ___, jeudi.", ["mercredi", "dimanche", "janvier", "matin"], 0),
    ("a1-g1", "A1", "grammar", None, None, "Je ___ dix ans.", ["ai", "suis", "as", "est"], 0),
    ("a1-g2", "A1", "grammar", None, None, "Elle ___ française.", ["est", "a", "es", "ont"], 0),
    ("a1-r1", "A1", "reading", L1, None, "Où habite Léa ?", ["À Lyon", "À Paris", "À Pékin", "À Nice"], 0),
    ("a1-r2", "A1", "reading", L1, None, "Qui est Tom ?", ["Son petit frère", "Son père", "Son ami", "Son chat"], 0),
    ("a2-v1", "A2", "vocab", None, None, "On achète du pain à la ___.", ["boulangerie", "pharmacie", "poste", "piscine"], 0),
    ("a2-v2", "A2", "vocab", None, None, "Il fait très froid : je mets mon ___.", ["manteau", "maillot de bain", "short", "tee-shirt"], 0),
    ("a2-g1", "A2", "grammar", None, None, "Hier, nous ___ au cinéma.", ["sommes allés", "allons", "irons", "aller"], 0),
    ("a2-g2", "A2", "grammar", None, None, "Tu veux des pommes ? — Oui, j'___ veux trois.", ["en", "y", "le", "les"], 0),
    ("a2-r1", "A2", "reading", L2, None, "Pourquoi Paul a-t-il pris le train ?", ["Pour voir sa grand-mère", "Pour aller à l'école", "Pour acheter des pommes", "Pour faire du sport"], 0),
    ("a2-r2", "A2", "reading", L2, None, "Quand Paul est-il rentré ?", ["Dimanche soir", "Samedi matin", "Lundi matin", "Samedi soir"], 0),
    ("b1-v1", "B1", "vocab", None, None, "Il a ___ son examen : il est très content.", ["réussi", "raté", "oublié", "perdu"], 0),
    ("b1-v2", "B1", "vocab", None, None, "Pour trouver le sens d'un mot, j'utilise un ___.", ["dictionnaire", "agenda", "calendrier", "annuaire"], 0),
    ("b1-g1", "B1", "grammar", None, None, "Si j'avais le temps, je ___ plus souvent.", ["lirais", "lis", "lirai", "ai lu"], 0),
    ("b1-g2", "B1", "grammar", None, None, "C'est le livre ___ je t'ai parlé.", ["dont", "que", "qui", "où"], 0),
    ("b1-r1", "B1", "reading", L3, None, "Pourquoi le directeur a-t-il pris cette décision ?", ["Pour aider les élèves à se concentrer", "Parce que les téléphones coûtent cher", "Pour faire plaisir aux parents", "Parce que les élèves l'ont demandé"], 0),
    ("b1-r2", "B1", "reading", L3, None, "Que veulent certains parents ?", ["Pouvoir joindre leurs enfants", "Interdire les ordinateurs", "Changer de collège", "Supprimer les cours du soir"], 0),
    ("b2-v1", "B2", "vocab", None, None, "Malgré la pluie, le match a été ___.", ["maintenu", "annulé", "reporté", "supprimé"], 0),
    ("b2-v2", "B2", "vocab", None, None, "Cette solution présente un ___ : elle coûte trop cher.", ["inconvénient", "avantage", "atout", "bénéfice"], 0),
    ("b2-g1", "B2", "grammar", None, None, "Bien qu'il ___ fatigué, il a continué à travailler.", ["soit", "est", "était", "sera"], 0),
    ("b2-g2", "B2", "grammar", None, None, "Je regrette que tu ne ___ pas venu.", ["sois", "es", "étais", "seras"], 0),
    ("b2-r1", "B2", "reading", L4, None, "Quel argument avancent les partisans de ces mesures ?", ["La baisse de la pollution", "Plus de clients pour les commerces", "Des parkings moins chers", "Des trajets plus rapides en voiture"], 0),
    ("b2-r2", "B2", "reading", L4, None, "Que craignent les opposants ?", ["Que les commerçants perdent des clients", "Que la pollution augmente", "Que les piétons soient trop nombreux", "Que les transports deviennent gratuits"], 0),
    # Écoute : posées seulement quand l'équipe a envoyé l'audio (lecture de la transcription)
    ("a1-l1", "A1", "listening", None, "Bonjour ! Je m'appelle Hugo. J'ai neuf ans et j'adore les chiens.", "Qu'est-ce que Hugo adore ?", ["Les chiens", "Les chats", "Le football", "La musique"], 0),
    ("a2-l1", "A2", "listening", None, "Attention, le train pour Lyon partira à dix heures quinze, voie trois.", "À quelle heure part le train ?", ["10 h 15", "10 h 30", "3 h", "13 h 15"], 0),
    ("b1-l1", "B1", "listening", None, "Pour le spectacle de fin d'année, nous cherchons des parents volontaires pour aider à installer la salle vendredi après-midi.", "Que cherche l'école ?", ["Des parents pour aider", "Des élèves pour chanter", "Une nouvelle salle", "Des billets"], 0),
    ("b2-l1", "B2", "listening", None, "Pour notre bibliothécaire, lire un peu chaque jour pour le plaisir est plus utile que de lire beaucoup une fois par mois.", "Que conseille la bibliothécaire ?", ["Lire un peu chaque jour", "Lire beaucoup une fois par mois", "Ne lire que pour l'école", "Acheter plus de livres"], 0),
]


def seed():
    with connect() as c:
        for i, (key, lv, sec, passage, tr, q, opts, ans) in enumerate(ITEMS):
            c.execute("""INSERT INTO placement_items (key, level, section, passage, transcript, question, options, answer, sort)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                         ON CONFLICT (key) DO UPDATE SET level=EXCLUDED.level, section=EXCLUDED.section, passage=EXCLUDED.passage,
                           transcript=EXCLUDED.transcript, question=EXCLUDED.question, options=EXCLUDED.options, answer=EXCLUDED.answer,
                           sort=EXCLUDED.sort""",
                      (key, lv, sec, passage, tr, q, json.dumps(opts, ensure_ascii=False), ans, i))
    print(f"banque de questions : {len(ITEMS)} questions")


if __name__ == "__main__":
    seed()
