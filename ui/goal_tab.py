# -*- coding: utf-8 -*-
"""
目標金額タブ（CustomTkinter版）
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from constants import C, _FONT_NAME, _F
from utils import fmt_money, parse_silver
from settings import save_settings


class GoalTab:
    def __init__(self, parent_frame: ctk.CTkFrame, app):
        self.app = app
        self.tab = parent_frame
        self.tab.configure(fg_color=C["bg"])
        self._goal_widgets: list[dict] = []  # カード再利用用
        self._build()

    def _build(self) -> None:
        tab = self.tab

        # ── 手持ち資産カード ────────────────────────
        asset_card = ctk.CTkFrame(tab, fg_color=C["surface"], border_color=C["accent"], border_width=1)
        asset_card.pack(fill="x", padx=20, pady=(14, 6))
        ac = ctk.CTkFrame(asset_card, fg_color=C["surface"])
        ac.pack(padx=16, pady=10, fill="x")

        ctk.CTkLabel(ac, text="💰 現在の手持ち資産", text_color=C["accent"],
                     fg_color=C["surface"],
                     font=_F(13, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        ctk.CTkLabel(ac, text="金額", text_color=C["fg"], fg_color=C["surface"],
                     font=_F(13)).grid(row=1, column=0, sticky="w", padx=(0, 6))
        self.asset_entry = ctk.CTkEntry(ac, width=130,
                                        fg_color=C["surface2"], border_color=C["border"],
                                        text_color=C["fg"],
                                        font=_F(13))
        self.asset_entry.grid(row=1, column=1, padx=(0, 4))

        self.asset_unit_var = tk.StringVar(value="G")
        ctk.CTkComboBox(ac, variable=self.asset_unit_var, values=["K", "M", "G", "T"], width=60,
                        fg_color=C["surface2"], border_color=C["border"],
                        button_color=C["surface"], button_hover_color=C["accent"],
                        text_color=C["fg"],
                        font=_F(13),
                        state="readonly").grid(row=1, column=2, padx=(0, 12))

        ctk.CTkButton(ac, text="設定", command=self._asset_set,
                      fg_color=C["accent"], hover_color=C["accent_dark"],
                      text_color="black", width=70,
                      font=_F(13, "bold")).grid(
            row=1, column=3, padx=(0, 16))

        self.asset_display_lbl = ctk.CTkLabel(ac, text="", text_color=C["fg"],
                                               fg_color=C["surface"],
                                               font=_F(16, "bold"))
        self.asset_display_lbl.grid(row=1, column=4)

        # ── 目標追加カード ──────────────────────────
        goal_card = ctk.CTkFrame(tab, fg_color=C["surface"], border_color=C["border"], border_width=1)
        goal_card.pack(fill="x", padx=20, pady=(0, 10))
        ga = ctk.CTkFrame(goal_card, fg_color=C["surface"])
        ga.pack(padx=16, pady=10, fill="x")

        ctk.CTkLabel(ga, text="🎯 目標を追加", text_color=C["fg"],
                     fg_color=C["surface"],
                     font=_F(13, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        ctk.CTkLabel(ga, text="目標名", text_color=C["fg"], fg_color=C["surface"],
                     font=_F(13)).grid(row=1, column=0, sticky="w", padx=(0, 6))
        self.goal_name_entry = ctk.CTkEntry(ga, width=180,
                                            fg_color=C["surface2"], border_color=C["border"],
                                            text_color=C["fg"],
                                            font=_F(13))
        self.goal_name_entry.grid(row=1, column=1, padx=(0, 14))

        ctk.CTkLabel(ga, text="目標金額", text_color=C["fg"], fg_color=C["surface"],
                     font=_F(13)).grid(row=1, column=2, sticky="w", padx=(0, 6))
        self.goal_amount_entry = ctk.CTkEntry(ga, width=120,
                                              fg_color=C["surface2"], border_color=C["border"],
                                              text_color=C["fg"],
                                              font=_F(13))
        self.goal_amount_entry.grid(row=1, column=3, padx=(0, 4))

        self.goal_unit_var = tk.StringVar(value="G")
        ctk.CTkComboBox(ga, variable=self.goal_unit_var, values=["K", "M", "G", "T"], width=60,
                        fg_color=C["surface2"], border_color=C["border"],
                        button_color=C["surface"], button_hover_color=C["accent"],
                        text_color=C["fg"],
                        font=_F(13),
                        state="readonly").grid(row=1, column=4, padx=(0, 12))

        ctk.CTkButton(ga, text="追加", command=self._goal_add,
                      fg_color=C["accent"], hover_color=C["accent_dark"],
                      text_color="black", width=70,
                      font=_F(13, "bold")).grid(row=1, column=5)

        # ── 目標一覧（スクロール）──────────────────
        self.scroll_frame = ctk.CTkScrollableFrame(tab, fg_color=C["bg"])
        self.scroll_frame.pack(fill="both", expand=True)

    def _asset_set(self) -> None:
        val = parse_silver(self.asset_entry.get(), self.asset_unit_var.get())
        if val is None:
            messagebox.showerror("エラー", "金額を正しく入力してください（例: 12.5）"); return
        self.app.settings["current_silver"] = val
        save_settings(self.app.settings)
        self.asset_entry.delete(0, "end")
        self.refresh()

    def _goal_add(self) -> None:
        name = self.goal_name_entry.get().strip()
        if not name:
            messagebox.showerror("エラー", "目標名を入力してください"); return
        val = parse_silver(self.goal_amount_entry.get(), self.goal_unit_var.get())
        if val is None:
            messagebox.showerror("エラー", "金額を正しく入力してください（例: 12.5）"); return
        self.app.settings.setdefault("goals", []).append({"name": name, "amount": val})
        save_settings(self.app.settings)
        self.goal_name_entry.delete(0, "end")
        self.goal_amount_entry.delete(0, "end")
        self._rebuild_cards()
        self.refresh()

    def _goal_delete(self, idx: int) -> None:
        if messagebox.askyesno("確認", f"「{self.app.settings['goals'][idx]['name']}」を削除しますか？"):
            self.app.settings["goals"].pop(idx)
            save_settings(self.app.settings)
            self._rebuild_cards()
            self.refresh()

    def _rebuild_cards(self) -> None:
        """目標数が変わったときだけカードを作り直す"""
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self._goal_widgets.clear()

        goals = self.app.settings.get("goals", [])
        if not goals:
            ctk.CTkLabel(self.scroll_frame, text="目標がまだありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(pady=40)
            return

        for i, g in enumerate(goals):
            card = ctk.CTkFrame(self.scroll_frame, fg_color=C["surface"],
                                border_color=C["border"], border_width=1)
            card.pack(fill="x", padx=24, pady=6)

            top_row = ctk.CTkFrame(card, fg_color=C["surface"])
            top_row.pack(fill="x", padx=14, pady=(10, 4))
            ctk.CTkLabel(top_row, text=g["name"], text_color=C["fg"],
                         fg_color=C["surface"],
                         font=_F(13, "bold")).pack(side="left")
            ctk.CTkLabel(top_row, text=f"目標: {fmt_money(g['amount'])}", text_color=C["fg_dim"],
                         fg_color=C["surface"],
                         font=_F(11)).pack(side="left", padx=10)
            ctk.CTkButton(top_row, text="✕", command=lambda idx=i: self._goal_delete(idx),
                          fg_color=C["error"], hover_color="#cc5555",
                          text_color="white", width=28, height=22,
                          font=_F(11)).pack(side="right")

            mid_row = ctk.CTkFrame(card, fg_color=C["surface"])
            mid_row.pack(fill="x", padx=14, pady=2)
            pct_lbl = ctk.CTkLabel(mid_row, text="", text_color=C["accent"],
                                   fg_color=C["surface"],
                                   font=_F(16, "bold"))
            pct_lbl.pack(side="left")
            remain_lbl = ctk.CTkLabel(mid_row, text="", text_color=C["fg_dim"],
                                      fg_color=C["surface"],
                                      font=_F(13))
            remain_lbl.pack(side="left")

            bar = ctk.CTkProgressBar(card, progress_color=C["accent"],
                                     fg_color=C["surface2"], height=14)
            bar.set(0)
            bar.pack(fill="x", padx=14, pady=(4, 12))

            self._goal_widgets.append({
                "amount": g["amount"],
                "pct_lbl": pct_lbl,
                "remain_lbl": remain_lbl,
                "bar": bar,
            })

    def refresh(self) -> None:
        """数値ラベル・バーだけ更新（ウィジェット再生成なし）"""
        current = self.app.settings.get("current_silver", 0)
        self.asset_display_lbl.configure(text=f"現在: {fmt_money(current)} シルバー")

        goals = self.app.settings.get("goals", [])

        # カード数が変わっていたら再構築
        if len(self._goal_widgets) != len(goals):
            self._rebuild_cards()
            # _rebuild_cards の後は改めてリストを更新
            goals = self.app.settings.get("goals", [])

        for wdict, g in zip(self._goal_widgets, goals):
            amount = g["amount"]
            ratio  = min(current / amount, 1.0) if amount > 0 else 0
            pct    = ratio * 100
            remain = max(amount - current, 0)
            pct_color = C["success"] if pct >= 100 else C["accent"]
            wdict["pct_lbl"].configure(text=f"{pct:.1f}%", text_color=pct_color)
            if pct < 100:
                wdict["remain_lbl"].configure(text=f"  あと {fmt_money(remain)} シルバー")
            else:
                wdict["remain_lbl"].configure(text="  🎉 達成！", text_color=C["success"])
            wdict["bar"].configure(progress_color=C["success"] if pct >= 100 else C["accent"])
            wdict["bar"].set(ratio)
