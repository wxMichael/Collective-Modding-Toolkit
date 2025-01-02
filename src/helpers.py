import logging
import platform
import re
import sys
import winreg
from abc import ABC, abstractmethod
from ctypes import windll
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import TYPE_CHECKING, NotRequired, TypedDict, final

import psutil

from enums import InstallType, ProblemType, SolutionType, Tab
from globals import COLOR_BAD, FONT_LARGE

if TYPE_CHECKING:
	import psutil._pswindows as pswin

	from autofixes import AutoFixResult
	from game_info import GameInfo

logger = logging.getLogger(__name__)


pattern_cpu = re.compile(r"(?:\d+(?:th|rd|nd) Gen| ?Processor| ?CPU|\d*[- ]Core|\(TM\)|\(R\))")
pattern_whitespace = re.compile(r"\s+")

os_versions = {
	"18362": "1903",
	"18363": "1909",
	"19041": "2004",
	"19042": "20H2",
	"19043": "21H1",
	"19044": "21H2",
	"19045": "22H2",
	"22000": "21H2",
	"22621": "22H2",
	"22631": "23H2",
	"26100": "24H2",
}


class PCInfo:
	def __init__(self) -> None:
		self.using_wine = hasattr(windll.ntdll, "wine_get_version")
		self.os = self._get_os() if not self.using_wine else "Linux (WINE)"
		self.ram = self._get_ram()
		self.cpu = self._get_cpu()
		self.gpu, self.vram = self._get_gpu()

	@staticmethod
	def _get_os() -> str:
		os = platform.system()
		release = platform.release()
		version = os_versions.get(str(sys.getwindowsversion().build), "") if os == "Windows" else ""
		return f"{os} {release} {version}"

	@staticmethod
	def _get_ram() -> int:
		mem: pswin.svmem = psutil.virtual_memory()  # type: ignore[reportUnknownVariableType]
		if TYPE_CHECKING:
			assert isinstance(mem, pswin.svmem)
		return round(mem.total / 1024**3)

	@staticmethod
	def _get_cpu() -> str:
		cpu_model = "Unknown CPU"
		try:
			with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, R"Hardware\Description\System\CentralProcessor\0") as key:
				model, value_type = winreg.QueryValueEx(key, "ProcessorNameString")
			if value_type == winreg.REG_SZ and isinstance(model, str):
				cpu_model = model
		except OSError:
			logger.exception("get_cpu():")
		else:
			if "Intel" in cpu_model and not cpu_model.startswith("Intel"):
				cpu_model = f"Intel {cpu_model.replace('Intel', '')}"
			cpu_model = pattern_cpu.sub("", cpu_model)
			cpu_model = pattern_whitespace.sub(" ", cpu_model)
			cpu_model = cpu_model.rsplit("@", 1)[0].strip()
		return cpu_model

	@staticmethod
	def _get_gpu() -> tuple[str, int]:
		gpu_model = "Unknown GPU"
		gpu_memory = 0
		try:
			with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, R"HARDWARE\DEVICEMAP\VIDEO") as key:
				video_device, value_type = winreg.QueryValueEx(key, R"\Device\Video0")
			if value_type == winreg.REG_SZ and isinstance(video_device, str):
				video_device = video_device.removeprefix("\\Registry\\Machine\\")
				with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, video_device) as key:
					model, value_type_1 = winreg.QueryValueEx(key, "HardwareInformation.AdapterString")
					memory, value_type_2 = winreg.QueryValueEx(key, "HardwareInformation.qwMemorySize")
				if value_type_1 == winreg.REG_SZ and isinstance(model, str):
					gpu_model = model.strip()
				if value_type_2 == winreg.REG_QWORD and isinstance(memory, int):
					gpu_memory = round(memory / 1024**3)
		except OSError:
			logger.exception("get_gpu():")
		return gpu_model, gpu_memory


class CMCheckerInterface(ABC):
	def __init__(self) -> None:
		self.root: Tk
		self.install_type_sv: StringVar
		self.game_path_sv: StringVar
		self.specs_sv_1: StringVar
		self.specs_sv_2: StringVar
		self.game: GameInfo
		self.pc: PCInfo
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
		logger.debug("Switch Tab : %s", self.__class__.__name__)
		if self._loaded:
			self._switch_to()
			return

		if self._loading:
			return

		if self.label_loading is not None:
			# Previously errored while loading.
			return

		logger.debug("Load Tab : %s", self.__class__.__name__)
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
			logger.error("Load Tab : %s : Failed : %s", self.__class__.__name__, self.loading_error)
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
		solution: SolutionType | str | None,
		*,
		file_list: list[tuple[int, Path]] | None = None,
		extra_data: list[str] | None = None,
	) -> None:
		self.type = problem
		self.path = path
		self.relative_path = relative_path
		self.mod = mod or ("<Unmanaged>" if problem != ProblemType.FileNotFound else "")
		self.summary = summary
		self.solution = solution
		self.file_list = file_list
		self.extra_data = extra_data
		self.autofix_result: AutoFixResult | None = None


class SimpleProblemInfo:
	def __init__(
		self,
		path: str,
		problem: str,
		summary: str,
		solution: str,
		*,
		file_list: list[tuple[int, Path]] | None = None,
		extra_data: list[str] | None = None,
	) -> None:
		self.path = path
		self.problem = problem
		self.summary = summary
		self.solution = solution
		self.type = problem
		self.relative_path = path
		self.mod = ""
		self.file_list = file_list
		self.extra_data = extra_data
		self.autofix_result: AutoFixResult | None = None


class Stderr:
	def __init__(self, root: Tk) -> None:
		self.root = root
		self.error_window: Toplevel | None = None
		self.txt: Text

	def create_window(self) -> None:
		if not self.error_window:
			self.error_window = Toplevel(self.root)
			self.error_window.wm_title("An Error Occurred")
			self.error_window.wm_protocol("WM_DELETE_WINDOW", self.on_close)
			self.txt = Text(self.error_window, width=120, height=25)
			self.txt.pack(expand=True, fill=BOTH)

	def write(self, string: str) -> int:
		logger.error("StdErr : %s", string)
		self.create_window()
		self.txt.insert("insert", string)
		return 0

	def flush(self) -> None:
		pass

	def on_close(self) -> None:
		if self.error_window:
			self.error_window.destroy()
			self.error_window = None
