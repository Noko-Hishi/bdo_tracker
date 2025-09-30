# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import json
import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import platform
from collections import defaultdict

# ---- フォント設定 ----
system = platform.system()
if system == 'Windows':
    matplotlib.rcParams['font.family'] = 'Meiryo'
elif system == 'Darwin':
    matplotlib.rcParams['font.family'] = 'Hiragino Sans'
else:
    matplotlib.rcParams['font.family'] = 'IPAPGothic'
matplotlib.rcParams["axes.unicode_minus"] = False

DB_FILE = "bdo_sessions.db"
SPOT_FILE = "spot.json"

# ---- 狩場情報 ----
def load_spots():
    if os.path.exists(SPOT_FILE):
        with open(SPOT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_spots(spots):
    with open(SPOT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

SPOTS = load_spots()

# ---- DB初期化 ----
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spot TEXT,
        trash_start INTEGER,
        trash_end INTEGER,
        duration INTEGER,
        trash_gained INTEGER,
        earned INTEGER,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def format_money(x):
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.0f}G"
    elif x >= 1_000_000:
        return f"{x/1_000_000:.0f}M"
    elif x >= 1_000:
        return f"{x/1_000:.0f}K"
    else:
        return str(int(x))

def format_hourly(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x/1_000:.1f}K"
    else:
        return str(int(x))

def format_axis_label(x, pos):
    """matplotlib軸ラベル用のフォーマッター"""
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f}G"
    elif x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x/1_000:.1f}K"
    else:
        return f"{int(x)}"

