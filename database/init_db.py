
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_database():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql)

        # CREATE TABLE IF NOT EXISTS does not upgrade existing tables.
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
            if "display_name" not in columns:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"
                )
            conn.execute(
                "UPDATE users SET display_name = username WHERE display_name = ''"
            )

        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        print("Database created successfully!")
        print("Tables:")

        for (table_name,) in tables:
            print("-", table_name)

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
