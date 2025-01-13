from enum import Enum
from tkinter import *
from typing import TYPE_CHECKING

from globals import *

if TYPE_CHECKING:
	from pathlib import Path

	from tabs._scanner import SidePane

IGNORE_FOLDERS = {
	"bodyslide",
	"fo4edit",
	"robco_patcher",
	"source",
}
"""These are always lowercase."""

DATA_WHITELIST = {
	"complex sorter": None,
	"f4se": None,
	"materials": {"bgem", "bgsm", "txt"},
	"meshes": {
		"bto",
		"btr",
		"hko",
		"hkx",
		"hkx_back",
		"hkx_backup",
		"lst",
		"max",
		"nif",
		"obj",
		"sclp",
		"ssf",
		"tri",
		"txt",
		"xml",
	},
	"music": {"wav", "xwm"},
	"textures": {"dds"},
	"scripts": {"pex", "psc", "txt", "zip"},
	"sound": {"cdf", "fuz", "lip", "wav", "xwm"},
	"vis": {"uvd"},
}
"""Keys and values are lowercase with no dot."""

JUNK_FILES = {
	"thumbs.db",
	"desktop.ini",
	".ds_store",
}

JUNK_FILE_SUFFIXES = (
	".tmp",
	".bak",
)

PROPER_FORMATS = {
	# Textures
	"bmp": ["dds"],
	"jpeg": ["dds"],
	"jpg": ["dds"],
	"png": ["dds"],
	"psd": ["dds"],
	"tga": ["dds"],
	# Sound
	"mp3": ["wav", "xwm"],
}
"Keys and values are always lowercase with no dot."

RECORD_TYPES = {
	# Sound
	"mp3": "Sound Descriptor (SNDR) or Music Track (MUST) ",
}
"Keys are always lowercase with no dot."


class ScanSetting(Enum):
	OverviewIssues = ("Overview Issues", TOOLTIP_SCAN_OVERVIEW)
	Errors = ("Errors", TOOLTIP_SCAN_ERRORS)
	WrongFormat = ("Wrong File Formats", TOOLTIP_SCAN_FORMATS)
	LoosePrevis = ("Loose Previs", TOOLTIP_SCAN_PREVIS)
	JunkFiles = ("Junk Files", TOOLTIP_SCAN_JUNK)
	ProblemOverrides = ("Problem Overrides", TOOLTIP_SCAN_BAD_OVERRIDES)
	RaceSubgraphs = ("Race Subgraphs", TOOLTIP_SCAN_RACE_SUBGRAPHS)


class ModFiles:
	def __init__(self) -> None:
		self.folders: dict[Path, tuple[str, Path]] = {}
		self.files: dict[Path, tuple[str, Path]] = {}
		self.modules: dict[str, tuple[str, Path]] = {}
		self.archives: dict[str, tuple[str, Path]] = {}


class ScanSettings(dict[ScanSetting, bool]):
	def __init__(self, side_pane: "SidePane") -> None:
		super().__init__()

		self.skip_data_scan = True
		self.mod_files: ModFiles | None = None

		non_data = {
			ScanSetting.OverviewIssues,
			ScanSetting.RaceSubgraphs,
		}

		settings = side_pane.scanner_tab.cmc.settings
		resave = False
		for setting in ScanSetting:
			self[setting] = side_pane.bool_vars[setting].get()
			if self[setting] and setting not in non_data:
				self.skip_data_scan = False

			name = str(f"scanner_{setting.name}")
			if settings.dict[name] != self[setting]:
				settings.dict[name] = self[setting]
				resave = True
		if resave:
			settings.save()

		self.manager = side_pane.scanner_tab.cmc.game.manager
		self.using_stage = side_pane.scanner_tab.using_stage
		if self.manager and self.manager.name == "Mod Organizer":
			self.skip_file_suffixes = (*self.manager.skip_file_suffixes, ".vortex_backup")
			self.skip_directories = IGNORE_FOLDERS.union(self.manager.skip_directories)
		else:
			self.skip_file_suffixes = (".vortex_backup",)
			self.skip_directories = IGNORE_FOLDERS