def get_available_months():
    """DBから利用可能な年月のリストを取得"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT created_at FROM sessions ORDER BY created_at")
    dates = [row[0] for row in cur.fetchall()]
    conn.close()
    
    months = set()
    for date_str in dates:
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            months.add(f"{date_obj.year}-{date_obj.month:02d}")
        except ValueError:
            continue
    
    return sorted(list(months), reverse=True)

# ---- デザイン設定 ----
def apply_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    bg_color = "#2e2e2e"   # 背景
    fg_color = "#f0f0f0"   # 文字色
    accent_color = "#d4af37"
    btn_color = "#3a3a3a"  # ボタン背景

    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Meiryo", 11))

    style.configure("TButton", background=btn_color, foreground=fg_color,
                    font=("Meiryo", 11, "bold"), padding=6)
    style.map("TButton",
              background=[("active", accent_color)],
              foreground=[("active", "black")])

    style.configure("TNotebook", background=bg_color, borderwidth=0)
    style.configure("TNotebook.Tab", background=btn_color, foreground=fg_color,
                    padding=[10, 5], font=("Meiryo", 11, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", accent_color)],
              foreground=[("selected", "black")])

    style.configure("TCombobox", foreground="black", font=("Meiryo", 11))

    root.option_add("*Listbox*Background", btn_color)
    root.option_add("*Listbox*Foreground", fg_color)
    root.option_add("*Listbox*Font", ("Meiryo", 11))

# ---- データ追加 ----
def add_session(spot, trash_start, trash_end, duration):
    gained = trash_end - trash_start
    earned = gained * SPOTS.get(spot, 0)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (spot, trash_start, trash_end, duration, trash_gained, earned, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        spot, trash_start, trash_end, duration, gained, earned, datetime.date.today().isoformat()
    ))
    conn.commit()
    conn.close()
    return gained, earned

# ---- GUI ----
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("BDO Tracker")

        self.running = False
        self.minutes = 0
        self.timer_id = None

        # タブ作成
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        # 操作
        self.tab_play = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_play, text="操作")

        # 日別グラフ
        self.tab_daily = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_daily, text="日別グラフ")

        # 平均時給
        self.tab_hourly = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hourly, text="平均時給")

        # 単価管理
        self.tab_spot = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_spot, text="狩場単価管理")

        self.build_play_tab()
        self.build_daily_tab()
        self.build_hourly_tab()
        self.build_spot_tab()
        self.update_total()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "日別グラフ":
            self.update_month_filter_daily()
            self.plot_daily()
        elif selected_tab == "平均時給":
            self.update_month_filter_hourly()
            self.plot_hourly()

    # ---- プレイタブ ----
    def build_play_tab(self):
        root = self.tab_play
        ttk.Label(root, text="狩場:").pack()
        self.spot_var = tk.StringVar(value=list(SPOTS.keys())[0] if SPOTS else "")
        self.spot_combo = ttk.Combobox(root, textvariable=self.spot_var, values=list(SPOTS.keys()))
        self.spot_combo.pack()

        ttk.Label(root, text="開始時ゴミドロ数:").pack()
        self.start_entry = ttk.Entry(root)
        self.start_entry.pack()

        ttk.Label(root, text="終了時ゴミドロ数:").pack()
        self.end_entry = ttk.Entry(root)
        self.end_entry.pack()

        self.timer_label = ttk.Label(root, text="プレイ時間: 0 分", font=("Meiryo", 14, "bold"))
        self.timer_label.pack(pady=5)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="開始", command=self.start_timer).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="休憩", command=self.pause_timer).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="再開", command=self.resume_timer).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="終了", command=self.end_session).grid(row=0, column=3, padx=5)

        self.total_label = ttk.Label(root, text="合計稼ぎ: 0 シルバー", font=("Meiryo", 12, "bold"))
        self.total_label.pack(pady=5)

    def start_timer(self):
        try:
            self.trash_start = int(self.start_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "開始時ゴミドロ数を正しく入力してください")
            return
        self.minutes = 0
        self.running = True
        self.update_timer()

    def update_timer(self):
        if self.running:
            self.minutes += 1
            self.timer_label.config(text=f"プレイ時間: {self.minutes} 分")
            self.timer_id = self.root.after(60000, self.update_timer)

    def pause_timer(self):
        if self.running:
            self.running = False
            if self.timer_id:
                self.root.after_cancel(self.timer_id)

    def resume_timer(self):
        if not self.running:
            self.running = True
            self.update_timer()

    def end_session(self):
        self.pause_timer()
        try:
            trash_end = int(self.end_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "終了時ゴミドロ数を正しく入力してください")
            return
        spot = self.spot_var.get()
        gained, earned = add_session(spot, self.trash_start, trash_end, self.minutes)
        messagebox.showinfo("終了", f"プレイ時間: {self.minutes} 分\nゴミドロ: {gained} 個\n稼ぎ: {format_money(earned)}")
        self.update_total()

    def update_total(self):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT SUM(earned) FROM sessions")
        total = cur.fetchone()[0] or 0
        conn.close()
        self.total_label.config(text=f"合計稼ぎ: {format_money(total)} シルバー")

    # ---- 日別グラフタブ ----
    def build_daily_tab(self):
        filter_frame = ttk.Frame(self.tab_daily)
        filter_frame.pack(pady=5, fill="x")
        
        ttk.Label(filter_frame, text="表示期間:").pack(side="left", padx=5)
        self.daily_month_var = tk.StringVar(value="全体")
        self.daily_month_combo = ttk.Combobox(filter_frame, textvariable=self.daily_month_var, width=15)
        self.daily_month_combo.pack(side="left", padx=5)
        
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="更新", command=self.plot_daily).pack(side="left", padx=2)
        
        self.daily_graph_frame = ttk.Frame(self.tab_daily)
        self.daily_graph_frame.pack(fill="both", expand=True)

    def update_month_filter_daily(self):
        """日別グラフタブの月フィルターを更新"""
        months = get_available_months()
        values = ["全体"] + months
        self.daily_month_combo['values'] = values
        if not self.daily_month_var.get() or self.daily_month_var.get() not in values:
            self.daily_month_var.set("全体")

    def get_daily_data(self, month_filter):
        """月フィルターに基づいて日別データを取得"""
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        if month_filter == "全体":
            cur.execute("""
                SELECT created_at, SUM(duration), SUM(earned)
                FROM sessions
                GROUP BY created_at
                ORDER BY created_at
            """)
        else:
            year, month = month_filter.split('-')
            cur.execute("""
                SELECT created_at, SUM(duration), SUM(earned)
                FROM sessions
                WHERE strftime('%Y-%m', created_at) = ?
                GROUP BY created_at
                ORDER BY created_at
            """, (month_filter,))
        
        rows = cur.fetchall()
        conn.close()
        return rows

    def plot_daily(self):
        for widget in self.daily_graph_frame.winfo_children():
            widget.destroy()
            
        month_filter = self.daily_month_var.get()
        rows = self.get_daily_data(month_filter)
        
        if not rows:
            ttk.Label(self.daily_graph_frame, text="データがありません").pack(expand=True)
            return
            
        dates = [r[0] for r in rows]
        durations = [r[1] for r in rows]
        earnings = [r[2] for r in rows]

        plt.style.use("dark_background")
        fig, ax1 = plt.subplots(figsize=(10,5), facecolor="#2e2e2e")
        ax1.set_facecolor("#2e2e2e")

        ax1.bar(dates, earnings, color="#d4af37", label="稼ぎ")
        ax1.set_ylabel("稼ぎ", color="#d4af37", fontweight="bold")
        ax1.tick_params(colors="#f0f0f0")
        
        formatter = FuncFormatter(format_axis_label)
        ax1.yaxis.set_major_formatter(formatter)

        ax2 = ax1.twinx()
        ax2.plot(dates, durations, color="#ff6666", marker="o", label="プレイ時間")
        ax2.set_ylabel("プレイ時間(分)", color="#ff6666", fontweight="bold")
        ax2.tick_params(colors="#f0f0f0")

        title = f"日別データ ({month_filter})" if month_filter != "全体" else "日別データ (全体)"
        fig.suptitle(title, color="#f0f0f0", fontweight="bold")

        fig.autofmt_xdate()
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.daily_graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    # ---- 平均時給タブ ----
    def build_hourly_tab(self):
        filter_frame = ttk.Frame(self.tab_hourly)
        filter_frame.pack(pady=5, fill="x")
        
        ttk.Label(filter_frame, text="表示期間:").pack(side="left", padx=5)
        self.hourly_month_var = tk.StringVar(value="全体")
        self.hourly_month_combo = ttk.Combobox(filter_frame, textvariable=self.hourly_month_var, width=15)
        self.hourly_month_combo.pack(side="left", padx=5)
        
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="更新", command=self.plot_hourly).pack(side="left", padx=2)
        
        self.hourly_graph_frame = ttk.Frame(self.tab_hourly)
        self.hourly_graph_frame.pack(fill="both", expand=True)

    def update_month_filter_hourly(self):
        """平均時給タブの月フィルターを更新"""
        months = get_available_months()
        values = ["全体"] + months
        self.hourly_month_combo['values'] = values
        if not self.hourly_month_var.get() or self.hourly_month_var.get() not in values:
            self.hourly_month_var.set("全体")

    def get_hourly_data(self, month_filter):
        """月フィルターに基づいて時給データを取得"""
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        if month_filter == "全体":
            cur.execute("""
                SELECT created_at, SUM(duration), SUM(earned)
                FROM sessions
                GROUP BY created_at
                ORDER BY created_at
            """)
        else:
            cur.execute("""
                SELECT created_at, SUM(duration), SUM(earned)
                FROM sessions
                WHERE strftime('%Y-%m', created_at) = ?
                GROUP BY created_at
                ORDER BY created_at
            """, (month_filter,))
        
        rows = cur.fetchall()
        conn.close()
        return rows

    def plot_hourly(self):
        for widget in self.hourly_graph_frame.winfo_children():
            widget.destroy()
            
        month_filter = self.hourly_month_var.get()
        rows = self.get_hourly_data(month_filter)
        
        if not rows:
            ttk.Label(self.hourly_graph_frame, text="データがありません").pack(expand=True)
            return
            
        dates = [r[0] for r in rows]
        hourly = [r[2]/(r[1]/60) if r[1]>0 else 0 for r in rows]

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10,4), facecolor="#2e2e2e")
        ax.set_facecolor("#2e2e2e")

        ax.plot(dates, hourly, color="#d4af37", marker="o", linewidth=2, markersize=6)
        ax.set_ylabel("平均時給", color="#d4af37", fontweight="bold")
        
        formatter = FuncFormatter(format_axis_label)
        ax.yaxis.set_major_formatter(formatter)
        
        title = f"日別平均時給 ({month_filter})" if month_filter != "全体" else "日別平均時給 (全体)"
        ax.set_title(title, color="#f0f0f0", fontweight="bold")
        
        ax.tick_params(colors="#f0f0f0")
        ax.set_xticklabels(dates, rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.hourly_graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

        table_frame = ttk.Frame(self.hourly_graph_frame)
        table_frame.pack(pady=5, fill="x")
        
        header_frame = ttk.Frame(table_frame)
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="日付", width=15, anchor="center", font=("Meiryo", 11, "bold")).grid(row=0, column=0, padx=1, pady=1)
        ttk.Label(header_frame, text="平均時給", width=15, anchor="center", font=("Meiryo", 11, "bold")).grid(row=0, column=1, padx=1, pady=1)
        
        canvas_frame = tk.Canvas(table_frame, height=200)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas_frame.yview)
        scrollable_frame = ttk.Frame(canvas_frame)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )
        
        canvas_frame.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_frame.configure(yscrollcommand=scrollbar.set)
        
        for i, (date, hourly_val) in enumerate(zip(dates, hourly)):
            ttk.Label(scrollable_frame, text=date, width=15, anchor="center").grid(row=i, column=0, padx=1, pady=1)
            ttk.Label(scrollable_frame, text=format_hourly(hourly_val), width=15, anchor="center").grid(row=i, column=1, padx=1, pady=1)
        
        canvas_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---- 狩場単価管理 ----
    def build_spot_tab(self):
        frame = self.tab_spot
        self.spot_listbox = tk.Listbox(frame, height=10)
        self.spot_listbox.pack(side="left", fill="y", padx=5, pady=5)
        self.update_spot_listbox()

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.spot_listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.spot_listbox.config(yscrollcommand=scrollbar.set)

        right_frame = ttk.Frame(frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(right_frame, text="狩場名:").pack()
        self.spot_name_entry = ttk.Entry(right_frame)
        self.spot_name_entry.pack()

        ttk.Label(right_frame, text="単価:").pack()
        self.spot_price_entry = ttk.Entry(right_frame)
        self.spot_price_entry.pack()

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="追加", command=self.add_spot).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="更新", command=self.update_spot).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="削除", command=self.delete_spot).grid(row=0, column=2, padx=5)

        self.spot_listbox.bind("<<ListboxSelect>>", self.on_spot_select)

    def update_spot_listbox(self):
        self.spot_listbox.delete(0, tk.END)
        for s in SPOTS.keys():
            self.spot_listbox.insert(tk.END, s)
        self.spot_combo['values'] = list(SPOTS.keys())
        if SPOTS:
            self.spot_var.set(list(SPOTS.keys())[0])

    def on_spot_select(self, event):
        selection = self.spot_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        spot = self.spot_listbox.get(idx)
        self.spot_name_entry.delete(0, tk.END)
        self.spot_name_entry.insert(0, spot)
        self.spot_price_entry.delete(0, tk.END)
        self.spot_price_entry.insert(0, str(SPOTS[spot]))

    def add_spot(self):
        name = self.spot_name_entry.get().strip()
        try:
            price = int(self.spot_price_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "単価は整数で入力してください")
            return
        if not name:
            messagebox.showerror("エラー", "狩場名を入力してください")
            return
        if name in SPOTS:
            messagebox.showerror("エラー", "既に存在する狩場名です")
            return
        SPOTS[name] = price
        save_spots(SPOTS)
        self.update_spot_listbox()

    def update_spot(self):
        selection = self.spot_listbox.curselection()
        if not selection:
            messagebox.showerror("エラー", "更新する狩場を選択してください")
            return
        old_name = self.spot_listbox.get(selection[0])
        new_name = self.spot_name_entry.get().strip()
        try:
            price = int(self.spot_price_entry.get())
        except ValueError:
            messagebox.showerror("エラー", "単価は整数で入力してください")
            return
        if not new_name:
            messagebox.showerror("エラー", "狩場名を入力してください")
            return
        if new_name != old_name and new_name in SPOTS:
            messagebox.showerror("エラー", "その狩場名は既に存在します")
            return
        del SPOTS[old_name]
        SPOTS[new_name] = price
        save_spots(SPOTS)
        self.update_spot_listbox()

    def delete_spot(self):
        selection = self.spot_listbox.curselection()
        if not selection:
            messagebox.showerror("エラー", "削除する狩場を選択してください")
            return
        name = self.spot_listbox.get(selection[0])
        del SPOTS[name]
        save_spots(SPOTS)
        self.update_spot_listbox()

# ---- 実行 ----
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    apply_style(root)
    app = App(root)
    root.mainloop()