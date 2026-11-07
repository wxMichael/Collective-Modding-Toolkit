#
# Collective Modding Toolkit
# Copyright (C) 2024, 2025  wxMichael
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
#


import queue
import stat
from pathlib import Path
from shutil import copy2
from threading import Thread
from tkinter import *
from tkinter import ttk
from types import MappingProxyType
from typing import TYPE_CHECKING

import pyxdelta
import requests

from enums import LogType, Tab
from globals import *
from logger import Logger
from modal_window import AboutWindow, ModalWindow
from utils import (
	add_tooltip,
	get_crc32,
	is_file,
)

if TYPE_CHECKING:
	from helpers import (
		CMCheckerInterface,
	)

COLOR_OG = "dodger blue"
COLOR_NG = "SlateBlue1"
COLOR_AE = "salmon"
PATCH_URL_BASE = "https://github.com/wxMichael/Collective-Modding-Toolkit/releases/download/delta-patches/"

SUPPORTED_VERSIONS = (InstallType.OG, InstallType.NG, InstallType.AE)
PATCH_PREFIXES = MappingProxyType({
	InstallType.OG: "OG",
	InstallType.NG: "NG",
	InstallType.AE: "AE",
})

BACKUP_SUFFIXES = MappingProxyType({
	InstallType.OG: "_upgradeBackup",
	InstallType.NG: "_downgradeBackup",
	InstallType.AE: "_anniversaryBackup",
})


