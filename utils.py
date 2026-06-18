# -*- coding: utf-8 -*-
"""
ユーティリティ：金額フォーマット
（CustomTkinter化によりapply_style()は不要のため削除）
"""

UNIT_MAP = {"K": 1_000, "M": 1_000_000, "G": 1_000_000_000, "T": 1_000_000_000_000}


def fmt_money(x: int | float) -> str:
    x = int(x or 0)
    if x >= 1_000_000_000: return f"{x/1_000_000_000:.1f}G"
    if x >= 1_000_000:     return f"{x/1_000_000:.1f}M"
    if x >= 1_000:         return f"{x/1_000:.1f}K"
    return str(x)


def parse_silver(text: str, unit: str) -> int | None:
    """'12.5' + 'G' → 12500000000  として返す。失敗時は None"""
    try:
        val = float(text.strip().replace(",", "").replace("_", ""))
        return int(val * UNIT_MAP.get(unit, 1))
    except (ValueError, TypeError):
        return None


def fmt_axis(x: float, _pos) -> str:
    if x >= 1_000_000_000: return f"{x/1_000_000_000:.1f}G"
    if x >= 1_000_000:     return f"{x/1_000_000:.1f}M"
    if x >= 1_000:         return f"{x/1_000:.1f}K"
    return f"{int(x)}"
