
from contextlib import closing
from database.db_service import connect_db


# ==========================================
# 1. TAO PHONG CHAT
# ==========================================

def create_room(name, creator_id):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tên phòng không được để trống")

    name = name.strip()

    with closing(connect_db()) as conn:
        with conn:
            user = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (creator_id,)
            ).fetchone()

            if user is None:
                raise ValueError("Người tạo không tồn tại")

            existing = conn.execute(
                "SELECT 1 FROM rooms WHERE name = ? COLLATE NOCASE",
                (name,)
            ).fetchone()

            if existing is not None:
                raise ValueError("Tên phòng đã tồn tại")

            cursor = conn.execute(
                """
                INSERT INTO rooms (name, created_by)
                VALUES (?, ?)
                """,
                (name, creator_id)
            )

            room_id = cursor.lastrowid

            # Nguoi tao tu dong tham gia
            conn.execute(
                """
                INSERT INTO room_members (room_id, user_id)
                VALUES (?, ?)
                """,
                (room_id, creator_id)
            )

            return room_id


# ==========================================
# 2. XEM DANH SACH PHONG
# ==========================================

def list_rooms():
    with closing(connect_db()) as conn:
        return conn.execute(
            """
            SELECT room_id, name, created_by, created_at
            FROM rooms
            ORDER BY room_id
            """
        ).fetchall()


# ==========================================
# 3. THAM GIA PHONG
# ==========================================

def join_room(room_id, user_id):
    with closing(connect_db()) as conn:
        with conn:
            room = conn.execute(
                "SELECT 1 FROM rooms WHERE room_id = ?",
                (room_id,)
            ).fetchone()

            if room is None:
                raise ValueError("Phòng chat không tồn tại")

            user = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if user is None:
                raise ValueError("Người dùng không tồn tại")

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO room_members
                (room_id, user_id)
                VALUES (?, ?)
                """,
                (room_id, user_id)
            )

            return cursor.rowcount > 0


# ==========================================
# 4. ROI PHONG CHAT
# ==========================================

def leave_room(room_id, user_id):
    with closing(connect_db()) as conn:
        with conn:
            cursor = conn.execute(
                """
                DELETE FROM room_members
                WHERE room_id = ? AND user_id = ?
                """,
                (room_id, user_id)
            )

            return cursor.rowcount > 0


# ==========================================
# 5. XEM THANH VIEN PHONG
# ==========================================

def get_room_members(room_id, *, include_display_name=False):
    """Keep legacy tuple fields; optionally append display_name."""
    extra = ", COALESCE(NULLIF(u.display_name, ''), u.username)" if include_display_name else ""
    with closing(connect_db()) as conn:
        return conn.execute(
            f"""
            SELECT u.user_id, u.username, rm.joined_at{extra}
            FROM room_members AS rm
            JOIN users AS u ON rm.user_id = u.user_id
            WHERE rm.room_id = ?
            ORDER BY u.user_id
            """,
            (room_id,)
        ).fetchall()


# ==========================================
# 6. LAY LICH SU TIN NHAN
# ==========================================

def get_room_history(room_id, user_id, limit=20, *, include_display_name=False):
    """Keep legacy tuple fields; optionally append sender display_name."""
    extra = ", COALESCE(NULLIF(u.display_name, ''), u.username)" if include_display_name else ""
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError(
            "Số tin nhắn phải nằm trong khoảng 1 đến 50"
        )

    with closing(connect_db()) as conn:
        member = conn.execute(
            """
            SELECT 1
            FROM room_members
            WHERE room_id = ? AND user_id = ?
            """,
            (room_id, user_id)
        ).fetchone()

        if member is None:
            raise ValueError(
                "Người dùng chưa tham gia phòng chat"
            )

        messages = conn.execute(
            f"""
            SELECT
                m.message_id,
                m.sender_id,
                u.username,
                m.content,
                m.sent_at{extra}
            FROM messages AS m
            JOIN users AS u
                ON m.sender_id = u.user_id
            WHERE m.room_id = ?
            ORDER BY m.message_id DESC
            LIMIT ?
            """,
            (room_id, limit)
        ).fetchall()

        messages.reverse()
        return messages
