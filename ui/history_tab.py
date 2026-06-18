# -*- coding: utf-8 -*-
"""
履歴タブ / 狩場管理タブ（CustomTkinter版）
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from constants import C, _FONT_NAME, _F
from utils import fmt_money
from db.bdo_db import bdo_get_sessions, bdo_delete_session, bdo_update_session
from data.spots import save_spots


class HistoryTab:
    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("履歴")
        self.tab = parent_notebook.tab("履歴")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        tab = self.tab

        hf = ctk.CTkFrame(tab, fg_color=C["bg"]); hf.pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(hf, text="更新", command=self.refresh, width=60,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack(side="left", padx=4)
        ctk.CTkLabel(hf, text="直近50件", text_color=C["fg_dim"],
                     font=_F(11)).pack(side="left", padx=6)

        self.scroll_frame = ctk.CTkScrollableFrame(tab, fg_color=C["bg"])
        self.scroll_frame.pack(fill="both", expand=True)

    def refresh(self) -> None:
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        rows = bdo_get_sessions(50)
        if not rows:
            ctk.CTkLabel(self.scroll_frame, text="履歴がありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(pady=40)
            return

        # ヘッダー
        hdr = ctk.CTkFrame(self.scroll_frame, fg_color=C["surface2"])
        hdr.pack(fill="x", padx=10, pady=(4, 2))
        for txt, w in [("日付", 10), ("狩場/活動", 18), ("時間", 7),
                       ("稼ぎ", 10), ("キャラ", 10), ("アグリス", 7),
                       ("スクロール", 8), ("操作", 10)]:
            ctk.CTkLabel(hdr, text=txt, text_color=C["fg_dim"], fg_color=C["surface2"],
                         font=_F(11),
                         width=w * 7, anchor="center").pack(side="left", padx=2)

        for row in rows:
            sid, spot, duration, earned, created_at, mode, trash, agris, scroll_lv, character = row
            h, m      = divmod(int(duration or 0), 60)
            dur_str   = f"{h}h{m:02d}m" if h > 0 else f"{m}分"
            agris_str = "ON" if agris else "OFF"

            rf = ctk.CTkFrame(self.scroll_frame, fg_color=C["surface"],
                              border_color=C["border"], border_width=1)
            rf.pack(fill="x", padx=10, pady=2)

            for txt, w in [
                (created_at,         10),
                (spot,               18),
                (dur_str,             7),
                (fmt_money(earned),  10),
                (character or "―",  10),
                (agris_str,           7),
                (scroll_lv or "lv0",  8),
            ]:
                ctk.CTkLabel(rf, text=txt, text_color=C["fg"], fg_color=C["surface"],
                             font=_F(11),
                             width=w * 7, anchor="center").pack(side="left", padx=2, pady=5)

            bf = ctk.CTkFrame(rf, fg_color=C["surface"]); bf.pack(side="left", padx=4)
            ctk.CTkButton(bf, text="編集", command=lambda r=row: self._edit(r),
                          fg_color=C["surface2"], hover_color=C["accent"], text_color=C["fg"],
                          width=50, height=24,
                          font=_F(11)).pack(side="left", padx=2)
            ctk.CTkButton(bf, text="削除", command=lambda i=sid: self._delete(i),
                          fg_color=C["error"], hover_color="#cc5555", text_color="white",
                          width=50, height=24,
                          font=_F(11)).pack(side="left", padx=2)

    def _delete(self, session_id: int) -> None:
        if messagebox.askyesno("確認", "このセッションを削除しますか？"):
            bdo_delete_session(session_id)
            self.refresh()
            self.app.update_total()

    def _edit(self, row) -> None:
        sid, spot, duration, earned, created_at, mode, trash, agris, scroll_lv, character = row

        win = ctk.CTkToplevel(self.app.root)
        win.title("セッション編集")
        win.configure(fg_color=C["bg"])
        win.resizable(False, False)
        win.grab_set()

        def lbl(text):
            ctk.CTkLabel(win, text=text, text_color=C["fg"],
                         font=_F(13)).pack(pady=(8, 2))

        lbl("狩場/活動")
        spot_var   = tk.StringVar(value=spot)
        ctk.CTkComboBox(win, variable=spot_var, values=list(self.app.spots.keys()), width=200,
                        fg_color=C["surface2"], border_color=C["border"],
                        button_color=C["surface"], button_hover_color=C["accent"],
                        text_color=C["fg"],
                        font=_F(13)).pack()

        lbl("プレイ時間（分）")
        dur_entry = ctk.CTkEntry(win, width=160,
                                 fg_color=C["surface2"], border_color=C["border"],
                                 text_color=C["fg"],
                                 font=_F(13))
        dur_entry.insert(0, str(duration or 0)); dur_entry.pack()

        lbl("稼ぎ（シルバー）")
        earn_entry = ctk.CTkEntry(win, width=160,
                                  fg_color=C["surface2"], border_color=C["border"],
                                  text_color=C["fg"],
                                  font=_F(13))
        earn_entry.insert(0, str(earned or 0)); earn_entry.pack()

        lbl("キャラ名")
        char_entry = ctk.CTkEntry(win, width=160,
                                  fg_color=C["surface2"], border_color=C["border"],
                                  text_color=C["fg"],
                                  font=_F(13))
        char_entry.insert(0, character or ""); char_entry.pack()

        lbl("アグリス")
        agris_var = tk.BooleanVar(value=bool(agris))
        ctk.CTkCheckBox(win, text="ON", variable=agris_var,
                        fg_color=C["accent"], hover_color=C["accent_dark"],
                        checkmark_color="black", text_color=C["fg"],
                        font=_F(13)).pack()

        lbl("スクロールLv")
        scroll_var = tk.StringVar(value=scroll_lv or "lv0")
        sf = ctk.CTkFrame(win, fg_color=C["bg"]); sf.pack()
        for v in ("lv0", "lv1", "lv2"):
            ctk.CTkRadioButton(sf, text=v, variable=scroll_var, value=v,
                               fg_color=C["accent"], hover_color=C["accent_dark"],
                               text_color=C["fg"],
                               font=_F(13)).pack(side="left", padx=4)

        def save():
            try:
                new_dur  = int(dur_entry.get())
                new_earn = int(earn_entry.get())
            except ValueError:
                messagebox.showerror("エラー", "時間と稼ぎは整数で入力してください", parent=win)
                return
            bdo_update_session(
                sid, spot_var.get(), new_dur, new_earn,
                character=char_entry.get().strip(),
                agris=1 if agris_var.get() else 0,
                scroll_lv=scroll_var.get(),
            )
            win.destroy()
            self.refresh()
            self.app.update_total()

        ctk.CTkButton(win, text="保存", command=save,
                      fg_color=C["accent"], hover_color=C["accent_dark"],
                      text_color="black", width=120,
                      font=_F(13, "bold")).pack(pady=14)


# ═══════════════════════════════════════════════
class SpotTab:
    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("狩場管理")
        self.tab = parent_notebook.tab("狩場管理")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        tab = self.tab

        left = ctk.CTkFrame(tab, fg_color=C["bg"]); left.pack(side="left", fill="y", padx=5, pady=5)
        self.listbox = tk.Listbox(left, height=14, bg=C["surface2"], fg=C["fg"],
                                  selectbackground=C["accent"], selectforeground="black",
                                  font=(_FONT_NAME, 11), relief="flat", bd=0,
                                  highlightthickness=0)
        self.listbox.pack(side="left", fill="y")
        sb = ctk.CTkScrollbar(left, command=self.listbox.yview)
        sb.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=sb.set)

        # 並び替えボタン
        ord_frame = ctk.CTkFrame(left, fg_color=C["bg"]); ord_frame.pack(side="left", fill="y", padx=(4, 0))
        ctk.CTkButton(ord_frame, text="▲", command=self._move_up, width=32,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack(pady=(4, 2))
        ctk.CTkButton(ord_frame, text="▼", command=self._move_down, width=32,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack()

        right = ctk.CTkFrame(tab, fg_color=C["bg"]); right.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(right, text="狩場名/活動名:", text_color=C["fg"],
                     font=_F(13)).pack()
        self.name_entry = ctk.CTkEntry(right, width=200,
                                       fg_color=C["surface2"], border_color=C["border"],
                                       text_color=C["fg"],
                                       font=_F(13))
        self.name_entry.pack()
        ctk.CTkLabel(right, text="単価:", text_color=C["fg"],
                     font=_F(13)).pack()
        self.price_entry = ctk.CTkEntry(right, width=200,
                                        fg_color=C["surface2"], border_color=C["border"],
                                        text_color=C["fg"],
                                        font=_F(13))
        self.price_entry.pack()

        bf = ctk.CTkFrame(right, fg_color=C["bg"]); bf.pack(pady=5)
        for i, (txt, cmd) in enumerate([("追加", self._add), ("更新", self._update), ("削除", self._delete)]):
            ctk.CTkButton(bf, text=txt, command=cmd, width=70,
                          fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                          font=_F(13)).grid(row=0, column=i, padx=5)

        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self._refresh_listbox()

    def _refresh_listbox(self) -> None:
        self.listbox.delete(0, tk.END)
        for s in self.app.spots.keys():
            self.listbox.insert(tk.END, s)
        self.app.bdo_tab.refresh_spots()

    def _on_select(self, _event) -> None:
        sel = self.listbox.curselection()
        if not sel: return
        name = self.listbox.get(sel[0])
        self.name_entry.delete(0, "end");  self.name_entry.insert(0, name)
        self.price_entry.delete(0, "end"); self.price_entry.insert(0, str(self.app.spots[name]))

    def _add(self) -> None:
        name = self.name_entry.get().strip()
        try:    price = int(self.price_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "単価は整数で入力してください"); return
        if not name:
            messagebox.showerror("エラー", "名前を入力してください"); return
        if name in self.app.spots:
            messagebox.showerror("エラー", "既に存在する名前です"); return
        self.app.spots[name] = price
        save_spots(self.app.spots); self._refresh_listbox()

    def _update(self) -> None:
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showerror("エラー", "更新する項目を選択してください"); return
        old = self.listbox.get(sel[0])
        new = self.name_entry.get().strip()
        try:    price = int(self.price_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "単価は整数で入力してください"); return
        if not new:
            messagebox.showerror("エラー", "名前を入力してください"); return
        if new != old and new in self.app.spots:
            messagebox.showerror("エラー", "その名前は既に存在します"); return
        del self.app.spots[old]; self.app.spots[new] = price
        save_spots(self.app.spots); self._refresh_listbox()

    def _delete(self) -> None:
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showerror("エラー", "削除する項目を選択してください"); return
        name = self.listbox.get(sel[0])
        del self.app.spots[name]
        save_spots(self.app.spots); self._refresh_listbox()

    def _move_up(self) -> None:
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        keys = list(self.app.spots.keys())
        keys[idx - 1], keys[idx] = keys[idx], keys[idx - 1]
        self.app.spots = {k: self.app.spots[k] for k in keys}
        save_spots(self.app.spots)
        self._refresh_listbox()
        self.listbox.selection_set(idx - 1)

    def _move_down(self) -> None:
        sel = self.listbox.curselection()
        if not sel or sel[0] >= self.listbox.size() - 1:
            return
        idx = sel[0]
        keys = list(self.app.spots.keys())
        keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]
        self.app.spots = {k: self.app.spots[k] for k in keys}
        save_spots(self.app.spots)
        self._refresh_listbox()
        self.listbox.selection_set(idx + 1)
