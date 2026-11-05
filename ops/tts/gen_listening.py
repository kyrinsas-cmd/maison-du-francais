"""Audios des questions d'écoute du test de niveau, par synthèse vocale Piper (hors du site, une seule fois).

Voix : fr_FR-siwis-medium (CC-BY 4.0) et fr_FR-upmc-medium, locuteurs jessica / pierre (CC-BY-SA 4.0),
https://huggingface.co/rhasspy/piper-voices. Chaque texte est lu 2 fois (comme au DELF), plus lentement en A1/A2.
Mode d'emploi : ops/tts/README.md. Les MP3 sortent dans <dossier>/out/<clé>.mp3, puis on les envoie
dans /admin/tests/questions (bouton « Envoyer l'audio ») ou comme en 2026-11-05 (voir NOTES).
"""
import json, subprocess, sys
import numpy as np, lameenc
from piper import PiperVoice
from piper.config import SynthesisConfig
D = sys.argv[1]
V = {"siwis": PiperVoice.load(f"{D}/voices/fr_FR-siwis-medium.onnx"), "upmc": PiperVoice.load(f"{D}/voices/fr_FR-upmc-medium.onnx")}
SPEED = {"A1": 1.25, "A2": 1.15, "B1": 1.05, "B2": 1.0}   # length_scale : > 1 = plus lent
VOICE = {"a1-l1": ("upmc", 1), "a1-l2": ("siwis", None), "a1-l3": ("upmc", 0), "a2-l1": ("siwis", None), "a2-l2": ("upmc", 1), "a2-l3": ("upmc", 0),
         "b1-l1": ("siwis", None), "b1-l2": ("upmc", 1), "b1-l3": ("upmc", 0), "b2-l1": ("upmc", 0), "b2-l2": ("siwis", None), "b2-l3": ("upmc", 1)}
items = json.load(sys.stdin)
for it in items:
    vname, spk = VOICE[it["key"]]
    v = V[vname]; sr = v.config.sample_rate
    cfg = SynthesisConfig(speaker_id=spk, length_scale=SPEED[it["level"]], noise_scale=0.6, noise_w_scale=0.7)
    once = np.concatenate([c.audio_int16_array for c in v.synthesize(it["transcript"], cfg)])
    sil = lambda s: np.zeros(int(sr * s), dtype=np.int16)
    pcm = np.concatenate([sil(0.6), once, sil(2.5), once, sil(0.8)])
    enc = lameenc.Encoder(); enc.set_bit_rate(64); enc.set_in_sample_rate(sr); enc.set_channels(1); enc.set_quality(2)
    mp3 = enc.encode(pcm.tobytes()) + enc.flush()
    open(f"{D}/out/{it['key']}.mp3", "wb").write(mp3)
    print(it["key"], vname, spk, f"{len(pcm)/sr:.1f}s", f"{len(mp3)//1024} Ko")
