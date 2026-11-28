import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from database import db_service, init_db
from database.room_service import (
    create_room, join_room, get_room_members, get_room_history
)


class TestDisplayName(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db_path = Path(temp.name) / "chat.db"
        for module in (db_service, init_db):
            p = patch.object(module, "DB_PATH", self.db_path)
            p.start()
            self.addCleanup(p.stop)

    def test_same_display_name_and_legacy_api(self):
        init_db.init_database()
        a = db_service.register_user("nam1", "password1", " Nam ")
        b = db_service.register_user("nam2", "password2", "Nam")
        c = db_service.register_user("legacy", "password3")
        self.assertNotEqual(a, b)
        self.assertEqual(db_service.login_user("nam1", "password1"), a)
        self.assertEqual(db_service.login_user("nam2", "password2"), b)
        self.assertEqual(db_service.get_user_profile(a), {
            "user_id": a, "username": "nam1", "display_name": "Nam"
        })
        self.assertEqual(db_service.get_user_profile(b)["display_name"], "Nam")
        self.assertEqual(db_service.get_user_profile(c)["display_name"], "legacy")
        self.assertIsNone(db_service.get_user_profile(-1))
        with self.assertRaises(ValueError):
            db_service.register_user("nam1", "password4", "Other")
        with self.assertRaises(ValueError):
            db_service.register_user("blank", "password", "   ")
        room = create_room("test", a)
        join_room(room, b)
        db_service.save_message(a, "A", room_id=room)
        db_service.save_message(b, "B", room_id=room)
        db_service.save_message(a, "private", receiver_id=b)
        members = get_room_members(room, include_display_name=True)
        self.assertEqual([(m[0], m[1], m[3]) for m in members],
                         [(a, "nam1", "Nam"), (b, "nam2", "Nam")])
        self.assertEqual([len(m) for m in get_room_members(room)], [3, 3])
        history = get_room_history(room, a, include_display_name=True)
        self.assertEqual([(m[1], m[2], m[3], m[5]) for m in history],
                         [(a, "nam1", "A", "Nam"), (b, "nam2", "B", "Nam")])
        self.assertEqual([len(m) for m in get_room_history(room, a)], [5, 5])
        with closing(db_service.connect_db()) as conn:
            self.assertEqual(conn.execute(
                "SELECT sender_id, receiver_id FROM messages WHERE content = 'private'"
            ).fetchone(), (a, b))

    def test_migrate_old_database_without_data_loss(self):
        schema = init_db.SCHEMA_PATH.read_text(encoding="utf-8")
        old_schema = schema.replace("    display_name TEXT NOT NULL DEFAULT '',\n", "")
        self.assertNotEqual(schema, old_schema)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(old_schema)
            with conn:
                conn.execute("INSERT INTO users (user_id, username, password_hash) VALUES (7, 'old', 'old_hash')")
                conn.execute("INSERT INTO users (user_id, username, password_hash) VALUES (8, 'other', 'other_hash')")
                conn.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (7, 8, 'saved')")
        init_db.init_database()
        init_db.init_database()
        self.assertEqual(db_service.get_user_profile(7), {
            "user_id": 7, "username": "old", "display_name": "old"
        })
        with closing(db_service.connect_db()) as conn:
            self.assertEqual(conn.execute(
                "SELECT user_id, username, password_hash FROM users ORDER BY user_id"
            ).fetchall(), [(7, "old", "old_hash"), (8, "other", "other_hash")])
            self.assertEqual(conn.execute(
                "SELECT sender_id, receiver_id, content FROM messages"
            ).fetchone(), (7, 8, "saved"))
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        a = db_service.register_user("new", "password", "old")
        self.assertNotEqual(a, 7)
        self.assertEqual(db_service.get_user_profile(a)["display_name"], "old")


if __name__ == "__main__":
    unittest.main()
