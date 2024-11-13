from pathlib import Path
from tkinter import *
from typing import Literal

from packaging.version import Version


class ModManagerInfo:
	def __init__(self, name: Literal["Mod Organizer", "Vortex"], path: Path, version: Version) -> None:
		self.name = name
		self.exe_path = path
		self.version = version

		self.selected_profile: str | None = None
		self.game_path: Path | None = None
		self.base_directory: Path | None = None
		self.stage_path: Path | None = None

	def read_mo2_ini(self, ini_path: Path) -> None:
		game_name = None
		selected_profile = None
		game_path = None
		base_directory = None
		with ini_path.open() as ini_file:
			for file_line in ini_file:
				line = file_line.removesuffix("\n")
				if game_name is None and line.startswith("gameName"):
					game_name = line.split("=", 1)[-1]
					if game_name != "Fallout 4":
						msg = "Only Fallout 4 is supported."
						raise ValueError(msg)
					# self.game_name = game_name
					continue

				if selected_profile is None and line.startswith("selected_profile"):
					selected_profile = line.split("=", 1)[-1]
					if selected_profile.startswith("@ByteArray("):
						selected_profile = selected_profile[11:-1]
					if not selected_profile:
						msg = "Profile is not set in ModOrganizer.ini."
						raise ValueError(msg)
					self.selected_profile = selected_profile
					continue

				if game_path is None and line.startswith("gamePath"):
					game_path = line.split("=", 1)[-1]
					if game_path.startswith("@ByteArray("):
						game_path = game_path[11:-1]
					if not game_path:
						msg = "gamePath is not set in ModOrganizer.ini."
						raise ValueError(msg)
					self.game_path = Path(game_path)
					continue

				if base_directory is None and line.startswith("base_directory"):
					base_directory = line.split("=", 1)[-1]
					if base_directory.startswith("@ByteArray("):
						base_directory = base_directory[11:-1]
					self.base_directory = Path(base_directory) if base_directory else self.exe_path.parent
					continue
