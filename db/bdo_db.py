# -*- coding: utf-8 -*-
"""
bdo_sessions.db の全操作
新規カラム:
  agris       INTEGER DEFAULT 0   (0=OFF, 1=ON)
  scroll_lv   TEXT    DEFAULT 'lv0'
  character   TEXT    DEFAULT ''
"""

import sqlite3
import datetime
from collections import defaultdict
from constants import BDO_DB


# ─────────────────────────────────────────────
#  初期化
# ─────────────────────────────────────────────
def bdo_init_db() -> None:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            spot        TEXT,
            trash_start INTEGER,
            trash_end   INTEGER,
            duration    INTEGER,
            trash_gained INTEGER,
            earned      INTEGER,
            created_at  TEXT,
            input_mode  TEXT DEFAULT 'trash',
            agris       INTEGER DEFAULT 0,
            scroll_lv   TEXT    DEFAULT 'lv0',
            character   TEXT    DEFAULT ''
        )
    """)
    # 既存 DB へのカラム追加（PRAGMA で確認してから ALTER）
    cur.execute("PRAGMA table_info(sessions)")
    cols = [c[1] for c in cur.fetchall()]
    for col, definition in [
        ("input_mode", "TEXT    DEFAULT 'trash'"),
        ("agris",      "INTEGER DEFAULT 0"),
        ("scroll_lv",  "TEXT    DEFAULT 'lv0'"),
        ("character",  "TEXT    DEFAULT ''"),
    ]:
        if col not in cols:
            cur.execute(f"ALTER TABLE sessions ADD COLUMN {col} {definition}")
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  追加
# ─────────────────────────────────────────────
def bdo_add_session(
    spot: str,
    trash_start: int,
    trash_end: int,
    duration: int,
    input_mode: str,
    spots: dict,
    agris: int = 0,
    scroll_lv: str = "lv0",
    character: str = "",
) -> tuple[int, int]:
    if input_mode == "silver":
        gained = 0
        earned = trash_end - trash_start
    else:
        gained = trash_end - trash_start
        earned = gained * spots.get(spot, 0)

    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO sessions
            (spot, trash_start, trash_end, duration, trash_gained, earned,
             created_at, input_mode, agris, scroll_lv, character)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (spot, trash_start, trash_end, duration, gained, earned,
          datetime.date.today().isoformat(), input_mode,
          agris, scroll_lv, character))
    conn.commit()
    conn.close()
    return gained, earned


# ─────────────────────────────────────────────
#  集計
# ─────────────────────────────────────────────
def bdo_get_total() -> int:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("SELECT SUM(earned) FROM sessions")
    v = cur.fetchone()[0] or 0
    conn.close()
    return v

def bdo_get_month_total(month: str) -> int:
    """指定月の合計稼ぎを返す"""
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("""
        SELECT SUM(earned) FROM sessions
        WHERE strftime('%Y-%m', created_at) = ?
    """, (month,))
    v = cur.fetchone()[0] or 0
    conn.close()
    return v

def bdo_get_available_months() -> list[str]:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT created_at FROM sessions ORDER BY created_at")
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    months: set[str] = set()
    for d in dates:
        try:
            o = datetime.datetime.strptime(d, "%Y-%m-%d")
            months.add(f"{o.year}-{o.month:02d}")
        except ValueError:
            pass
    return sorted(list(months), reverse=True)


def bdo_get_daily_data(month_filter: str) -> list:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    if month_filter == "全体":
        cur.execute("""
            SELECT created_at, SUM(duration), SUM(earned)
            FROM sessions GROUP BY created_at ORDER BY created_at
        """)
    else:
        cur.execute("""
            SELECT created_at, SUM(duration), SUM(earned)
            FROM sessions WHERE strftime('%Y-%m', created_at) = ?
            GROUP BY created_at ORDER BY created_at
        """, (month_filter,))
    rows = cur.fetchall()
    conn.close()
    return rows


def bdo_get_spot_ranking(month_filter: str) -> list[dict]:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    base = """
        SELECT spot,
               SUM(earned), SUM(duration), COUNT(*),
               MAX(CASE WHEN duration > 0
                        THEN CAST(earned AS REAL)/(duration/60.0) ELSE 0 END),
               -- アグリスONのみの平均時給
               SUM(CASE WHEN agris=1 THEN earned ELSE 0 END),
               SUM(CASE WHEN agris=1 THEN duration ELSE 0 END),
               -- アグリスOFFのみの平均時給
               SUM(CASE WHEN agris=0 THEN earned ELSE 0 END),
               SUM(CASE WHEN agris=0 THEN duration ELSE 0 END)
        FROM sessions
    """
    if month_filter != "全体":
        cur.execute(base + " WHERE strftime('%Y-%m', created_at) = ? GROUP BY spot",
                    (month_filter,))
    else:
        cur.execute(base + " GROUP BY spot")
    rows = cur.fetchall()
    conn.close()

    result = []
    for spot, earned, duration, count, max_hourly, \
        on_earned, on_dur, off_earned, off_dur in rows:
        hourly     = (earned   / (duration / 60)) if duration > 0 else 0
        hourly_on  = (on_earned  / (on_dur  / 60)) if on_dur  > 0 else None
        hourly_off = (off_earned / (off_dur / 60)) if off_dur > 0 else None
        result.append({
            "spot":       spot,
            "earned":     earned or 0,
            "duration":   duration or 0,
            "count":      count,
            "hourly":     hourly,
            "max_hourly": max_hourly or 0,
            "hourly_on":  hourly_on,   # Noneはデータなし
            "hourly_off": hourly_off,
        })
    return result


def bdo_get_sessions(limit: int = 50) -> list:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, spot, duration, earned, created_at, input_mode, trash_gained,
               agris, scroll_lv, character
        FROM sessions ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def bdo_get_daily_spot_data(month_filter: str) -> dict:
    """日付 -> {spot: earned} の辞書を返す"""
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    if month_filter == "全体":
        cur.execute("""
            SELECT created_at, spot, SUM(earned)
            FROM sessions GROUP BY created_at, spot ORDER BY created_at
        """)
    else:
        cur.execute("""
            SELECT created_at, spot, SUM(earned)
            FROM sessions WHERE strftime('%Y-%m', created_at) = ?
            GROUP BY created_at, spot ORDER BY created_at
        """, (month_filter,))
    rows = cur.fetchall()
    conn.close()
    result: dict = defaultdict(dict)
    for date, spot, earned in rows:
        result[date][spot] = earned
    return result


# ─────────────────────────────────────────────
#  セッション別時給グラフ用
# ─────────────────────────────────────────────
def bdo_get_session_hourly(
    month_filter: str,
    char_filter: str = "全員",
    agris_filter: str = "全て",
    scroll_filter: str = "全て",
) -> list[dict]:
    """
    セッションごとの時給を返す。
    戻り値: [{"label": "2025-04-10 #1", "hourly": …, "spot": …,
              "character": …, "agris": …, "scroll_lv": …,
              "date": …, "seq": …}, …]
    """
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()

    base = """
        SELECT id, spot, duration, earned, created_at,
               agris, scroll_lv, character
        FROM sessions
    """
    conditions = []
    params: list = []

    if month_filter != "全体":
        conditions.append("strftime('%Y-%m', created_at) = ?")
        params.append(month_filter)
    if char_filter != "全員":
        conditions.append("character = ?")
        params.append(char_filter)
    if agris_filter != "全て":
        conditions.append("agris = ?")
        params.append(1 if agris_filter == "ON" else 0)
    if scroll_filter != "全て":
        conditions.append("scroll_lv = ?")
        params.append(scroll_filter)

    if conditions:
        base += " WHERE " + " AND ".join(conditions)
    base += " ORDER BY created_at ASC, id ASC"

    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()

    # 日付ごとの連番を付与
    seq_counter: dict[str, int] = {}
    result = []
    for sid, spot, duration, earned, date, agris, scroll_lv, character in rows:
        seq_counter[date] = seq_counter.get(date, 0) + 1
        seq = seq_counter[date]
        hourly = (earned / (duration / 60)) if duration and duration > 0 else 0
        result.append({
            "label":     f"{date} #{seq}",
            "date":      date,
            "seq":       seq,
            "spot":      spot or "",
            "hourly":    hourly,
            "duration":  duration or 0,
            "earned":    earned or 0,
            "character": character or "",
            "agris":     agris or 0,
            "scroll_lv": scroll_lv or "lv0",
        })
    return result


def bdo_get_all_characters() -> list[str]:
    """セッションに登録されているキャラ名一覧（重複なし）"""
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT character FROM sessions WHERE character != '' ORDER BY character")
    names = [r[0] for r in cur.fetchall()]
    conn.close()
    return names


# ─────────────────────────────────────────────
#  更新 / 削除
# ─────────────────────────────────────────────
def bdo_delete_session(session_id: int) -> None:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def bdo_update_session(session_id: int, spot: str, duration: int, earned: int,
                       character: str = "", agris: int = 0, scroll_lv: str = "lv0") -> None:
    conn = sqlite3.connect(BDO_DB)
    cur  = conn.cursor()
    cur.execute("""
        UPDATE sessions SET spot=?, duration=?, earned=?,
               character=?, agris=?, scroll_lv=? WHERE id=?
    """, (spot, duration, earned, character, agris, scroll_lv, session_id))
    conn.commit()
    conn.close()
