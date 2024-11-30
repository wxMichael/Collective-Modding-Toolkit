import os
import struct
from pathlib import Path
from tkinter import *
from tkinter import messagebox, ttk
from typing import Literal

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from downgrader import Downgrader
from enums import ArchiveVersion, Magic, ModuleFlag
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from modal_window import AboutWindow
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
		self.get_info_modules()
		self.get_info_archives()
		return True

	def _build_gui(self) -> None:
		self.build_tab_overview()

	def refresh(self) -> None:
		self.get_info_binaries()
		self.get_info_modules()
		self.get_info_archives()
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
			text="Mod Manager:\nGame Path:\nVersion:",
			font=FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=5)

		manager = self.cmc.game.manager
		if manager:
			label_mod_manager_icon = ttk.Label(
				frame_top,
				compound="image",
				image=self.cmc.get_image("images/info-16.png"),
			)
			label_mod_manager_icon.grid(column=1, row=0, sticky=W, padx=(0, 5), ipady=3)
			ToolTip(label_mod_manager_icon, "Detection details")
			label_mod_manager_icon.bind(
				"<Button-1>",
				lambda _: AboutWindow(
					self.cmc.root,
					self.cmc,
					750,
					350,
					"Detected Mod Manager Settings",
					(
						f"EXE: {manager.exe_path}"
						f"INI: {manager.ini_path}"
						f"Portable: {manager.portable}{f'\nPortable.txt: {manager.portable_txt_path}' if manager.portable_txt_path else ''}"
						f"{'\n'.join([f'{k}: {v}' for k, v in manager.mo2_settings.items()])}"
					),
				),
			)

		ttk.Label(
			frame_top,
			text=f"{self.cmc.game.manager.name} v{self.cmc.game.manager.version} [Profile: {self.cmc.game.manager.selected_profile or 'Unknown'}]"
			if self.cmc.game.manager
			else "Not Found",
			font=FONT,
			foreground=COLOR_NEUTRAL_2 if self.cmc.game.manager else COLOR_BAD,
		).grid(column=2, row=0, sticky=W)

		label_path = ttk.Label(
			frame_top,
			textvariable=self.cmc.game_path_sv,
			font=FONT,
			foreground=COLOR_NEUTRAL_2,
			cursor="hand2",
		)
		label_path.grid(column=2, row=1, sticky=W)
		label_path.bind("<Button-1>", lambda _: os.startfile(self.cmc.game.game_path))
		ToolTip(label_path, TOOLTIP_GAME_PATH)

		ttk.Label(
			frame_top,
			textvariable=self.cmc.install_type_sv,
			font=FONT,
			foreground=COLOR_GOOD,
		).grid(column=2, row=2, sticky=W)

		button_refresh = ttk.Button(
			frame_top,
			compound="image",
			image=self.cmc.get_image("images/refresh-32.png"),
			command=self.refresh,
			padding=0,
		)
		button_refresh.grid(column=3, row=0, rowspan=2, sticky=E, padx=10)
		ToolTip(button_refresh, TOOLTIP_REFRESH)

		self.build_tab_overview_binaries()
		self.build_tab_overview_archives()
		self.build_tab_overview_modules()

	def build_tab_overview_binaries(self) -> None:
		self.frame_info_binaries = ttk.Labelframe(self, text="Binaries (EXE/DLL/BIN)")
		self.frame_info_binaries.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		file_names = "\n".join([f.rsplit(".", 1)[0] + ":" for f in self.cmc.game.file_info])
		rows = len(self.cmc.game.file_info)

		label_file_names = ttk.Label(self.frame_info_binaries, text=file_names, font=FONT, justify=RIGHT)
		label_file_names.grid(column=0, row=0, rowspan=rows, sticky=E, padx=5)

		ttk.Label(
			self.frame_info_binaries,
			text="Address Library:",
			font=FONT,
			justify=RIGHT,
		).grid(column=0, row=rows, sticky=E, padx=5)

		label_address_library = ttk.Label(
			self.frame_info_binaries,
			text="Not Found" if not self.cmc.game.address_library else "Next-Gen" if self.cmc.game.is_fong() else "Old-Gen",
			font=FONT,
			foreground=COLOR_GOOD if self.cmc.game.address_library else COLOR_BAD,
		)
		label_address_library.grid(column=1, row=rows, sticky=W)
		if not self.cmc.game.address_library:
			ToolTip(label_address_library, TOOLTIP_ADDRESS_LIBRARY_MISSING)

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
				font=FONT,
				foreground=color,
				width=10,
			)
			version_label.grid(column=1, row=i, sticky=W)
			if install_type:
				version = ver_to_str(self.cmc.game.file_info[file_name]["Version"] or "Not Found")

				def on_enter(event: "Event[ttk.Label]", ver: str = version) -> None:
					event.widget.config(text=ver)

				def on_leave(event: "Event[ttk.Label]", it: str = install_type or "Not Found") -> None:
					event.widget.config(text=it)

				version_label.bind("<Enter>", on_enter)
				version_label.bind("<Leave>", on_leave)

		size = self.frame_info_binaries.grid_size()
		ttk.Button(
			self.frame_info_binaries,
			text="Downgrade Manager...",
			padding=5,
			command=lambda: Downgrader(self.cmc.root, self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=10)
		self.frame_info_binaries.grid_rowconfigure(size[1], weight=2)

	def build_tab_overview_archives(self) -> None:
		self.frame_info_archives = ttk.Labelframe(self, text="Archives (BA2)")
		self.frame_info_archives.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		label_ba2_formats = ttk.Label(
			self.frame_info_archives,
			text="General:\nTexture:\nTotal:",
			font=FONT,
			justify=RIGHT,
		)
		label_ba2_formats.grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))
		ToolTip(label_ba2_formats, TOOLTIP_BA2_FORMATS)

		color_unreadable = COLOR_BAD if self.cmc.game.archives_unreadable else COLOR_NEUTRAL_1
		label_unreadable = ttk.Label(
			self.frame_info_archives,
			text="Unreadable:",
			font=FONT,
			foreground=color_unreadable,
		)
		label_unreadable.grid(column=0, row=3, sticky=E, padx=(5, 0))
		ToolTip(label_unreadable, TOOLTIP_UNREADABLE)

		add_separator(self.frame_info_archives, HORIZONTAL, 0, 4, 3)

		label_ba2_versions = ttk.Label(
			self.frame_info_archives,
			text="v1 (OG):\nv7/8 (NG):",
			font=FONT,
			justify=RIGHT,
		)
		label_ba2_versions.grid(column=0, row=5, rowspan=2, sticky=E, padx=(5, 0))
		ToolTip(label_ba2_versions, TOOLTIP_BA2_VERSIONS)

		# Column 1
		self.add_count_label(self.frame_info_archives, 1, 0, "GNRL")
		self.add_count_label(self.frame_info_archives, 1, 1, "DX10")
		self.add_count_label(self.frame_info_archives, 1, 2, "TotalBA2s")

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_unreadable),
			font=FONT,
			foreground=color_unreadable,
		).grid(column=1, row=3, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_og),
			font=FONT,
		).grid(column=1, row=5, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_archives,
			text=len(self.cmc.game.archives_ng),
			font=FONT,
		).grid(column=1, row=6, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(
			self.frame_info_archives,
			text=f" / {MAX_ARCHIVES_GNRL}\n / {MAX_ARCHIVES_DX10 or '???'}\n / {MAX_ARCHIVES_GNRL + MAX_ARCHIVES_DX10}",
			font=FONT,
		).grid(column=2, row=0, rowspan=3, sticky=EW)

		# Column 0
		size = self.frame_info_archives.grid_size()
		ttk.Button(
			self.frame_info_archives,
			text="Archive Patcher...",
			padding=5,
			command=lambda: ArchivePatcher(self.cmc.root, self.cmc),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=10)
		self.frame_info_archives.grid_rowconfigure(size[1], weight=2)
		self.frame_info_archives.grid_columnconfigure(2, weight=1)

	def build_tab_overview_modules(self) -> None:
		self.frame_info_modules = ttk.Labelframe(self, text="Modules (ESM/ESL/ESP)")
		self.frame_info_modules.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		label_module_types = ttk.Label(
			self.frame_info_modules,
			text="Full:\nLight:\nTotal:",
			font=FONT,
			justify=RIGHT,
		)
		label_module_types.grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))
		ToolTip(label_module_types, TOOLTIP_MODULE_TYPES)

		color_unreadable = COLOR_BAD if self.cmc.game.modules_unreadable else COLOR_NEUTRAL_1
		label_unreadable = ttk.Label(
			self.frame_info_modules,
			text="Unreadable:",
			font=FONT,
			foreground=color_unreadable,
		)
		label_unreadable.grid(column=0, row=3, sticky=E, padx=(5, 0))
		ToolTip(label_unreadable, TOOLTIP_UNREADABLE)

		add_separator(self.frame_info_modules, HORIZONTAL, 0, 4, 3)

		label_hedr100 = ttk.Label(
			self.frame_info_modules,
			text="HEDR v1.00:",
			font=FONT,
		)
		label_hedr100.grid(column=0, row=5, sticky=E, padx=(5, 0))
		ToolTip(label_hedr100, TOOLTIP_HEDR100)

		# color_95 = COLOR_WARNING if self.cmc.game.modules_v95 else COLOR_NEUTRAL_1
		label_hedr95 = ttk.Label(
			self.frame_info_modules,
			text="HEDR v0.95:",
			font=FONT,
			# foreground=color_95,
		)
		label_hedr95.grid(column=0, row=6, sticky=E, padx=(5, 0))
		ToolTip(label_hedr95, TOOLTIP_HEDR95)

		# Column 1
		self.add_count_label(self.frame_info_modules, 1, 0, "Full")
		self.add_count_label(self.frame_info_modules, 1, 1, "Light")
		self.add_count_label(self.frame_info_modules, 1, 2, "TotalModules")

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_unreadable),
			font=FONT,
			foreground=color_unreadable,
		).grid(column=1, row=3, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_modules,
			text=self.cmc.game.module_count_v1,
			font=FONT,
		).grid(column=1, row=5, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_modules,
			text=len(self.cmc.game.modules_v95),
			font=FONT,
			# foreground=color_95,
		).grid(column=1, row=6, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(
			self.frame_info_modules,
			text=f" /  {MAX_MODULES_FULL}\n / {MAX_MODULES_LIGHT}\n / {MAX_MODULES_FULL + MAX_MODULES_LIGHT}",
			font=FONT,
			justify=RIGHT,
		).grid(column=2, row=0, rowspan=3, sticky=EW)

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
				limit = MAX_ARCHIVES_GNRL
			case "DX10":
				num = self.cmc.game.ba2_count_dx10
				limit = MAX_ARCHIVES_DX10
			case "Full":
				num = self.cmc.game.module_count_full
				limit = MAX_MODULES_FULL
			case "Light":
				num = self.cmc.game.module_count_light
				limit = MAX_MODULES_LIGHT
			case "TotalBA2s":
				num = self.cmc.game.ba2_count_gnrl + self.cmc.game.ba2_count_dx10
				limit = MAX_ARCHIVES_GNRL + MAX_ARCHIVES_DX10
			case "TotalModules":
				num = self.cmc.game.module_count_full + self.cmc.game.module_count_light
				limit = MAX_MODULES_FULL + MAX_MODULES_LIGHT

		color = COLOR_GOOD if num < limit else COLOR_BAD

		ttk.Label(frame, text=str(num).rjust(4), font=FONT, foreground=color).grid(
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
						self.cmc.game.address_library = address_library_path

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

		game_language = self.cmc.game.game_settings.get("general", {}).get("slanguage", "en").lower()
		if game_language == "en":
			ba2_suffixes: tuple[str, ...] = (" - Main", " - Textures", " - Voices_en")
		else:
			ba2_suffixes = (" - Main", " - Textures", " - Voices_en", f" - Voices_{game_language}")

		settings_archive_lists = (
			"sResourceIndexFileList",
			"sResourceStartUpArchiveList",
			"SResourceArchiveList",
			"SResourceArchiveList2",
		)

		enabled_archives = {
			self.cmc.game.data_path / n.strip()
			for archive_list in settings_archive_lists
			for n in self.cmc.game.game_settings.get("archive", {}).get(archive_list, "").split(",")
		}

		enabled_archives.update({
			ps for p in self.cmc.game.modules_enabled for s in ba2_suffixes if (ps := p.with_name(f"{p.stem}{s}.ba2")).is_file()
		})

		if self.cmc.game.game_prefs.get("nvflex", {}).get("bnvflexenable", "0") == "1":
			flex_ba2_path = self.cmc.game.data_path / "Fallout4 - Nvflex.ba2"
			if flex_ba2_path.is_file():
				enabled_archives.add(flex_ba2_path)

		for ba2_file in enabled_archives:
			try:
				with ba2_file.open("rb") as f:
					head = f.read(12)
			except PermissionError:
				continue

			if len(head) != 12:
				self.cmc.game.archives_unreadable.add(ba2_file)
				continue

			if head[:4] != Magic.BTDX:
				self.cmc.game.archives_unreadable.add(ba2_file)
				continue

			match head[4]:
				case ArchiveVersion.OG:
					is_ng = False

				case ArchiveVersion.NG7 | ArchiveVersion.NG:
					is_ng = True

				case _:
					self.cmc.game.archives_unreadable.add(ba2_file)
					continue

			match head[8:]:
				case Magic.GNRL:
					self.cmc.game.ba2_count_gnrl += 1

				case Magic.DX10:
					self.cmc.game.ba2_count_dx10 += 1

				case _:
					self.cmc.game.archives_unreadable.add(ba2_file)
					continue

			if is_ng:
				self.cmc.game.archives_ng.add(ba2_file)
			else:
				self.cmc.game.archives_og.add(ba2_file)

	def get_info_modules(self) -> None:
		self.cmc.game.reset_modules()

		data_path = self.cmc.game.data_path
		if data_path is None:
			return

		self.cmc.game.modules_enabled = [master_path for master in GAME_MASTERS if (master_path := data_path / master).is_file()]

		ccc_path = self.cmc.game.game_path / "Fallout4.ccc"
		if ccc_path.is_file():
			with ccc_path.open() as ccc_file:
				self.cmc.game.modules_enabled.extend([
					cc_path for cc in ccc_file.read().splitlines() if (cc_path := data_path / cc).is_file()
				])
		else:
			messagebox.showwarning("Warning", f"{ccc_path.name} not found.\nCC files may not be detected.")

		plugins_path = Path.home() / "AppData\\Local\\Fallout4\\plugins.txt"
		if plugins_path.is_file():
			with plugins_path.open() as plugins_file:
				self.cmc.game.modules_enabled.extend([
					plugin_path
					for plugin in plugins_file.read().splitlines()
					if plugin.startswith("*") and (plugin_path := data_path / plugin[1:]).is_file()
				])
		else:
			messagebox.showwarning(
				"Warning",
				f"{plugins_path.name} not found.\nEnable state of plugins can't be detected.\nCounts will reflect all plugins in Data.",
			)
			current_plugins = self.cmc.game.modules_enabled.copy()
			self.cmc.game.modules_enabled.extend([p for p in data_path.glob("*.es[mlp]") if p not in current_plugins])

		for module_file in self.cmc.game.modules_enabled:
			try:
				with module_file.open("rb") as f:
					head = f.read(34)
			except PermissionError:
				continue

			if len(head) != 34:
				self.cmc.game.modules_unreadable.add(module_file)
				continue

			if head[:4] != Magic.TES4:
				self.cmc.game.modules_unreadable.add(module_file)
				continue

			if head[24:28] != Magic.HEDR:
				self.cmc.game.modules_unreadable.add(module_file)
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
