# -*- coding: utf-8 -*-
"""
記録タブ（セッション入力）CustomTkinter版
"""

import datetime
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from constants import C, FONT_BIG, FONT_HDR, FONT_UI, _FONT_NAME, _F
from utils import fmt_money
from db.bdo_db import bdo_add_session


class BdoTab:
    """金策 > 記録 タブ"""

    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("記録")
        self.tab = parent_notebook.tab("記録")
        self.tab.configure(fg_color=C["bg"])

        self.bdo_running     = False
        self.bdo_minutes     = 0
        self.bdo_timer_id    = None
        self.bdo_trash_start = None

        self._build()

    def _build(self) -> None:
        tab = self.tab
        app = self.app

        # ── 入力モード ──────────────────────────
        mf = ctk.CTkFrame(tab, fg_color=C["bg"]); mf.pack(pady=6)
        ctk.CTkLabel(mf, text="入力モード:",
                     text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=5)
        self.input_mode = tk.StringVar(value="trash")
        for val, txt in [("trash", "ゴミドロ数"), ("silver", "シルバー直接")]:
            ctk.CTkRadioButton(mf, text=txt, variable=self.input_mode, value=val,
                               fg_color=C["accent"], hover_color=C["accent_dark"],
                               text_color=C["fg"],
                               font=_F(13),
                               command=self._update_labels).pack(side="left", padx=4)

        # ── 狩場 ────────────────────────────────
        ctk.CTkLabel(tab, text="狩場/活動:",
                     text_color=C["fg"],
                     font=_F(13)).pack()
        last       = app.settings.get("last_spot", "")
        default_sp = last if last in app.spots else (
                     list(app.spots.keys())[0] if app.spots else "")
        self.spot_var   = tk.StringVar(value=default_sp)
        self.spot_combo = ctk.CTkComboBox(tab, variable=self.spot_var,
                                          values=list(app.spots.keys()),
                                          fg_color=C["surface2"],
                                          border_color=C["border"],
                                          button_color=C["surface"],
                                          button_hover_color=C["accent"],
                                          text_color=C["fg"],
                                          font=_F(13))
        self.spot_combo.pack()

        # ── 開始 / 終了値 ────────────────────────
        self.start_lbl = ctk.CTkLabel(tab, text="開始時ゴミドロ数:",
                                      text_color=C["fg"],
                                      font=_F(13))
        self.start_lbl.pack()
        self.start_entry = ctk.CTkEntry(tab,
                                        fg_color=C["surface2"],
                                        border_color=C["border"],
                                        text_color=C["fg"],
                                        font=_F(13))
        self.start_entry.pack()
        last_trash = app.settings.get("last_trash_end", "")
        if last_trash:
            self.start_entry.insert(0, str(last_trash))

        self.end_lbl = ctk.CTkLabel(tab, text="終了時ゴミドロ数:",
                                    text_color=C["fg"],
                                    font=_F(13))
        self.end_lbl.pack()
        self.end_entry = ctk.CTkEntry(tab,
                                      fg_color=C["surface2"],
                                      border_color=C["border"],
                                      text_color=C["fg"],
                                      font=_F(13))
        self.end_entry.pack()

        # ── キャラ名 ─────────────────────────────
        char_frame = ctk.CTkFrame(tab, fg_color=C["bg"]); char_frame.pack(pady=(6, 0))
        ctk.CTkLabel(char_frame, text="キャラ名:",
                     text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=4)
        self.char_var   = tk.StringVar(value=app.settings.get("last_character", ""))
        self.char_entry = ctk.CTkEntry(char_frame, textvariable=self.char_var, width=160,
                                       fg_color=C["surface2"],
                                       border_color=C["border"],
                                       text_color=C["fg"],
                                       font=_F(13))
        self.char_entry.pack(side="left", padx=4)

        # ── アグリス / スクロール Lv ──────────────
        opt_frame = ctk.CTkFrame(tab, fg_color=C["bg"]); opt_frame.pack(pady=4)

        ctk.CTkLabel(opt_frame, text="アグリス:",
                     text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(4, 2))
        self.agris_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_frame, text="ON", variable=self.agris_var,
                        fg_color=C["accent"], hover_color=C["accent_dark"],
                        checkmark_color="black",
                        text_color=C["fg"],
                        font=_F(13)).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(opt_frame, text="スクロール:",
                     text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(4, 2))
        self.scroll_var = tk.StringVar(value="lv0")
        for v in ("lv0", "lv1", "lv2"):
            ctk.CTkRadioButton(opt_frame, text=v, variable=self.scroll_var, value=v,
                               fg_color=C["accent"], hover_color=C["accent_dark"],
                               text_color=C["fg"],
                               font=_F(13)).pack(side="left", padx=2)

        # ── タイマー ＋ 現在時刻 ──────────────────
        time_row = ctk.CTkFrame(tab, fg_color=C["bg"]); time_row.pack(pady=6)
        self.timer_lbl = ctk.CTkLabel(time_row, text="プレイ時間: 0 分",
                                      text_color=C["fg"],
                                      font=_F(16, "bold"))
        self.timer_lbl.pack(side="left", padx=(0, 20))
        self.clock_lbl = ctk.CTkLabel(time_row, text="",
                                      text_color=C["accent"],
                                      font=_F(16, "bold"))
        self.clock_lbl.pack(side="left")
        self._clock_id = None
        self._clock_tick()

        # ── ボタン ────────────────────────────────
        bf = ctk.CTkFrame(tab, fg_color=C["bg"]); bf.pack(pady=4)
        for i, (txt, cmd) in enumerate([
            ("開始", self.start),
            ("休憩", self.pause),
            ("再開", self.resume),
            ("終了", self.end),
        ]):
            ctk.CTkButton(bf, text=txt, command=cmd,
                          fg_color=C["surface"],
                          hover_color=C["accent"],
                          text_color=C["fg"],
                          font=_F(13, "bold"),
                          width=80).grid(row=0, column=i, padx=5)

    def _update_labels(self) -> None:
        if self.input_mode.get() == "silver":
            self.start_lbl.configure(text="開始時シルバー:")
            self.end_lbl.configure(text="終了時シルバー:")
        else:
            self.start_lbl.configure(text="開始時ゴミドロ数:")
            self.end_lbl.configure(text="終了時ゴミドロ数:")

    def _clock_tick(self) -> None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_lbl.configure(text=now)
        self._clock_id = self.tab.after(1000, self._clock_tick)

    def refresh_spots(self) -> None:
        self.spot_combo.configure(values=list(self.app.spots.keys()))

    def start(self) -> None:
        try:
            self.bdo_trash_start = int(self.start_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "開始値を正しく入力してください")
            return
        self.bdo_minutes = 0
        self.bdo_running = True
        self._tick()

    def _tick(self) -> None:
        if self.bdo_running:
            self.bdo_minutes += 1
            self.timer_lbl.configure(text=f"プレイ時間: {self.bdo_minutes} 分")
            self.bdo_timer_id = self.tab.after(60000, self._tick)

    def pause(self) -> None:
        if self.bdo_running:
            self.bdo_running = False
            if self.bdo_timer_id:
                self.tab.after_cancel(self.bdo_timer_id)

    def resume(self) -> None:
        if not self.bdo_running:
            self.bdo_running = True
            self._tick()

    def end(self) -> None:
        self.pause()
        if self.bdo_trash_start is None:
            messagebox.showerror("エラー", "先に「開始」ボタンを押してください")
            return
        try:
            trash_end = int(self.end_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "終了値を正しく入力してください")
            return
        spot = self.spot_var.get()
        if not spot:
            messagebox.showerror("エラー", "狩場/活動を選択してください")
            return

        mode      = self.input_mode.get()
        agris     = 1 if self.agris_var.get() else 0
        scroll_lv = self.scroll_var.get()
        character = self.char_var.get().strip()

        gained, earned = bdo_add_session(
            spot, self.bdo_trash_start, trash_end,
            self.bdo_minutes, mode, self.app.spots,
            agris=agris, scroll_lv=scroll_lv, character=character,
        )

        if mode == "silver":
            messagebox.showinfo("終了",
                f"プレイ時間: {self.bdo_minutes} 分\n稼ぎ: {fmt_money(earned)}")
        else:
            messagebox.showinfo("終了",
                f"プレイ時間: {self.bdo_minutes} 分\n"
                f"ゴミドロ: {gained} 個\n稼ぎ: {fmt_money(earned)}")

        self.start_entry.delete(0, "end")
        self.end_entry.delete(0, "end")
        self.bdo_minutes     = 0
        self.bdo_trash_start = None
        self.timer_lbl.configure(text="プレイ時間: 0 分")

        self.app.settings["last_spot"]      = spot
        self.app.settings["last_character"] = character
        if mode == "trash":
            self.app.settings["last_trash_end"] = trash_end
            self.start_entry.insert(0, str(trash_end))
        from settings import save_settings
        save_settings(self.app.settings)

        self.app._last_earned = earned
        self.app.update_total()
