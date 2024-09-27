import os
import struct
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import Literal

from tkextrafont import Font

from downgrader import Downgrader
from globals import *
from helpers import (
	ArchiveVersion,
	CMCheckerInterface,
	DLLInfo,
	FileInfo,
	Magic,
	ModuleFlag,
	Tab,
)
from patcher_archives import ArchivePatcher
from utils import (
	add_separator,
	check_for_update_github,
	check_for_update_nexus,
	copy_text_button,
	find_game_paths,
	find_mod_manager,
	get_asset_path,
	get_crc32,
	get_file_version,
	parse_dll,
	ver_to_str,
)

TAG_NEUTRAL = "neutral"
TAG_GOOD = "good"
TAG_BAD = "bad"

EMOJI_DLL_UNKNOWN = "\N{BLACK QUESTION MARK ORNAMENT}"
EMOJI_DLL_GOOD = "\N{HEAVY CHECK MARK}"
EMOJI_DLL_BAD = ""


class CMChecker(CMCheckerInterface):
	def __init__(self, window: Tk) -> None:
		self.window = window

		self.cascadia = Font(file=get_asset_path("fonts/CascadiaMono.ttf"), name="Cascadia Mono")

		self.FONT = (self.cascadia.name, 12)
		self.FONT_SMALL = (self.cascadia.name, 10)
		self.FONT_LARGE = (self.cascadia.name, 20)

		self.file_info: dict[str, FileInfo] = {}
		self.dll_info: dict[str, DLLInfo | None] = {}
		self.address_library: Path | None = None
		self.ckpe_loader_found = False
		self.ckfixes_found = False

		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.archives_og: set[Path] = set()
		self.archives_ng: set[Path] = set()
		self.archives_invalid: set[Path] = set()

		self.module_count_full = 0
		self.module_count_light = 0
		self.modules_invalid: set[Path] = set()
		self.modules_v95: set[Path] = set()

		self.tabs_built: set[Tab] = set()
		self._install_type_sv = StringVar()
		self._game_path_sv = StringVar()
		self.install_type = InstallType.Unknown
		self.game_path, self.data_path, self.f4se_path = find_game_paths()
		self.mod_manager = find_mod_manager()
		self._images: dict[str, PhotoImage] = {}
		self.setup_window()

	def get_image(self, relative_path: str) -> PhotoImage:
		if relative_path not in self._images:
			self._images[relative_path] = PhotoImage(file=get_asset_path(relative_path))

		return self._images[relative_path]

	@property
	def game_path(self) -> Path:
		return self._game_path

	@game_path.setter
	def game_path(self, value: Path) -> None:
		self._game_path = value
		self._game_path_sv.set(str(value))

	@property
	def install_type(self) -> InstallType:
		return self._install_type

	@install_type.setter
	def install_type(self, value: InstallType) -> None:
		self._install_type = value
		self._install_type_sv.set(str(value))

	def setup_window(self) -> None:
		self.window.resizable(width=False, height=False)
		self.window.wm_attributes("-fullscreen", "false")
		self.window.iconphoto(True, self.get_image("images/icon-32.png"))  # noqa: FBT003
		self.window.title(f"{APP_TITLE} v{APP_VERSION}")

		x = (self.window.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
		y = (self.window.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
		self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
		self.window.grid_columnconfigure(0, weight=1)

		nexus_version = check_for_update_nexus()
		github_version = check_for_update_github()
		if nexus_version or github_version:
			update_frame = ttk.Frame(self.window)
			update_frame.grid(sticky=NSEW)

			column = 0
			ttk.Label(
				update_frame,
				image=self.get_image("images/update-24.png"),
				text="An update is available:",
				compound=LEFT,
				background="pale green",
				foreground="dark green",
				anchor=E,
				justify=RIGHT,
				padding="5 5",
				font=self.FONT,
			).grid(column=column, row=0, sticky=NSEW)

			if nexus_version is not None:
				column += 1
				hyperlink_label_nexus = ttk.Label(
					update_frame,
					text=f"v{nexus_version} (NexusMods)",
					background="pale green",
					foreground="SteelBlue4",
					cursor="hand2",
					anchor=W,
					justify=LEFT,
					padding="0",
					font=(*self.FONT, "bold underline"),
				)
				hyperlink_label_nexus.grid(column=column, row=0, sticky=NSEW)
				hyperlink_label_nexus.bind("<Button-1>", lambda _: webbrowser.open(NEXUS_LINK))

			if github_version and nexus_version:
				column += 1
				ttk.Label(
					update_frame,
					text=" / ",
					background="pale green",
					foreground="dark green",
					anchor=W,
					justify=LEFT,
					font=self.FONT,
				).grid(column=column, row=0, sticky=NSEW)

			if github_version is not None:
				column += 1
				hyperlink_label_github = ttk.Label(
					update_frame,
					text=f"v{github_version} (GitHub)",
					background="pale green",
					foreground="SteelBlue4",
					cursor="hand2",
					anchor=W,
					justify=LEFT,
					font=(*self.FONT, "bold underline"),
				)
				hyperlink_label_github.grid(column=column, row=0, sticky=NSEW)
				hyperlink_label_github.bind("<Button-1>", lambda _: webbrowser.open(GITHUB_LINK))

			update_frame.grid_columnconfigure(0, weight=1)
			update_frame.grid_columnconfigure(column, weight=1)
			update_frame.grid_rowconfigure(0, weight=1)

		notebook = ttk.Notebook(self.window)
		notebook.grid(sticky=NSEW)

		self.window.grid_rowconfigure(self.window.grid_size()[1] - 1, weight=1)

		self.tabs: dict[str, ttk.Frame] = {}
		for tab in Tab.__members__:
			self.tabs[tab] = ttk.Frame(notebook)
			notebook.add(self.tabs[tab], text=tab.replace("_", " "))

		notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

	def refresh_overview(self) -> None:
		self.game_path, self.data_path, self.f4se_path = find_game_paths()
		self.get_info_binaries()
		self.get_info_archives()
		self.get_info_modules()
		if Tab.Overview in self.tabs_built:
			self.frame_info_binaries.destroy()
			self.frame_info_archives.destroy()
			self.frame_info_modules.destroy()
			self.build_tab_overview_binaries()
			self.build_tab_overview_archives()
			self.build_tab_overview_modules()
		else:
			self.build_tab_overview()

	def build_tab_overview(self) -> None:
		frame_top = ttk.Frame(self.tabs[Tab.Overview])
		frame_top.pack(anchor=W, fill=X, pady=5)
		frame_top.grid_columnconfigure(index=2, weight=1)

		ttk.Label(
			frame_top,
			text="Install:\nDetected:\nMod Manager:",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=5)

		label_path = ttk.Label(
			frame_top,
			textvariable=self._game_path_sv,
			font=self.FONT,
			foreground=COLOR_NEUTRAL_2,
			cursor="hand2",
		)
		label_path.grid(column=1, row=0, sticky=W)
		label_path.bind("<Button-1>", lambda _: os.startfile(self.game_path))

		ttk.Label(
			frame_top,
			textvariable=self._install_type_sv,
			font=self.FONT,
			foreground=COLOR_GOOD,
		).grid(column=1, row=1, sticky=W)

		ttk.Label(
			frame_top,
			text=self.mod_manager or "Not Found",
			font=self.FONT,
			foreground=COLOR_NEUTRAL_2,
		).grid(column=1, row=2, sticky=W)

		ttk.Button(
			frame_top,
			compound="image",
			image=self.get_image("images/refresh-32.png"),
			command=self.refresh_overview,
			padding=0,
		).grid(column=2, row=0, rowspan=2, sticky=E, padx=10)

		self.build_tab_overview_binaries()
		self.build_tab_overview_archives()
		self.build_tab_overview_modules()

	def build_tab_overview_binaries(self) -> None:
		self.frame_info_binaries = ttk.Labelframe(self.tabs[Tab.Overview], text="Binaries (EXE/DLL/BIN)")
		self.frame_info_binaries.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		file_names = "\n".join([f.rsplit(".", 1)[0] + ":" for f in self.file_info])
		rows = len(self.file_info)

		label_file_names = ttk.Label(self.frame_info_binaries, text=file_names, font=self.FONT, justify=RIGHT)
		label_file_names.grid(column=0, row=0, rowspan=rows, sticky=E, padx=5)

		ttk.Label(
			self.frame_info_binaries,
			text="Address Library:",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=0, row=rows, sticky=E, padx=5)

		ttk.Label(
			self.frame_info_binaries,
			text="Installed" if self.address_library else "Not Found",
			font=self.FONT,
			foreground=COLOR_GOOD if self.address_library else COLOR_BAD,
		).grid(column=1, row=rows, sticky=W, padx=5)

		for i, file_name in enumerate(self.file_info.keys()):
			match self.file_info[file_name]["InstallType"]:
				case self.install_type:
					color = COLOR_GOOD

				case InstallType.OG:
					color = COLOR_GOOD if self.is_fodg() else COLOR_BAD

				case None:
					if file_name in {"CreationKit.exe", "Archive2.exe"} or (
						self.is_fong() and BASE_FILES[file_name].get("OnlyOG", False)
					):
						color = COLOR_NEUTRAL_1
					else:
						color = COLOR_BAD

				case _:
					color = COLOR_BAD

			ttk.Label(
				self.frame_info_binaries,
				text=ver_to_str(self.file_info[file_name]["Version"] or "Not Found"),
				font=self.FONT,
				foreground=color,
			).grid(column=1, row=i, sticky=W, padx=5)

		size = self.frame_info_binaries.grid_size()
		ttk.Button(
			self.frame_info_binaries,
			text="Manage Downgrade...",
			padding=0,
			command=lambda: Downgrader(self),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=5)
		self.frame_info_binaries.grid_rowconfigure(size[1], weight=2)

	def build_tab_overview_archives(self) -> None:
		self.frame_info_archives = ttk.Labelframe(self.tabs[Tab.Overview], text="Archives (BA2)")
		self.frame_info_archives.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		ttk.Label(
			self.frame_info_archives,
			text="General:\nTexture:\nTotal:",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))

		add_separator(self.frame_info_archives, HORIZONTAL, 0, 3, 3)

		ttk.Label(
			self.frame_info_archives,
			text="v1 (OG):\nv7/8 (NG):",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=0, row=4, rowspan=2, sticky=E, padx=(5, 0))

		color_invalid = COLOR_BAD if self.archives_invalid else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_archives,
			text="Invalid:",
			font=self.FONT,
			foreground=color_invalid,
		).grid(column=0, row=6, sticky=E, padx=(5, 0))

		# Column 1
		self.add_count_label(self.frame_info_archives, 1, 0, "GNRL")
		self.add_count_label(self.frame_info_archives, 1, 1, "DX10")

		ttk.Label(
			self.frame_info_archives,
			text=len(self.archives_og) + len(self.archives_ng),
			font=self.FONT,
		).grid(column=1, row=2, sticky=E, padx=(5, 0))

		ttk.Label(self.frame_info_archives, text=len(self.archives_og), font=self.FONT).grid(
			column=1,
			row=4,
			sticky=E,
			padx=(5, 0),
		)

		ttk.Label(self.frame_info_archives, text=len(self.archives_ng), font=self.FONT).grid(
			column=1,
			row=5,
			sticky=E,
			padx=(5, 0),
		)

		ttk.Label(
			self.frame_info_archives,
			text=len(self.archives_invalid),
			font=self.FONT,
			foreground=color_invalid,
		).grid(column=1, row=6, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(self.frame_info_archives, text=f" / {MAX_ARCHIVES_GNRL}", font=self.FONT).grid(
			column=2,
			row=0,
			sticky=EW,
		)
		if MAX_ARCHIVES_DX10 is not None:
			ttk.Label(self.frame_info_archives, text=f" / {MAX_ARCHIVES_DX10}", font=self.FONT).grid(
				column=2,
				row=1,
				sticky=EW,
			)

		# Column 0
		size = self.frame_info_archives.grid_size()
		ttk.Button(
			self.frame_info_archives,
			text="Archive Patcher...",
			padding=0,
			command=lambda: ArchivePatcher(self),
		).grid(column=0, row=size[1], columnspan=size[0], sticky=S, pady=5)
		self.frame_info_archives.grid_rowconfigure(size[1], weight=2)
		self.frame_info_archives.grid_columnconfigure(2, weight=1)

	def build_tab_overview_modules(self) -> None:
		self.frame_info_modules = ttk.Labelframe(self.tabs[Tab.Overview], text="Modules (ESM/ESL/ESP)")
		self.frame_info_modules.pack(anchor=N, fill=BOTH, side=LEFT, expand=True)

		# Column 0
		ttk.Label(
			self.frame_info_modules,
			text="Full:\nLight:\nTotal:",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=0, row=0, rowspan=3, sticky=E, padx=(5, 0))

		add_separator(self.frame_info_modules, HORIZONTAL, 0, 3, 3)

		color_95 = COLOR_WARNING if self.modules_v95 else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_modules,
			text="v0.95 HEDR:",
			font=self.FONT,
			foreground=color_95,
		).grid(column=0, row=4, sticky=E, padx=(5, 0))

		color_invalid = COLOR_BAD if self.modules_invalid else COLOR_NEUTRAL_1
		ttk.Label(
			self.frame_info_modules,
			text="Invalid:",
			font=self.FONT,
			foreground=color_invalid,
		).grid(column=0, row=5, sticky=E, padx=(5, 0))

		# Column 1
		self.add_count_label(self.frame_info_modules, 1, 0, "Full")
		self.add_count_label(self.frame_info_modules, 1, 1, "Light")
		self.add_count_label(self.frame_info_modules, 1, 2, "Total")

		ttk.Label(
			self.frame_info_modules,
			text=len(self.modules_v95),
			font=self.FONT,
			foreground=color_95,
		).grid(column=1, row=4, sticky=E, padx=(5, 0))

		ttk.Label(
			self.frame_info_modules,
			text=len(self.modules_invalid),
			font=self.FONT,
			foreground=color_invalid,
		).grid(column=1, row=5, sticky=E, padx=(5, 0))

		# Column 2
		ttk.Label(
			self.frame_info_modules,
			text=f" /  {MAX_MODULES_FULL}\n / {MAX_MODULES_LIGHT}\n / {MAX_MODULES_FULL + MAX_MODULES_LIGHT}",
			font=self.FONT,
			justify=RIGHT,
		).grid(column=2, row=0, rowspan=3, sticky=EW)

	def build_tab_f4se(self) -> None:
		self.tabs[Tab.F4SE_DLLs].grid_columnconfigure(0, weight=1)
		self.tabs[Tab.F4SE_DLLs].grid_rowconfigure(0, weight=1)

		error_message = None
		if self.data_path is None:
			error_message = "Data folder not found"
		elif self.f4se_path is None:
			error_message = "Data/F4SE/Plugins folder not found"

		if error_message is not None:
			ttk.Label(
				self.tabs[Tab.F4SE_DLLs],
				text=error_message,
				font=self.FONT_LARGE,
				foreground=COLOR_BAD,
				justify=CENTER,
			).grid(column=0, row=0)
			return

		assert self.f4se_path is not None

		label_loading_dlls = ttk.Label(
			self.tabs[Tab.F4SE_DLLs],
			text="Scanning DLLs...",
			font=self.FONT_LARGE,
			justify=CENTER,
		)
		label_loading_dlls.grid(column=0, row=0)
		self.tabs[Tab.F4SE_DLLs].update_idletasks()

		self.dll_info.clear()
		for dll_file in self.f4se_path.glob("*.dll"):
			self.dll_info[dll_file.name] = parse_dll(dll_file)

		label_loading_dlls.destroy()

		style = ttk.Style()
		style.configure("Treeview", font=self.FONT_SMALL)  # type: ignore
		tree_dlls = ttk.Treeview(self.tabs[Tab.F4SE_DLLs], columns=("og", "ng", "user"))
		tree_dlls.heading("#0", text="DLL")
		tree_dlls.heading("og", text="OG")
		tree_dlls.heading("ng", text="NG")
		tree_dlls.heading("user", text="Your Version")

		tree_dlls.column("#0", width=300, stretch=False, anchor=E)
		tree_dlls.column("og", width=60, stretch=False, anchor=CENTER)
		tree_dlls.column("ng", width=60, stretch=False, anchor=CENTER)
		tree_dlls.column("user", width=80, stretch=False, anchor=CENTER)

		tree_dlls.tag_configure(TAG_NEUTRAL, foreground=COLOR_NEUTRAL_1)
		tree_dlls.tag_configure(TAG_GOOD, foreground=COLOR_GOOD)
		tree_dlls.tag_configure(TAG_BAD, foreground=COLOR_BAD)

		scroll_tree_y = ttk.Scrollbar(
			self.tabs[Tab.F4SE_DLLs],
			orient=VERTICAL,
			command=tree_dlls.yview,  # type: ignore
		)

		tree_dlls.grid(column=0, row=0, sticky=NSEW)
		scroll_tree_y.grid(column=1, row=0, sticky=NS)
		tree_dlls.configure(yscrollcommand=scroll_tree_y.set)

		for dll, info in self.dll_info.items():
			values: list[str] = []
			tags: list[str] = []
			if info is None or not info["IsF4SE"]:
				tags.append(TAG_NEUTRAL)
				values = [EMOJI_DLL_UNKNOWN] * 4
			else:
				if info.get("SupportsOG"):
					values.append(EMOJI_DLL_GOOD)
				else:
					values.append(EMOJI_DLL_BAD)

				if info.get("SupportsNG"):
					values.append(EMOJI_DLL_GOOD)
				else:
					values.append(EMOJI_DLL_BAD)

				if (self.is_foog() and info.get("SupportsOG")) or (self.is_fong() and info.get("SupportsNG")):
					tags.append(TAG_GOOD)
					values.append(EMOJI_DLL_GOOD)
				else:
					tags.append(TAG_BAD)
					values.append("\N{CROSS MARK}")

			tree_dlls.insert("", END, text=dll, values=values, tags=tags)

	def show_wip(self, tab: Tab) -> None:
		ttk.Label(self.tabs[tab], text="WIP", font=self.FONT_LARGE, justify=CENTER).grid(column=0, row=0)
		self.tabs[tab].grid_columnconfigure(0, weight=1)
		self.tabs[tab].grid_rowconfigure(0, weight=1)

	def build_tab_errors(self) -> None:
		self.show_wip(Tab.Errors)

	def build_tab_conflicts(self) -> None:
		self.show_wip(Tab.Conflicts)

	def build_tab_suggestions(self) -> None:
		self.show_wip(Tab.Suggestions)

	def build_tab_tools(self) -> None:
		self.show_wip(Tab.Tools)

	def build_tab_about(self) -> None:
		ttk.Label(
			self.tabs[Tab.About],
			text="\n".join(APP_TITLE.rsplit(maxsplit=1)),
			font=self.FONT_LARGE,
			justify=CENTER,
		).grid(column=0, row=0, pady=10)

		ttk.Label(
			self.tabs[Tab.About],
			compound="image",
			image=self.get_image("images/icon-256.png"),
		).grid(column=0, row=1)
		self.tabs[Tab.About].grid_columnconfigure(0, weight=1)

		frame_about_text = ttk.Frame(self.tabs[Tab.About])
		frame_about_text.grid(column=1, row=0, rowspan=2, padx=(0, 20))

		ttk.Label(
			frame_about_text,
			text=f"v{APP_VERSION}\n\nCreated by wxMichael for the\nCollective Modding Community",
			font=self.FONT,
			justify=CENTER,
		).grid(column=0, row=1, rowspan=2, pady=(20, 10))

		frame_nexus = ttk.Frame(frame_about_text)
		frame_nexus.grid(column=0, row=3, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_nexus,
			compound="image",
			image=self.get_image("images/logo-nexusmods.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_nexus, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_nexus,
			text="Open Link",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(NEXUS_LINK),
		).grid(column=2, row=0, padx=0, pady=5)

		button_nexus_copy = ttk.Button(frame_nexus, text="Copy Link", padding=0, width=12)
		button_nexus_copy.configure(command=lambda: copy_text_button(button_nexus_copy, NEXUS_LINK))
		button_nexus_copy.grid(column=2, row=1, padx=0, pady=5)

		frame_discord = ttk.Frame(frame_about_text)
		frame_discord.grid(column=0, row=4, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_discord,
			compound="image",
			image=self.get_image("images/logo-discord.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_discord, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_discord,
			text="Open Invite",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(DISCORD_INVITE),
		).grid(column=2, row=0, padx=0, pady=5)

		button_discord_copy = ttk.Button(frame_discord, text="Copy Invite", padding=0, width=12)
		button_discord_copy.configure(command=lambda: copy_text_button(button_discord_copy, DISCORD_INVITE))
		button_discord_copy.grid(column=2, row=1, padx=0, pady=5)

		frame_github = ttk.Frame(frame_about_text)
		frame_github.grid(column=0, row=5, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_github,
			compound="image",
			image=self.get_image("images/logo-github.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_github, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_github,
			text="Open Link",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(GITHUB_LINK),
		).grid(column=2, row=0, padx=0, pady=5)

		button_github_copy = ttk.Button(frame_github, text="Copy Link", padding=0, width=12)
		button_github_copy.configure(command=lambda: copy_text_button(button_github_copy, GITHUB_LINK))
		button_github_copy.grid(column=2, row=1, padx=0, pady=5)

	def on_tab_changed(self, event: "Event[ttk.Notebook]") -> None:
		new_tab_index = event.widget.index("current")  # type: ignore
		new_tab = Tab[event.widget.tab(new_tab_index, "text").replace(" ", "_")]  # type: ignore

		if new_tab in self.tabs_built:
			return

		match new_tab:
			case Tab.Overview:
				self.refresh_overview()

			case Tab.F4SE_DLLs:
				self.build_tab_f4se()

			case Tab.Errors:
				self.build_tab_errors()

			case Tab.Conflicts:
				self.build_tab_conflicts()

			case Tab.Suggestions:
				self.build_tab_suggestions()

			case Tab.Tools:
				self.build_tab_tools()

			case Tab.About:
				self.build_tab_about()

		self.tabs_built.add(new_tab)
		self.window.update()

	def get_info_binaries(self) -> None:
		self.install_type = InstallType.Unknown
		self.file_info.clear()

		self.address_library = None
		self.ckfixes_found = self.game_path.joinpath("F4CKFixes").exists()

		for file_name in BASE_FILES:
			file_path = self.game_path / file_name
			if not file_path.is_file():
				self.file_info[file_path.name] = {
					"File": None,
					"Version": None,
					"InstallType": None,
				}
				continue

			if BASE_FILES[file_name].get("UseHash", False):
				version = get_crc32(file_path)
			else:
				version = ver_to_str(get_file_version(file_path))

			self.file_info[file_path.name] = {
				"File": file_path,
				"Version": version,
				"InstallType": BASE_FILES[file_name]["Versions"].get(version, InstallType.Unknown),
			}

			if file_path.name == "Fallout4.exe":
				self.install_type = self.file_info[file_path.name]["InstallType"] or InstallType.Unknown

				if self.f4se_path is not None:
					address_library_path = self.f4se_path / f'version-{version.replace(".", "-")}.bin'
					if address_library_path.is_file():
						self.address_library = address_library_path

				if self.data_path is not None and self.is_foog():
					startup_ba2 = self.data_path / "Fallout4 - Startup.ba2"
					if startup_ba2.is_file():
						startup_crc = get_crc32(startup_ba2, skip_ba2_header=True)
						if startup_crc == NG_STARTUP_BA2_CRC:
							self.install_type = InstallType.DG

	def get_info_archives(self) -> None:
		self.ba2_count_gnrl = 0
		self.ba2_count_dx10 = 0
		self.archives_og.clear()
		self.archives_ng.clear()
		self.archives_invalid.clear()

		if self.data_path is None:
			return

		for ba2_file in self.data_path.glob("*.ba2"):
			try:
				with ba2_file.open("rb") as f:
					head = f.read(12)
			except PermissionError:
				continue

			if head[:4] != Magic.BTDX:
				self.archives_invalid.add(ba2_file)
				continue

			match head[4]:
				case ArchiveVersion.OG:
					is_ng = False

				case ArchiveVersion.NG7 | ArchiveVersion.NG:
					is_ng = True

				case _:
					self.archives_invalid.add(ba2_file)
					continue

			match head[8:]:
				case Magic.GNRL:
					self.ba2_count_gnrl += 1

				case Magic.DX10:
					self.ba2_count_dx10 += 1

				case _:
					self.archives_invalid.add(ba2_file)
					continue

			if is_ng:
				self.archives_ng.add(ba2_file)
			else:
				self.archives_og.add(ba2_file)

	def get_info_modules(self) -> None:
		self.module_count_full = 0
		self.module_count_light = 0
		self.modules_invalid.clear()
		self.modules_v95.clear()

		if self.data_path is None:
			return

		for module_file in self.data_path.glob("*.es[mlp]"):
			with module_file.open("rb") as f:
				if f.read(4) != Magic.TES4:
					self.modules_invalid.add(module_file)
					continue

				f.seek(24)
				if f.read(4) != Magic.HEDR:
					self.modules_invalid.add(module_file)
					continue

				if module_file.name not in GAME_MASTERS:
					f.seek(30)
					if f.read(4) == MODULE_VERSION_95:
						self.modules_v95.add(module_file)

				f.seek(8)
				flags = struct.unpack("<I", f.read(4))[0]
				if flags & ModuleFlag.Light:
					self.module_count_light += 1
				else:
					self.module_count_full += 1

	def add_count_label(
		self,
		frame: ttk.LabelFrame,
		column: int,
		row: int,
		count: Literal["GNRL", "DX10", "Full", "Light", "Total"],
	) -> None:
		match count:
			case "GNRL":
				num = self.ba2_count_gnrl
				limit = MAX_ARCHIVES_GNRL
			case "DX10":
				num = self.ba2_count_dx10
				limit = MAX_ARCHIVES_DX10 or 9999
			case "Full":
				num = self.module_count_full
				limit = MAX_MODULES_FULL
			case "Light":
				num = self.module_count_light
				limit = MAX_MODULES_LIGHT
			case "Total":
				num = self.module_count_full + self.module_count_light
				limit = MAX_MODULES_FULL + MAX_MODULES_LIGHT

		color = COLOR_GOOD if num < limit else COLOR_BAD

		ttk.Label(frame, text=str(num).rjust(4), font=self.FONT, foreground=color).grid(
			column=column,
			row=row,
			sticky=E,
			padx=(5, 0),
		)
