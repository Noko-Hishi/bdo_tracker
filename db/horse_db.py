# -*- coding: utf-8 -*-
"""
horse.db の全操作
"""

import sqlite3
import datetime
from constants import HORSE_DB


def horse_init_db() -> None:
    conn = sqlite3.connect(HORSE_DB)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS horses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            caught_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def horse_add(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    now = datetime.datetime.now().isoformat(timespec="seconds")
    cur.execute("INSERT INTO horses (caught_at) VALUES (?)", (now,))
    conn.commit()


def horse_remove_last(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> bool:
    cur.execute("SELECT id FROM horses ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM horses WHERE id = ?", (row[0],))
        conn.commit()
        return True
    return False


def horse_get_today_count(cur: sqlite3.Cursor) -> int:
    today = datetime.date.today().isoformat()
    cur.execute("SELECT COUNT(*) FROM horses WHERE date(caught_at) = ?", (today,))
    return cur.fetchone()[0]


def horse_get_total_count(cur: sqlite3.Cursor) -> int:
    cur.execute("SELECT COUNT(*) FROM horses")
    return cur.fetchone()[0]


def horse_get_daily_counts(cur: sqlite3.Cursor) -> dict[str, int]:
    cur.execute("""
        SELECT date(caught_at) as day, COUNT(*) as cnt
        FROM horses GROUP BY day ORDER BY day ASC
    """)
    return {day: cnt for day, cnt in cur.fetchall()}
