"""Audios des leçons pilotes (lessons_seed.py) par synthèse vocale Piper, hors du site (2026-11-14, demande de l'utilisateur :
« les enregistrements, utilise les tiens pour l'instant »). À remplacer par la voix d'un professeur quand c'est possible.

Voix (comme les écoutes du test de niveau) : fr_FR-siwis-medium (CC-BY 4.0) pour Madame Martin ; fr_FR-upmc-medium
(CC-BY-SA 4.0), locutrice jessica pour les filles, locuteur pierre pour les garçons.
Texte de la leçon : chaque réplique une fois, avec la voix du personnage. Écoutes des exercices : SEGMENTS ci-dessous, lus deux
fois avec une pause, comme au DELF. Les lettres épelées sont écrites comme elles se prononcent (SAY).
Sortie : <dossier>/out/<clé>__<piste>.mp3, puis import :
  sudo install -d -m 755 /tmp/audios-lecons && sudo cp <dossier>/out/*.mp3 /tmp/audios-lecons/
  sudo -u maisondufrancais sh -c "cd /var/www/maisondufrancais/app && ./venv/bin/python lesson_audio_import.py /tmp/audios-lecons"
Mode d'emploi : ops/tts/README.md."""
import os
import sys

import lameenc
import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

WHO = {"Madame Martin": "martin", "Les enfants": "lili", "Léo": "leo", "Xiaoming": "leo", "Hugo": "leo", "Lili": "lili", "Chloé": "lili", "Amélie": "lili"}
SAY = {"X - I - A - O - M - I - N - G.": "ixe, i, a, o, aime, i, ène, gé.", "C - H - L - O - E accent aigu.": "cé, ache, elle, o, e accent aigu."}
SEGMENTS = {
    ("a1-u1-l1", "s1"): [("lili", "Bonsoir, madame !"), ("martin", "Bonsoir, Lili !")],
    ("a1-u1-l1", "s2"): [("lili", "Salut, Léo ! Ça va ?"), ("leo", "Ça va bien, merci !")],
    ("a1-u1-l2", "n1"): [("martin", "Bonjour ! Comment tu t'appelles ?"), ("leo", "Je m'appelle Hugo.")],
    ("a1-u1-l2", "n2"): [("leo", "C'est ma copine. Elle s'appelle Chloé.")],
    ("a1-u1-l3", "a1"): [("lili", "zède, o, e accent aigu. Zoé.")],
    ("a1-u1-l3", "a2"): [("martin", "ji.")],
    ("a1-u1-l4", "m1"): [("martin", "Léo, tu as quel âge ?"), ("leo", "J'ai huit ans.")],
    ("a1-u1-l4", "m2"): [("martin", "quatorze.")],
    ("a1-u1-l5", "p1"): [("leo", "Chloé, tu habites où ?"), ("lili", "J'habite à Paris.")],
    ("a1-u1-l5", "p2"): [("lili", "Je suis française.")],
    ("a1-u1-l6", "r1"): [("leo", "Je m'appelle Hugo. J'ai douze ans.")],
    ("a1-u1-l6", "r2"): [("lili", "Je m'appelle Léa. J'habite à Lyon, en France.")],
    ("a1-u1-politesse", "o1"): [("lili", "Madame, je ne comprends pas. Vous pouvez répéter, s'il vous plaît ?")],
    ("a1-u1-politesse", "o2"): [("lili", "Merci beaucoup, Xiaoming !"), ("leo", "De rien !")],
    ("a1-u1-langues", "g1"): [("lili", "Je m'appelle Chloé. Je parle français et anglais.")],
    ("a1-u1-langues", "g2"): [("martin", "Hugo, tu parles chinois ?"), ("leo", "Oui, un peu !")],
    ("a1-u1-quiestce", "q1"): [("martin", "Voici Xiaoming. Il a onze ans. Il habite à Shanghai.")],
    ("a1-u1-quiestce", "q2"): [("lili", "C'est mon amie. Elle s'appelle Zoé. Elle est française.")],
    ("a1-u1-jeux", "j1"): [("leo", "J'ai onze ans. Je suis chinois. J'habite à Shanghai. Qui suis-je ?")],
    ("a1-u1-jeux", "j2"): [("lili", "Je m'appelle Chloé. J'ai dix ans. J'habite à Lyon.")],
    ("a1-u1-sons", "v1"): [("martin", "tout.")], ("a1-u1-sons", "v2"): [("martin", "tu.")], ("a1-u1-sons", "v3"): [("martin", "Tu as dix ans ?")],
    ("a1-u1-projet", "k1"): [("lili", "Je m'appelle Amélie. Je suis canadienne. J'habite à Montréal.")],
    ("a1-u1-test", "t1"): [("leo", "Je m'appelle Hugo. J'ai sept ans.")],
    ("a1-u1-test", "t2"): [("martin", "Tu habites où ?"), ("leo", "J'habite à Pékin.")],
    ("a1-u1-test", "t3"): [("lili", "Bonsoir, madame !")],
    ("a1-u1-test", "t4"): [("lili", "elle, e accent aigu, a. Léa.")],
}
FIX = [("Xiaoming", "Chiaomine"), ("habites où", "habite où")]   # sinon la voix lit « Xiaoming » à l'anglaise et ajoute un [z]
SPEED = 1.2          # length_scale : > 1 = plus lent (A1)


def main(folder):
    from lessons_seed import LESSONS
    vs = {"siwis": PiperVoice.load(os.path.join(folder, "voices", "fr_FR-siwis-medium.onnx")),
          "upmc": PiperVoice.load(os.path.join(folder, "voices", "fr_FR-upmc-medium.onnx"))}
    voice = {"martin": ("siwis", None), "lili": ("upmc", 0), "leo": ("upmc", 1)}
    sr = 22050

    def say(who, text):
        name, spk = voice[who]
        cfg = SynthesisConfig(speaker_id=spk, length_scale=SPEED, noise_scale=0.6, noise_w_scale=0.7)
        text = SAY.get(text, text)
        for a, b in FIX:
            text = text.replace(a, b)
        return np.concatenate([c.audio_int16_array for c in vs[name].synthesize(text, cfg)])

    def sil(s):
        return np.zeros(int(sr * s), dtype=np.int16)

    os.makedirs(os.path.join(folder, "out"), exist_ok=True)
    for L in LESSONS:
        c = L["content"]
        for a in c.get("audio", []):
            slot = a["id"]
            if c.get("text", {}).get("audio") == slot:
                parts = [sil(0.5)]
                for line in c["text"]["lines"]:
                    parts += [say(WHO.get(line["who"], "martin"), line["t"]), sil(0.7)]
                pcm = np.concatenate(parts)
            else:
                once = np.concatenate([x for who, t in SEGMENTS[(L["key"], slot)] for x in (say(who, t), sil(0.8))])
                pcm = np.concatenate([sil(0.6), once, sil(2.5), once, sil(0.5)])
            enc = lameenc.Encoder(); enc.set_bit_rate(64); enc.set_in_sample_rate(sr); enc.set_channels(1); enc.set_quality(2)
            mp3 = enc.encode(pcm.tobytes()) + enc.flush()
            open(os.path.join(folder, "out", f"{L['key']}__{slot}.mp3"), "wb").write(mp3)
            print(L["key"], slot, f"{len(pcm) / sr:.1f} s", f"{len(mp3) // 1024} Ko")


if __name__ == "__main__":
    main(sys.argv[1])
