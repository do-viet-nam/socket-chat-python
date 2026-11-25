
import sqlite3
import tempfile
import unittest
import time
import threading
import os

from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from database import db_service
from database.room_service import create_room, join_room


NUM_USERS = int(os.getenv("TEST_USERS", "10"))
MESSAGES_PER_USER = 10


class TestDBConcurrency(unittest.TestCase):

    def test_concurrent_messages(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            test_db = Path(temp_dir) / "concurrency.db"

            schema_path = (
                Path(__file__).resolve().parents[1]
                / "database"
                / "schema.sql"
            )

            # Khoi tao database tam
            with closing(sqlite3.connect(test_db)) as conn:
                with conn:
                    conn.executescript(
                        schema_path.read_text(encoding="utf-8")
                    )

            with patch.object(db_service, "DB_PATH", test_db):

                # Tao danh sach tai khoan thu nghiem
                user_ids = []

                for i in range(NUM_USERS):
                    user_id = db_service.register_user(
                        f"concurrent_user_{i}",
                        "Test123456"
                    )

                    user_ids.append(user_id)

                # Tao phong chat thu nghiem
                room_id = create_room(
                    "concurrency_test_room",
                    user_ids[0]
                )

                # Them tat ca nguoi dung vao phong
                for user_id in user_ids[1:]:
                    join_room(room_id, user_id)

                # Dong bo cac luong truoc khi gui
                barrier = threading.Barrier(NUM_USERS)

                def send_messages(user_id):

                    barrier.wait(timeout=30)

                    latencies = []

                    for i in range(MESSAGES_PER_USER):

                        start = time.perf_counter()

                        db_service.save_message(
                            user_id,
                            f"User {user_id} - Message {i}",
                            room_id=room_id
                        )

                        elapsed = (
                            time.perf_counter() - start
                        ) * 1000

                        latencies.append(elapsed)

                    return latencies

                print("\nBAT DAU KIEM THU SQLITE")
                print(f"So nguoi dung: {NUM_USERS}")
                print(
                    f"So tin moi nguoi: {MESSAGES_PER_USER}"
                )

                start = time.perf_counter()

                # Chay nhieu luong dong thoi
                with ThreadPoolExecutor(
                    max_workers=NUM_USERS
                ) as executor:

                    results = list(
                        executor.map(
                            send_messages,
                            user_ids
                        )
                    )

                total_time = time.perf_counter() - start

                latencies = [
                    latency
                    for result in results
                    for latency in result
                ]

                # Kiem tra du lieu da luu
                with closing(
                    db_service.connect_db()
                ) as conn:

                    messages = conn.execute(
                        """
                        SELECT sender_id, content
                        FROM messages
                        WHERE room_id = ?
                        """,
                        (room_id,)
                    ).fetchall()

                expected = [
                    (
                        user_id,
                        f"User {user_id} - Message {i}"
                    )
                    for user_id in user_ids
                    for i in range(MESSAGES_PER_USER)
                ]

                expected_count = len(expected)
                actual_count = len(messages)

                throughput = actual_count / total_time
                avg_latency = sum(latencies) / len(latencies)

                print("\nKET QUA KIEM THU")
                print(f"So tin du kien: {expected_count}")
                print(f"So tin da luu: {actual_count}")
                print(f"Thoi gian: {total_time:.3f} giay")
                print(f"Throughput: {throughput:.2f} tin/giay")
                print(f"Do tre trung binh: {avg_latency:.2f} ms")
                print(f"Do tre lon nhat: {max(latencies):.2f} ms")

                # Kiem tra so luong va noi dung tin nhan
                self.assertEqual(
                    actual_count,
                    expected_count
                )

                self.assertCountEqual(
                    messages,
                    expected
                )

                print("PASS: Khong thieu hoac trung tin nhan")


if __name__ == "__main__":
    unittest.main()
