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


import logging
import os
import struct
import sys
from pathlib import Path
from tkinter import *
from tkinter import messagebox, ttk
from typing import Literal

from packaging.version import Version

from downgrader import Downgrader
from enums import CSIDL, ArchiveVersion, Magic, ModuleFlag, ProblemType, SolutionType
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, FileInfo, ProblemInfo, SimpleProblemInfo
from modal_window import AboutWindow, TreeWindow
from patcher import ArchivePatcher
from utils import (
	add_separator,
	add_tooltip,
	exists,
	get_crc32,
	get_environment_path,
	get_file_version,
	is_file,
	ver_to_str,
)

logger = logging.getLogger(__name__)


class OverviewTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Overview")

	def _load(self) -> bool:
		self.cmc.overview_problems.clear()
		self.get_info_binaries()
		self.get_info_modules()
		self.get_info_archives()
		return True

	def refresh(self) -> None:
		self.cmc.overview_problems.clear()
		self.get_info_binaries()
		self.get_info_modules(refresh=True)
		self.get_info_archives()
		if not self.is_loaded:
			return
		self.frame_info_binaries.destroy()
		self.frame_info_archives.destroy()
		self.frame_info_modules.destroy()
		self.build_gui_binaries()
		self.build_gui_archives()
		self.build_gui_modules()

	def _build_gui(self) -> None:
		frame_top = ttk.Frame(self)
		frame_top.pack(anchor=W, fill=X, pady=scale(5))
		frame_top.grid_columnconfigure(2, weight=1)

		ttk.Label(
			frame_top,
			text="Mod Manager:\nGame Path:\nVersion:\nPC Specs:\n",
			font=FONT,
			justify=RIGHT,
			foreground=COLOR_DEFAULT,
		).grid(column=0, row=0, rowspan=4, sticky=E, padx=scale(5))

		manager = self.cmc.game.manager
		if manager:
			if manager.name == "Mod Organizer":
				label_mod_manager_icon = ttk.Label(
					frame_top,
					compound="image",
					image=self.cmc.get_image("images/info-16.png"),
					cursor="hand2",
				)
				tooltip = "Detection details"

				max_len = 0
				for key in manager.mo2_settings:
					max_len = max(max_len, len(key))

				label_mod_manager_icon.bind(
					"<Button-1>",
					lambda _: AboutWindow(
						self.cmc.root,
						self.cmc,
						750,
						350,
						"Detected Mod Manager Settings",
						(
							f"EXE: {manager.exe_path}\n"
							f"INI: {manager.ini_path}\n"
							f"Portable: {manager.portable}\n{f'Portable.txt: {manager.portable_txt_path}\n' if manager.portable_txt_path else ''}"
							f"{'\n'.join([f'{k.rjust(max_len)}: {v}' for k, v in manager.mo2_settings.items()])}"
						),
					),
				)

				if self.cmc.pc.os == "Windows 11 24H2" and manager.version <= Version("2.5.2"):
					label_os_icon = ttk.Label(
						frame_top,
						compound="image",
						image=self.cmc.get_image("images/warning-16.png"),
					)
					os_tooltip = (
						"Note: MO2 2.5.2 and earlier have issues on Windows 11 24H2+.\n"
						"Python apps such as Wrye Bash and CLASSIC may give errors\n"
						"such as FileNotFound or fail to detect files that are only\n"
						"present in the VFS and not the Data folder."
					)
					label_os_icon.grid(column=1, row=3, sticky=NW, padx=(0, scale(5)), ipady=scale(3))
					add_tooltip(label_os_icon, os_tooltip)

			# elif manager.name == "Vortex":
			else:
				label_mod_manager_icon = ttk.Label(
					frame_top,
					compound="image",
					image=self.cmc.get_image("images/warning-16.png"),
				)
				tooltip = (
					"Note: Vortex is not yet fully supported.\n"
					"Overview should be accurate but Scanner "
					"will only look in Data and not your staging folders, "
					"so it cannot yet identify the source mod for each issue."
				)
			label_mod_manager_icon.grid(column=1, row=0, sticky=W, padx=(0, scale(5)), ipady=scale(3))
			add_tooltip(label_mod_manager_icon, tooltip)

		label_mod_manager = ttk.Label(
			frame_top,
			text=f"{manager.name} v{manager.version} [Profile: {manager.selected_profile or 'Unknown'}]"
			if manager
			else "Not Found",
			font=FONT,
			foreground=COLOR_NEUTRAL_2 if manager else COLOR_BAD,
		)
		label_mod_manager.grid(column=2, row=0, sticky=W)
		if not manager:
			add_tooltip(label_mod_manager, TOOLTIP_NO_MOD_MANAGER)

		label_path = ttk.Label(
			frame_top,
			textvariable=self.cmc.game_path_sv,
			font=FONT,
			foreground=COLOR_NEUTRAL_2,
			cursor="hand2",
		)
		label_path.grid(column=2, row=1, sticky=W)
		label_path.bind("<Button-1>", lambda _: os.startfile(self.cmc.game.game_path))
		add_tooltip(label_path, TOOLTIP_GAME_PATH)

		ttk.Label(
			frame_top,
			textvariable=self.cmc.install_type_sv,
			font=FONT,
			foreground=COLOR_GOOD,
		).grid(column=2, row=2, sticky=W)

		frame_specs = ttk.Frame(frame_top)
		frame_specs.grid(column=2, row=3, sticky=NSEW)

		ttk.Label(
			frame_specs,
			textvariable=self.cmc.specs_sv_1,
			font=FONT,
			foreground=COLOR_NEUTRAL_2,
		).grid(column=0, row=0, sticky=W)

		ttk.Label(
			frame_specs,
			textvariable=self.cmc.specs_sv_2,
			font=FONT,
			foreground=COLOR_NEUTRAL_2,
		).grid(column=1, row=0, sticky=W, padx=(scale(30), 0))

		button_refresh = ttk.Button(
			frame_top,
			compound="image",
			image=self.cmc.get_image("images/refresh-32.png"),
			command=self.refresh,
			padding=0,
		)
		button_refresh.grid(column=3, row=0, rowspan=2, sticky=E, padx=scale(10))
		add_tooltip(button_refresh, TOOLTIP_REFRESH)

		self.build_gui_binaries()
		self.build_gui_archives()
		self.build_gui_modules()

	def build_gui_binaries(self) -> None:
		self.frame_info_binaries = ttk.Labelframe(self, text="Binaries (EXE/DLL/BIN)")
		self.frame_info_binaries.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		file_names = "\n".join([f.rsplit(".", 1)[0] + ":" for f in self.cmc.game.file_info])
		rows = len(self.cmc.game.file_info)

		label_file_names = ttk.Label(
			self.frame_info_binaries,
			text=file_names,
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		)
		label_file_names.grid(column=0, row=0, rowspan=rows, sticky=E, padx=scale(5))

		ttk.Label(
			self.frame_info_binaries,
			text="Address Library:",
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		).grid(column=0, row=rows, sticky=E, padx=scale(5))

		label_address_library = ttk.Label(
			self.frame_info_binaries,
			text="Installed" if self.cmc.game.address_library else "Not Found",
			font=FONT,
			foreground=COLOR_GOOD if self.cmc.game.address_library else COLOR_BAD,
		)
		label_address_library.grid(column=1, row=rows, sticky=W)
		if not self.cmc.game.address_library:
			add_tooltip(label_address_library, TOOLTIP_ADDRESS_LIBRARY_MISSING)

		for i, file_name in enumerate(self.cmc.game.file_info.keys()):
			file_path = self.cmc.game.file_info[file_name]["File"] or Path(file_name)

			match self.cmc.game.file_info[file_name]["InstallType"]:
				case self.cmc.game.install_type:
					color = COLOR_GOOD

				case InstallType.OG:
					if self.cmc.game.is_fodg():
						color = COLOR_GOOD
					else:
						color = COLOR_BAD
						self.cmc.overview_problems.append(
							ProblemInfo(
								ProblemType.WrongVersion,
								file_path,
								file_path.relative_to(file_path.parent, walk_up=True),
								None,
								"The version of this binary does not match your installed game version.",
								None,
							),
						)

				case InstallType.NotFound:
					if file_name in {"CreationKit.exe", "Archive2.exe"} or (
						self.cmc.game.is_fongae() and file_name == "f4se_steam_loader.dll"
					):
						color = COLOR_NEUTRAL_1
					else:
						color = COLOR_BAD
						self.cmc.overview_problems.append(
							ProblemInfo(
								ProblemType.FileNotFound,
								file_path,
								file_path.relative_to(file_path.parent, walk_up=True),
								None,
								"This file is missing from your game installation.",
								None,
							),
						)

				case _:
					color = COLOR_BAD
					self.cmc.overview_problems.append(
						ProblemInfo(
							ProblemType.WrongVersion,
							file_path,
							file_path.relative_to(file_path.parent, walk_up=True),
							None,
							"The version of this binary does not match your installed game version.",
							None,
						),
					)

			install_type = self.cmc.game.file_info[file_name]["InstallType"]
			version_label = ttk.Label(
				self.frame_info_binaries,
				text=install_type or "Not Found",
				font=FONT,
				foreground=color,
				width=11,
			)
			version_label.grid(column=1, row=i, sticky=W)
			if install_type:
				version = ver_to_str(self.cmc.game.file_info[file_name]["Version"] or "Not Found")

				def on_enter(event: Event[ttk.Label], ver: str = version) -> None:
					event.widget.configure(text=ver)

				def on_leave(event: Event[ttk.Label], it: str = install_type or "Not Found") -> None:
					event.widget.configure(text=it)

				version_label.bind("<Enter>", on_enter)
				version_label.bind("<Leave>", on_leave)

		size = self.frame_info_binaries.grid_size()
		ttk.Button(
			self.frame_info_binaries,
			text="Downgrade Manager...",
			padding=scale(5),
			command=lambda: Downgrader(self.cmc.root, self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=scale(10))
		self.frame_info_binaries.grid_rowconfigure(size[1], weight=2)

	def build_gui_archives(self) -> None:
		self.frame_info_archives = ttk.Labelframe(self, text="Archives (BA2)")
		self.frame_info_archives.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		label_ba2_formats = ttk.Label(
			self.frame_info_archives,
			text="General:\nTexture:\nTotal:",
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		)
		label_ba2_formats.grid(column=0, row=0, rowspan=3, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_ba2_formats, TOOLTIP_BA2_FORMATS)

		color_unreadable = COLOR_BAD if self.cmc.game.archives_unreadable else COLOR_NEUTRAL_1
		label_unreadable = ttk.Label(
			self.frame_info_archives,
			text="Unreadable:",
			font=FONT,
			foreground=color_unreadable,
		)
		label_unreadable.grid(column=0, row=3, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_unreadable, TOOLTIP_UNREADABLE)

		add_separator(self.frame_info_archives, HORIZONTAL, 0, 4, 3)

		label_ba2_versions = ttk.Label(
			self.frame_info_archives,
			text="v1 (OG):\nv7/8 (NG):",
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		)
		label_ba2_versions.grid(column=0, row=5, rowspan=2, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_ba2_versions, TOOLTIP_BA2_VERSIONS)

		# Column 1
		self.add_count_label(self.frame_info_archives, 1, 0, "GNRL")
		self.add_count_label(self.frame_info_archives, 1, 1, "DX10")
		self.add_count_label(self.frame_info_archives, 1, 2, "TotalBA2s")

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_unreadable),
			font=FONT,
			foreground=color_unreadable,
		).grid(column=1, row=3, sticky=E, padx=(scale(5), 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_og),
			font=FONT,
			foreground=COLOR_DEFAULT,
		).grid(column=1, row=5, sticky=E, padx=(scale(5), 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_ng),
			font=FONT,
			foreground=COLOR_DEFAULT,
		).grid(column=1, row=6, sticky=E, padx=(scale(5), 0))

		# Column 2
		if self.cmc.game.install_type in {InstallType.Obsolete2, InstallType.AE2}:
			results = f" / {MAX_ARCHIVES_GNRL_AE}\n / {MAX_ARCHIVES_DX10_AE}\n / {MAX_ARCHIVES_GNRL_AE + MAX_ARCHIVES_DX10_AE}"
		else:
			results = f" / {MAX_ARCHIVES_GNRL}\n / {MAX_ARCHIVES_DX10}\n / {MAX_ARCHIVES_GNRL + MAX_ARCHIVES_DX10}"

		label_archives_max = ttk.Label(
			self.frame_info_archives,
			text=results,
			font=FONT,
			foreground=COLOR_DEFAULT,
		)
		label_archives_max.grid(column=2, row=0, rowspan=3, sticky=EW)
		add_tooltip(label_archives_max, TOOLTIP_BA2_FORMATS)

		# Column 0
		size = self.frame_info_archives.grid_size()
		ttk.Button(
			self.frame_info_archives,
			text="Archive Patcher...",
			padding=scale(5),
			command=lambda: ArchivePatcher(self.cmc.root, self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=scale(10))
		self.frame_info_archives.grid_rowconfigure(size[1], weight=2)
		self.frame_info_archives.grid_columnconfigure(2, weight=1)

	def build_gui_modules(self) -> None:
		self.frame_info_modules = ttk.Labelframe(self, text="Modules (ESM/ESL/ESP)")
		self.frame_info_modules.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		label_module_types = ttk.Label(
			self.frame_info_modules,
			text="Full:\nLight:\nTotal:",
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		)
		label_module_types.grid(column=0, row=0, rowspan=3, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_module_types, TOOLTIP_MODULE_TYPES)

		color_unreadable = COLOR_BAD if self.cmc.game.modules_unreadable else COLOR_NEUTRAL_1
		label_unreadable = ttk.Label(
			self.frame_info_modules,
			text="Unreadable:",
			font=FONT,
			foreground=color_unreadable,
		)
		label_unreadable.grid(column=0, row=3, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_unreadable, TOOLTIP_UNREADABLE)

		add_separator(self.frame_info_modules, HORIZONTAL, 0, 4, 3)

		label_hedr_100 = ttk.Label(
			self.frame_info_modules,
			text="HEDR v1.00:",
			font=FONT,
			foreground=COLOR_DEFAULT,
		)
		label_hedr_100.grid(column=0, row=5, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_hedr_100, TOOLTIP_HEDR_100)

		label_hedr_95 = ttk.Label(
			self.frame_info_modules,
			text="HEDR v0.95:",
			font=FONT,
			foreground=COLOR_DEFAULT,
		)
		label_hedr_95.grid(column=0, row=6, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_hedr_95, TOOLTIP_HEDR_95)

		color_hedr_unknown = COLOR_BAD if self.cmc.game.modules_hedr_unknown else COLOR_NEUTRAL_1
		label_hedr_unknown = ttk.Label(
			self.frame_info_modules,
			text="HEDR v????:",
			font=FONT,
			foreground=color_hedr_unknown,
		)
		label_hedr_unknown.grid(column=0, row=7, sticky=E, padx=(scale(5), 0))
		add_tooltip(label_hedr_unknown, TOOLTIP_HEDR_UNKNOWN)

		# Column 1
		self.add_count_label(self.frame_info_modules, 1, 0, "Full")
		self.add_count_label(self.frame_info_modules, 1, 1, "Light")
		self.add_count_label(self.frame_info_modules, 1, 2, "TotalModules")

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_unreadable),
			font=FONT,
			foreground=color_unreadable,
		).grid(column=1, row=3, sticky=E, padx=(scale(5), 0))

		ttk.Label(
			self.frame_info_modules,
			text=self.cmc.game.module_count_v1,
			font=FONT,
			foreground=COLOR_DEFAULT,
		).grid(column=1, row=5, sticky=E, padx=(scale(5), 0))

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_hedr_95),
			font=FONT,
			foreground=COLOR_DEFAULT,
		).grid(column=1, row=6, sticky=E, padx=(scale(5), 0))

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_hedr_unknown),
			font=FONT,
			foreground=color_hedr_unknown,
		).grid(column=1, row=7, sticky=E, padx=(scale(5), 0))

		# Column 2
		label_module_max = ttk.Label(
			self.frame_info_modules,
			text=f" /  {MAX_MODULES_FULL}\n / {MAX_MODULES_LIGHT}\n / {MAX_MODULES_FULL + MAX_MODULES_LIGHT}",
			font=FONT,
			foreground=COLOR_DEFAULT,
			justify=RIGHT,
		)
		label_module_max.grid(column=2, row=0, rowspan=3, sticky=EW)
		add_tooltip(label_module_max, TOOLTIP_MODULE_TYPES)

		if self.cmc.game.modules_hedr_unknown:
			label_hedr_unknown_icon = ttk.Label(
				self.frame_info_modules,
				compound="image",
				image=self.cmc.get_image("images/info-16.png"),
				cursor="hand2",
			)
			label_hedr_unknown_icon.grid(column=2, row=7, sticky=W, padx=(scale(5), 0), ipady=scale(3))
			add_tooltip(label_hedr_unknown_icon, "Detection details")
			label_hedr_unknown_icon.bind(
				"<Button-1>",
				lambda _: TreeWindow(
					self.cmc.root,
					self.cmc,
					400,
					500,
					"Detected Invalid Module Versions",
					"",
					("HEDR", " Module"),
					[(v, k) for k, v in self.cmc.game.modules_hedr_unknown.items()],
				),
			)

	def add_count_label(
		self,
		frame: ttk.Labelframe,
		column: int,
		row: int,
		count: Literal["GNRL", "DX10", "TotalBA2s", "Full", "Light", "TotalModules"],
	) -> None:
		match count:
			case "GNRL":
				num = self.cmc.game.ba2_count_gnrl
				# num = len(self.cmc.game.archives_gnrl)
				limit = (
					MAX_ARCHIVES_GNRL_AE
					if self.cmc.game.install_type in {InstallType.Obsolete2, InstallType.AE2}
					else MAX_ARCHIVES_GNRL
				)
			case "DX10":
				num = self.cmc.game.ba2_count_dx10
				# num = len(self.cmc.game.archives_dx10)
				limit = (
					MAX_ARCHIVES_DX10_AE
					if self.cmc.game.install_type in {InstallType.Obsolete2, InstallType.AE2}
					else MAX_ARCHIVES_DX10
				)
			case "Full":
				num = self.cmc.game.module_count_full
				limit = MAX_MODULES_FULL
			case "Light":
				num = self.cmc.game.module_count_light
				limit = MAX_MODULES_LIGHT
			case "TotalBA2s":
				num = self.cmc.game.ba2_count_gnrl + self.cmc.game.ba2_count_dx10
				# num = len(self.cmc.game.archives_gnrl) + len(self.cmc.game.archives_dx10)
				limit = (
					MAX_ARCHIVES_GNRL_AE + MAX_ARCHIVES_DX10_AE
					if self.cmc.game.install_type in {InstallType.Obsolete2, InstallType.AE2}
					else MAX_ARCHIVES_GNRL + MAX_ARCHIVES_DX10
				)
			case "TotalModules":
				num = self.cmc.game.module_count_full + self.cmc.game.module_count_light
				limit = MAX_MODULES_FULL + MAX_MODULES_LIGHT

		warn_limit = int(0.95 * limit)
		if num < warn_limit:
			color = COLOR_GOOD
		elif num <= limit:
			color = COLOR_WARNING
		else:
			color = COLOR_BAD
			if not count.startswith("Total"):
				file_type = "Archive" if count in {"GNRL", "DX10"} else "Module"
				file_format = "General" if count == "GNRL" else "Texture" if count == "DX10" else count
				if file_type == "Archive":
					solution = "Archives can be unpacked or merged to reduce your total.\nNote: Do not mix texture and non-texture archives when merging.\nUnpacking is only suggested for small non-texture archives for performance reasons.\nYou can use Unpackrr to quickly unpack small archives:"
					extra_data = ["https://www.nexusmods.com/fallout4/mods/82082"]

				# Modules
				elif count == "Full":
					solution = "Many Full modules are eligible to be flagged as Light (ESL).\n\nThis guide walks you through the process in xEdit:"
					extra_data = ["https://themidnightride.moddinglinked.com/esl.html"]
				else:
					# Light
					solution = "Some plugins will need to be removed or manually merged.\nWarning: Do not use old/outdated tools like zMerge with Fallout 4 unless\nyou understand their issues and how to fix the merged plugins afterward."
					extra_data = None

				self.cmc.overview_problems.append(
					SimpleProblemInfo(
						f"{num} {file_format} {file_type}s",
						"Limit Exceeded",
						f"You have {num} {file_format} {file_type}s enabled. The limit is {limit}.",
						solution,
						extra_data=extra_data,
					),
				)

		ttk.Label(frame, text=str(num).rjust(4), font=FONT, foreground=color).grid(
			column=column,
			row=row,
			sticky=E,
			padx=(scale(5), 0),
		)

	def get_file_info(self, file_name: str, file_path: Path) -> FileInfo:
		logger.debug("Get File Info: %s", file_path)

		if not is_file(file_path):
			return {
				"File": None,
				"Version": None,
				"VersionString": None,
				"Hash": None,
				"InstallType": InstallType.NotFound,
			}

		version = get_file_version(file_path)
		file_hash = get_crc32(file_path)

		if version:
			version_string = ver_to_str(version)
			install_type = BASE_FILES[file_name].get(version_string) or BASE_FILES[file_name].get(file_hash)
		else:
			version_string = file_hash
			install_type = BASE_FILES[file_name].get(file_hash)

		if install_type == InstallType.NGAE and self.cmc.game.install_type in {InstallType.NG, InstallType.AE, InstallType.AE2}:
			install_type = self.cmc.game.install_type

		return {
			"File": file_path,
			"Version": version,
			"VersionString": version_string,
			"Hash": file_hash,
			"InstallType": install_type or InstallType.Unknown,
		}

	def get_info_binaries(self) -> None:
		logger.debug("Gathering Info: Binaries")
		self.cmc.game.reset_binaries()

		if not self.cmc.game.manager:
			self.cmc.overview_problems.append(
				SimpleProblemInfo(
					Path(sys.argv[0]).name,
					"No Mod Manager",
					"No Mod Manager Detected",
					TOOLTIP_NO_MOD_MANAGER,
				),
			)

		for file_name in BASE_FILES:
			file_path = self.cmc.game.game_path / file_name
			file_info = self.get_file_info(file_name, file_path)
			self.cmc.game.file_info[file_path.name] = file_info

			if file_name == "Fallout4.exe":
				self.cmc.game.install_type = file_info["InstallType"]

				if self.cmc.game.install_type == InstallType.Unknown:
					self.cmc.overview_problems.append(
						SimpleProblemInfo(
							"Fallout4.exe",
							"Unknown Game Version",
							f"{file_info['VersionString'] or file_info['Hash']} is an unknown version.\nPossible causes:\n1. The game is an old version and should be updated.\n2. The exe file may be corrupted.\n3. The game is a new version and the Toolkit needs to be updated.",
							"Either update the game/verify files in Steam, or report this issue.",
						),
					)

				if self.cmc.game.data_path and file_info["VersionString"]:
					address_library_name = f"version-{file_info['VersionString'].replace('.', '-')}.bin"
					relative_path = Path("F4SE/Plugins", address_library_name)
					address_library_path = self.cmc.game.data_path / relative_path
					if is_file(address_library_path):
						self.cmc.game.address_library = address_library_path
					else:
						self.cmc.overview_problems.append(
							ProblemInfo(
								ProblemType.FileNotFound,
								address_library_path,
								relative_path,
								None,
								"Address Library is a requirement for many F4SE mods and playing downgraded,\nand likely needs to be installed.",
								SolutionType.DownloadMod,
								extra_data=["https://www.nexusmods.com/fallout4/mods/47327"],
							),
						)

				if self.cmc.game.data_path is not None and self.cmc.game.is_foog():
					startup_name = Path("Fallout4 - Startup.ba2")
					startup_ba2 = self.cmc.game.data_path / startup_name
					if is_file(startup_ba2):
						startup_crc = get_crc32(startup_ba2, skip_ba2_header=True)
						if startup_crc == NG_STARTUP_BA2_CRC:
							self.cmc.game.install_type = InstallType.DG
					else:
						self.cmc.overview_problems.append(
							ProblemInfo(
								ProblemType.FileNotFound,
								startup_ba2,
								startup_name,
								None,
								"This is a base game file, and is used by CM Toolkit to differentiate between\nOld-Gen and Down-Grade.",
								SolutionType.VerifyFiles,
							),
						)

	def get_info_archives(self) -> None:
		logger.debug("Gathering Info: Archives")
		self.cmc.game.reset_archives()

		if self.cmc.game.data_path is None:
			logger.debug("Archives: No Data Path")
			# Reported to Scanner in get_info_modules.
			return

		settings_archive_lists = (
			"sresourceindexfilelist",
			"sresourcestartuparchivelist",
			"sresourcearchivelist",
			"sresourcearchivelist2",
		)

		ini_archive = self.cmc.game.game_settings.get("archive")
		if ini_archive is None:
			ini_archive = {}
			self.cmc.overview_problems.append(
				SimpleProblemInfo(
					"Fallout4.ini",
					ProblemType.FileNotFound,
					"The [Archive] section is missing from your game INIs.\nBase game archives can't be detected, so archive counts will be inaccurate.",
					"Run the Fallout 4 Launcher or Bethini Pie to generate the INIs.",
				),
			)

		self.cmc.game.archives_enabled = {
			archive_path
			for archive_list in settings_archive_lists
			for n in ini_archive.get(archive_list, "").split(",")
			if is_file(archive_path := self.cmc.game.data_path / n.strip())
		}

		self.cmc.game.archives_enabled.update({
			ps
			for p in self.cmc.game.modules_enabled
			for s in self.cmc.game.ba2_suffixes
			if is_file(ps := p.with_name(f"{p.stem} - {s}.ba2"))
		})

		if self.cmc.game.game_prefs.get("nvflex", {}).get("bnvflexenable", "0") == "1":
			flex_ba2_path = self.cmc.game.data_path / "Fallout4 - Nvflex.ba2"
			if is_file(flex_ba2_path):
				self.cmc.game.archives_enabled.add(flex_ba2_path)
			else:
				self.cmc.overview_problems.append(
					SimpleProblemInfo(
						"Fallout4 - Nvflex.ba2",
						ProblemType.FileNotFound,
						"Nvidia Flex is enabled in your game INIs (bNVFlexEnable=1) but the Nvflex BA2 is missing.\nThe exe is hardcoded to load this BA2.",
						SolutionType.VerifyFiles,
					),
				)

		if self.cmc.game.install_type in {InstallType.AE, InstallType.AE2}:
			ae_ba2_path = self.cmc.game.data_path / "Fallout4 - TexturesPatch.ba2"
			if is_file(ae_ba2_path):
				self.cmc.game.archives_enabled.add(ae_ba2_path)
			else:
				self.cmc.overview_problems.append(
					SimpleProblemInfo(
						"Fallout4 - TexturesPatch.ba2",
						ProblemType.FileNotFound,
						"Your game is Anniversary Edition but the TexturesPatch BA2 is missing.\nThe exe is hardcoded to load this BA2.",
						SolutionType.VerifyFiles,
					),
				)

		for ba2_file in self.cmc.game.archives_enabled:
			logger.debug("Archives: Checking %s", ba2_file.name)

			try:
				with ba2_file.open("rb") as f:
					head = f.read(12)
			except PermissionError, FileNotFoundError:
				self.cmc.game.archives_unreadable.add(ba2_file)
				self.cmc.overview_problems.append(
					ProblemInfo(
						ProblemType.InvalidArchive,
						ba2_file,
						Path(ba2_file.name),
						"OVERVIEW",
						"Failed to read archive due to permissions or the file is missing.",
						None,
					),
				)
				continue

			if len(head) != 12 or head[:4] != Magic.BTDX:
				self.cmc.game.archives_unreadable.add(ba2_file)
				self.cmc.overview_problems.append(
					ProblemInfo(
						ProblemType.InvalidArchive,
						ba2_file,
						Path(ba2_file.name),
						"OVERVIEW",
						"Archive is either corrupt or not in Bethesda Archive 2 format.",
						None,
					),
				)
				continue

			match head[4]:
				case ArchiveVersion.OG:
					is_ng = False

				case ArchiveVersion.NG7 | ArchiveVersion.NG:
					is_ng = True

				case _:
					self.cmc.game.archives_unreadable.add(ba2_file)
					# TODO: Report known wrong versions
					self.cmc.overview_problems.append(
						ProblemInfo(
							ProblemType.InvalidArchive,
							ba2_file,
							Path(ba2_file.name),
							"OVERVIEW",
							f"Archive version ({head[4]}) is not valid for Fallout 4.",
							None,
						),
					)
					continue

			match head[8:]:
				case Magic.GNRL:
					self.cmc.game.ba2_count_gnrl += 1

				case Magic.DX10:
					self.cmc.game.ba2_count_dx10 += 1

				case _:
					self.cmc.game.archives_unreadable.add(ba2_file)
					self.cmc.overview_problems.append(
						ProblemInfo(
							ProblemType.InvalidArchive,
							ba2_file,
							Path(ba2_file.name),
							"OVERVIEW",
							f"Archive format ({head[8:].decode('utf-8', errors='replace')}) is not valid for Fallout 4.",
							None,
						),
					)
					continue

			if is_ng:
				self.cmc.game.archives_ng.add(ba2_file)
			else:
				self.cmc.game.archives_og.add(ba2_file)

	def get_info_modules(self, *, refresh: bool = False) -> None:
		logger.debug("Gathering Info: Modules")
		self.cmc.game.reset_modules()

		data_path = self.cmc.game.data_path
		if data_path is None:
			self.cmc.overview_problems.append(
				SimpleProblemInfo(
					"Data",
					ProblemType.FileNotFound,
					"The Data folder was not found in your game install path.",
					SolutionType.VerifyFiles,
				),
			)
			return

		self.cmc.game.modules_enabled = [master_path for master in GAME_MASTERS if exists(master_path := data_path / master)]

		ccc_path = self.cmc.game.game_path / "Fallout4.ccc"
		if is_file(ccc_path):
			self.cmc.game.modules_enabled.extend([
				cc_path for cc in ccc_path.read_text("utf-8").splitlines() if is_file(cc_path := data_path / cc)
			])
		else:
			self.cmc.overview_problems.append(
				SimpleProblemInfo(
					"Fallout4.ccc",
					ProblemType.FileNotFound,
					"The CC list file was not found in your game install path.\nThis is used to detect which CC modules/archives may be enabled.",
					SolutionType.VerifyFiles,
				),
			)
			if not refresh:
				messagebox.showwarning(
					"Warning",
					f"{ccc_path.name} not found.\nCC files may not be detected. Verifying Steam files or reinstalling should fix this.",
				)

		plugins_path = get_environment_path(CSIDL.AppDataLocal) / "Fallout4\\plugins.txt"
		try:
			plugins_content = plugins_path.read_text("utf-8")
		except PermissionError, FileNotFoundError:
			self.cmc.overview_problems.append(
				SimpleProblemInfo(
					plugins_path.name,
					ProblemType.FileNotFound,
					"plugins.txt was not found.\nThis is used to detect which modules/archives are enabled.",
					"N/A" if self.cmc.game.manager else "Launch this app with your mod manager.",
				),
			)
			if not refresh:
				messagebox.showwarning(
					"Warning",
					"plugins.txt not found.\nEnable state of plugins can't be detected.\nCounts will reflect all modules/archives in Data, which is likely higher than your actual counts.",
				)
			current_plugins = self.cmc.game.modules_enabled.copy()
			self.cmc.game.modules_enabled.extend([
				p for p in data_path.iterdir() if p.suffix.lower() in {".esp", ".esl", ".esm"} and p not in current_plugins
			])
		else:
			self.cmc.game.modules_enabled.extend([
				plugin_path
				for plugin in plugins_content.splitlines()
				if plugin.startswith("*") and is_file(plugin_path := data_path / plugin[1:])
			])

		for module_path in self.cmc.game.modules_enabled:
			try:
				with module_path.open("rb") as f:
					head = f.read(34)
			except PermissionError, FileNotFoundError:
				self.cmc.game.modules_unreadable.add(module_path)
				self.cmc.overview_problems.append(
					ProblemInfo(
						ProblemType.InvalidModule,
						module_path,
						Path(module_path.name),
						"OVERVIEW",
						"Failed to read module due to permissions or the file is missing.",
						None,
					),
				)
				continue

			if len(head) != 34 or head[:4] != Magic.TES4:
				self.cmc.game.modules_unreadable.add(module_path)
				self.cmc.overview_problems.append(
					ProblemInfo(
						ProblemType.InvalidModule,
						module_path,
						Path(module_path.name),
						"OVERVIEW",
						"Module is either corrupt or not in TES4 format.",
						None,
					),
				)
				continue

			if head[24:28] != Magic.HEDR:
				self.cmc.game.modules_unreadable.add(module_path)
				continue

			hedr_version = head[30:34]
			if hedr_version == MODULE_VERSION_95:
				self.cmc.game.modules_hedr_95.add(module_path)
			elif hedr_version == MODULE_VERSION_1:
				self.cmc.game.module_count_v1 += 1
			else:
				hedr = round(struct.unpack("<f", hedr_version)[0], 2)
				valid_games = [g for g, v in MODULE_VERSION_SUPPORT.items() if str(hedr) in v]
				valid_games_str = (f"\nGames supporting v{hedr}: " + ", ".join(valid_games)) if valid_games else ""
				self.cmc.game.modules_hedr_unknown[module_path] = hedr
				self.cmc.overview_problems.append(
					ProblemInfo(
						ProblemType.InvalidModule,
						module_path,
						Path(module_path.name),
						"OVERVIEW",
						f"Module version ({hedr}) is not valid for Fallout 4.{valid_games_str}",
						"It may be possible to open/resave this file with Creation Kit to update its format for Fallout 4.\nYou should compare the original and resaved files with xEdit to verify no undesired changes were made.",
					),
				)

			flags = struct.unpack("<I", head[8:12])[0]
			if flags & ModuleFlag.Light or module_path.suffix.lower() == ".esl":
				self.cmc.game.module_count_light += 1
			else:
				self.cmc.game.module_count_full += 1
