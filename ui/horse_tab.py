# -*- coding: utf-8 -*-
"""
馬捕獲タブ（CustomTkinter版）
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from constants import C, _FONT_NAME, _F
from db.horse_db import (horse_add, horse_remove_last,
                         horse_get_today_count, horse_get_total_count,
                         horse_get_daily_counts)


class HorseTab:
    def __init__(self, parent_frame: ctk.CTkFrame, app):
        self.app = app
        self.tab = parent_frame
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        tab = self.tab
        app = self.app

        top = ctk.CTkFrame(tab, fg_color=C["bg"]); top.pack(pady=8)
        ctk.CTkLabel(top, text="🐎 今日の捕獲数", text_color=C["fg"],
                     font=_F(13, "bold")).pack()
        self.today_lbl = ctk.CTkLabel(top, text="0 頭", text_color=C["accent"],
                                       font=_F(16, "bold"))
        self.today_lbl.pack()
        self.total_lbl = ctk.CTkLabel(top, text="（総捕獲数: 0 頭）", text_color=C["fg_dim"],
                                       font=_F(13))
        self.total_lbl.pack()

        ctk.CTkLabel(tab, text="F9：捕獲 +1    F10：直前取消    F8：HUD切替",
                     text_color=C["fg_dim"],
                     font=_F(11)).pack(pady=3)

        bf = ctk.CTkFrame(tab, fg_color=C["bg"]); bf.pack(pady=4)
        for i, (txt, cmd) in enumerate([
            ("＋ 捕獲",    self.add),
            ("↩ 直前取消", self.remove),
            ("HUD 切替",   app.hud.toggle),
        ]):
            ctk.CTkButton(bf, text=txt, command=cmd, width=110,
                          fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                          font=_F(13)).grid(row=0, column=i, padx=6)

        self.graph_frame = ctk.CTkFrame(tab, fg_color=C["bg"])
        self.graph_frame.pack(fill="both", expand=True)

        self._update_labels()

    def add(self) -> None:
        app = self.app
        horse_add(app.horse_conn, app.horse_cur)
        app.horse_today = horse_get_today_count(app.horse_cur)
        app.horse_total = horse_get_total_count(app.horse_cur)
        self._update_labels()
        app.hud.update(app.horse_today)
        self.plot()

    def remove(self) -> None:
        app = self.app
        if horse_remove_last(app.horse_conn, app.horse_cur):
            app.horse_today = horse_get_today_count(app.horse_cur)
            app.horse_total = horse_get_total_count(app.horse_cur)
            self._update_labels()
            app.hud.update(app.horse_today)
            self.plot()

    def _update_labels(self) -> None:
        self.today_lbl.configure(text=f"{self.app.horse_today} 頭")
        self.total_lbl.configure(text=f"（総捕獲数: {self.app.horse_total} 頭）")

    def plot(self) -> None:
        for w in self.graph_frame.winfo_children():
            w.destroy()

        daily = horse_get_daily_counts(self.app.horse_cur)
        if not daily:
            ctk.CTkLabel(self.graph_frame, text="データがありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(expand=True)
            return

        dates  = [d.replace("-", "/") for d in daily.keys()]
        counts = list(daily.values())

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 5), facecolor=C["plot_bg"])
        ax.set_facecolor(C["plot_bg"])
        ax.plot(dates, counts, color=C["plot_line"], marker="o", linewidth=2, markersize=7)
        ax.set_ylabel("頭数", color=C["plot_line"], fontweight="bold")
        ax.set_title("日別 馬捕獲数", color=C["fg"], fontweight="bold")
        ax.tick_params(colors=C["fg"])
        ax.set_xticklabels([])
        ax.tick_params(axis="x", length=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

        scatter = ax.scatter(range(len(counts)), counts, s=60,
                             color=C["plot_line"], zorder=5, alpha=0)
        annot = ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.6", fc="#1a1a1a",
                      ec=C["accent"], lw=1.5, alpha=0.95),
            color=C["fg"], fontsize=10, ha="left", va="bottom",
        )
        annot.set_visible(False)

        def on_motion(event):
            if event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False); canvas.draw_idle()
                return
            cont, ind = scatter.contains(event)
            if cont:
                idx   = ind["ind"][0]
                lines = [dates[idx], f"{counts[idx]} 頭"]
                fig_w = fig.get_figwidth()  * fig.dpi
                fig_h = fig.get_figheight() * fig.dpi
                tip_w = max(len(l) for l in lines) * 7 + 24
                tip_h = len(lines) * 18 + 20
                ox = -tip_w - 8 if event.x + tip_w + 20 > fig_w else 12
                oy = -tip_h - 8 if event.y - tip_h - 20 < 0      else 12
                annot.xy = (idx, counts[idx])
                annot.set_text("\n".join(lines))
                annot.set_position((ox, oy))
                annot.set_ha("right" if ox < 0 else "left")
                annot.set_va("top"   if oy < 0 else "bottom")
                annot.set_visible(True)
            else:
                if annot.get_visible():
                    annot.set_visible(False)
            canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)
