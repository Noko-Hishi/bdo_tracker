# -*- coding: utf-8 -*-
"""
タスク管理タブ群（一覧 / 作成 / 完了済み）CustomTkinter版
"""

import datetime
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from constants import C, _FONT_NAME, _F
from data.tasks import task_save


class TaskListTab:
    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("タスク一覧")
        self.tab = parent_notebook.tab("タスク一覧")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab, fg_color=C["bg"])
        self.scroll_frame.pack(fill="both", expand=True)
        # セクションヘッダーとアイテムコンテナを固定で作り、中身だけ更新する
        self._sections: dict[str, ctk.CTkFrame] = {}
        for ttype, tlabel in [("deadline", "期限付き"), ("daily", "毎日"), ("weekly", "毎週")]:
            # ヘッダー（固定）
            hf = ctk.CTkFrame(self.scroll_frame, fg_color=C["bg"])
            hf.pack(fill="x", padx=20, pady=(14, 4))
            ctk.CTkFrame(hf, fg_color=C["border"], height=1).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(hf, text=f" {tlabel} ", text_color=C["accent"], fg_color=C["bg"],
                         font=_F(13, "bold")).pack(side="left", padx=8)
            ctk.CTkFrame(hf, fg_color=C["border"], height=1).pack(side="left", fill="x", expand=True)
            # アイテムコンテナ（ここだけ中身を入れ替える）
            container = ctk.CTkFrame(self.scroll_frame, fg_color=C["bg"])
            container.pack(fill="x")
            self._sections[ttype] = container
        self.refresh()

    def refresh(self) -> None:
        for ttype, tlabel in [("deadline", "期限付き"), ("daily", "毎日"), ("weekly", "毎週")]:
            container = self._sections[ttype]
            for w in container.winfo_children():
                w.destroy()
            tasks = [t for t in self.app.task_data["tasks"] if t["type"] == ttype]
            if ttype == "deadline":
                tasks.sort(key=lambda x: x.get("deadline", "9999-12-31"))
            if not tasks:
                ctk.CTkLabel(container, text="タスクがありません",
                             text_color=C["fg_dim"], fg_color=C["bg"],
                             font=_F(11)).pack(padx=40, pady=3, anchor="w")
            else:
                for task in tasks:
                    self._item(container, task)

    def _item(self, container: ctk.CTkFrame, task: dict) -> None:
        outer = ctk.CTkFrame(container, fg_color=C["surface"],
                             border_color=C["border"], border_width=1)
        outer.pack(fill="x", padx=28, pady=3)
        inner = ctk.CTkFrame(outer, fg_color=C["surface"]); inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(inner, text=f"• {task['text']}", text_color=C["fg"],
                     fg_color=C["surface"], anchor="w",
                     font=_F(13)).pack(side="left", fill="x", expand=True)

        if "deadline" in task:
            try:
                dl  = datetime.datetime.strptime(task["deadline"], "%Y-%m-%d")
                rem = (dl - datetime.datetime.now()).days
                if rem < 0:    txt, col = f"期限切れ ({task['deadline']})", C["error"]
                elif rem == 0: txt, col = "今日まで!", C["error"]
                elif rem <= 3: txt, col = f"残り{rem}日", "#e0a860"
                else:          txt, col = task["deadline"], C["fg_dim"]
                ctk.CTkLabel(inner, text=txt, text_color=col, fg_color=C["surface"],
                             font=_F(11)).pack(side="left", padx=8)
            except Exception:
                pass

        bf = ctk.CTkFrame(inner, fg_color=C["surface"]); bf.pack(side="right")
        ctk.CTkButton(bf, text="✓", command=lambda t=task: self._complete(t),
                      fg_color=C["success"], hover_color="#3aaa90", text_color="white",
                      width=32, height=26,
                      font=_F(13, "bold")).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="✕", command=lambda t=task: self._delete(t),
                      fg_color=C["error"], hover_color="#cc5555", text_color="white",
                      width=32, height=26,
                      font=_F(13, "bold")).pack(side="left", padx=2)

    def _complete(self, task: dict) -> None:
        c = task.copy()
        c["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.app.task_data["completed"].append(c)
        self.app.task_data["tasks"].remove(task)
        task_save(self.app.task_data)
        self.refresh()
        self.app.task_done_tab.refresh()

    def _delete(self, task: dict) -> None:
        if messagebox.askyesno("確認", f"「{task['text']}」を削除しますか？"):
            self.app.task_data["tasks"].remove(task)
            task_save(self.app.task_data)
            self.refresh()


# ═══════════════════════════════════════════════
class TaskCreateTab:
    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("タスク作成")
        self.tab = parent_notebook.tab("タスク作成")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        card  = ctk.CTkFrame(self.tab, fg_color=C["surface"],
                              border_color=C["border"], border_width=1)
        card.pack(expand=True, padx=60, pady=40)
        inner = ctk.CTkFrame(card, fg_color=C["surface"]); inner.pack(padx=30, pady=30)

        def lbl(text, row):
            ctk.CTkLabel(inner, text=text, text_color=C["fg"], fg_color=C["surface"],
                         font=_F(13, "bold")).grid(
                row=row, column=0, sticky="w", pady=(0, 4))

        lbl("タスク名", 0)
        self.name_entry = ctk.CTkEntry(inner, width=340,
                                       fg_color=C["surface2"], border_color=C["border"],
                                       text_color=C["fg"],
                                       font=_F(13))
        self.name_entry.grid(row=1, column=0, pady=(0, 16), sticky="ew")

        lbl("タイプ", 2)
        tf = ctk.CTkFrame(inner, fg_color=C["surface"])
        tf.grid(row=3, column=0, sticky="w", pady=(0, 16))
        self.type_var = tk.StringVar(value="deadline")
        for val, txt in [("deadline", "期限付き"), ("daily", "毎日"), ("weekly", "毎週")]:
            ctk.CTkRadioButton(tf, text=txt, variable=self.type_var, value=val,
                               fg_color=C["accent"], hover_color=C["accent_dark"],
                               text_color=C["fg"],
                               font=_F(13),
                               command=self._toggle_deadline).pack(side="left", padx=(0, 12))

        self.dl_lbl = ctk.CTkLabel(inner, text="期限", text_color=C["fg"],
                                    fg_color=C["surface"],
                                    font=_F(13, "bold"))
        self.dl_lbl.grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.dl_entry = ctk.CTkEntry(inner, width=340,
                                     fg_color=C["surface2"], border_color=C["border"],
                                     text_color=C["fg"],
                                     font=_F(13))
        self.dl_entry.grid(row=5, column=0, pady=(0, 4), sticky="ew")
        self.dl_entry.insert(0, (datetime.datetime.now() +
                                  datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
        ctk.CTkLabel(inner, text="YYYY-MM-DD形式", text_color=C["fg_dim"],
                     fg_color=C["surface"],
                     font=_F(11)).grid(
            row=6, column=0, sticky="w", pady=(0, 16))

        # 週リセット曜日設定
        self.wd_frame = ctk.CTkFrame(inner, fg_color=C["surface"])
        self.wd_frame.grid(row=8, column=0, sticky="w", pady=(0, 4))
        self.wd_lbl = ctk.CTkLabel(self.wd_frame, text="週リセット曜日:",
                                    text_color=C["fg"], fg_color=C["surface"],
                                    font=_F(13, "bold"))
        self.wd_lbl.pack(side="left", padx=(0, 8))
        wd_names = ["月", "火", "水", "木", "金", "土", "日"]
        current_wd = self.app.task_data.get("weekly_reset_weekday", 3)
        self.wd_var = tk.IntVar(value=current_wd)
        self.wd_combo = ctk.CTkComboBox(self.wd_frame, variable=tk.StringVar(),
                                         values=[f"{i}:{n}曜日" for i, n in enumerate(wd_names)],
                                         width=130,
                                         fg_color=C["surface2"], border_color=C["border"],
                                         button_color=C["surface"], button_hover_color=C["accent"],
                                         text_color=C["fg"],
                                         font=_F(13),
                                         state="readonly",
                                         command=self._on_wd_change)
        self.wd_combo.set(f"{current_wd}:{wd_names[current_wd]}曜日")
        self.wd_combo.pack(side="left")
        ctk.CTkLabel(self.wd_frame, text="（全週次タスク共通）", text_color=C["fg_dim"],
                     fg_color=C["surface"], font=_F(11)).pack(side="left", padx=(8, 0))
        self.wd_frame.grid_remove()  # 初期はdeadlineなので非表示

        ctk.CTkButton(inner, text="タスクを追加", command=self._add,
                      fg_color=C["accent"], hover_color=C["accent_dark"],
                      text_color="black", height=38,
                      font=_F(13, "bold")).grid(
            row=9, column=0, sticky="ew", pady=(8, 0))

    def _toggle_deadline(self) -> None:
        ttype = self.type_var.get()
        if ttype == "deadline":
            self.dl_entry.configure(state="normal")
            self.dl_lbl.configure(text_color=C["fg"])
            self.wd_frame.grid_remove()
        elif ttype == "weekly":
            self.dl_entry.configure(state="disabled")
            self.dl_lbl.configure(text_color=C["fg_dim"])
            self.wd_frame.grid()
        else:
            self.dl_entry.configure(state="disabled")
            self.dl_lbl.configure(text_color=C["fg_dim"])
            self.wd_frame.grid_remove()

    def _on_wd_change(self, value: str) -> None:
        try:
            wd = int(value.split(":")[0])
            self.app.task_data["weekly_reset_weekday"] = wd
            task_save(self.app.task_data)
        except Exception:
            pass

    def _add(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("警告", "タスク名を入力してください"); return
        ttype = self.type_var.get()
        task  = {"text": name, "type": ttype,
                 "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if ttype == "deadline":
            dl = self.dl_entry.get().strip()
            try:
                datetime.datetime.strptime(dl, "%Y-%m-%d")
                task["deadline"] = dl
            except ValueError:
                messagebox.showerror("エラー", "日付の形式が正しくありません (YYYY-MM-DD)"); return
        self.app.task_data["tasks"].append(task)
        task_save(self.app.task_data)
        self.name_entry.delete(0, "end")
        self.app.task_list_tab.refresh()
        messagebox.showinfo("成功", "タスクを追加しました")


# ═══════════════════════════════════════════════
class TaskDoneTab:
    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("完了済み")
        self.tab = parent_notebook.tab("完了済み")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab, fg_color=C["bg"])
        self.scroll_frame.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self) -> None:
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        sorted_tasks = sorted(self.app.task_data["completed"],
                              key=lambda x: x.get("completed_at", ""), reverse=True)
        if not sorted_tasks:
            ctk.CTkLabel(self.scroll_frame, text="完了したタスクがありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(pady=50)
            return
        for task in sorted_tasks:
            self._item(task)

    def _item(self, task: dict) -> None:
        outer = ctk.CTkFrame(self.scroll_frame, fg_color=C["surface"],
                             border_color=C["border"], border_width=1)
        outer.pack(fill="x", padx=28, pady=3)
        inner = ctk.CTkFrame(outer, fg_color=C["surface"]); inner.pack(fill="x", padx=12, pady=8)

        tlabel = {"deadline": "期限付き", "daily": "毎日", "weekly": "毎週"}.get(
            task.get("type", ""), "不明")
        ctk.CTkLabel(inner, text=f"[{tlabel}] {task['text']}", text_color=C["fg_dim"],
                     fg_color=C["surface"], anchor="w",
                     font=_F(13)).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(inner, text=task.get("completed_at", ""), text_color=C["fg_dim"],
                     fg_color=C["surface"],
                     font=_F(11)).pack(side="left", padx=8)

        bf = ctk.CTkFrame(inner, fg_color=C["surface"]); bf.pack(side="right")
        ctk.CTkButton(bf, text="↺", command=lambda t=task: self._uncomplete(t),
                      fg_color=C["accent"], hover_color=C["accent_dark"], text_color="black",
                      width=32, height=26,
                      font=_F(13, "bold")).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="✕", command=lambda t=task: self._perm_delete(t),
                      fg_color=C["error"], hover_color="#cc5555", text_color="white",
                      width=32, height=26,
                      font=_F(13, "bold")).pack(side="left", padx=2)

    def _uncomplete(self, task: dict) -> None:
        r = task.copy(); r.pop("completed_at", None)
        self.app.task_data["tasks"].append(r)
        self.app.task_data["completed"].remove(task)
        task_save(self.app.task_data)
        self.app.task_list_tab.refresh()
        self.refresh()

    def _perm_delete(self, task: dict) -> None:
        if messagebox.askyesno("確認", f"「{task['text']}」を完全削除しますか？"):
            self.app.task_data["completed"].remove(task)
            task_save(self.app.task_data)
            self.refresh()
