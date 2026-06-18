# -*- coding: utf-8 -*-
"""
日別グラフタブ（CustomTkinter版）
"""

import tkinter as tk
import customtkinter as ctk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from constants import C, _FONT_NAME, _F
from utils import fmt_money, fmt_axis
from db.bdo_db import (bdo_get_daily_data, bdo_get_daily_spot_data,
                       bdo_get_total, bdo_get_available_months, bdo_get_month_total)


class DailyTab:
    """金策 > 日別グラフ タブ"""

    def __init__(self, parent_notebook: ctk.CTkTabview, app):
        self.app = app
        parent_notebook.add("日別グラフ")
        self.tab = parent_notebook.tab("日別グラフ")
        self.tab.configure(fg_color=C["bg"])
        self._build()

    def _build(self) -> None:
        tab = self.tab

        ff = ctk.CTkFrame(tab, fg_color=C["bg"]); ff.pack(pady=5, fill="x")
        ctk.CTkLabel(ff, text="表示期間:", text_color=C["fg"],
                     font=_F(13)).pack(side="left", padx=5)
        self.month_var   = tk.StringVar(value="全体")
        self.month_combo = ctk.CTkComboBox(ff, variable=self.month_var, width=130,
                                           fg_color=C["surface2"], border_color=C["border"],
                                           button_color=C["surface"], button_hover_color=C["accent"],
                                           text_color=C["fg"],
                                           font=_F(13),
                                           command=lambda _: self.plot())
        self.month_combo.pack(side="left", padx=5)
        ctk.CTkButton(ff, text="更新", command=self.plot, width=60,
                      fg_color=C["surface"], hover_color=C["accent"], text_color=C["fg"],
                      font=_F(13)).pack(side="left", padx=4)

        self.total_lbl = ctk.CTkLabel(
            ff, text=f"合計稼ぎ: {fmt_money(bdo_get_total())} シルバー",
            text_color=C["accent"],
            font=_F(13, "bold"))
        self.total_lbl.pack(side="right", padx=14)

        self.month_total_lbl = ctk.CTkLabel(ff, text="", text_color=C["fg_dim"],
                                             font=_F(13, "bold"))
        self.month_total_lbl.pack(side="right", padx=4)

        self.graph_frame = ctk.CTkFrame(tab, fg_color=C["bg"])
        self.graph_frame.pack(fill="both", expand=True)

    def refresh_filter(self) -> None:
        months = ["全体"] + bdo_get_available_months()
        self.month_combo.configure(values=months)
        cur = self.month_var.get() if self.month_var.get() in months else "全体"
        self.month_var.set(cur)
        self.month_combo.set(cur)  # CTkComboBoxの表示バグ対策
        self._update_month_label()

    def update_total_label(self) -> None:
        self.total_lbl.configure(
            text=f"合計稼ぎ: {fmt_money(bdo_get_total())} シルバー")

    def _update_month_label(self) -> None:
        import datetime
        mf     = self.month_var.get()
        target = mf if mf != "全体" else datetime.date.today().strftime("%Y-%m")
        total  = bdo_get_month_total(target)
        label  = mf if mf != "全体" else "今月"
        self.month_total_lbl.configure(text=f"{label}: {fmt_money(total)} シルバー")

    def plot(self) -> None:
        self._update_month_label()
        for w in self.graph_frame.winfo_children():
            w.destroy()

        mf   = self.month_var.get()
        rows = bdo_get_daily_data(mf)
        if not rows:
            ctk.CTkLabel(self.graph_frame, text="データがありません",
                         text_color=C["fg_dim"],
                         font=_F(13)).pack(expand=True)
            return

        spot_data = bdo_get_daily_spot_data(mf)
        dates     = [r[0] for r in rows]
        durations = [r[1] for r in rows]
        earnings  = [r[2] for r in rows]

        plt.style.use("dark_background")
        fig, ax1 = plt.subplots(figsize=(10, 5), facecolor=C["plot_bg"])
        ax1.set_facecolor(C["plot_bg"])

        bars = ax1.bar(dates, earnings, color=C["plot_line"], label="稼ぎ")
        ax1.set_ylabel("稼ぎ", color=C["plot_line"], fontweight="bold")
        ax1.tick_params(colors=C["fg"])
        ax1.yaxis.set_major_formatter(FuncFormatter(fmt_axis))

        ax2 = ax1.twinx()
        ax2.plot(dates, durations, color=C["plot_red"], marker="o", label="プレイ時間")
        line_scatter = ax2.scatter(range(len(durations)), durations,
                                   s=80, color=C["plot_red"], zorder=5, alpha=0)
        ax2.set_ylabel("プレイ時間(分)", color=C["plot_red"], fontweight="bold")
        ax2.tick_params(colors=C["fg"])

        title_str = f"日別データ ({mf})" if mf != "全体" else "日別データ (全体)"
        fig.suptitle(title_str, color=C["fg"], fontweight="bold")
        ax1.set_xticklabels([])
        ax1.tick_params(axis="x", length=0)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

        annot_bar = ax1.annotate(
            "", xy=(0, 0), xytext=(14, 14), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.6", fc="#1a1a1a",
                      ec=C["accent"], lw=1.5, alpha=0.95),
            color=C["fg"], fontsize=9, ha="left", va="bottom",
        )
        annot_bar.set_visible(False)

        annot_line = ax2.annotate(
            "", xy=(0, 0), xytext=(14, 14), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.6", fc="#1a1a1a",
                      ec=C["plot_red"], lw=1.5, alpha=0.95),
            color=C["fg"], fontsize=9, ha="left", va="bottom",
        )
        annot_line.set_visible(False)

        def _tip_offset(event, lines):
            fig_w = fig.get_figwidth()  * fig.dpi
            fig_h = fig.get_figheight() * fig.dpi
            tip_w = max(len(l) for l in lines) * 6.5 + 24
            tip_h = len(lines) * 16 + 20
            ox = -tip_w - 8 if event.x + tip_w + 20 > fig_w else 14
            oy = -tip_h - 8 if event.y - tip_h - 20 < 0      else 14
            ha = "right" if ox < 0 else "left"
            va = "top"   if oy < 0 else "bottom"
            return ox, oy, ha, va

        def on_motion(event):
            changed = False
            if event.inaxes not in (ax1, ax2):
                for a in (annot_bar, annot_line):
                    if a.get_visible():
                        a.set_visible(False); changed = True
                if changed: canvas.draw_idle()
                return

            hit_bar = False
            if event.inaxes == ax2:
                inv    = ax1.transData.inverted()
                disp   = ax2.transData.transform((event.xdata, event.ydata))
                x1, y1 = inv.transform(disp)
                for bar, date in zip(bars, dates):
                    bx = bar.get_x(); bw = bar.get_width(); bh = bar.get_height()
                    if bx <= x1 <= bx + bw and 0 <= y1 <= bh:
                        cx        = bx + bw / 2
                        breakdown = spot_data.get(date, {})
                        lines     = [f"【{date}】", f"合計: {fmt_money(bh)}"]
                        for sp, val in sorted(breakdown.items(), key=lambda kv: -kv[1]):
                            lines.append(f"  {sp}: {fmt_money(val)}")
                        ox, oy, ha, va = _tip_offset(event, lines)
                        annot_bar.xy = (cx, bh)
                        annot_bar.set_text("\n".join(lines))
                        annot_bar.set_position((ox, oy))
                        annot_bar.set_ha(ha); annot_bar.set_va(va)
                        annot_bar.set_visible(True)
                        hit_bar = True; changed = True
                        break
            else:
                for bar, date in zip(bars, dates):
                    if bar.contains(event)[0]:
                        cx = bar.get_x() + bar.get_width() / 2
                        bh = bar.get_height()
                        breakdown = spot_data.get(date, {})
                        lines = [f"【{date}】", f"合計: {fmt_money(bh)}"]
                        for sp, val in sorted(breakdown.items(), key=lambda kv: -kv[1]):
                            lines.append(f"  {sp}: {fmt_money(val)}")
                        ox, oy, ha, va = _tip_offset(event, lines)
                        annot_bar.xy = (cx, bh)
                        annot_bar.set_text("\n".join(lines))
                        annot_bar.set_position((ox, oy))
                        annot_bar.set_ha(ha); annot_bar.set_va(va)
                        annot_bar.set_visible(True)
                        hit_bar = True; changed = True
                        break

            if not hit_bar and annot_bar.get_visible():
                annot_bar.set_visible(False); changed = True

            cont, ind = line_scatter.contains(event)
            if cont:
                idx = ind["ind"][0]; dur = durations[idx]
                h, m = divmod(int(dur), 60)
                time_str = f"{h}時間{m}分" if h > 0 else f"{m}分"
                lines_l  = [dates[idx], time_str]
                ox, oy, ha, va = _tip_offset(event, lines_l)
                annot_line.xy = (idx, dur)
                annot_line.set_text(f"{dates[idx]}\n{time_str}")
                annot_line.set_position((ox, oy))
                annot_line.set_ha(ha); annot_line.set_va(va)
                annot_line.set_visible(True); changed = True
            else:
                if annot_line.get_visible():
                    annot_line.set_visible(False); changed = True

            if changed:
                canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)
