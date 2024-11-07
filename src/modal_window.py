from abc import ABC
from tkinter import *
from typing import final

from globals import *
from helpers import CMCheckerInterface
from utils import set_titlebar_style


class ModalWindow(Toplevel, ABC):
	def __init__(self, parent: CMCheckerInterface, window_title: str, width: int, height: int) -> None:
		super().__init__(parent.window, takefocus=True)
		self.parent = parent
		self._window_title = window_title
		self.width = width
		self.height = height

		self.setup_window()

	@final
	def setup_window(self) -> None:
		self.resizable(width=False, height=False)
		self.wm_attributes("-fullscreen", "false")
		self.protocol("WM_DELETE_WINDOW", self._ungrab_and_destroy)
		self.transient(self.parent.window)

		self.withdraw()
		self.title(self._window_title)

		x = (self.winfo_screenwidth() // 2) - (self.width // 2)
		y = (self.winfo_screenheight() // 2) - (self.height // 2)
		self.geometry(f"{self.width}x{self.height}+{x}+{y}")

		self.deiconify()
		set_titlebar_style(self)
		self.focus()
		self.grab_set()

	@final
	def _ungrab_and_destroy(self) -> None:
		self.grab_release()
		self.destroy()
