# -*- coding: utf-8 -*-
"""
HUD ウィンドウ（常時最前面・今日の馬捕獲数表示）CustomTkinter版
"""

import customtkinter as ctk
from constants import C, _FONT_NAME, _F


class HUDWindow:
    def __init__(self, root: ctk.CTk):
        self.win = ctk.CTkToplevel(root)
        self.win.title("HUD")
        self.win.geometry("90x70+50+50")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(fg_color="black")

        ctk.CTkLabel(self.win, text="🐎 今日",
                     text_color="white", fg_color="black",
                     font=_F(11)).pack()
        self.lbl = ctk.CTkLabel(self.win, text="0",
                                text_color="white", fg_color="black",
                                font=_F(22, "bold"))
        self.lbl.pack()
        self.visible = False
        self.win.withdraw()

    def update(self, count: int) -> None:
        self.lbl.configure(text=str(count))

    def toggle(self) -> None:
        if self.visible:
            self.win.withdraw()
        else:
            self.win.deiconify()
        self.visible = not self.visible
