
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path
from contextlib import closing


# ==========================================
# 1. KET NOI DATABASE
# ==========================================

DB_PATH = Path(__file__).resolve().parent / "chat.db"


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==========================================
# 2. DANG KY
# ==========================================

def register_user(username, password, display_name=None):
    username = username.strip()

    if not username or not password:
        raise ValueError(
            "Tên đăng nhập và mật khẩu không được để trống"
        )

    if display_name is None:
        display_name = username
    elif not isinstance(display_name, str) or not display_name.strip():
        raise ValueError("Tên hiển thị không được để trống")
    else:
        display_name = display_name.strip()

    salt = secrets.token_bytes(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    password_hash = (
        f"pbkdf2_sha256$600000${salt.hex()}${hashed.hex()}"
    )

    try:
        with closing(connect_db()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, display_name)
                    VALUES (?, ?, ?)
                    """,
                    (username, password_hash, display_name)
                )

                return cursor.lastrowid

    except sqlite3.IntegrityError as e:
        if "users.username" in str(e):
            raise ValueError(
                "Tên đăng nhập đã tồn tại"
            ) from e
        raise


# ==========================================
# 3. DANG NHAP
# ==========================================

def login_user(username, password):
    username = username.strip()

    with closing(connect_db()) as conn:
        user = conn.execute(
            """
            SELECT user_id, password_hash
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if user is None:
        return None

    user_id, stored_hash = user

    try:
        algorithm, rounds, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return None

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds)
        )

        if hmac.compare_digest(
            new_hash,
            bytes.fromhex(hash_hex)
        ):
            return user_id

    except (ValueError, TypeError, OverflowError):
        return None

    return None


# ==========================================
# 4. THONG TIN NGUOI DUNG
# ==========================================

def get_user_profile(user_id):
    """Return public account fields, or None if the user does not exist."""
    with closing(connect_db()) as conn:
        row = conn.execute(
            """
            SELECT user_id, username,
                   COALESCE(NULLIF(display_name, ''), username)
            FROM users WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

    if row is None:
        return None

    return dict(zip(("user_id", "username", "display_name"), row))


# ==========================================
# 5. LUU TIN NHAN
# ==========================================

def save_message(
    sender_id,
    content,
    receiver_id=None,
    room_id=None
):
    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "Nội dung tin nhắn không được để trống"
        )

    if receiver_id is None and room_id is None:
        raise ValueError(
            "Phải có người nhận hoặc phòng chat"
        )

    if receiver_id is not None and room_id is not None:
        raise ValueError(
            "Không thể gửi đồng thời tới người nhận và phòng"
        )

    with closing(connect_db()) as conn:
        with conn:

            # Kiem tra thanh vien truoc khi gui tin phong
            if room_id is not None:
                member = conn.execute(
                    """
                    SELECT 1
                    FROM room_members
                    WHERE room_id = ? AND user_id = ?
                    """,
                    (room_id, sender_id)
                ).fetchone()

                if member is None:
                    raise ValueError(
                        "Người gửi chưa tham gia phòng chat"
                    )

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
