from abc import ABC
from tkinter import *
from tkinter import ttk
from typing import final

from globals import *
from helpers import CMCheckerInterface
from utils import set_titlebar_style


class ModalWindow(Toplevel, ABC):
	def __init__(self, parent: Wm, cmc: CMCheckerInterface, window_title: str, width: int, height: int) -> None:
		super().__init__(cmc.root, takefocus=True)
		self.parent = parent
		self.cmc = cmc
		self._window_title = window_title
		self.width = width
		self.height = height
		self.previous_grabber: Misc = self.cmc.root.grab_current()
		self.setup_window()

	@final
	def setup_window(self) -> None:
		self.wm_withdraw()
		self.wm_resizable(width=False, height=False)
		self.wm_attributes("-fullscreen", "false")
		self.wm_protocol("WM_DELETE_WINDOW", self._ungrab_and_destroy)
		self.wm_title(self._window_title)

		x = (self.winfo_screenwidth() // 2) - (self.width // 2)
		y = (self.winfo_screenheight() // 2) - (self.height // 2)
		self.wm_geometry(f"{self.width}x{self.height}+{x}+{y}")

		self.wm_transient(self.parent)
		set_titlebar_style(self)
		self.wm_deiconify()
		self.update()
		self.focus_set()
		self.grab_set()
		self.bind("<Escape>", lambda _: self._ungrab_and_destroy())

	@final
	def _ungrab_and_destroy(self) -> None:
		self.grab_release()
		if self.previous_grabber:
			self.previous_grabber.grab_set()
		self.destroy()
		self.update()


class AboutWindow(ModalWindow):
	def __init__(self, parent: Wm, cmc: CMCheckerInterface, width: int, height: int, title: str, text: str) -> None:
		super().__init__(parent, cmc, title, width, height)
		self.win_title = title
		self.win_text = text
		self.win_width = width
		self.build_gui()

	def build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		label_about = ttk.Label(
			self,
			text=self.win_text,
			font=FONT_SMALL,
			justify=LEFT,
			anchor=N,
			wraplength=self.win_width,
		)
		label_about.grid(sticky=NSEW, padx=10, pady=10)
		self.button_close = ttk.Button(
			self,
			text="Close",
			command=self._ungrab_and_destroy,
			width=self.win_width // 2,
		)
		self.button_close.grid(row=1, padx=10, pady=10)