class Downgrader(ModalWindow):
	CRCs_game = MappingProxyType({
		"Fallout4.exe": {
			"97DA3E03": InstallType.Obsolete,  # 1.10.120
			"2ED2A242": InstallType.Obsolete,  # 1.10.130
			"A0100017": InstallType.Obsolete,  # 1.10.138
			"9ABC94F0": InstallType.Obsolete,  # 1.10.162
			"C6053902": InstallType.OG,  # 1.10.163
			"B61675B1": InstallType.Obsolete,  # 1.10.980
			"C5965A2E": InstallType.NG,  # 1.10.984
			"0AEB19A7": InstallType.Obsolete,  # 1.11.137
			"1E90BE57": InstallType.Obsolete,  # 1.11.159
			"0481725D": InstallType.Obsolete,  # 1.11.169a
			"0E176ABC": InstallType.Obsolete,  # 1.11.169b
			"CF47788D": InstallType.Obsolete,  # 1.11.191
			"67545AFB": InstallType.AE,  # 1.11.240
		},
		"Fallout4Launcher.exe": {
			"02445570": InstallType.OG,  # 1.10.120 to 1.10.163
			"F6A06FF5": InstallType.NG,  # 1.10.980 to 1.10.984
			"0E696744": InstallType.Obsolete,  # 1.11.137
			"D15C6A49": InstallType.Obsolete,  # 1.11.159
			"8C52BE93": InstallType.Obsolete,  # 1.11.169a
			"591009C9": InstallType.Obsolete,  # 1.11.169b
			"720BB9C3": InstallType.Obsolete,  # 1.11.191
			"CA61EDD7": InstallType.Obsolete,  # 1.11.221
			"57D1C794": InstallType.AE,  # 1.11.240
		},
		"steam_api64.dll": {
			"BBD912FC": InstallType.OG,
			"E36E7B4D": InstallType.NGAE,
		},
	})
	CRCs_ck = MappingProxyType({
		"CreationKit.exe": {
			"0F5C065B": InstallType.OG,  # 1.10.163
			"481CCE95": InstallType.NG,  # 1.10.984
			"49E45284": InstallType.Obsolete,  # 1.11.191
			"3E8BBBE7": InstallType.AE,  # 1.11.240
		},
		"Tools\\Archive2\\Archive2.exe": {
			"4CDFC7B5": InstallType.OG,  # 1.10.163
			"71A5240B": InstallType.NG,  # 1.10.984
			"C867674F": InstallType.Obsolete,  # 1.11.191
			"B2EEF34A": InstallType.AE,  # 1.11.240
		},
		"Tools\\Archive2\\Archive2Interop.dll": {
			"850D36A9": InstallType.OG,  # 1.10.163
			"EFBE3622": InstallType.NG,  # 1.10.984
			"7B893B0D": InstallType.Obsolete,  # 1.11.191
			"2690FD20": InstallType.AE,  # 1.11.240
		},
	})
	CRCs_by_type: MappingProxyType[InstallType, list[str]] = MappingProxyType({
		InstallType.Obsolete: [],
		InstallType.OG: [],
		InstallType.NG: [],
		InstallType.AE: [],
	})
	for CRCs in list(CRCs_game.values()) + list(CRCs_ck.values()):
		for crc, install_type in CRCs.items():
			if install_type == InstallType.NGAE:
				CRCs_by_type[InstallType.NG].append(crc)
				CRCs_by_type[InstallType.AE].append(crc)
			else:
				CRCs_by_type[install_type].append(crc)

	def __init__(self, parent: Wm, cmc: CMCheckerInterface) -> None:
		super().__init__(parent, cmc, "Downgrader", 600, 334)

		self.current_versions: dict[str, InstallType] = {}
		self.unknown_game = False
		self.unknown_ck = False

		self.version_labels: list[ttk.Label] = []

		self.download_queue: queue.Queue[tuple[str, Path, Path]] = queue.Queue()
		self.download_progress_updates: queue.Queue[float] = queue.Queue()
		self.download_or_patch_in_progress = False
		self.download_thread: Thread | None = None
		self.download_error: str | None = None

		self.get_info()

		current_game_version = self.current_versions["Fallout4.exe"]
		self.sv_desired_version = StringVar(
			value=current_game_version if current_game_version in SUPPORTED_VERSIONS else InstallType.NG,
		)
		self.bv_keep_backups = BooleanVar(value=cmc.settings.dict["downgrader_keep_backups"])
		self.bv_delete_deltas = BooleanVar(value=cmc.settings.dict["downgrader_delete_deltas"])

		self.build_gui()

	def get_info(self) -> None:
		self.unknown_game = False
		self.unknown_ck = False
		for file_name, file_crcs in list(Downgrader.CRCs_game.items()) + list(Downgrader.CRCs_ck.items()):
			file_path = self.cmc.game.game_path / file_name
			if is_file(file_path):
				crc = get_crc32(file_path)
				self.current_versions[file_name] = file_crcs.get(crc, InstallType.Unknown)
			else:
				self.current_versions[file_name] = InstallType.NotFound

			if self.current_versions[file_name] in {InstallType.Unknown, InstallType.NotFound}:
				if file_name in self.CRCs_game:
					self.unknown_game = True
				else:
					self.unknown_ck = True

	def build_gui(self) -> None:
		self.grid_columnconfigure(2, weight=1)
		self.frame_game = ttk.Labelframe(self, text="Current Game", padding=scale(5))
		self.frame_game.grid(column=0, row=0, rowspan=2, sticky=NSEW, padx=scale(10))
		self.frame_game.grid_columnconfigure(0, weight=1)
		self.frame_ck = ttk.Labelframe(self, text="Current Creation Kit", padding=scale(5))
		self.frame_ck.grid(column=0, row=2, rowspan=2, sticky=NSEW, padx=scale(10))
		self.frame_ck.grid_columnconfigure(0, weight=1)

		file_names_game = "\n".join([f"{Path(f).name}:" for f in self.CRCs_game])
		file_names_ck = "\n".join([f"{Path(f).name}:" for f in self.CRCs_ck])

		label_file_names_game = ttk.Label(self.frame_game, text=file_names_game, font=FONT, justify=RIGHT)
		label_file_names_game.grid(column=0, row=0, rowspan=len(self.CRCs_game), sticky=E, padx=scale(5))

		label_file_names_ck = ttk.Label(self.frame_ck, text=file_names_ck, font=FONT, justify=RIGHT)
		label_file_names_ck.grid(column=0, row=0, rowspan=len(self.CRCs_ck), sticky=E, padx=scale(5))

		self.draw_versions()

		frame_radio_desired = ttk.Labelframe(self, text="Desired Version", padding=scale(5))
		frame_radio_desired.grid(column=1, row=0, rowspan=2, sticky=NSEW, padx=scale(5))

		for row, version in enumerate(SUPPORTED_VERSIONS):
			ttk.Radiobutton(
				frame_radio_desired,
				text=version,
				variable=self.sv_desired_version,
				value=version,
			).grid(column=0, row=row, sticky=NSEW)

		frame_options = ttk.Labelframe(self, text="Options", padding=scale(5))
		frame_options.grid(column=1, row=2, rowspan=2, sticky=NSEW, padx=scale(5))
		self.check_keep_backups = ttk.Checkbutton(
			frame_options,
			text="Keep Backups",
			variable=self.bv_keep_backups,
			padding=0,
		)
		self.check_keep_backups.grid(column=0, row=0, sticky=W, pady=scale(5))
		add_tooltip(self.check_keep_backups, TOOLTIP_DOWNGRADER_BACKUPS)

		self.check_delete_deltas = ttk.Checkbutton(
			frame_options,
			text="Delete Patches",
			variable=self.bv_delete_deltas,
			padding=0,
		)
		self.check_delete_deltas.grid(column=0, row=1, sticky=W, pady=scale(5))
		add_tooltip(self.check_delete_deltas, TOOLTIP_DOWNGRADER_DELTAS)

		self.button_patch = ttk.Button(self, text="Patch\n All", command=self.patch_files)
		self.button_patch.grid(column=2, row=0, rowspan=2, sticky=NSEW, padx=(scale(5), scale(10)), pady=(scale(10), 0))

		ttk.Button(
			self,
			text="About",
			command=lambda: AboutWindow(self, self.cmc, 500, 320, ABOUT_DOWNGRADING_TITLE, ABOUT_DOWNGRADING),
		).grid(column=2, row=2, sticky=EW, padx=(scale(5), scale(10)), pady=(scale(5), 0))

		frame_bottom = ttk.Frame(self)
		frame_bottom.grid(column=0, row=5, columnspan=3, sticky=EW, pady=(scale(5), 0))
		frame_bottom.grid_columnconfigure(0, weight=1)
		self.logger = Logger(frame_bottom)

		self.logger.log_message(LogType.Info, "Patches will be downloaded and applied as-needed.", skip_logging=True)

		self.progress_var = DoubleVar()
		self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
		self.progress_bar.grid(column=0, row=6, columnspan=3, sticky=EW, ipady=scale(1))

	def draw_versions(self) -> None:
		for label in self.version_labels:
			label.destroy()

		frame = self.frame_game
		i = 0
		for file_name, install_type in self.current_versions.items():
			if file_name == "CreationKit.exe":
				frame = self.frame_ck
				i = 0

			install_type_string = install_type

			if install_type == InstallType.AE:
				color = COLOR_AE
			elif install_type == InstallType.NGAE:
				if self.cmc.game.is_foae():
					color = COLOR_AE
					install_type_string = InstallType.AE
				elif self.cmc.game.is_fong():
					color = COLOR_NG
					install_type_string = InstallType.NG
				else:
					color = COLOR_BAD
			elif install_type == InstallType.NG:
				color = COLOR_NG
			elif install_type == InstallType.NotFound:
				color = COLOR_NEUTRAL_1
			elif install_type in {InstallType.Unknown, InstallType.Obsolete}:
				color = COLOR_BAD
			else:
				color = COLOR_OG

			label = ttk.Label(
				frame,
				text=install_type_string,
				font=FONT,
				foreground=color,
				justify=RIGHT,
			)
			label.grid(column=1, row=i, sticky=E, padx=scale(5))
			self.version_labels.append(label)
			i += 1

	def patch_files(self) -> None:
		self.button_patch.configure(state=DISABLED)
		self.logger.clear()

		settings = self.cmc.settings
		resave = False
		if settings.dict["downgrader_keep_backups"] != self.bv_keep_backups.get():
			settings.dict["downgrader_keep_backups"] = self.bv_keep_backups.get()
			resave = True
		if settings.dict["downgrader_delete_deltas"] != self.bv_delete_deltas.get():
			settings.dict["downgrader_delete_deltas"] = self.bv_delete_deltas.get()
			resave = True
		if resave:
			settings.save()

		desired_version = InstallType(self.sv_desired_version.get())

		patch_needed = False
		for file_name, install_type in self.current_versions.items():
			file_path = self.cmc.game.game_path / file_name

			if install_type == InstallType.NotFound:
				self.logger.log_message(LogType.Info, f"Skipped {file_path.name}: Not Found.")
				continue

			if install_type == desired_version or (
				install_type == InstallType.NGAE and desired_version in {InstallType.NG, InstallType.AE}
			):
				self.logger.log_message(LogType.Info, f"Skipped {file_path.name}: Already {desired_version}.")
				continue

			# NG & AE files are identical; use NG patches.
			current_version = InstallType.NG if install_type == InstallType.NGAE else install_type

			if current_version not in SUPPORTED_VERSIONS:
				self.logger.log_message(LogType.Info, f"Skipped {file_path.name}: Unsupported Version.")
				continue

			patch_needed = True
			self.patch_file(file_path, current_version, desired_version)

		if not patch_needed:
			self.button_patch.configure(state=NORMAL)

	@staticmethod
	def get_backup_path(file_path: Path, install_type: InstallType) -> Path:
		return file_path.with_name(f"{file_path.stem}{BACKUP_SUFFIXES[install_type]}{file_path.suffix}")

	def find_backup(self, file_path: Path, desired_version: InstallType) -> Path | None:
		backup_paths = [self.get_backup_path(file_path, desired_version)]
		backup_paths.extend(self.get_backup_path(file_path, v) for v in SUPPORTED_VERSIONS if v != desired_version)
		for backup_path in backup_paths:
			if is_file(backup_path) and get_crc32(backup_path) in self.CRCs_by_type[desired_version]:
				return backup_path
		return None

	def patch_file(self, file_path: Path, current_version: InstallType, desired_version: InstallType) -> None:
		patch_direction = f"{PATCH_PREFIXES[current_version]}-to-{PATCH_PREFIXES[desired_version]}-"
		backup_file_path_current = self.get_backup_path(file_path, current_version)

		try:  # ruff: ignore[too-many-statements-in-try-clause]
			if file_path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
				file_path.chmod(stat.S_IWRITE)

			backup_file_path_desired = self.find_backup(file_path, desired_version)
			if backup_file_path_desired is not None:
				print(f"Found backup of {desired_version}: {backup_file_path_desired.name}")
				if backup_file_path_desired == backup_file_path_current:
					own_backup_path = self.get_backup_path(file_path, desired_version)
					own_backup_path.unlink(missing_ok=True)
					backup_file_path_desired = backup_file_path_desired.rename(own_backup_path)

			if is_file(backup_file_path_current):
				print("Backup of current version exists.")
				if get_crc32(backup_file_path_current) == get_crc32(file_path):
					print(f"Backup CRC good. Deleting {file_path.name}")
					file_path.unlink()
				else:
					print(f"Backup CRC bad. Deleting {backup_file_path_current.name}")
					backup_file_path_current.unlink()

			if is_file(file_path):
				print(f"Backing up {file_path.name} to {backup_file_path_current.name}")
				file_path.rename(backup_file_path_current)

			if backup_file_path_desired is not None:
				print(f"Restoring {backup_file_path_desired.name} to {file_path.name}")
				if self.bv_keep_backups.get():
					copy2(backup_file_path_desired, file_path)
				else:
					backup_file_path_desired.replace(file_path)
					backup_file_path_current.unlink()
				self.logger.log_message(LogType.Good, f"Patched {file_path.name}")
			else:
				print("Restore from backup not possible. Patch download needed.")
				url = f"{PATCH_URL_BASE}{patch_direction}{file_path.name}.xdelta"
				self.download_queue.put((url, backup_file_path_current, file_path))

		except OSError as e:
			print("Restore failed due to exception.", e)
			self.logger.log_message(LogType.Bad, f"Failed patching {file_path.name}")

		if not self.download_or_patch_in_progress:
			self.download_or_patch_in_progress = True
			self.processing_data = True
			self.check_download_queue()

	def check_download_queue(self) -> None:
		try:
			next_download = self.download_queue.get_nowait()
		except queue.Empty:
			print("Queue empty...")
			self.cmc.refresh_tab(Tab.Overview)
			self.get_info()
			self.draw_versions()
			self.button_patch.configure(state=NORMAL)
			self.download_or_patch_in_progress = False
			self.processing_data = False
			return

		self.download_error = None
		file_path = Path(Path(next_download[0]).name)
		if is_file(file_path):
			self.progress_var.set(100)
		else:
			self.progress_var.set(0)
			self.download_thread = Thread(target=self._threaded_download, args=(next_download[0],))
			self.download_thread.start()
		self.check_download_progress(*next_download)

	def _threaded_download(self, url: str) -> None:
		file_path = Path(Path(url).name)
		part_path = file_path.with_name(f"{file_path.name}.part")

		try:  # ruff: ignore[too-many-statements-in-try-clause]
			with requests.get(url, timeout=10, stream=True) as response:
				response.raise_for_status()
				total_size = int(response.headers.get("content-length", 0))
				downloaded_size = 0
				with part_path.open("wb") as f:
					for data in response.iter_content(chunk_size=65536):
						downloaded_size += len(data)
						f.write(data)
						if total_size > 0:
							self.download_progress_updates.put(downloaded_size / total_size * 100)
			part_path.replace(file_path)
			self.download_progress_updates.put(100)
		except (requests.RequestException, OSError) as e:
			self.download_error = str(e) or e.__class__.__name__
			part_path.unlink(missing_ok=True)

	def check_download_progress(self, url: str, infile: Path, outfile: Path) -> None:
		while self.download_progress_updates.qsize():
			try:
				value = self.download_progress_updates.get()
			except queue.Empty:
				break
			else:
				self.progress_var.set(value)

		if self.download_thread is not None and self.download_thread.is_alive():
			self.cmc.root.after(100, self.check_download_progress, url, infile, outfile)
			return

		self.download_thread = None
		if self.download_error is not None:
			print("Download failed:", self.download_error)
			self.logger.log_message(LogType.Bad, f"Failed downloading patch for {outfile.name}: {self.download_error}")
			self.restore_original(infile, outfile)
			self.check_download_queue()
			return

		print("Download completed. Patching...")
		self.apply_patch(url, infile, outfile)

	def restore_original(self, infile: Path, outfile: Path) -> None:
		try:  # ruff: ignore[too-many-statements-in-try-clause]
			if is_file(infile):
				if self.bv_keep_backups.get():
					outfile.unlink(missing_ok=True)
					copy2(infile, outfile)
				else:
					infile.replace(outfile)
				self.logger.log_message(LogType.Info, f"Restored original {outfile.name}")
		except OSError as e:
			print("Restore of original failed.", e)
			self.logger.log_message(LogType.Bad, f"Failed restoring original {outfile.name} from {infile.name}")

	def apply_patch(self, url: str, infile: Path, outfile: Path) -> None:
		patch_name = Path(url).name
		print(f"Applying {patch_name} to {infile.name}")
		try:
			patch_successful = bool(
				pyxdelta.decode(
					str(infile),
					patch_name,
					str(outfile),
				),
			)
		except Exception as e:
			print("Patching raised an exception.", e)
			patch_successful = False

		if patch_successful:
			self.logger.log_message(LogType.Good, f"Patched {outfile.name}")
			if not self.bv_keep_backups.get():
				infile.unlink(missing_ok=True)
			if self.bv_delete_deltas.get():
				Path(patch_name).unlink(missing_ok=True)
		else:
			self.logger.log_message(LogType.Bad, f"Failed patching {outfile.name}")
			self.restore_original(infile, outfile)
			Path(patch_name).unlink(missing_ok=True)

		self.check_download_queue()
