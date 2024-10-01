from abc import ABC, abstractmethod
from enum import Enum, IntEnum, IntFlag, StrEnum
from pathlib import Path
from tkinter import PhotoImage, StringVar, Tk, ttk
from typing import NotRequired, TypedDict, final


class InstallType(StrEnum):
	OG = "Old-Gen"
	DG = "Down-Grade"
	NG = "Next-Gen"
	Unknown = "Unknown"


class Magic(bytes, Enum):
	BTDX = b"BTDX"
	GNRL = b"GNRL"
	DX10 = b"DX10"
	TES4 = b"TES4"
	HEDR = b"HEDR"


class Tab(StrEnum):
	Overview = "Overview"
	F4SE = "F4SE"
	Errors = "Errors"
	Conflicts = "Conflicts"
	Suggestions = "Suggestions"
	Tools = "Tools"
	About = "About"


class CMCheckerInterface(ABC):
	def __init__(self) -> None:
		self.window: Tk
		self.data_path: Path | None
		self.f4se_path: Path | None
		self.archives_og: set[Path]
		self.archives_ng: set[Path]
		self.archives_invalid: set[Path]
		self.modules_invalid: set[Path]
		self.modules_v95: set[Path]
		self.FONT: tuple[str, int]
		self.FONT_SMALL: tuple[str, int]
		self.FONT_LARGE: tuple[str, int]
		self.install_type_sv: StringVar
		self.game_path_sv: StringVar

	@property
	@abstractmethod
	def install_type(self) -> InstallType: ...

	@install_type.setter
	@abstractmethod
	def install_type(self, value: InstallType) -> None: ...

	@property
	@abstractmethod
	def game_path(self) -> Path: ...

	@game_path.setter
	@abstractmethod
	def game_path(self, value: Path) -> None: ...

	@abstractmethod
	def refresh_tab(self, tab: Tab) -> None: ...

	@abstractmethod
	def get_image(self, relative_path: str) -> PhotoImage: ...

	@abstractmethod
	def find_game_paths(self) -> None: ...

	@final
	def is_foog(self) -> bool:
		return self.install_type in {InstallType.OG, InstallType.DG}

	@final
	def is_fong(self) -> bool:
		return self.install_type == InstallType.NG

	@final
	def is_fodg(self) -> bool:
		return self.install_type == InstallType.DG


class CMCTabFrame(ttk.Frame, ABC):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook, tab_title: str) -> None:
		super().__init__(notebook)
		notebook.add(self, text=tab_title)
		self.cmc = cmc
		self._loaded = False

	@abstractmethod
	def _load(self) -> None: ...

	def refresh(self) -> None:
		raise NotImplementedError

	@final
	def load(self) -> None:
		if self._loaded:
			return
		self._load()
		self._loaded = True

	@final
	@property
	def is_loaded(self) -> bool:
		return self._loaded


class LogType(StrEnum):
	Info = "info"
	Good = "good"
	Bad = "bad"


class ArchiveVersion(IntEnum):
	OG = 1
	NG7 = 7
	NG = 8


class ModuleFlag(IntFlag):
	Light = 0x0200


class BaseGameFile(TypedDict):
	OnlyOG: NotRequired[bool]
	UseHash: NotRequired[bool]
	Versions: dict[str, InstallType]


class FileInfo(TypedDict):
	File: Path | None
	Version: tuple[int, int, int, int] | str | None
	InstallType: InstallType | None


class DLLInfo(TypedDict):
	IsF4SE: bool
	SupportsOG: NotRequired[bool]
	SupportsNG: NotRequired[bool]
