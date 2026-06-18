# -*- coding: utf-8 -*-
"""
狩場ランキングタブ（CustomTkinter版）
"""

import tkinter as tk
import customtkinter as ctk

from constants import C, _FONT_NAME, _F
from utils import fmt_money
from db.bdo_db import bdo_get_spot_ranking, bdo_get_available_months


class RankingTab:
    """金策 > ランキング タブ"""

    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("ランキング")
        self.tab = parent_notebook.tab("ランキング")
        self.tab.configure(fg_color=C["bg"])
        self._cached_data: list[dict] | None = None  # 前回のデータキャッシュ
        self._cached_month: str = ""
        self._build()

    def _build(self) -> None:
        tab = self.tab

        ff = ctk.CTkFrame(tab, fg_color=C["bg"]); ff.pack(pady=6, fill="x")
        ctk.CTkLabel(ff, text="表示期間:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=5)
        self.month_var   = tk.StringVar(value="全体")
        self.month_combo = ctk.CTkComboBox(ff, variable=self.month_var, width=130,
                                           fg_color=C["surface2"], border_color=C["border"],
                                           button_color=C["surface"], button_hover_color=C["accent"],
                                           text_color=C["fg"],
                                           font=_F(13),
                                           command=lambda _: self.refresh())
        self.month_combo.pack(side="left", padx=5)

        ctk.CTkLabel(ff, text="並び替え:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(14, 4))
        self.sort_var = tk.StringVar(value="hourly_off")
        for val, txt in [("earned", "累計稼ぎ"), ("hourly_off", "AG OFF時給"),
                         ("hourly_on", "AG ON時給"), ("hourly", "全体平均時給"),
                         ("max_hourly", "最高時給"), ("duration", "総プレイ時間")]:
            ctk.CTkRadioButton(ff, text=txt, variable=self.sort_var, value=val,
                               fg_color=C["accent"], hover_color=C["accent_dark"],
                               text_color=C["fg"],
                               font=_F(13),
                               command=self._sort_and_render).pack(side="left", padx=3)

        ctk.CTkButton(ff, text="更新", command=self.refresh, width=60,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack(side="left", padx=8)

        # スクロール領域
        self.scroll_frame = ctk.CTkScrollableFrame(tab, fg_color=C["bg"])
        self.scroll_frame.pack(fill="both", expand=True)

        # カード再利用用
        self._cards: list[dict] = []

    def refresh_filter(self) -> None:
        months = ["全体"] + bdo_get_available_months()
        self.month_combo.configure(values=months)
        cur = self.month_var.get() if self.month_var.get() in months else "全体"
        self.month_var.set(cur)
        self.month_combo.set(cur)

    def refresh(self) -> None:
        """DBから取得して描画"""
        mf = self.month_var.get()
        self._cached_data  = bdo_get_spot_ranking(mf)
        self._cached_month = mf
        self._sort_and_render()

    def _sort_and_render(self) -> None:
        """ソートだけして再描画（DB再取得なし）"""
        data = self._cached_data
        if data is None:
            self.refresh()
            return

        key = self.sort_var.get()
        data = sorted(data, key=lambda x: (x[key] or 0), reverse=True)

        # カード数が変わったら再構築
        if len(data) != len(self._cards):
            self._rebuild_cards(data)
        else:
            self._update_cards(data)

    def _rebuild_cards(self, data: list[dict]) -> None:
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self._cards.clear()

        if not data:
            ctk.CTkLabel(self.scroll_frame, text="データがありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(pady=40)
            return

        medal = ["🥇", "🥈", "🥉"]
        for rank, d in enumerate(data):
            card = ctk.CTkFrame(self.scroll_frame, fg_color=C["surface"],
                                border_color=C["border"], border_width=1)
            card.pack(fill="x", padx=24, pady=5)
            inner = ctk.CTkFrame(card, fg_color=C["surface"])
            inner.pack(fill="x", padx=14, pady=10)

            left = ctk.CTkFrame(inner, fg_color=C["surface"]); left.pack(side="left", fill="y")
            rank_icon = medal[rank] if rank < 3 else f"#{rank+1}"
            rank_lbl = ctk.CTkLabel(left, text=rank_icon, text_color=C["accent"],
                                    fg_color=C["surface"], font=_F(18, "bold"), width=36)
            rank_lbl.pack(side="left")
            spot_lbl = ctk.CTkLabel(left, text=d["spot"], text_color=C["fg"],
                                    fg_color=C["surface"], font=_F(13, "bold"), anchor="w")
            spot_lbl.pack(side="left", padx=6)

            right = ctk.CTkFrame(inner, fg_color=C["surface"]); right.pack(side="right")
            stat_labels: dict[str, ctk.CTkLabel] = {}
            for label in ("累計稼ぎ", "時給(AG ON)", "時給(AG OFF)", "最高時給", "総時間"):
                col = ctk.CTkFrame(right, fg_color=C["surface"]); col.pack(side="left", padx=10)
                ctk.CTkLabel(col, text=label, text_color=C["fg_dim"],
                             fg_color=C["surface"], font=_F(11)).pack()
                fg = C["accent"] if label != "総時間" else C["fg"]
                val_lbl = ctk.CTkLabel(col, text="", text_color=fg,
                                       fg_color=C["surface"], font=_F(13, "bold"))
                val_lbl.pack()
                stat_labels[label] = val_lbl

            self._cards.append({
                "rank_lbl": rank_lbl,
                "spot_lbl": spot_lbl,
                "stat_labels": stat_labels,
            })
        self._update_cards(data)

    def _update_cards(self, data: list[dict]) -> None:
        medal = ["🥇", "🥈", "🥉"]
        for rank, (d, card) in enumerate(zip(data, self._cards)):
            rank_icon = medal[rank] if rank < 3 else f"#{rank+1}"
            card["rank_lbl"].configure(text=rank_icon)
            card["spot_lbl"].configure(text=d["spot"])
            h, m  = divmod(int(d["duration"]), 60)
            dur_str = f"{h}h{m:02d}m" if h > 0 else f"{m}分"
            hon  = fmt_money(d["hourly_on"])  if d["hourly_on"]  is not None else "ー"
            hoff = fmt_money(d["hourly_off"]) if d["hourly_off"] is not None else "ー"
            vals = {
                "累計稼ぎ":    fmt_money(d["earned"]),
                "時給(AG ON)":  hon,
                "時給(AG OFF)": hoff,
                "最高時給":    fmt_money(d["max_hourly"]),
                "総時間":      dur_str,
            }
            for label, val in vals.items():
                card["stat_labels"][label].configure(text=val)
