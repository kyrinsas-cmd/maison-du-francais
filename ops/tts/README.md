# Audios d'écoute du test de niveau (synthèse vocale)

Générés le 2026-11-05 avec Piper 1.8 (pas de service payant). Rien de tout ça ne tourne sur le site.

```sh
D=$(mktemp -d); cd $D
python3 -m venv venv && ./venv/bin/pip install piper-tts lameenc
mkdir voices out
for m in siwis/medium/fr_FR-siwis-medium upmc/medium/fr_FR-upmc-medium; do for e in onnx onnx.json; do
  curl -sL -o voices/$(basename $m).$e "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/$m.$e"; done; done
sudo -u postgres psql -d maisondufrancais -Atc "SELECT json_agg(json_build_object('key',key,'level',level,'transcript',transcript))
  FROM placement_items WHERE section='listening'" | ./venv/bin/python ~/maisondufrancais/ops/tts/gen_listening.py $D
```

Pour une nouvelle question d'écoute, ajouter sa clé dans `VOICE` (voix + locuteur) avant de lancer.
Licences des voix : SIWIS CC-BY 4.0, UPMC CC-BY-SA 4.0 (citer « Piper, voix SIWIS et UPMC » si on mentionne les sources).
