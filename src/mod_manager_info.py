import csv
import sys
from pathlib import Path
from tkinter import *
from typing import Literal, TypedDict

from packaging.version import Version

from enums import Tool

win11_24h2 = sys.getwindowsversion().build >= 26100


def is_file(path: Path) -> bool:
	if not win11_24h2:
		return path.is_file()

	try:
		with path.open():
			pass
	except FileNotFoundError:
		return False
	except PermissionError:
		# Probably a folder
		try:
			_ = next(path.iterdir(), None)
		except NotADirectoryError:
			# Was a file with actual PermissionError
			return True
		except OSError:
			pass
		return False
	return True


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
		"""These are always lowercase."""
		self.skip_directories: set[str]
		"""These are always lowercase."""

		self.mo2_settings: MO2Settings = {}
		self.executables: dict[Tool, set[Path]] = {}

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
			"[customExecutables]": {""},
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

		section = None
		for line in ini_path.read_text(encoding="utf-8").splitlines():
			if line.startswith("["):
				section = line if line in mo2_setting_list else None
				continue
			if section is None:
				continue
			try:
				setting, value = line.split("=", 1)
			except ValueError:
				continue
			if section == "[customExecutables]":
				if setting.endswith("binary"):
					value_lower = value.lower()

					for tool in Tool:
						if value_lower.endswith(tool):
							exe_path = Path(value)
							if is_file(exe_path):
								self.executables.setdefault(tool, set()).add(exe_path)
							if tool == Tool.xEdit:
								bsarch_path = exe_path.with_name("BSArch.exe")
								if is_file(bsarch_path):
									self.executables.setdefault(Tool.BSArch, set()).add(bsarch_path)
							break
				continue

			if setting in mo2_setting_list[section]:
				self.mo2_settings[setting] = value[11:-1] if value.startswith("@ByteArray(") else value
				if setting == "base_directory":
					self.mo2_settings["base_directory"] = Path(str(self.mo2_settings["base_directory"]))
				continue

		for name, val in self.mo2_settings.items():
			if name != "base_directory":
				if name.endswith(("directory", "Path")):
					if isinstance(val, str):
						if "%BASE_DIR%" in val:
							self.mo2_settings[name] = self.mo2_settings["base_directory"] / val.replace("%BASE_DIR%", "")
						else:
							self.mo2_settings[name] = Path(val)
					elif isinstance(val, Path) and val.parts[0] == "%BASE_DIR%":
						self.mo2_settings[name] = self.mo2_settings["base_directory"] / val.relative_to("%BASE_DIR%")
				elif name.startswith("skip_"):
					csv_reader = csv.reader((str(val),), doublequote=False, escapechar="\\", skipinitialspace=True)
					self.mo2_settings[name] = next(csv_reader)

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
		self.skip_file_suffixes = tuple(s.lower() for s in self.mo2_settings["skip_file_suffixes"])
		self.skip_directories = {s.lower() for s in self.mo2_settings["skip_directories"]}
