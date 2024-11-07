from abc import abstractmethod
from pathlib import Path
from tkinter import *
from tkinter import messagebox, ttk
from typing import final

from globals import *
from helpers import CMCheckerInterface, LogType, Tab
from logger import Logger
from modal_window import ModalWindow


class PatcherBase(ModalWindow):
	def __init__(self, parent: CMCheckerInterface, window_title: str) -> None:
		super().__init__(parent, window_title, WINDOW_WIDTH_PATCHER, WINDOW_HEIGHT_PATCHER)

		self._build_gui_primary()
		self.populate_tree()

	@property
	@abstractmethod
	def about_title(self) -> str: ...

	@property
	@abstractmethod
	def about_text(self) -> str: ...

	@property
	@abstractmethod
	def filter_text(self) -> str: ...

	@property
	@abstractmethod
	def files_to_patch(self) -> set[Path]: ...

	@abstractmethod
	def patch_files(self) -> None: ...

	@abstractmethod
	def build_gui_secondary(self, frame_top: ttk.Frame) -> None: ...

	@final
	def _build_gui_primary(self) -> None:
		frame_top = ttk.Frame(self)
		frame_middle = ttk.Frame(self)
		frame_bottom = ttk.Frame(self)

		frame_top.grid(column=0, row=0, sticky=EW)
		frame_middle.grid(column=0, row=1, sticky=NSEW)
		frame_bottom.grid(column=0, row=2, sticky=EW)

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)
		frame_middle.grid_columnconfigure(0, weight=1)
		frame_middle.grid_rowconfigure(0, weight=1)
		frame_bottom.grid_columnconfigure(0, weight=1)

		# frame_top
		self.label_filter = ttk.Label(frame_top, text=self.filter_text, foreground=COLOR_NEUTRAL_2)
		button_patch_all = ttk.Button(frame_top, text="Patch All", padding=(6, 2), command=self._patch_wrapper)
		button_patcher_info = ttk.Button(frame_top, text=self.about_title, padding=(6, 2))
		button_patcher_info.config(command=lambda: messagebox.showinfo(self.about_title, self.about_text, parent=self))

		button_patcher_info.pack(side=RIGHT, padx=24, pady=5)
		button_patch_all.pack(side=RIGHT, padx=5, pady=5)

		# frame_middle
		style = ttk.Style()
		style.configure("Treeview", font=self.parent.FONT_SMALL)
		self._tree_files = ttk.Treeview(frame_middle, show="tree")
		self._scroll_tree_y = ttk.Scrollbar(frame_middle, orient=VERTICAL, command=self._tree_files.yview)  # pyright: ignore[reportUnknownArgumentType]

		self._tree_files.grid(column=0, row=0, sticky=NSEW)
		self._scroll_tree_y.grid(column=1, row=0, sticky=NS)
		self._tree_files.configure(yscrollcommand=self._scroll_tree_y.set)

		# frame_bottom
		self.logger = Logger(frame_bottom)

		self.build_gui_secondary(frame_top)

	@final
	def _patch_wrapper(self) -> None:
		assert self.parent.data_path is not None

		self.patch_files()

		self.parent.refresh_tab(Tab.Overview)
		self.populate_tree()

	@final
	def populate_tree(self) -> None:
		assert self.parent.data_path is not None

		self._tree_files.delete(*self._tree_files.get_children())
		for item in sorted(self.files_to_patch):
			self._tree_files.insert("", END, text=item.name)

		self.logger.log_message(LogType.Info, f"Showing {len(self.files_to_patch)} matching files.")
