import os
import sys
import winreg
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Literal

from enums import InstallType
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
		self.archives_og: set[Path] = set()
		self.archives_ng: set[Path] = set()
		self.archives_invalid: set[Path] = set()
		self.modules_invalid: set[Path] = set()
		self.modules_v95: set[Path] = set()
		self.file_info: dict[str, FileInfo] = {}
		self.address_library: Path | None = None
		self.ckfixes_found = False

		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.module_count_full = 0
		self.module_count_light = 0
		self.module_count_v1 = 0
		self.manager = find_mod_manager()
		self.find_path()

	def reset_binaries(self) -> None:
		self.install_type = InstallType.Unknown
		self.file_info.clear()
		self.address_library = None
		self.ckfixes_found = False

	def reset_modules(self) -> None:
		self.module_count_full = 0
		self.module_count_light = 0
		self.modules_v95.clear()
		self.modules_invalid.clear()

	def reset_archives(self) -> None:
		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.archives_og.clear()
		self.archives_ng.clear()
		self.archives_invalid.clear()

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

				if (self.manager.exe_path.parent / "portable.txt").is_file():
					if not portable_ini_exists:
						raise FileNotFoundError
					self.manager.read_mo2_ini(portable_ini_path)

				elif get_registry_value(
					winreg.HKEY_CURRENT_USER,
					R"Software\Mod Organizer Team\Mod Organizer",
					"CurrentInstance",
				):
					appdata_local = os.getenv("LOCALAPPDATA")
					if appdata_local:
						appdata_ini_path = Path(appdata_local) / "ModOrganizer/ModOrganizer.ini"
						if appdata_ini_path.is_file():
							self.manager.read_mo2_ini(appdata_ini_path)

				if not self.manager.game_path:
					if not portable_ini_exists:
						raise FileNotFoundError
					self.manager.read_mo2_ini(portable_ini_path)

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

		if game_path is None:
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
			raise FileNotFoundError

		self.game_path = game_path_as_path

	def is_foog(self) -> bool:
		return self._install_type in {InstallType.OG, InstallType.DG}

	def is_fong(self) -> bool:
		return self._install_type == InstallType.NG

	def is_fodg(self) -> bool:
		return self._install_type == InstallType.DG
