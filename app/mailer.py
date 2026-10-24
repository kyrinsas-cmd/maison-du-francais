"""Envoi d'e-mails par l'API Resend (même service que chine-france).

Configuration dans le .env (écrite par ops/set-mail.sh, jamais par un agent) :
  RESEND_API_KEY  clé API Resend limitée au domaine maisondufrancais.fr
  MAIL_FROM       expéditeur, ex. « Maison du français <no-reply@maisondufrancais.fr> »
  TEAM_EMAIL      adresse de l'équipe : alertes et notifications, et adresse de réponse des e-mails envoyés

MAIL_DISABLED=1 (variable d'environnement, utilisée par les tests) coupe tout envoi.
Sans clé, rien n'est envoyé : le sujet est écrit dans le journal, le site continue de fonctionner.
Les notifications à l'équipe ne contiennent pas de données personnelles : seulement un lien vers l'admin.
Jamais d'e-mail aux familles (leurs données restent en Chine).
"""
import logging
import os

log = logging.getLogger("mailer")


def _cfg():
    return os.environ.get("RESEND_API_KEY"), os.environ.get("MAIL_FROM", "Maison du français <no-reply@maisondufrancais.fr>"), os.environ.get("TEAM_EMAIL")


def configured():
    key, _, _ = _cfg()
    return bool(key)


def send(to, subject, text, reply_to=None):
    """Envoie un e-mail texte. Renvoie True si Resend l'a accepté."""
    key, sender, team = _cfg()
    if not to:
        return False
    if to.endswith("@example.test") or os.environ.get("MAIL_DISABLED") == "1":  # tests e2e : jamais d'envoi réel
        log.info("e-mail de test non envoyé : %s", subject)
        return False
    if not key:
        log.warning("RESEND_API_KEY absente, e-mail non envoyé : %s", subject)
        return False
    reply_to = reply_to or team
    try:
        import httpx
        r = httpx.post("https://api.resend.com/emails", timeout=10, headers={"Authorization": f"Bearer {key}"},
                       json={"from": sender, "to": [to], "subject": subject, "text": text, **({"reply_to": [reply_to]} if reply_to else {})})
        r.raise_for_status()
        return True
    except Exception as e:
        log.error("échec d'envoi (%s) : %s", subject, e)
        return False


def notify_team(subject, text):
    _, _, team = _cfg()
    if not team:
        log.warning("TEAM_EMAIL absente, notification non envoyée : %s", subject)
        return False
    return send(team, subject, text)


SIGN = "\n\n—\nMaison du français · 法语之家\nhttps://maisondufrancais.fr"


if __name__ == "__main__":
    # Test : python mailer.py test  → envoie un e-mail à TEAM_EMAIL
    import sys

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    logging.basicConfig(level=logging.INFO)
    if sys.argv[1:] == ["test"]:
        ok = notify_team("Test d'envoi — maisondufrancais.fr", "Si vous lisez ce message, l'envoi d'e-mails du site fonctionne." + SIGN)
        print("envoyé" if ok else "ÉCHEC : voir le message ci-dessus")
        sys.exit(0 if ok else 1)
    print("Usage : python mailer.py test")
