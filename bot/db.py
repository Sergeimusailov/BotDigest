import sqlite3
from contextlib import closing

from . import config


def init_db() -> None:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


def add_entry(user_id: int, user_name: str, text: str) -> None:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO news (user_id, user_name, text) VALUES (?, ?, ?)",
            (user_id, user_name, text),
        )
        conn.commit()


def get_all_entries() -> list[tuple[str, str]]:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        rows = conn.execute(
            "SELECT user_name, text FROM news ORDER BY user_id, id"
        ).fetchall()
    return rows


def clear_entries() -> None:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        conn.execute("DELETE FROM news")
        conn.commit()


def get_entries_for_user(user_id: int) -> list[str]:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        rows = conn.execute(
            "SELECT text FROM news WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
    return [row[0] for row in rows]


def delete_all_for_user(user_id: int) -> int:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        cursor = conn.execute("DELETE FROM news WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount


def delete_last_for_user(user_id: int) -> bool:
    with closing(sqlite3.connect(config.DB_PATH)) as conn:
        row = conn.execute(
            "SELECT id FROM news WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM news WHERE id = ?", (row[0],))
        conn.commit()
        return True
