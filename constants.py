# -*- coding: utf-8 -*-
"""
定数定義：カラーパレット / フォント / ファイルパス（CustomTkinter版）
"""

import os
import sys
import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ─────────────────────────────────────────────
#  フォント設定
# ─────────────────────────────────────────────
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
_FONT_PATH = os.path.join(_BASE_DIR, "uzura_font.ttf")

if os.path.exists(_FONT_PATH):
    # matplotlib 用登録
    fm.fontManager.addfont(_FONT_PATH)
    _prop = fm.FontProperties(fname=_FONT_PATH)
    _FONT_NAME = _prop.get_name()

    # Windows GDI（Tkinter）用：フォントをプロセス内に一時登録する
    # これをしないと Tkinter はフォント名を解決できずシステムフォントにフォールバックし、
    # ジャギーになる。AddFontResourceEx の FR_PRIVATE(0x10) でプロセス終了時に自動解除。
    if sys.platform == "win32":
        import ctypes
        _gdi32 = ctypes.windll.gdi32
        _FR_PRIVATE = 0x10
        _gdi32.AddFontResourceExW(_FONT_PATH, _FR_PRIVATE, None)
else:
    _FONT_NAME = "Meiryo"  # フォールバック

matplotlib.rcParams["font.family"] = _FONT_NAME
matplotlib.rcParams["axes.unicode_minus"] = False


_font_cache: dict[tuple, ctk.CTkFont] = {}

def _F(size: int, weight: str = "normal") -> ctk.CTkFont:
    """CTkFont キャッシュ（同一 size/weight は同一インスタンスを返す）"""
    key = (size, weight)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=_FONT_NAME, size=size, weight=weight)
    return _font_cache[key]


# tkinter互換タプル（matplotlib 等で使う箇所向け）
FONT_UI  = (_FONT_NAME, 13)
FONT_BIG = (_FONT_NAME, 16, "bold")
FONT_MID = (_FONT_NAME, 14, "bold")
FONT_SML = (_FONT_NAME,  11)
FONT_HDR = (_FONT_NAME, 13, "bold")

# ─────────────────────────────────────────────
#  カラーパレット（CTk ウィジェットの fg_color 等に直接渡せる）
# ─────────────────────────────────────────────
C = {
    "bg":          "#2e2e2e",
    "surface":     "#3a3a3a",
    "surface2":    "#444444",
    "border":      "#555555",
    "fg":          "#f0f0f0",
    "fg_dim":      "#aaaaaa",
    "accent":      "#d4af37",
    "accent_dark": "#b8952d",
    "success":     "#4ec9b0",
    "error":       "#f48771",
    "plot_bg":     "#2e2e2e",
    "plot_line":   "#d4af37",
    "plot_red":    "#ff6666",
}

# ─────────────────────────────────────────────
#  ファイルパス
# ─────────────────────────────────────────────
BDO_DB        = "bdo_sessions.db"
HORSE_DB      = "horse.db"
SPOT_FILE     = "spot.json"
TASK_FILE     = "tasks_data.json"
SETTINGS_FILE = "bdo_settings.json"
