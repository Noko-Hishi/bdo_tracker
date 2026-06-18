# -*- coding: utf-8 -*-
"""
タスクデータ (tasks_data.json) の読み書き・リセット処理
"""

import json
import os
import datetime
from constants import TASK_FILE


def task_load() -> dict:
    if os.path.exists(TASK_FILE):
        try:
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in ("tasks", "completed", "last_weekly_reset", "last_daily_reset"):
                data.setdefault(k, None if "reset" in k else [])
            # 週リセット曜日デフォルト: 3=木曜
            data.setdefault("weekly_reset_weekday", 3)
            return data
        except Exception:
            pass
    return {"tasks": [], "completed": [],
            "last_weekly_reset": None, "last_daily_reset": None,
            "weekly_reset_weekday": 3}


def task_save(data: dict) -> None:
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def task_check_daily_reset(data: dict) -> None:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if data["last_daily_reset"] == today_str:
        return
    # 完了済みのdailyタスクを未完了一覧に戻す
    existing = [t["text"] for t in data["tasks"] if t["type"] == "daily"]
    for t in data["completed"]:
        if t.get("type") == "daily" and t["text"] not in existing:
            r = t.copy()
            r.pop("completed_at", None)
            data["tasks"].append(r)
    data["completed"] = [t for t in data["completed"] if t.get("type") != "daily"]
    data["last_daily_reset"] = today_str
    task_save(data)


def task_check_weekly_reset(data: dict) -> None:
    today     = datetime.datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    last      = data.get("last_weekly_reset")
    reset_wd  = data.get("weekly_reset_weekday", 3)  # 0=月 ... 6=日

    def next_reset(d):
        """d の次のリセット曜日の日付を返す（当日含まず）"""
        days = (reset_wd - d.weekday()) % 7 or 7
        return d + datetime.timedelta(days=days)

    def last_reset(d):
        """d から見た直近過去のリセット曜日（当日含む）"""
        days = (d.weekday() - reset_wd) % 7
        return (d - datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    def _do_reset():
        """完了済みのweeklyを一覧に戻し、未完了のweeklyを完了済みに移す"""
        # 完了済みのweeklyを未完了一覧に戻す
        existing = [t["text"] for t in data["tasks"] if t["type"] == "weekly"]
        for t in data["completed"]:
            if t.get("type") == "weekly" and t["text"] not in existing:
                r = t.copy()
                r.pop("completed_at", None)
                data["tasks"].append(r)
        data["completed"] = [t for t in data["completed"] if t.get("type") != "weekly"]
        data["last_weekly_reset"] = today_str
        task_save(data)

    if last is None:
        if today.weekday() == reset_wd:
            _do_reset()
        else:
            data["last_weekly_reset"] = last_reset(today)
            task_save(data)
    else:
        last_dt = datetime.datetime.strptime(last, "%Y-%m-%d")
        if today.date() >= next_reset(last_dt).date():
            _do_reset()
