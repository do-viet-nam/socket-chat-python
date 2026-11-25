
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch

from database import db_service
from database.room_service import (
    create_room,
    get_room_history
)


class TestRoomHistory(unittest.TestCase):

    def test_history_limit(self):

        # Tao database tam de kiem thu
        with tempfile.TemporaryDirectory() as temp_dir:

            test_db = Path(temp_dir) / "test_chat.db"

            schema_path = (
                Path(__file__).resolve().parents[1]
                / "database"
                / "schema.sql"
            )

            # Khoi tao cac bang
            with closing(sqlite3.connect(test_db)) as conn:
                with conn:
                    conn.executescript(
                        schema_path.read_text(encoding="utf-8")
                    )

            # Su dung database tam thay cho chat.db
            with patch.object(db_service, "DB_PATH", test_db):

                user_id = db_service.register_user(
                    "history_test_user",
                    "Test123456"
                )

                room_id = create_room(
                    "history_test_room",
                    user_id
                )

                # Tao 60 tin nhan
                for i in range(1, 61):
                    db_service.save_message(
                        user_id,
                        f"Tin nhan {i}",
                        room_id=room_id
                    )

                print("\nDa tao 60 tin nhan.")

                # Test 1: Lay 20 tin nhan gan nhat
                history_20 = get_room_history(
                    room_id, user_id, 20
                )

                self.assertEqual(len(history_20), 20)
                self.assertEqual(
                    history_20[0][3], "Tin nhan 41"
                )
                self.assertEqual(
                    history_20[-1][3], "Tin nhan 60"
                )

                print("PASS: Lay dung 20 tin nhan gan nhat")

                # Test 2: Lay 50 tin nhan gan nhat
                history_50 = get_room_history(
                    room_id, user_id, 50
                )

                self.assertEqual(len(history_50), 50)
                self.assertEqual(
                    history_50[0][3], "Tin nhan 11"
                )
                self.assertEqual(
                    history_50[-1][3], "Tin nhan 60"
                )

                print("PASS: Lay dung 50 tin nhan gan nhat")

                # Test 3: Khong cho phep lay 51 tin
                with self.assertRaises(ValueError):
                    get_room_history(
                        room_id, user_id, 51
                    )

                print("PASS: Tu choi gioi han 51 tin nhan")


if __name__ == "__main__":
    unittest.main()
