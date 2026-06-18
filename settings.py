# -*- coding: utf-8 -*-
"""
設定ファイル (bdo_settings.json) の読み書き
"""

import json
import os
from constants import SETTINGS_FILE


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_spot": "", "goals": []}


def save_settings(s: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
