"""Importe des audios de leçons (fichiers <clé de la leçon>__<piste>.mp3) dans uploads/lessons/ et les relie à la leçon.
Usage (en tant qu'utilisateur du site, depuis le dossier app) : ./venv/bin/python lesson_audio_import.py <dossier> [--remplacer]
Sans --remplacer, une piste qui a déjà un fichier (envoyé par l'équipe) n'est pas touchée.
Même contrôle qu'à l'envoi dans l'admin : MP3 (signature) de 15 Mo au plus."""
import os
import secrets
import shutil
import sys

from psycopg.types.json import Jsonb

from db import connect

UPLOADS = os.path.join(os.environ.get("UPLOADS_DIR", "/var/www/maisondufrancais/uploads"), "lessons")


def is_mp3(path):
    with open(path, "rb") as f:
        head = f.read(4)
    return head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")


def run(folder, replace=False):
    os.makedirs(UPLOADS, exist_ok=True)
    done = skipped = 0
    with connect() as c:
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".mp3") or "__" not in name:
                continue
            key, slot = name[:-4].split("__", 1)
            path = os.path.join(folder, name)
            les = c.execute("SELECT id, content, audio_files FROM lessons WHERE key=%s", (key,)).fetchone()
            if not les or slot not in {a["id"] for a in les["content"].get("audio", [])}:
                print("inconnu :", name); skipped += 1; continue
            if not is_mp3(path) or os.path.getsize(path) > 15 * 1024 * 1024:
                print("refusé (pas un MP3 ou trop lourd) :", name); skipped += 1; continue
            files = dict(les["audio_files"] or {})
            if files.get(slot) and not replace:
                skipped += 1; continue
            new = f"l{les['id']}-{slot}-{secrets.token_hex(6)}.mp3"
            shutil.copyfile(path, os.path.join(UPLOADS, new))
            old = files.get(slot)
            files[slot] = new
            c.execute("UPDATE lessons SET audio_files=%s WHERE id=%s", (Jsonb(files), les["id"]))
            if old and old != new:
                try:
                    os.remove(os.path.join(UPLOADS, old))
                except FileNotFoundError:
                    pass
            done += 1
    print(f"audios : {done} importé(s), {skipped} ignoré(s)")


if __name__ == "__main__":
    run(sys.argv[1], "--remplacer" in sys.argv[2:])
