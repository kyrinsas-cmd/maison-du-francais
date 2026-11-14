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

## Audios des leçons (2026-11-14)

`gen_lessons.py` : textes et écoutes des leçons de `lessons_seed.py`, mêmes voix (SIWIS pour Madame Martin, UPMC jessica / pierre
pour les élèves). Lettres épelées écrites comme elles se prononcent (`SAY`), corrections de lecture (`FIX` : « Xiaoming »
lu à l'anglaise par la voix, liaison fautive dans « habites où »).
```sh
./venv/bin/pip install "psycopg[binary]" python-dotenv      # en plus de piper-tts et lameenc
./venv/bin/python ~/maisondufrancais/ops/tts/gen_lessons.py $D
sudo install -d -m 755 /tmp/audios-lecons && sudo cp $D/out/*.mp3 /tmp/audios-lecons/
sudo -u maisondufrancais sh -c "cd /var/www/maisondufrancais/app && ./venv/bin/python lesson_audio_import.py /tmp/audios-lecons" && sudo rm -r /tmp/audios-lecons
```
