
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path
from contextlib import closing


# 1. DUONG DAN VA KET NOI DATABASE
DB_PATH = Path(__file__).resolve().parent / "chat.db"


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# 2. CHUC NANG DANG KY TAI KHOAN
def register_user(username, password):
    username = username.strip()

    if not username or not password:
        raise ValueError(
            "Tên đăng nhập và mật khẩu không được để trống"
        )

    # Tạo salt ngẫu nhiên
    salt = secrets.token_bytes(16)

    # Băm mật khẩu
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    password_hash = (
        f"pbkdf2_sha256$600000${salt.hex()}${hashed.hex()}"
    )

    # Lưu tài khoản vào SQLite
    try:
        with closing(connect_db()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, password_hash)
                )

                return cursor.lastrowid

    except sqlite3.IntegrityError as e:
        if "users.username" in str(e):
            raise ValueError(
                "Tên đăng nhập đã tồn tại"
            ) from e
        raise


# 3. CHUC NANG DANG NHAP TAI KHOAN
def login_user(username, password):
    username = username.strip()

    # Tìm tài khoản trong SQLite
    with closing(connect_db()) as conn:
        cursor = conn.execute(
            """
            SELECT user_id, password_hash
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        user = cursor.fetchone()

    # Không tìm thấy tài khoản
    if user is None:
        return None

    user_id, stored_hash = user

    try:
        # Tách thông tin mật khẩu đã băm
        algorithm, rounds, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return None

        # Băm lại mật khẩu vừa nhập
        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds)
        )

        # So sánh mật khẩu
        if hmac.compare_digest(
            new_hash,
            bytes.fromhex(hash_hex)
        ):
            return user_id

    except (ValueError, TypeError, OverflowError):
        return None

    return None


# 4. CHUC NANG LUU TIN NHAN
def save_message(
    sender_id,
    content,
    receiver_id=None,
    room_id=None
):
    # Kiểm tra nội dung tin nhắn
    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "Nội dung tin nhắn không được để trống"
        )

    # Phải là chat riêng HOẶC chat phòng
    if receiver_id is None and room_id is None:
        raise ValueError(
            "Phải có người nhận hoặc phòng chat"
        )

    if receiver_id is not None and room_id is not None:
        raise ValueError(
            "Không thể gửi đồng thời tới người nhận và phòng"
        )

    # Lưu tin nhắn vào SQLite
    with closing(connect_db()) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO messages
                (sender_id, receiver_id, room_id, content)
                VALUES (?, ?, ?, ?)
                """,
                (
                    sender_id,
                    receiver_id,
                    room_id,
                    content
                )
            )

            return cursor.lastrowid
