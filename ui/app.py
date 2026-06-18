# -*- coding: utf-8 -*-
"""
Appクラス：タブ組み立て・ホットキー・共通コールバック（CustomTkinter版）

CTkTabview の構造:
  tab_view.add("タブ名")           → タブ追加（戻り値: フレーム）
  tab_view.tab("タブ名")           → そのタブのフレームを取得
  tab_view.set("タブ名")           → タブを選択
  tab_view.get()                    → 現在選択中のタブ名
"""

import sqlite3
import customtkinter as ctk

from constants import C, _FONT_NAME, _F
from settings import load_settings, save_settings
from data.spots import load_spots
from data.tasks import task_load, task_check_daily_reset, task_check_weekly_reset
from db.bdo_db import bdo_get_total
from db.horse_db import horse_get_today_count, horse_get_total_count
from utils import fmt_money
from constants import HORSE_DB

from ui.hud import HUDWindow
from ui.bdo_tab import BdoTab
from ui.daily_tab import DailyTab
from ui.graph_tab import GraphTab
from ui.ranking_tab import RankingTab
from ui.horse_tab import HorseTab
from ui.task_tab import TaskListTab, TaskCreateTab, TaskDoneTab
from ui.goal_tab import GoalTab
from ui.history_tab import HistoryTab, SpotTab


