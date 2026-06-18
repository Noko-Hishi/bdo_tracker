# -*- coding: utf-8 -*-
"""
セッション別時給グラフタブ（CustomTkinter版）
AGあり=赤、AGなし=青 の2本線で同一グラフに表示
"""

import tkinter as tk
import customtkinter as ctk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from constants import C, _FONT_NAME, _F
from utils import fmt_money, fmt_axis
from db.bdo_db import bdo_get_session_hourly, bdo_get_all_characters, bdo_get_available_months


class GraphTab:
    """金策 > セッション別時給 タブ"""

    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("セッション別時給")
        self.tab = parent_notebook.tab("セッション別時給")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        tab = self.tab

        ff = ctk.CTkFrame(tab, fg_color=C["bg"]); ff.pack(pady=5, fill="x")

        ctk.CTkLabel(ff, text="期間:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(5, 2))
        self.month_var   = tk.StringVar(value="全体")
        self.month_combo = ctk.CTkComboBox(ff, variable=self.month_var, width=120,
                                           fg_color=C["surface2"], border_color=C["border"],
                                           button_color=C["surface"], button_hover_color=C["accent"],
                                           text_color=C["fg"],
                                           font=_F(13),
                                           command=lambda _: self.plot())
        self.month_combo.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(ff, text="キャラ:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(0, 2))
        self.char_var   = tk.StringVar(value="全員")
        self.char_combo = ctk.CTkComboBox(ff, variable=self.char_var, width=110,
                                          fg_color=C["surface2"], border_color=C["border"],
                                          button_color=C["surface"], button_hover_color=C["accent"],
                                          text_color=C["fg"],
                                          font=_F(13),
                                          command=lambda _: self.plot())
        self.char_combo.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(ff, text="スクロール:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=(0, 2))
        self.scroll_var   = tk.StringVar(value="全て")
        self.scroll_combo = ctk.CTkComboBox(ff, variable=self.scroll_var,
                                            values=["全て", "lv0", "lv1", "lv2"],
                                            width=70,
                                            fg_color=C["surface2"], border_color=C["border"],
                                            button_color=C["surface"], button_hover_color=C["accent"],
                                            text_color=C["fg"],
                                            font=_F(13),
                                            state="readonly",
                                            command=lambda _: self.plot())
        self.scroll_combo.pack(side="left", padx=(0, 10))

        ctk.CTkButton(ff, text="更新", command=self.plot, width=60,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack(side="left", padx=4)

        self.avg_label = ctk.CTkLabel(ff, text="",
                                      text_color=C["fg"],
                                      font=_F(13))
        self.avg_label.pack(side="left", padx=(16, 4))

        self.graph_frame = ctk.CTkFrame(tab, fg_color=C["bg"])
        self.graph_frame.pack(fill="both", expand=True)

    def refresh_filters(self) -> None:
        months = ["全体"] + bdo_get_available_months()
        self.month_combo.configure(values=months)
        cur_m = self.month_var.get() if self.month_var.get() in months else "全体"
        self.month_var.set(cur_m)
        self.month_combo.set(cur_m)

        chars = ["全員"] + bdo_get_all_characters()
        self.char_combo.configure(values=chars)
        cur_c = self.char_var.get() if self.char_var.get() in chars else "全員"
        self.char_var.set(cur_c)
        self.char_combo.set(cur_c)

    def plot(self) -> None:
        for w in self.graph_frame.winfo_children():
            w.destroy()

        # AGあり (agris=ON) と AGなし (agris=OFF) を個別取得
        data_on = bdo_get_session_hourly(
            month_filter  = self.month_var.get(),
            char_filter   = self.char_var.get(),
            agris_filter  = "ON",
            scroll_filter = self.scroll_var.get(),
        )
        data_off = bdo_get_session_hourly(
            month_filter  = self.month_var.get(),
            char_filter   = self.char_var.get(),
            agris_filter  = "OFF",
            scroll_filter = self.scroll_var.get(),
        )

        # 平均時給ラベル更新
        parts = []
        if data_on:
            avg_on = sum(d["hourly"] for d in data_on) / len(data_on)
            parts.append(f"AGあり: {fmt_money(avg_on)}/h ({len(data_on)}件)")
        if data_off:
            avg_off = sum(d["hourly"] for d in data_off) / len(data_off)
            parts.append(f"AGなし: {fmt_money(avg_off)}/h ({len(data_off)}件)")
        self.avg_label.configure(
            text=("平均時給: " + "　" + "  /  ".join(parts)) if parts else "平均時給: ―"
        )

        if not data_on and not data_off:
            ctk.CTkLabel(self.graph_frame, text="データがありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(expand=True)
            return

        # ─── 全データを時系列順に統合してX軸を共通化 ───
        all_data = []
        for d in data_on:
            all_data.append({**d, "_agris": True})
        for d in data_off:
            all_data.append({**d, "_agris": False})
        # label（日時文字列想定）でソート
        all_data.sort(key=lambda d: d["label"])
        # 通し番号を振る
        for i, d in enumerate(all_data):
            d["_idx"] = i

        # AGあり/なしに再分離（通し番号付き）
        data_on_merged  = [d for d in all_data if d["_agris"]]
        data_off_merged = [d for d in all_data if not d["_agris"]]

        # ─── プロット ───
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 5), facecolor=C["plot_bg"])
        ax.set_facecolor(C["plot_bg"])

        COLOR_ON  = "#e05555"   # 赤 = AGあり
        COLOR_OFF = "#5599e0"   # 青 = AGなし

        scatter_on  = None
        scatter_off = None

        if data_on_merged:
            idx_on    = [d["_idx"] for d in data_on_merged]
            hourly_on = [d["hourly"] for d in data_on_merged]
            ax.plot(idx_on, hourly_on, color=COLOR_ON, linewidth=1.6, label="AGあり")
            scatter_on = ax.scatter(idx_on, hourly_on, s=70, color=COLOR_ON, zorder=5, alpha=0)

        if data_off_merged:
            idx_off    = [d["_idx"] for d in data_off_merged]
            hourly_off = [d["hourly"] for d in data_off_merged]
            ax.plot(idx_off, hourly_off, color=COLOR_OFF, linewidth=1.6, label="AGなし")
            scatter_off = ax.scatter(idx_off, hourly_off, s=70, color=COLOR_OFF, zorder=5, alpha=0)

        # ツールチップ用に通し番号付きデータで上書き
        data_on  = data_on_merged
        data_off = data_off_merged

        ax.set_ylabel("時給", color=C["fg"], fontweight="bold")
        ax.yaxis.set_major_formatter(FuncFormatter(fmt_axis))
        ax.set_xticks([])
        ax.tick_params(colors=C["fg"])

        title = "セッション別時給"
        if self.month_var.get() != "全体":
            title += f" ({self.month_var.get()})"
        ax.set_title(title, color=C["fg"], fontweight="bold")

        legend = ax.legend(
            facecolor=C["plot_bg"], edgecolor=C["border"],
            labelcolor=C["fg"], fontsize=10,
            loc="upper left",
        )

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

        # ─── ツールチップ ───
        annot = ax.annotate(
            "", xy=(0, 0), xytext=(14, 14), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.7", fc="#1a1a1a",
                      ec=C["accent"], lw=1.5, alpha=0.96),
            color=C["fg"], fontsize=9, ha="left", va="bottom",
        )
        annot.set_visible(False)

        def _show_tip(event, sc, data, color):
            """scatterにヒットした場合にアノテーションを表示してTrueを返す"""
            if sc is None:
                return False
            cont, ind = sc.contains(event)
            if not cont:
                return False
            idx = ind["ind"][0]
            d   = data[idx]
            agris_str = "ON" if d["agris"] else "OFF"
            lines = [
                d["label"],
                f"狩場: {d['spot']}   時給: {fmt_money(d['hourly'])}",
                f"キャラ: {d['character'] or '―'}   "
                f"アグリス: {agris_str}   スクロール: {d['scroll_lv']}",
            ]
            annot.xy = (d["_idx"], d["hourly"])
            annot.set_text("\n".join(lines))
            annot.get_bbox_patch().set_edgecolor(color)
            fig_w = fig.get_figwidth()  * fig.dpi
            fig_h = fig.get_figheight() * fig.dpi
            tip_w = max(len(l) for l in lines) * 6.5 + 24
            tip_h = len(lines) * 16 + 20
            ox = -tip_w - 8 if event.x + tip_w + 20 > fig_w else 14
            oy = -tip_h - 8 if event.y - tip_h - 20 < 0      else 14
            annot.set_position((ox, oy))
            annot.set_ha("right" if ox < 0 else "left")
            annot.set_va("top"   if oy < 0 else "bottom")
            annot.set_visible(True)
            return True

        def on_motion(event):
            if event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False)
                    canvas.draw_idle()
                return
            hit = _show_tip(event, scatter_on,  data_on,  COLOR_ON)
            if not hit:
                hit = _show_tip(event, scatter_off, data_off, COLOR_OFF)
            if not hit and annot.get_visible():
                annot.set_visible(False)
            canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)