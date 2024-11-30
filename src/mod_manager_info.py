import csv
from pathlib import Path
from tkinter import *
from typing import Literal, TypedDict

from packaging.version import Version


class MO2Settings(TypedDict, total=False):
	gameName: Literal["Fallout 4"]
	gamePath: Path
	selected_profile: str
	base_directory: Path
	cache_directory: Path
	download_directory: Path
	mod_directory: Path
	overwrite_directory: Path
	profile_local_inis: bool
	profile_local_saves: bool
	profiles_directory: Path
	skip_file_suffixes: tuple[str, ...]
	skip_directories: set[str]


class ModManagerInfo:
	def __init__(self, name: Literal["Mod Organizer", "Vortex"], path: Path, version: Version) -> None:
		self.name: Literal["Mod Organizer", "Vortex"] = name
		self.exe_path = path
		self.version = version

		self.ini_path: Path
		self.portable_txt_path: Path | None = None
		self.portable: bool = False
		self.game_path: Path | None = None
		self.stage_path: Path | None = None
		self.overwrite_path: Path | None = None
		self.profiles_path: Path | None = None
		self.selected_profile: str | None = None

		self.skip_file_suffixes: tuple[str, ...]
		self.skip_directories: set[str]

		self.mo2_settings: MO2Settings = {}

	def read_mo2_ini(self, ini_path: Path) -> None:
		self.ini_path = ini_path
		mo2_setting_list = {
			"[General]": {
				"gameName",
				"gamePath",
				"selected_profile",
			},
			"[Settings]": {
				"base_directory",
				"cache_directory",
				"download_directory",
				"mod_directory",
				"overwrite_directory",
				"profile_local_inis",
				"profile_local_saves",
				"profiles_directory",
				"skip_file_suffixes",
				"skip_directories",
			},
		}
		# Default values
		self.mo2_settings = {
			"base_directory": ini_path.parent,
			"cache_directory": Path("%BASE_DIR%/webcache"),
			"download_directory": Path("%BASE_DIR%/downloads"),
			"mod_directory": Path("%BASE_DIR%/mods"),
			"overwrite_directory": Path("%BASE_DIR%/overwrite"),
			"profile_local_inis": False,
			"profile_local_saves": False,
			"profiles_directory": Path("%BASE_DIR%/profiles"),
			"skip_file_suffixes": (".mohidden",),
			"skip_directories": set(),
		}

		with ini_path.open() as ini_file:
			ini_contents = ini_file.read().splitlines()

		section = None
		for line in ini_contents:
			if line.startswith("["):
				if line in mo2_setting_list:
					section = line
				continue
			if section is None:
				continue
			try:
				setting, value = line.split("=", 1)
			except ValueError:
				continue
			if setting in mo2_setting_list[section]:
				self.mo2_settings[setting] = value[11:-1] if value.startswith("@ByteArray(") else value
				if setting == "base_directory":
					self.mo2_settings["base_directory"] = Path(str(self.mo2_settings["base_directory"]))
				continue

		for name, val in self.mo2_settings.items():
			if name != "base_directory" and name.endswith(("directory", "Path")):
				if isinstance(val, str):
					if "%BASE_DIR%" in val:
						self.mo2_settings[name] = self.mo2_settings["base_directory"] / val.replace("%BASE_DIR%", "")
				elif isinstance(val, Path) and val.parts[0] == "%BASE_DIR%":
					self.mo2_settings[name] = self.mo2_settings["base_directory"] / val.relative_to("%BASE_DIR%")
			elif name.startswith("skip_"):
				self.mo2_settings[name] = next(csv.reader((str(val),), doublequote=False, escapechar="\\", skipinitialspace=True))

		if self.mo2_settings.get("gameName", "Fallout 4") != "Fallout 4":
			msg = "Only Fallout 4 is supported."
			raise ValueError(msg)

		if "selected_profile" not in self.mo2_settings:
			msg = "Profile is not set in ModOrganizer.ini."
			raise ValueError(msg)

		if "gamePath" in self.mo2_settings:
			self.game_path = Path(self.mo2_settings["gamePath"])

		self.selected_profile = self.mo2_settings["selected_profile"]
		self.stage_path = self.mo2_settings["mod_directory"]
		self.overwrite_path = self.mo2_settings["overwrite_directory"]
		self.profiles_path = self.mo2_settings["profiles_directory"]
		self.skip_file_suffixes = tuple(self.mo2_settings["skip_file_suffixes"])
		self.skip_directories = set(self.mo2_settings["skip_directories"])
