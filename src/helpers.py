from abc import ABC, abstractmethod
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import TYPE_CHECKING, NotRequired, TypedDict, final

from enums import InstallType, ProblemType, SolutionType, Tab
from globals import FONT_LARGE

if TYPE_CHECKING:
	from game_info import GameInfo

COLOR_BAD = "firebrick1"


class CMCheckerInterface(ABC):
	def __init__(self) -> None:
		self.root: Tk
		self.install_type_sv: StringVar
		self.game_path_sv: StringVar
		self.game: GameInfo
		self.overview_problems: list[ProblemInfo | SimpleProblemInfo]

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
		self.sv_loading_text = StringVar()
		self.loading_error: str | None = None
		self.label_loading: ttk.Label | None = None

	def _load(self) -> bool:  # noqa: PLR6301
		"""Load any data needed for this tab. Return False on failure."""
		return True

	def switch_from(self) -> None:  # noqa: PLR6301
		return

	def _switch_to(self) -> None:  # noqa: PLR6301
		return

	@abstractmethod
	def _build_gui(self) -> None: ...

	def refresh(self) -> None:
		raise NotImplementedError

	@final
	def load(self) -> None:
		if self._loaded:
			self._switch_to()
			return

		if self._loading:
			return

		if self.label_loading is not None:
			# Previously errored while loading.
			return

		self._loading = True
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)
		self.sv_loading_text.set(self.loading_text or "")
		self.label_loading = ttk.Label(
			self,
			textvariable=self.sv_loading_text,
			font=FONT_LARGE,
			justify=CENTER,
		)
		self.label_loading.grid()

		if self._load():
			self.label_loading.destroy()
			self.label_loading = None
			self._loaded = True
			self._build_gui()
			self._switch_to()
		else:
			self.sv_loading_text.set(self.loading_error or "Failed to load tab.")
			self.label_loading.configure(foreground=COLOR_BAD)
		self._loading = False

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


class ProblemInfo:
	def __init__(
		self,
		problem: ProblemType,
		path: Path,
		relative_path: Path,
		mod: str | None,
		summary: str,
		solution: SolutionType | None,
		extra_data: list[str] | None = None,
	) -> None:
		self.type = problem
		self.path = path
		self.relative_path = relative_path
		self.mod = mod or "<Unmanaged>"
		self.summary = summary
		self.solution = solution
		self.extra_data = extra_data


class SimpleProblemInfo:
	def __init__(self, path: str, problem: str, summary: str, solution: str, extra_data: list[str] | None = None) -> None:
		self.path = path
		self.problem = problem
		self.summary = summary
		self.solution = solution
		self.type = problem
		self.relative_path = path
		self.mod = ""
		self.extra_data = extra_data


class Stderr:
	def __init__(self, root: Tk) -> None:
		self.root = root
		self.error_window: Toplevel | None = None
		self.txt: Text

	def create_window(self) -> None:
		if not self.error_window:
			self.error_window = Toplevel(self.root, width=900, height=700)
			self.error_window.wm_title("An Error Occurred")
			self.error_window.wm_protocol("WM_DELETE_WINDOW", self.on_close)
			self.txt = Text(self.error_window)
			self.txt.pack()

	def write(self, string: str) -> int:
		self.create_window()
		self.txt.insert("insert", string)
		return 0

	def flush(self) -> None:
		pass

	def on_close(self) -> None:
		if self.error_window:
			self.error_window.destroy()
			self.error_window = None