class App:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("BDO Tracker")
        self.root.configure(fg_color=C["bg"])

        # 共有データ
        self.spots    = load_spots()
        self.settings = load_settings()
        self._last_earned = 0

        # 馬捕獲 DB 接続
        self.horse_conn  = sqlite3.connect(HORSE_DB)
        self.horse_cur   = self.horse_conn.cursor()
        self.horse_today = horse_get_today_count(self.horse_cur)
        self.horse_total = horse_get_total_count(self.horse_cur)

        # タスクデータ
        self.task_data = task_load()
        task_check_daily_reset(self.task_data)
        task_check_weekly_reset(self.task_data)

        # HUD
        self.hud = HUDWindow(root)
        self.hud.update(self.horse_today)

        # ホットキー
        self._start_hotkey_listener()

        # ── 外側タブビュー ─────────────────────────
        self.nb = ctk.CTkTabview(root,
                                 fg_color=C["bg"],
                                 segmented_button_fg_color=C["surface"],
                                 segmented_button_selected_color=C["accent"],
                                 segmented_button_selected_hover_color=C["accent_dark"],
                                 segmented_button_unselected_color=C["surface"],
                                 segmented_button_unselected_hover_color=C["surface2"],
                                 text_color=C["fg"],
                                 text_color_disabled=C["fg_dim"],
                                 command=self._on_outer_tab_changed)
        self.nb.pack(expand=True, fill="both")

        # ── 金策グループ ──────────────────────────
        self.nb.add("金策")
        grp_bdo = self.nb.tab("金策")
        grp_bdo.configure(fg_color=C["bg"])

        nb_bdo = ctk.CTkTabview(grp_bdo,
                                fg_color=C["bg"],
                                segmented_button_fg_color=C["surface2"],
                                segmented_button_selected_color=C["surface"],
                                segmented_button_selected_hover_color=C["surface"],
                                segmented_button_unselected_color=C["surface2"],
                                segmented_button_unselected_hover_color=C["surface"],
                                text_color=C["accent"],
                                text_color_disabled=C["fg_dim"],
                                command=self._on_bdo_tab_changed)
        nb_bdo.pack(expand=True, fill="both")
        self._nb_bdo = nb_bdo

        self.bdo_tab     = BdoTab(nb_bdo, self)
        self.daily_tab   = DailyTab(nb_bdo, self)
        self.graph_tab   = GraphTab(nb_bdo, self)
        self.ranking_tab = RankingTab(nb_bdo, self)

        # ── 目標金額（独立）───────────────────────
        self.nb.add("目標金額")
        grp_goal = self.nb.tab("目標金額")
        grp_goal.configure(fg_color=C["bg"])
        self.goal_tab = GoalTab(grp_goal, self)

        # ── 馬捕獲（独立）────────────────────────
        self.nb.add("馬捕獲")
        grp_horse = self.nb.tab("馬捕獲")
        grp_horse.configure(fg_color=C["bg"])
        self.horse_tab = HorseTab(grp_horse, self)

        # ── タスク管理グループ ─────────────────────
        self.nb.add("タスク管理")
        grp_task = self.nb.tab("タスク管理")
        grp_task.configure(fg_color=C["bg"])

        nb_task = ctk.CTkTabview(grp_task,
                                 fg_color=C["bg"],
                                 segmented_button_fg_color=C["surface2"],
                                 segmented_button_selected_color=C["surface"],
                                 segmented_button_selected_hover_color=C["surface"],
                                 segmented_button_unselected_color=C["surface2"],
                                 segmented_button_unselected_hover_color=C["surface"],
                                 text_color=C["accent"],
                                 text_color_disabled=C["fg_dim"],
                                 command=self._on_task_tab_changed)
        nb_task.pack(expand=True, fill="both")
        self._nb_task = nb_task

        self.task_list_tab   = TaskListTab(nb_task, self)
        self.task_create_tab = TaskCreateTab(nb_task, self)
        self.task_done_tab   = TaskDoneTab(nb_task, self)

        # ── 管理グループ ──────────────────────────
        self.nb.add("管理")
        grp_mgmt = self.nb.tab("管理")
        grp_mgmt.configure(fg_color=C["bg"])

        nb_mgmt = ctk.CTkTabview(grp_mgmt,
                                 fg_color=C["bg"],
                                 segmented_button_fg_color=C["surface2"],
                                 segmented_button_selected_color=C["surface"],
                                 segmented_button_selected_hover_color=C["surface"],
                                 segmented_button_unselected_color=C["surface2"],
                                 segmented_button_unselected_hover_color=C["surface"],
                                 text_color=C["accent"],
                                 text_color_disabled=C["fg_dim"],
                                 command=self._on_mgmt_tab_changed)
        nb_mgmt.pack(expand=True, fill="both")
        self._nb_mgmt = nb_mgmt

        self.spot_tab    = SpotTab(nb_mgmt, self)
        self.history_tab = HistoryTab(nb_mgmt, self)

        # 初期化
        self.update_total()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────────────────────
    #  ホットキー
    # ─────────────────────────────────────────
    def _start_hotkey_listener(self) -> None:
        try:
            from pynput import keyboard

            def on_press(key):
                try:
                    if key == keyboard.Key.f9:
                        self.root.after(0, self.horse_tab.add)
                    elif key == keyboard.Key.f10:
                        self.root.after(0, self.horse_tab.remove)
                    elif key == keyboard.Key.f8:
                        self.root.after(0, self.hud.toggle)
                except Exception:
                    pass

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.start()
        except ImportError:
            self._listener = None

    # ─────────────────────────────────────────
    #  タブ切替コールバック
    # ─────────────────────────────────────────
    def _on_outer_tab_changed(self, *_) -> None:
        tab = self.nb.get()
        if tab == "目標金額":
            self.goal_tab.refresh()
        elif tab == "馬捕獲":
            self.horse_tab.plot()
        elif tab == "金策":
            self._on_bdo_tab_changed()
        elif tab == "タスク管理":
            self._on_task_tab_changed()

    def _on_bdo_tab_changed(self, *_) -> None:
        tab = self._nb_bdo.get()
        if tab == "日別グラフ":
            self.daily_tab.refresh_filter()
            self.daily_tab.plot()
        elif tab == "セッション別時給":
            self.graph_tab.refresh_filters()
            self.graph_tab.plot()
        elif tab == "ランキング":
            self.ranking_tab.refresh_filter()
            self.ranking_tab.refresh()

    def _on_task_tab_changed(self, *_) -> None:
        tab = self._nb_task.get()
        if tab == "タスク一覧":
            self.task_list_tab.refresh()
        elif tab == "完了済み":
            self.task_done_tab.refresh()

    def _on_mgmt_tab_changed(self, *_) -> None:
        tab = self._nb_mgmt.get()
        if tab == "履歴":
            self.history_tab.refresh()

    # ─────────────────────────────────────────
    #  合計更新
    # ─────────────────────────────────────────
    def update_total(self) -> None:
        # ① 合計ラベルは常に更新（軽い）
        self.daily_tab.update_total_label()

        # ② 稼ぎがあれば設定に反映
        if self._last_earned:
            prev = self.settings.get("current_silver", 0)
            self.settings["current_silver"] = prev + self._last_earned
            save_settings(self.settings)
            self._last_earned = 0

        # ③ 現在表示中のタブだけ更新（非表示タブはタブ切替時に遅延更新される）
        try:
            outer = self.nb.get()
            if outer == "目標金額":
                self.goal_tab.refresh()
            elif outer == "金策":
                cur = self._nb_bdo.get()
                if cur == "セッション別時給":
                    self.graph_tab.refresh_filters()
                    self.graph_tab.plot()
                elif cur == "ランキング":
                    self.ranking_tab.refresh_filter()
                    self.ranking_tab.refresh()
                elif cur == "日別グラフ":
                    self.daily_tab.refresh_filter()
                    self.daily_tab.plot()
        except Exception:
            pass
            pass

    # ─────────────────────────────────────────
    #  終了
    # ─────────────────────────────────────────
    def _on_close(self) -> None:
        if self._listener:
            self._listener.stop()
        self.horse_conn.close()
        self.root.destroy()
