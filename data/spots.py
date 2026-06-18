# -*- coding: utf-8 -*-
"""
狩場スポット (spot.json) の読み書き
"""

import json
import os
from constants import SPOT_FILE


def load_spots() -> dict:
    if os.path.exists(SPOT_FILE):
        with open(SPOT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_spots(spots: dict) -> None:
    with open(SPOT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
