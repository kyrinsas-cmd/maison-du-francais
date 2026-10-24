import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init():
    """Applique schema.sql (idempotent). Usage : python db.py init"""
    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), encoding="utf-8") as f:
        sql = f.read()
    with connect() as c:
        c.execute(sql)
    print("schéma OK")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["init"]:
        init()
    else:
        print("Usage : python db.py init")
