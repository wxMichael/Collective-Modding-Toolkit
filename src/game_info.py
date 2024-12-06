import os
import sys
import winreg
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Literal

from enums import InstallType, Language
from utils import (
	find_mod_manager,
	get_registry_value,
	is_fo4_dir,
)

if TYPE_CHECKING:
	from helpers import FileInfo


class GameInfo:
	def __init__(self, install_type_sv: StringVar, game_path_sv: StringVar) -> None:
		self._install_type_sv = install_type_sv
		self._game_path_sv = game_path_sv
		self.name: Literal["Fallout4"]
		self.install_type = InstallType.Unknown
		self._game_path: Path
		self._data_path: Path | None = None
		self._f4se_path: Path | None = None
		self.archives_gnrl: set[Path] = set()
		self.archives_dx10: set[Path] = set()
		self.archives_og: set[Path] = set()
		self.archives_ng: set[Path] = set()
		self.archives_enabled: set[Path] = set()
		self.archives_unreadable: set[Path] = set()
		self.modules_unreadable: set[Path] = set()
		self.modules_hedr_95: set[Path] = set()
		self.modules_hedr_unknown: set[Path] = set()
		self.modules_enabled: list[Path] = []
		self.file_info: dict[str, FileInfo] = {}
		self.address_library: Path | None = None
		self.ckfixes_found = False
		self.game_settings: dict[str, dict[str, str]] = {}
		self.game_prefs: dict[str, dict[str, str]] = {}
		self.language = Language.English

		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.module_count_full = 0
		self.module_count_light = 0
		self.module_count_v1 = 0
		self.manager = find_mod_manager()
		self.find_path()
		self.load_game_inis()

	def load_game_inis(self) -> None:
		# TODO: Replace with ini_file code?
		docs_path = Path.home() / R"Documents\My Games\Fallout4"
		section = "NO-SECTION"
		for name in ("Fallout4.ini", "Fallout4Prefs.ini", "Fallout4Custom.ini"):
			ini_path = docs_path / name
			if not ini_path.is_file():
				continue
			ini_dict = self.game_prefs if name == "Fallout4Prefs.ini" else self.game_settings
			for line in ini_path.read_text(encoding="utf-8").splitlines():
				if line.startswith("[") and line.endswith("]"):
					section = line[1:-1].lower()
					if section not in ini_dict:
						ini_dict[section] = {}
					continue
				try:
					setting, value = line.split("=", 1)
				except ValueError:
					continue
				ini_dict[section][setting.lower()] = value

		try:
			self.language = Language(self.game_settings.get("general", {}).get("slanguage", "en").lower())
		except ValueError:
			self.language = Language.English
			# TODO: Warn on invalid language. suggest bethini pie
		if self.language == Language.English:
			self.ba2_suffixes: tuple[str, ...] = ("main", "textures", "voices_en")
		else:
			self.ba2_suffixes = ("main", "textures", "voices_en", f"voices_{self.language}")

	def reset_binaries(self) -> None:
		self.install_type = InstallType.Unknown
		self.file_info.clear()
		self.address_library = None
		self.ckfixes_found = False

	def reset_modules(self) -> None:
		self.module_count_full = 0
		self.module_count_light = 0
		self.module_count_v1 = 0
		self.modules_hedr_95.clear()
		self.modules_hedr_unknown.clear()
		self.modules_enabled.clear()
		self.modules_unreadable.clear()

	def reset_archives(self) -> None:
		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.archives_gnrl.clear()
		self.archives_dx10.clear()
		self.archives_og.clear()
		self.archives_ng.clear()
		self.archives_enabled.clear()
		self.archives_unreadable.clear()

	@property
	def game_path(self) -> Path:
		return self._game_path

	@game_path.setter
	def game_path(self, value: Path) -> None:
		self._game_path = value
		self._game_path_sv.set(str(value))

		data_path = value / "Data"
		if data_path.is_dir():
			self._data_path = data_path
			f4se_path = data_path / "F4SE/Plugins"
			self._f4se_path = f4se_path if f4se_path.is_dir() else None
		else:
			self._data_path = None
			self._f4se_path = None

	@property
	def data_path(self) -> Path | None:
		return self._data_path

	@property
	def f4se_path(self) -> Path | None:
		return self._f4se_path

	@property
	def install_type(self) -> InstallType:
		return self._install_type

	@install_type.setter
	def install_type(self, value: InstallType) -> None:
		self._install_type = value
		self._install_type_sv.set(str(value))

	def find_path(self) -> None:
		if self.manager is not None:
			if self.manager.name == "Mod Organizer":
				portable_ini_path = self.manager.exe_path.parent / "ModOrganizer.ini"
				portable_ini_exists = portable_ini_path.is_file()

				portable_txt_path = self.manager.exe_path.parent / "portable.txt"
				if portable_txt_path.is_file():
					if not portable_ini_exists:
						msg = "portable.txt found but no ModOrganizer.ini found in MO2 install path"
						raise FileNotFoundError(msg)
					self.manager.read_mo2_ini(portable_ini_path)
					self.manager.portable = True
					self.manager.portable_txt_path = portable_txt_path

				else:
					current_instance = get_registry_value(
						winreg.HKEY_CURRENT_USER,
						R"Software\Mod Organizer Team\Mod Organizer",
						"CurrentInstance",
					)
					if current_instance:
						appdata_local = os.getenv("LOCALAPPDATA")
						if appdata_local:
							appdata_ini_path = Path(appdata_local) / "ModOrganizer" / current_instance / "ModOrganizer.ini"
							if appdata_ini_path.is_file():
								self.manager.read_mo2_ini(appdata_ini_path)

				if not self.manager.game_path:
					if not portable_ini_exists:
						msg = "Unable to find ModOrganizer.ini. Please report this along with your MO2 instance details."
						raise FileNotFoundError(msg)
					self.manager.read_mo2_ini(portable_ini_path)
					self.manager.portable = True

			elif self.manager.name == "Vortex":
				pass

			if self.manager.game_path:
				self.game_path = self.manager.game_path
				return

		if is_fo4_dir(Path.cwd()):
			self.game_path = Path.cwd()
			return

		game_path = get_registry_value(
			winreg.HKEY_LOCAL_MACHINE,
			R"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4",
			"Installed Path",
		) or get_registry_value(
			winreg.HKEY_LOCAL_MACHINE,
			R"SOFTWARE\WOW6432Node\GOG.com\Games\1998527297",
			"path",
		)

		if not game_path:
			ask_location = messagebox.askyesno(
				"Fallout 4 Not Found",
				(
					"Your Fallout 4 installation could not be detected.\n"
					"This is usually due to the game being moved or the launcher not being run once from its current location.\n\n"
					"Manually specify a location? CM Toolkit will close otherwise."
				),
			)
			if not ask_location:
				sys.exit()

			game_path = filedialog.askopenfilename(
				title="Select Fallout4.exe",
				filetypes=(("Fallout 4", "Fallout4.exe"),),
			)

			if not game_path:
				# Empty string if filedialog cancelled
				messagebox.showerror(
					"Game not found",
					"A Fallout 4 installation could not be found.",
				)
				sys.exit()

		game_path_as_path = Path(game_path)
		if game_path_as_path.is_file():
			game_path_as_path = game_path_as_path.parent

		if not is_fo4_dir(game_path_as_path):
			messagebox.showerror(
				"Game not found",
				"A Fallout 4 installation could not be found.",
			)
			sys.exit()

		self.game_path = game_path_as_path

	def is_foog(self) -> bool:
		return self._install_type in {InstallType.OG, InstallType.DG}

	def is_fong(self) -> bool:
		return self._install_type == InstallType.NG

	def is_fodg(self) -> bool:
		return self._install_type == InstallType.DG
