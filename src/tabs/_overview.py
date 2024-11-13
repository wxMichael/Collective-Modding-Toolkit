import os
import struct
from tkinter import *
from tkinter import ttk
from typing import Literal

from downgrader import Downgrader
from enums import ArchiveVersion, Magic, ModuleFlag
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from patcher import ArchivePatcher
from utils import (
	add_separator,
	get_crc32,
	get_file_version,
	ver_to_str,
)


class OverviewTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Overview")

	def _load(self) -> bool:
		self.get_info_binaries()
		self.get_info_archives()
		self.get_info_modules()
		return True

	def _build_gui(self) -> None:
		self.build_tab_overview()

	def refresh(self) -> None:
		self.get_info_binaries()
		self.get_info_archives()
		self.get_info_modules()
		self.frame_info_binaries.destroy()
		self.frame_info_archives.destroy()
		self.frame_info_modules.destroy()
		self.build_tab_overview_binaries()
		self.build_tab_overview_archives()
		self.build_tab_overview_modules()

	def build_tab_overview(self) -> None:
		frame_top = ttk.Frame(self)
		frame_top.pack(anchor=W, fill=X, pady=5)
		frame_top.grid_columnconfigure(index=2, weight=1)

		ttk.Label(
			frame_top,
			text="Install:\nDetected:\nMod Manager:",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=5)

		label_path = ttk.Label(
			frame_top,
			textvariable=self.cmc.game_path_sv,
			font=self.cmc.FONT,
			foreground=COLOR_NEUTRAL_2,
			cursor="hand2",
		)
		label_path.grid(column=1, row=0, sticky=W)
		label_path.bind("<Button-1>", lambda _: os.startfile(self.cmc.game.game_path))

		ttk.Label(
			frame_top,
			textvariable=self.cmc.install_type_sv,
			font=self.cmc.FONT,
			foreground=COLOR_GOOD,
		).grid(column=1, row=1, sticky=W)

		ttk.Label(
			frame_top,
			text=f"{self.cmc.game.manager.name} v{self.cmc.game.manager.version}" if self.cmc.game.manager else "Not Found",
			font=self.cmc.FONT,
			foreground=COLOR_NEUTRAL_2,
		).grid(column=1, row=2, sticky=W)

		ttk.Button(
			frame_top,
			compound="image",
			image=self.cmc.get_image("images/refresh-32.png"),
			command=self.refresh,
			padding=0,
		).grid(column=2, row=0, rowspan=2, sticky=E, padx=10)

		self.build_tab_overview_binaries()
		self.build_tab_overview_archives()
		self.build_tab_overview_modules()

	def build_tab_overview_binaries(self) -> None:
		self.frame_info_binaries = ttk.Labelframe(self, text="Binaries (EXE/DLL/BIN)")
		self.frame_info_binaries.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		file_names = "\n".join([f.rsplit(".", 1)[0] + ":" for f in self.cmc.game.file_info])
		rows = len(self.cmc.game.file_info)

		label_file_names = ttk.Label(self.frame_info_binaries, text=file_names, font=self.cmc.FONT, justify=RIGHT)
		label_file_names.grid(column=0, row=0, rowspan=rows, sticky=E, padx=5)

		ttk.Label(
			self.frame_info_binaries,
			text="Address Library:",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=0, row=rows, sticky=E, padx=5)

		ttk.Label(
			self.frame_info_binaries,
			text="Not Found" if not self.address_library else "Next-Gen" if self.cmc.game.is_fong() else "Old-Gen",
			font=self.cmc.FONT,
			foreground=COLOR_GOOD if self.address_library else COLOR_BAD,
		).grid(column=1, row=rows, sticky=W)

		for i, file_name in enumerate(self.cmc.game.file_info.keys()):
			match self.cmc.game.file_info[file_name]["InstallType"]:
				case self.cmc.game.install_type:
					color = COLOR_GOOD

				case InstallType.OG:
					color = COLOR_GOOD if self.cmc.game.is_fodg() else COLOR_BAD

				case None:
					if file_name.lower() in {"creationkit.exe", "archive2.exe"} or (
						self.cmc.game.is_fong() and BASE_FILES[file_name].get("OnlyOG", False)
					):
						color = COLOR_NEUTRAL_1
					else:
						color = COLOR_BAD

				case _:
					color = COLOR_BAD

			install_type = self.cmc.game.file_info[file_name]["InstallType"]
			version_label = ttk.Label(
				self.frame_info_binaries,
				text=install_type or "Not Found",
				font=self.cmc.FONT,
				foreground=color,
				width=10,
			)
			version_label.grid(column=1, row=i, sticky=W)
			if install_type:
				installed_version = ver_to_str(self.cmc.game.file_info[file_name]["Version"] or "Not Found")
				version_label.bind("<Enter>", lambda event, v=installed_version: event.widget.config(text=v))
				version_label.bind("<Leave>", lambda event, it=install_type: event.widget.config(text=it or "Not Found"))

		size = self.frame_info_binaries.grid_size()
		ttk.Button(
			self.frame_info_binaries,
			text="Downgrade Manager...",
			padding=0,
			command=lambda: Downgrader(self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=5)
		self.frame_info_binaries.grid_rowconfigure(size[1], weight=2)

	def build_tab_overview_archives(self) -> None:
		self.frame_info_archives = ttk.Labelframe(self, text="Archives (BA2)")
		self.frame_info_archives.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		ttk.Label(
			self.frame_info_archives,
			text="General:\nTexture:\nTotal:",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))

		color_invalid = COLOR_BAD if self.cmc.game.archives_invalid else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_archives,
			text="Unreadable:",
			font=self.cmc.FONT,
			foreground=color_invalid,
		).grid(column=0, row=3, sticky=E, padx=(5, 0))

		add_separator(self.frame_info_archives, HORIZONTAL, 0, 4, 3)

		ttk.Label(
			self.frame_info_archives,
			text="v1 (OG):\nv7/8 (NG):",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=0, row=5, rowspan=2, sticky=E, padx=(5, 0))

		# Column 1
		self.add_count_label(self.frame_info_archives, 1, 0, "GNRL")
		self.add_count_label(self.frame_info_archives, 1, 1, "DX10")

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_og) + len(self.cmc.game.archives_ng),
			font=self.cmc.FONT,
		).grid(column=1, row=2, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_invalid),
			font=self.cmc.FONT,
			foreground=color_invalid,
		).grid(column=1, row=3, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_og),
			font=self.cmc.FONT,
		).grid(column=1, row=5, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_ng),
			font=self.cmc.FONT,
		).grid(column=1, row=6, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(
			self.frame_info_archives,
			text=f" / {MAX_ARCHIVES_GNRL}",
			font=self.cmc.FONT,
		).grid(column=2, row=0, sticky=EW)

		ttk.Label(
			self.frame_info_archives,
			text=f" / {MAX_ARCHIVES_DX10 or '???'}",
			font=self.cmc.FONT,
		).grid(column=2, row=1, sticky=EW)

		# Column 0
		size = self.frame_info_archives.grid_size()
		ttk.Button(
			self.frame_info_archives,
			text="Archive Patcher...",
			padding=0,
			command=lambda: ArchivePatcher(self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=5)
		self.frame_info_archives.grid_rowconfigure(size[1], weight=2)
		self.frame_info_archives.grid_columnconfigure(2, weight=1)

	def build_tab_overview_modules(self) -> None:
		self.frame_info_modules = ttk.Labelframe(self, text="Modules (ESM/ESL/ESP)")
		self.frame_info_modules.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		ttk.Label(
			self.frame_info_modules,
			text="Full:\nLight:\nTotal:",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))

		color_invalid = COLOR_BAD if self.cmc.game.modules_invalid else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_modules,
			text="Unreadable:",
			font=self.cmc.FONT,
			foreground=color_invalid,
		).grid(column=0, row=3, sticky=E, padx=(5, 0))

		add_separator(self.frame_info_modules, HORIZONTAL, 0, 4, 3)

		ttk.Label(
			self.frame_info_modules,
			text="HEDR v1.00:",
			font=self.cmc.FONT,
			foreground=COLOR_NEUTRAL_1,
		).grid(column=0, row=5, sticky=E, padx=(5, 0))

		color_95 = COLOR_WARNING if self.cmc.game.modules_v95 else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_modules,
			text="HEDR v0.95:",
			font=self.cmc.FONT,
			foreground=color_95,
		).grid(column=0, row=6, sticky=E, padx=(5, 0))

		# Column 1
		self.add_count_label(self.frame_info_modules, 1, 0, "Full")
		self.add_count_label(self.frame_info_modules, 1, 1, "Light")
		self.add_count_label(self.frame_info_modules, 1, 2, "Total")

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_invalid),
			font=self.cmc.FONT,
			foreground=color_invalid,
		).grid(column=1, row=3, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_modules,
			text=self.cmc.game.module_count_v1,
			font=self.cmc.FONT,
			foreground=COLOR_NEUTRAL_1,
		).grid(column=1, row=5, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_v95),
			font=self.cmc.FONT,
			foreground=color_95,
		).grid(column=1, row=6, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(
			self.frame_info_modules,
			text=f" /  {MAX_MODULES_FULL}\n / {MAX_MODULES_LIGHT}\n / {MAX_MODULES_FULL + MAX_MODULES_LIGHT}",
			font=self.cmc.FONT,
			justify=RIGHT,
		).grid(column=2, row=0, rowspan=3, sticky=EW)

	def add_count_label(
		self,
		frame: ttk.LabelFrame,
		column: int,
		row: int,
		count: Literal["GNRL", "DX10", "Full", "Light", "Total"],
	) -> None:
		match count:
			case "GNRL":
				num = self.cmc.game.ba2_count_gnrl
				limit = MAX_ARCHIVES_GNRL
			case "DX10":
				num = self.cmc.game.ba2_count_dx10
				limit = MAX_ARCHIVES_DX10 or 9999
			case "Full":
				num = self.cmc.game.module_count_full
				limit = MAX_MODULES_FULL
			case "Light":
				num = self.cmc.game.module_count_light
				limit = MAX_MODULES_LIGHT
			case "Total":
				num = self.cmc.game.module_count_full + self.cmc.game.module_count_light
				limit = MAX_MODULES_FULL + MAX_MODULES_LIGHT

		color = COLOR_GOOD if num < limit else COLOR_BAD

		ttk.Label(frame, text=str(num).rjust(4), font=self.cmc.FONT, foreground=color).grid(
			column=column,
			row=row,
			sticky=E,
			padx=(5, 0),
		)

	def get_info_binaries(self) -> None:
		self.cmc.game.reset_binaries()
		self.ckfixes_found = self.cmc.game.game_path.joinpath("F4CKFixes").exists()

		for file_name in BASE_FILES:
			file_path = self.cmc.game.game_path / file_name
			if not file_path.is_file():
				self.cmc.game.file_info[file_path.name] = {
					"File": None,
					"Version": None,
					"InstallType": None,
				}
				continue

			if BASE_FILES[file_name].get("UseHash", False):
				version = get_crc32(file_path)
			else:
				version = ver_to_str(get_file_version(file_path))

			self.cmc.game.file_info[file_path.name] = {
				"File": file_path,
				"Version": version,
				"InstallType": BASE_FILES[file_name]["Versions"].get(version, InstallType.Unknown),
			}

			if file_path.name.lower() == "fallout4.exe":
				self.cmc.game.install_type = self.cmc.game.file_info[file_path.name]["InstallType"] or InstallType.Unknown

				if self.cmc.game.f4se_path is not None:
					address_library_path = self.cmc.game.f4se_path / f"version-{version.replace('.', '-')}.bin"
					if address_library_path.is_file():
						self.address_library = address_library_path

				if self.cmc.game.data_path is not None and self.cmc.game.is_foog():
					startup_ba2 = self.cmc.game.data_path / "Fallout4 - Startup.ba2"
					if startup_ba2.is_file():
						startup_crc = get_crc32(startup_ba2, skip_ba2_header=True)
						if startup_crc == NG_STARTUP_BA2_CRC:
							self.cmc.game.install_type = InstallType.DG

	def get_info_archives(self) -> None:
		self.cmc.game.reset_archives()

		if self.cmc.game.data_path is None:
			return

		for ba2_file in self.cmc.game.data_path.glob("*.ba2"):
			try:
				with ba2_file.open("rb") as f:
					head = f.read(12)
			except PermissionError:
				continue

			if len(head) != 12:  # noqa: PLR2004
				self.cmc.game.archives_invalid.add(ba2_file)
				continue

			if head[:4] != Magic.BTDX:
				self.cmc.game.archives_invalid.add(ba2_file)
				continue

			match head[4]:
				case ArchiveVersion.OG:
					is_ng = False

				case ArchiveVersion.NG7 | ArchiveVersion.NG:
					is_ng = True

				case _:
					self.cmc.game.archives_invalid.add(ba2_file)
					continue

			match head[8:]:
				case Magic.GNRL:
					self.cmc.game.ba2_count_gnrl += 1

				case Magic.DX10:
					self.cmc.game.ba2_count_dx10 += 1

				case _:
					self.cmc.game.archives_invalid.add(ba2_file)
					continue

			if is_ng:
				self.cmc.game.archives_ng.add(ba2_file)
			else:
				self.cmc.game.archives_og.add(ba2_file)

	def get_info_modules(self) -> None:
		self.cmc.game.reset_modules()

		if self.cmc.game.data_path is None:
			return

		for module_file in self.cmc.game.data_path.glob("*.es[mlp]"):
			try:
				with module_file.open("rb") as f:
					head = f.read(34)
			except PermissionError:
				continue

			if len(head) != 34:  # noqa: PLR2004
				self.cmc.game.modules_invalid.add(module_file)
				continue

			if head[:4] != Magic.TES4:
				self.cmc.game.modules_invalid.add(module_file)
				continue

			if head[24:28] != Magic.HEDR:
				self.cmc.game.modules_invalid.add(module_file)
				continue

			name_lower = module_file.name.lower()
			if name_lower not in GAME_MASTERS:
				if head[30:34] == MODULE_VERSION_95:
					self.cmc.game.modules_v95.add(module_file)
				elif head[30:34] == MODULE_VERSION_1:
					self.cmc.game.module_count_v1 += 1

			flags = struct.unpack("<I", head[8:12])[0]
			if flags & ModuleFlag.Light or name_lower[-4:] == ".esl":
				self.cmc.game.module_count_light += 1
			else:
				self.cmc.game.module_count_full += 1
