"""Banque de questions du test de niveau (questions originales, écrites pour Maison du français ; pas d'extraits du DELF).
Par niveau : 6 vocabulaire, 6 grammaire, 3 textes de lecture (2 questions chacun), 3 écoutes. Chaque test tire au hasard
2 vocabulaire + 2 grammaire + 1 texte (ses 2 questions) + 1 écoute (si un audio existe) : voir placement.items_for.
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

L1B = ("Aujourd'hui, c'est mercredi. Il n'y a pas d'école. Le matin, Sami va à la piscine avec son papa. "
       "L'après-midi, il fait un gâteau avec sa grand-mère.")
L1C = "Bonjour ! Je suis Emma. J'ai un chien. Il s'appelle Max. Il est petit et blanc. Il aime courir dans le parc."
L2B = ("Chère Lina, je suis en vacances à la mer avec ma famille. Il fait chaud et je me baigne tous les jours. "
       "Hier, nous avons visité un vieux château. Je rentre lundi prochain. Bises, Chloé")
L2C = ("Le club de théâtre du collège cherche de nouveaux élèves. Les répétitions ont lieu le jeudi de 17 h à 18 h 30. "
       "L'inscription est gratuite. Rendez-vous en salle 12 pour en savoir plus.")
L3B = ("Depuis septembre, la bibliothèque municipale prête aussi des jeux de société. Chaque famille peut emprunter deux jeux "
       "pendant trois semaines. Ce nouveau service a déjà beaucoup de succès : plus de 300 jeux ont été empruntés le premier mois.")
L3C = ("Thomas a passé un an en Espagne pour ses études. Au début, il avait du mal à comprendre ses professeurs, qui parlaient "
       "très vite. Mais grâce à ses colocataires espagnols, il a fait de grands progrès et il parle maintenant couramment.")
L4B = ("Le télétravail, longtemps marginal, s'est largement développé ces dernières années. S'il permet de gagner du temps sur "
       "les trajets, il peut aussi isoler les salariés et brouiller la frontière entre vie professionnelle et vie privée. "
       "Beaucoup d'entreprises optent donc pour une formule mixte.")
L4C = ("Si la lecture sur écran se répand, le livre papier résiste mieux qu'on ne l'avait prédit. De nombreux lecteurs disent "
       "mieux retenir ce qu'ils lisent sur papier et apprécier l'objet lui-même. Les deux supports semblent finalement plus "
       "complémentaires que concurrents.")

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
    # --- ajouts du 2026-10-25 (banque élargie : chaque test tire ses questions au hasard) ---
    ("a1-v3", "A1", "vocab", None, None, "Quand il fait beau, le ciel est ___.", ["bleu", "noir", "vert", "marron"], 0),
    ("a1-v4", "A1", "vocab", None, None, "On mange la soupe avec une ___.", ["cuillère", "chaise", "porte", "fenêtre"], 0),
    ("a1-v5", "A1", "vocab", None, None, "Il y a sept ___ dans une semaine.", ["jours", "mois", "heures", "ans"], 0),
    ("a1-v6", "A1", "vocab", None, None, "Mon père et ma mère sont mes ___.", ["parents", "frères", "amis", "voisins"], 0),
    ("a1-g3", "A1", "grammar", None, None, "Nous ___ à l'école.", ["allons", "allez", "vont", "vais"], 0),
    ("a1-g4", "A1", "grammar", None, None, "C'est ___ pomme rouge.", ["une", "un", "des", "du"], 0),
    ("a1-g5", "A1", "grammar", None, None, "Tu ___ un frère ?", ["as", "ai", "a", "avez"], 0),
    ("a1-g6", "A1", "grammar", None, None, "Ils ___ dans le jardin.", ["jouent", "joue", "jouons", "jouez"], 0),
    ("a1-r3", "A1", "reading", L1B, None, "Quel jour est-ce ?", ["Mercredi", "Lundi", "Samedi", "Dimanche"], 0),
    ("a1-r4", "A1", "reading", L1B, None, "Avec qui Sami fait-il un gâteau ?", ["Avec sa grand-mère", "Avec son papa", "Avec son ami", "Tout seul"], 0),
    ("a1-r5", "A1", "reading", L1C, None, "Comment s'appelle le chien ?", ["Max", "Emma", "Minou", "Sami"], 0),
    ("a1-r6", "A1", "reading", L1C, None, "De quelle couleur est le chien ?", ["Blanc", "Noir", "Marron", "Gris"], 0),
    ("a2-v3", "A2", "vocab", None, None, "Pour envoyer une lettre, je vais à la ___.", ["poste", "boulangerie", "piscine", "bibliothèque"], 0),
    ("a2-v4", "A2", "vocab", None, None, "J'ai mal à la tête : je vais chez le ___.", ["médecin", "boulanger", "coiffeur", "facteur"], 0),
    ("a2-v5", "A2", "vocab", None, None, "Il pleut : prends ton ___ !", ["parapluie", "maillot de bain", "short", "ballon"], 0),
    ("a2-v6", "A2", "vocab", None, None, "Le contraire de « facile », c'est « ___ ».", ["difficile", "rapide", "gentil", "content"], 0),
    ("a2-g3", "A2", "grammar", None, None, "Demain, je ___ mes grands-parents.", ["vais voir", "suis allé voir", "ai vu", "voyais"], 0),
    ("a2-g4", "A2", "grammar", None, None, "Ce matin, elle ___ levée à sept heures.", ["s'est", "a", "est", "s'a"], 0),
    ("a2-g5", "A2", "grammar", None, None, "Il y a beaucoup ___ monde dans le magasin.", ["de", "du", "des", "le"], 0),
    ("a2-g6", "A2", "grammar", None, None, "C'est la fille ___ habite à côté de chez moi.", ["qui", "que", "dont", "où"], 0),
    ("a2-r3", "A2", "reading", L2B, None, "Où est Chloé ?", ["À la mer", "À la montagne", "À la maison", "À l'école"], 0),
    ("a2-r4", "A2", "reading", L2B, None, "Qu'est-ce que Chloé a fait hier ?", ["Elle a visité un château", "Elle est rentrée chez elle", "Elle a pris le train", "Elle est allée au cinéma"], 0),
    ("a2-r5", "A2", "reading", L2C, None, "Quand ont lieu les répétitions ?", ["Le jeudi après les cours", "Le samedi matin", "Tous les jours", "Le dimanche"], 0),
    ("a2-r6", "A2", "reading", L2C, None, "Combien coûte l'inscription ?", ["Rien, elle est gratuite", "12 euros", "17 euros", "18 euros"], 0),
    ("b1-v3", "B1", "vocab", None, None, "Je suis arrivé en retard : j'ai ___ mon bus.", ["raté", "pris", "acheté", "vendu"], 0),
    ("b1-v4", "B1", "vocab", None, None, "Cette ville est très ___ : il y a toujours beaucoup de visiteurs étrangers.", ["touristique", "tranquille", "vide", "silencieuse"], 0),
    ("b1-v5", "B1", "vocab", None, None, "Pour ne pas oublier le rendez-vous, je le note dans mon ___.", ["agenda", "dictionnaire", "roman", "passeport"], 0),
    ("b1-v6", "B1", "vocab", None, None, "Le film était si ___ que je me suis endormi.", ["ennuyeux", "passionnant", "drôle", "effrayant"], 0),
    ("b1-g3", "B1", "grammar", None, None, "Quand j'étais petit, je ___ souvent chez ma tante.", ["allais", "irai", "vais", "irais"], 0),
    ("b1-g4", "B1", "grammar", None, None, "Il faut que tu ___ tes devoirs.", ["fasses", "fais", "feras", "faisais"], 0),
    ("b1-g5", "B1", "grammar", None, None, "J'ai décidé ___ apprendre le chinois.", ["d'", "à", "pour", "par"], 0),
    ("b1-g6", "B1", "grammar", None, None, "Si tu viens demain, je te ___ mes photos.", ["montrerai", "montrerais", "montrais", "ai montré"], 0),
    ("b1-r3", "B1", "reading", L3B, None, "Qu'est-ce que la bibliothèque propose de nouveau ?", ["Le prêt de jeux de société", "Des cours de français", "Des livres gratuits", "Un café"], 0),
    ("b1-r4", "B1", "reading", L3B, None, "Pendant combien de temps peut-on garder un jeu ?", ["Trois semaines", "Deux jours", "Un mois", "Une semaine"], 0),
    ("b1-r5", "B1", "reading", L3C, None, "Quelle difficulté Thomas a-t-il rencontrée au début ?", ["Comprendre ses professeurs", "Trouver un logement", "Se faire des amis", "Payer ses études"], 0),
    ("b1-r6", "B1", "reading", L3C, None, "Qui l'a aidé à progresser ?", ["Ses colocataires", "Ses professeurs", "Ses parents", "Un cours en ligne"], 0),
    ("b2-v3", "B2", "vocab", None, None, "Le Parlement a ___ une nouvelle loi sur l'environnement.", ["adopté", "adapté", "adoré", "adhéré"], 0),
    ("b2-v4", "B2", "vocab", None, None, "Son discours était si ___ que tout le monde a été convaincu.", ["persuasif", "hésitant", "confus", "ennuyeux"], 0),
    ("b2-v5", "B2", "vocab", None, None, "Avant de décider, il faut ___ le pour et le contre.", ["peser", "lever", "tirer", "jeter"], 0),
    ("b2-v6", "B2", "vocab", None, None, "Cette décision a eu des ___ importantes sur l'économie.", ["répercussions", "réparations", "répétitions", "réservations"], 0),
    ("b2-g3", "B2", "grammar", None, None, "Il est parti sans que nous ___ lui dire au revoir.", ["puissions", "pouvons", "pourrons", "pouvions"], 0),
    ("b2-g4", "B2", "grammar", None, None, "Si j'avais su, je ___ venu plus tôt.", ["serais", "suis", "serai", "étais"], 0),
    ("b2-g5", "B2", "grammar", None, None, "C'est la raison pour ___ il a démissionné.", ["laquelle", "lequel", "quoi", "qui"], 0),
    ("b2-g6", "B2", "grammar", None, None, "Après ___ terminé son travail, elle est sortie.", ["avoir", "avait", "ayant", "a"], 0),
    ("b2-r3", "B2", "reading", L4B, None, "Quel avantage du télétravail le texte cite-t-il ?", ["Gagner du temps sur les trajets", "Gagner plus d'argent", "Travailler moins", "Avoir plus de collègues"], 0),
    ("b2-r4", "B2", "reading", L4B, None, "Que choisissent beaucoup d'entreprises ?", ["Une formule mixte", "Le télétravail à 100 %", "L'interdiction du télétravail", "Des horaires plus longs"], 0),
    ("b2-r5", "B2", "reading", L4C, None, "Que dit le texte du livre papier ?", ["Il résiste mieux que prévu", "Il va disparaître", "Il coûte trop cher", "Il n'intéresse plus personne"], 0),
    ("b2-r6", "B2", "reading", L4C, None, "Quelle conclusion le texte propose-t-il ?", ["Les deux supports sont complémentaires", "L'écran va remplacer le papier", "Le papier est meilleur pour tout", "Il faut interdire les écrans"], 0),
    ("a1-l2", "A1", "listening", None, "J'ai deux sœurs et un frère. Ma sœur Julie a douze ans.", "Combien de sœurs a cette personne ?", ["Deux", "Une", "Trois", "Aucune"], 0),
    ("a1-l3", "A1", "listening", None, "Il est huit heures. Je prends mon petit-déjeuner : du pain et du lait.", "Qu'est-ce que cette personne boit ?", ["Du lait", "Du café", "Du jus d'orange", "De l'eau"], 0),
    ("a2-l2", "A2", "listening", None, "Bonjour, je voudrais deux croissants et une baguette, s'il vous plaît.", "Où est cette personne ?", ["Dans une boulangerie", "À la poste", "À la pharmacie", "Au cinéma"], 0),
    ("a2-l3", "A2", "listening", None, "Le cours de français commence à quatorze heures, dans la salle huit.", "Dans quelle salle est le cours ?", ["La salle huit", "La salle quatre", "La salle quatorze", "La salle deux"], 0),
    ("b1-l2", "B1", "listening", None, "En raison de travaux, la ligne 4 du métro sera fermée ce week-end. Des bus remplaceront les trains.", "Que se passe-t-il ce week-end ?", ["La ligne 4 est fermée", "Le métro est gratuit", "Il y a plus de trains", "Les bus sont en grève"], 0),
    ("b1-l3", "B1", "listening", None, "Je voudrais réserver une table pour quatre personnes samedi soir, vers vingt heures.", "Que veut faire cette personne ?", ["Réserver une table au restaurant", "Acheter des billets de train", "Louer une voiture", "Prendre rendez-vous chez le médecin"], 0),
    ("b2-l2", "B2", "listening", None, "Contrairement à une idée répandue, faire des pauses régulières pendant le travail aide à rester concentré.", "Selon ce message, qu'est-ce qui aide à rester concentré ?", ["Faire des pauses régulières", "Travailler sans s'arrêter", "Boire du café", "Travailler la nuit"], 0),
    ("b2-l3", "B2", "listening", None, "La réunion prévue jeudi est reportée à la semaine prochaine, faute de participants.", "Pourquoi la réunion est-elle reportée ?", ["Il n'y a pas assez de participants", "La salle n'est pas libre", "Le directeur est malade", "Il y a une grève"], 0),
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
