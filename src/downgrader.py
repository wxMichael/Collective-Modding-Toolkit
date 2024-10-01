import queue
import stat
from pathlib import Path
from shutil import copy2
from threading import Thread
from tkinter import *
from tkinter import messagebox, ttk
from types import MappingProxyType

import pyxdelta
import requests

from globals import *
from helpers import (
	CMCheckerInterface,
	LogType,
	Tab,
)
from logger import Logger
from modal_window import ModalWindow
from utils import (
	get_crc32,
)

COLOR_OG = "dodger blue"
COLOR_NG = "SlateBlue1"
PATCH_URL_BASE = "https://github.com/wxMichael/Collective-Modding-Toolkit/releases/download/delta-patches/"


class Downgrader(ModalWindow):
	CRCs_game = MappingProxyType({
		"Fallout4.exe": {
			"C6053902": InstallType.OG,
			"C5965A2E": InstallType.NG,
		},
		"Fallout4Launcher.exe": {
			"02445570": InstallType.OG,
			"F6A06FF5": InstallType.NG,
		},
		"steam_api64.dll": {
			"BBD912FC": InstallType.OG,
			"E36E7B4D": InstallType.NG,
		},
	})
	CRCs_ck = MappingProxyType({
		"CreationKit.exe": {
			"0F5C065B": InstallType.OG,
			"481CCE95": InstallType.NG,
		},
		"Tools\\Archive2\\Archive2.exe": {
			"4CDFC7B5": InstallType.OG,
			"71A5240B": InstallType.NG,
		},
		"Tools\\Archive2\\Archive2Interop.dll": {
			"850D36A9": InstallType.OG,
			"EFBE3622": InstallType.NG,
		},
	})
	CRCs_by_type: MappingProxyType[InstallType, list[str]] = MappingProxyType({
		InstallType.OG: [],
		InstallType.NG: [],
	})
	for CRCs in list(CRCs_game.values()) + list(CRCs_ck.values()):
		for crc, install_type in CRCs.items():
			CRCs_by_type[install_type].append(crc)

	def __init__(self, parent: CMCheckerInterface) -> None:
		super().__init__(parent, "Downgrader", 550, 334)

		self.current_versions: dict[str, InstallType | None] = {}
		self.unknown_game = False
		self.unknown_ck = False

		self.version_labels: list[ttk.Label] = []

		self.download_queue: queue.Queue[tuple[str, Path, Path]] = queue.Queue()
		self.download_progress_updates: queue.Queue[float] = queue.Queue()
		self.download_or_patch_in_progress = False
		self.download_thread: Thread | None = None

		self.get_info()

		self.wants_downgrade_game = BooleanVar(value=self.current_versions["Fallout4.exe"] == InstallType.OG)
		self.wants_downgrade_ck = BooleanVar(value=self.current_versions["CreationKit.exe"] == InstallType.OG)

		self.build_gui()

	def get_info(self) -> None:
		self.unknown_game = False
		self.unknown_ck = False
		for file_name, file_crcs in list(Downgrader.CRCs_game.items()) + list(Downgrader.CRCs_ck.items()):
			file_path = self.parent.game_path / file_name
			if file_path.is_file():
				crc = get_crc32(file_path)
				self.current_versions[file_name] = file_crcs.get(crc, InstallType.Unknown)
			else:
				self.current_versions[file_name] = None

			if self.current_versions[file_name] in {InstallType.Unknown, None}:
				if file_name in self.CRCs_game:
					self.unknown_game = True
				else:
					self.unknown_ck = True

	def build_gui(self) -> None:
		self.grid_columnconfigure(2, weight=1)
		self.frame_game = ttk.Labelframe(self, text="Current Game", padding="6")
		self.frame_game.grid(column=0, row=0, rowspan=2, sticky=NSEW, padx=10)
		self.frame_game.grid_columnconfigure(0, weight=1)
		self.frame_ck = ttk.Labelframe(self, text="Current Creation Kit", padding="6")
		self.frame_ck.grid(column=0, row=2, rowspan=2, sticky=NSEW, padx=10)
		self.frame_ck.grid_columnconfigure(0, weight=1)

		file_names_game = "\n".join([f"{Path(f).name}:" for f in self.CRCs_game])
		file_names_ck = "\n".join([f"{Path(f).name}:" for f in self.CRCs_ck])

		label_file_names_game = ttk.Label(self.frame_game, text=file_names_game, font=self.parent.FONT, justify=RIGHT)
		label_file_names_game.grid(column=0, row=0, rowspan=len(self.CRCs_game), sticky=E, padx=5)

		label_file_names_ck = ttk.Label(self.frame_ck, text=file_names_ck, font=self.parent.FONT, justify=RIGHT)
		label_file_names_ck.grid(column=0, row=0, rowspan=len(self.CRCs_ck), sticky=E, padx=5)

		self.draw_versions()

		frame_radio_game = ttk.Labelframe(self, text="Desired Version", padding="6")
		frame_radio_game.grid(column=1, row=0, rowspan=2, sticky=NSEW, padx=5)
		frame_radio_ck = ttk.Labelframe(self, text="Desired Version", padding="6")
		frame_radio_ck.grid(column=1, row=2, rowspan=2, sticky=NSEW, padx=5)

		ttk.Radiobutton(
			frame_radio_game,
			text="Old-Gen",
			variable=self.wants_downgrade_game,
			value=True,
		).grid(column=0, row=0, sticky=NSEW)

		ttk.Radiobutton(
			frame_radio_game,
			text="Next-Gen",
			variable=self.wants_downgrade_game,
			value=False,
		).grid(column=0, row=1, sticky=NSEW)

		ttk.Radiobutton(
			frame_radio_ck,
			text="Old-Gen",
			variable=self.wants_downgrade_ck,
			value=True,
		).grid(column=0, row=0, sticky=NSEW)

		ttk.Radiobutton(
			frame_radio_ck,
			text="Next-Gen",
			variable=self.wants_downgrade_ck,
			value=False,
		).grid(column=0, row=1, sticky=NSEW)

		self.button_patch = ttk.Button(self, text="Patch All", command=self.patch_files)
		self.button_patch.grid(column=2, row=1, rowspan=2, sticky=NSEW, padx=(5, 10))  # , pady=10)

		ttk.Button(
			self,
			text="About",
			command=lambda: messagebox.showinfo("About Downgrading", "WIP", parent=self),
		).grid(column=2, row=3, sticky=EW, padx=(5, 10))

		frame_bottom = ttk.Frame(self)
		frame_bottom.grid(column=0, row=4, columnspan=3, sticky=EW, pady=(5, 0))
		frame_bottom.grid_columnconfigure(0, weight=1)
		self.logger = Logger(frame_bottom)

		self.logger.log_message(LogType.Info, "Patches will be downloaded and applied as-needed.")

		self.progress_var = DoubleVar()
		self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
		self.progress_bar.grid(column=0, row=5, columnspan=3, sticky=EW, ipady=1)

	def draw_versions(self) -> None:
		for label in self.version_labels:
			label.destroy()

		frame = self.frame_game
		i = 0
		for file_name, install_type in self.current_versions.items():
			if file_name == "CreationKit.exe":
				frame = self.frame_ck
				i = 0

			if install_type == InstallType.NG:
				color = COLOR_NG
			elif install_type == InstallType.Unknown:
				color = COLOR_BAD
			else:
				color = COLOR_OG

			label = ttk.Label(
				frame,
				text=install_type or "Not Found",
				font=self.parent.FONT,
				foreground=color,
				justify=RIGHT,
			)
			label.grid(column=1, row=i, sticky=E, padx=5)
			self.version_labels.append(label)
			i += 1

	def patch_files(self) -> None:
		self.button_patch.configure(state=DISABLED)
		self.logger.clear()

		desired_version_game = InstallType.OG if self.wants_downgrade_game.get() else InstallType.NG
		desired_version_ck = InstallType.OG if self.wants_downgrade_ck.get() else InstallType.NG
		desired_version = desired_version_game

		patch_needed = False
		for file_name, install_type in self.current_versions.items():
			file_path = self.parent.game_path / file_name

			if file_name == "CreationKit.exe":
				desired_version = desired_version_ck

			match install_type:
				case desired_version.value:
					self.logger.log_message(
						LogType.Info,
						f"Skipped {file_path.name}: Already {desired_version}.",
					)
					continue

				case None:
					self.logger.log_message(LogType.Bad, f"Skipped {file_path.name}: Unknown version.")
					continue

				case _:
					patch_needed = True
					self.patch_file(file_path, desired_version)

		if not patch_needed:
			self.button_patch.configure(state=NORMAL)

	def patch_file(self, file_path: Path, desired_version: InstallType) -> None:
		backup_name_og = f"{file_path.stem}_upgradeBackup{file_path.suffix}"
		backup_name_ng = f"{file_path.stem}_downgradeBackup{file_path.suffix}"

		if desired_version == InstallType.OG:
			patch_direction = "NG-to-OG-"
			backup_file_name_desired = backup_name_og
			backup_file_name_current = backup_name_ng
		else:
			patch_direction = "OG-to-NG-"
			backup_file_name_desired = backup_name_ng
			backup_file_name_current = backup_name_og

		backup_file_path_desired = file_path.with_name(backup_file_name_desired)
		backup_file_path_current = file_path.with_name(backup_file_name_current)

		try:
			if file_path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
				file_path.chmod(stat.S_IWRITE)
			if backup_file_path_current.is_file():
				print("Backup of current version exists.")
				if get_crc32(backup_file_path_current) == get_crc32(file_path):
					print(f"Backup CRC good. Deleting {file_path.name}")
					file_path.unlink()
				else:
					print(f"Backup CRC bad. Deleting {backup_file_path_current.name}")
					backup_file_path_current.unlink()

			if file_path.is_file():
				print(f"Backing up {file_path.name} to {backup_file_path_current.name}")
				file_path.rename(backup_file_path_current)

			if backup_file_path_desired.is_file():
				print(f"{backup_file_path_desired.name} exists.")
				if get_crc32(backup_file_path_desired) in self.CRCs_by_type[desired_version]:
					print(f"Backup CRC good. Restoring to {file_path.name}")
					copy2(backup_file_path_desired, file_path)
					self.logger.log_message(LogType.Good, f"Patched {file_path.name}")

				else:
					print(f"Backup CRC bad. Deleting {backup_file_path_desired.name}")
					backup_file_path_desired.unlink()

			if not file_path.is_file():
				print("Restore from backup not possible. Patch download needed.")
				url = f"{PATCH_URL_BASE}{patch_direction}{file_path.name}.xdelta"
				self.download_queue.put((url, backup_file_path_current, file_path))

		except OSError as e:
			print("Restore failed due to exception.", e)
			self.logger.log_message(LogType.Bad, f"Failed patching {file_path.name}")

		if not self.download_or_patch_in_progress:
			self.download_or_patch_in_progress = True
			self.check_download_queue()

	def check_download_queue(self) -> None:
		try:
			next_download = self.download_queue.get_nowait()
		except queue.Empty:
			print("Queue empty...")
			self.parent.refresh_tab(Tab.Overview)
			self.get_info()
			self.draw_versions()
			self.button_patch.configure(state=NORMAL)
			self.download_or_patch_in_progress = False
			return

		file_path = Path(Path(next_download[0]).name)
		if file_path.is_file():
			self.download_thread = None
			self.progress_var.set(100)
		else:
			self.progress_var.set(0)
			self.download_thread = Thread(target=self._threaded_download, args=(next_download[0],))
			self.download_thread.start()
		self.check_download_progress(*next_download)

	def _threaded_download(self, url: str) -> None:
		file_path = Path(Path(url).name)

		response = requests.get(url, timeout=10, stream=True)
		total_size = int(response.headers.get("content-length", 0))
		downloaded_size = 0
		with file_path.open("wb") as f:
			for data in response.iter_content(chunk_size=1024):
				downloaded_size += len(data)
				f.write(data)
				self.download_progress_updates.put(downloaded_size / total_size * 100)
		self.download_progress_updates.put(100)
		self.download_thread = None

	def check_download_progress(self, url: str, infile: Path, outfile: Path) -> None:
		while self.download_progress_updates.qsize():
			try:
				value = self.download_progress_updates.get()
			except queue.Empty:
				break
			else:
				self.progress_var.set(value)

		if self.download_thread is None:
			print("Download completed. Patching...")
			self.apply_patch(url, infile, outfile)
			return
		self.parent.window.after(100, self.check_download_progress, url, infile, outfile)

	def apply_patch(self, url: str, infile: Path, outfile: Path) -> None:
		patch_name = Path(url).name
		print(f"Applying {patch_name} to {infile.name}")
		patch_successful = pyxdelta.decode(
			str(infile),
			patch_name,
			str(outfile),
		)

		if patch_successful:
			self.logger.log_message(LogType.Good, f"Patched {outfile.name}")
		else:
			self.logger.log_message(LogType.Bad, f"Failed patching {outfile.name}")

		self.check_download_queue()
