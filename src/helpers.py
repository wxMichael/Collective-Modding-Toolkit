from abc import ABC, abstractmethod
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import TYPE_CHECKING, NotRequired, TypedDict, final

from enums import InstallType, Tab

if TYPE_CHECKING:
	from game_info import GameInfo

COLOR_BAD = "firebrick1"


class CMCheckerInterface(ABC):
	def __init__(self) -> None:
		self.window: Tk
		self.FONT: tuple[str, int]
		self.FONT_SMALLER: tuple[str, int]
		self.FONT_SMALL: tuple[str, int]
		self.FONT_LARGE: tuple[str, int]
		self.install_type_sv: StringVar
		self.game_path_sv: StringVar
		self.game: GameInfo

	@abstractmethod
	def refresh_tab(self, tab: Tab) -> None: ...

	@abstractmethod
	def get_image(self, relative_path: str) -> PhotoImage: ...


class CMCTabFrame(ttk.Frame, ABC):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook, tab_title: str) -> None:
		super().__init__(notebook)
		notebook.add(self, text=tab_title)
		self.cmc = cmc
		self._loading = False
		self._loaded = False
		self.loading_text: str | None = None
		self.loading_error: str | None = None
		self.label_loading: ttk.Label | None = None

	def _load(self) -> bool:  # noqa: PLR6301
		"""Load any data needed for this tab. Return False on failure."""
		return True

	@abstractmethod
	def _build_gui(self) -> None: ...

	def refresh(self) -> None:
		raise NotImplementedError

	@final
	def load(self) -> None:
		if self._loaded or self._loading:
			return

		if self.label_loading is not None:
			# Previously errored while loading.
			return

		self._loading = True
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)
		self.label_loading = ttk.Label(
			self,
			text=self.loading_text or "",
			font=self.cmc.FONT_LARGE,
			justify=CENTER,
		)
		self.label_loading.grid()
		self.update_idletasks()

		if self._load():
			self.label_loading.destroy()
			self.label_loading = None
			self._loaded = True
		else:
			self.label_loading.configure(
				foreground=COLOR_BAD,
				text=self.loading_error or "Failed to load tab.",
			)

		self._loading = False
		self._build_gui()

	@final
	@property
	def is_loaded(self) -> bool:
		return self._loaded


class FileInfo(TypedDict):
	File: Path | None
	Version: tuple[int, int, int, int] | str | None
	InstallType: InstallType | None


class DLLInfo(TypedDict):
	IsF4SE: bool
	SupportsOG: NotRequired[bool]
	SupportsNG: NotRequired[bool]
