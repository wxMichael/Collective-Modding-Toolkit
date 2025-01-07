import logging
from abc import abstractmethod
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import final

from enums import LogType, Tab
from globals import *
from helpers import CMCheckerInterface
from logger import Logger
from modal_window import AboutWindow, ModalWindow

logger = logging.getLogger()


class PatcherBase(ModalWindow):
	def __init__(self, parent: Wm, cmc: CMCheckerInterface, window_title: str) -> None:
		super().__init__(parent, cmc, window_title, WINDOW_WIDTH_PATCHER, WINDOW_HEIGHT_PATCHER)

		self.name_filter: str | None = None
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
	def build_gui_secondary(self) -> None: ...

	@final
	def _build_gui_primary(self) -> None:
		self.frame_top = ttk.Frame(self)
		self.frame_middle = ttk.Frame(self)
		self.frame_bottom = ttk.Frame(self)

		self.frame_top.grid(column=0, row=0, sticky=EW)
		self.frame_middle.grid(column=0, row=1, sticky=NSEW)
		self.frame_bottom.grid(column=0, row=2, sticky=EW)

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)
		self.frame_middle.grid_columnconfigure(1, weight=1)
		self.frame_middle.grid_rowconfigure(1, weight=1)
		self.frame_bottom.grid_columnconfigure(0, weight=1)

		# frame_top
		# self.label_filter = ttk.Label(frame_top, text=self.filter_text, foreground=COLOR_NEUTRAL_2)
		button_patch_all = ttk.Button(self.frame_top, text="Patch All", padding=(6, 2), command=self._patch_wrapper)
		button_patcher_info = ttk.Button(self.frame_top, text="About", padding=(6, 2))
		button_patcher_info.config(command=lambda: AboutWindow(self, self.cmc, 500, 435, self.about_title, self.about_text))

		button_patcher_info.pack(side=RIGHT, padx=24, pady=5)
		button_patch_all.pack(side=RIGHT, padx=5, pady=5)

		# frame_middle
		self._tree_files = ttk.Treeview(self.frame_middle, show="tree")
		self._scroll_tree_y = ttk.Scrollbar(self.frame_middle, orient=VERTICAL, command=self._tree_files.yview)  # pyright: ignore[reportUnknownArgumentType]

		self._tree_files.grid(column=0, row=1, columnspan=2, sticky=NSEW)
		self._scroll_tree_y.grid(column=2, row=1, sticky=NS)
		self._tree_files.configure(yscrollcommand=self._scroll_tree_y.set)

		# frame_bottom
		self.logger = Logger(self.frame_bottom)

		self.build_gui_secondary()

	@final
	def _patch_wrapper(self) -> None:
		assert self.cmc.game.data_path is not None
		self.processing_data = True

		logger.info("Patcher Running: %s", self.__class__.__name__)
		self.patch_files()
		logger.info("Patcher Finished")

		self.cmc.refresh_tab(Tab.Overview)
		self.populate_tree()
		self.processing_data = False

	@final
	def populate_tree(self) -> None:
		assert self.cmc.game.data_path is not None

		self._tree_files.delete(*self._tree_files.get_children())
		for item in sorted(self.files_to_patch):
			self._tree_files.insert("", END, text=item.name)

		self.logger.log_message(LogType.Info, f"Showing {len(self.files_to_patch)} files to be patched.", skip_logging=True)
