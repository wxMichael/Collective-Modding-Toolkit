import operator
from abc import ABC
from pathlib import Path
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
		self.processing_data = False
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
		self.bind("<Escape>", self._ungrab_and_destroy)

	@final
	def _ungrab_and_destroy(self, _: "Event[Misc] | None" = None) -> None:
		if self.processing_data:
			return

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
		self.bind("<space>", self._ungrab_and_destroy)

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
		label_about.grid(sticky=NSEW, padx=10, pady=(10, 0))
		self.button_close = ttk.Button(
			self,
			text="Close",
			command=self._ungrab_and_destroy,
			width=self.win_width // 2,
		)
		self.button_close.grid(row=1, padx=10, pady=10)


class TreeWindow(ModalWindow):
	def __init__(
		self,
		parent: Wm,
		cmc: CMCheckerInterface,
		width: int,
		height: int,
		title: str,
		text: str,
		headers: tuple[str, str],
		items: list[tuple[int, Path]] | None,
	) -> None:
		super().__init__(parent, cmc, title, width, height)
		self.win_title = title
		self.win_text = text
		self.win_width = width
		self.headers = headers
		self.items = items
		self.build_gui()
		self.bind("<space>", self._ungrab_and_destroy)

	def build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_columnconfigure(1, weight=0)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)
		self.grid_rowconfigure(2, weight=0)

		label_about = ttk.Label(
			self,
			text=self.win_text,
			font=FONT_SMALL,
			justify=LEFT,
			anchor=W,
			wraplength=self.win_width,
		)
		label_about.grid(column=0, row=0, columnspan=2, sticky=NSEW, padx=10, pady=10)

		columns = tuple(f"#{i}" for i in range(1, len(self.items[0]) if self.items else 2))
		self.tree_items = ttk.Treeview(
			self,
			columns=columns,
			selectmode=NONE,
			show="tree headings" if self.headers else "tree",
			padding=1,
		)
		scroll_items_y = ttk.Scrollbar(
			self,
			orient=VERTICAL,
			command=self.tree_items.yview,  # pyright: ignore[reportUnknownArgumentType]
		)

		for c, title in enumerate(self.headers):
			self.tree_items.heading(f"#{c}", text=title, anchor=W if c else CENTER)

		self.tree_items.grid(column=0, row=1, sticky=NSEW)
		scroll_items_y.grid(column=1, row=1, sticky=NS)
		self.tree_items.configure(yscrollcommand=scroll_items_y.set)

		self.button_close = ttk.Button(
			self,
			text="Close",
			command=self._ungrab_and_destroy,
			width=self.win_width // 2,
		)
		self.button_close.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

		self.tree_items.column("#0", width=60, stretch=False, anchor=W)
		if self.items:
			for col in columns:
				self.tree_items.column(col, stretch=True, anchor=W)
			for item in sorted(self.items, key=operator.itemgetter(0), reverse=True):
				self.tree_items.insert("", END, text=f"{item[0]: 3}", values=(item[1].name,))
		else:
			self.tree_items.insert("", END, text="No items to display.")
