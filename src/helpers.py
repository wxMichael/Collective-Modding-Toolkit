from abc import ABC, abstractmethod
from enum import Enum, IntEnum, IntFlag, StrEnum
from pathlib import Path
from tkinter import PhotoImage, Tk
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


class CMCheckerInterface(ABC):
	def __init__(self) -> None:
		self.window: Tk
		self.data_path: Path | None
		self.archives_og: set[Path]
		self.archives_ng: set[Path]
		self.modules_v95: set[Path]
		self.FONT: tuple[str, int]
		self.FONT_SMALL: tuple[str, int]
		self.FONT_LARGE: tuple[str, int]

	@property
	@abstractmethod
	def install_type(self) -> InstallType: ...

	@property
	@abstractmethod
	def game_path(self) -> Path: ...

	@abstractmethod
	def refresh_overview(self) -> None: ...

	@abstractmethod
	def get_image(self, relative_path: str) -> PhotoImage: ...

	@final
	def is_foog(self) -> bool:
		return self.install_type in {InstallType.OG, InstallType.DG}

	@final
	def is_fong(self) -> bool:
		return self.install_type == InstallType.NG

	@final
	def is_fodg(self) -> bool:
		return self.install_type == InstallType.DG


class Tab(StrEnum):
	Overview = "Overview"
	F4SE_DLLs = "F4SE_DLLs"
	Errors = "Errors"
	Conflicts = "Conflicts"
	Suggestions = "Suggestions"
	Tools = "Tools"
	About = "About"


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
