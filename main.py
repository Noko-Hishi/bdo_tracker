# -*- coding: utf-8 -*-
"""
BDO Tracker - 起動エントリポイント（CustomTkinter版）
"""

import sys
import os

# ── DPI設定 ──────────────────────────────────────────────────────────────
# CustomTkinter が起動時に内部で SetProcessDpiAwareness(1) を呼ぶため、
# ここでは何もしない。
# （元の SetProcessDpiAwareness(2) = Per-Monitor は CTk と干渉しジャギーの原因）
# ─────────────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from db.bdo_db import bdo_init_db
from db.horse_db import horse_init_db
from ui.app import App


if __name__ == "__main__":
    bdo_init_db()
    horse_init_db()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # CustomTkinter に DPI スケーリングを完全に委ねる
    # （deactivate_automatic_dpi_awareness() は呼ばない）

    root = ctk.CTk()
    App(root)
    root.mainloop()
