import os
import queue
import threading
import webbrowser
from enum import Enum
from pathlib import Path
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from enums import ProblemType, SolutionType, Tab
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, ProblemInfo, SimpleProblemInfo
from utils import copy_text

IGNORE_FOLDERS = {
	"bodyslide",
	"complex sorter",
	"fo4edit",
	"robco_patcher",
	"source",
}
"""These are always lowercase."""

DATA_WHITELIST = {
	"f4se": None,
	"materials": {"bgem", "bgsm", "txt"},
	"meshes": {
		"bto",
		"btr",
		"hko",
		"hkx",
		"hkx_back",
		"hkx_backup",
		"lst",
		"max",
		"nif",
		"obj",
		"sclp",
		"ssf",
		"tri",
		"txt",
		"xml",
	},
	"music": {"wav", "xwm"},
	"textures": {"dds"},
	"scripts": {"pex", "psc", "txt", "zip"},
	"sound": {"cdf", "fuz", "lip", "wav", "xwm"},
	"vis": {"uvd"},
}
"""Keys and values are lowercase with no dot."""

JUNK_FILES = {
	"thumbs.db",
	"desktop.ini",
	".ds_store",
}

JUNK_FOLDERS_DATA_ROOT = {
	"fomod",
}
"""These are always lowercase."""

PROPER_FORMATS = {
	# Textures
	"bmp": ["dds"],
	"jpeg": ["dds"],
	"jpg": ["dds"],
	"png": ["dds"],
	"psd": ["dds"],
	"tga": ["dds"],
	# Sound
	"mp3": ["wav", "xwm"],
}
"Keys and values are always lowercase with no dot."

RECORD_TYPES = {
	# Sound
	"mp3": "Sound Descriptor (SNDR) or Music Track (MUST) ",
}
"Keys are always lowercase with no dot."


class ScanSetting(Enum):
	OverviewIssues = ("Overview Issues", TOOLTIP_SCAN_OVERVIEW)
	WrongFormat = ("Wrong File Formats", TOOLTIP_SCAN_FORMATS)
	LoosePrevis = ("Loose Previs", TOOLTIP_SCAN_PREVIS)
	JunkFiles = ("Junk Files", TOOLTIP_SCAN_JUNK)
	ProblemOverrides = ("Problem Overrides", TOOLTIP_SCAN_BAD_OVERRIDES)

	DDSChecks = ("DDS Checks", TOOLTIP_SCAN_DDS)
	BA2Content = ("BA2 Contents", TOOLTIP_SCAN_BA2)
	ModConflicts = ("Mod Conflicts", TOOLTIP_SCAN_CONFLICTS)
	Suggestions = ("Suggestions", TOOLTIP_SCAN_SUGGEST)


WIP_SETTINGS = (
	ScanSetting.DDSChecks,
	ScanSetting.BA2Content,
	ScanSetting.ModConflicts,
	ScanSetting.Suggestions,
)


class ModFiles:
	def __init__(self) -> None:
		self.folders: dict[Path, str] = {}
		self.files: dict[Path, str] = {}
		self.modules: dict[str, str] = {}
		self.archives: dict[str, str] = {}


class ScanSettings(dict[ScanSetting, bool]):
	def __init__(self, side_pane: "SidePane") -> None:
		super().__init__()

		self.overview_only = True
		self.mod_files: ModFiles | None = None

		for setting in ScanSetting:
			self[setting] = side_pane.bool_vars[setting].get()
			if setting == ScanSetting.OverviewIssues:
				self.overview_only = self.overview_only and self[ScanSetting.OverviewIssues]
			else:
				self.overview_only = self.overview_only and not self[setting]

		self.manager = side_pane.scanner_tab.cmc.game.manager
		self.using_stage = side_pane.scanner_tab.using_stage
		if self.manager:
			self.skip_file_suffixes = self.manager.skip_file_suffixes
			self.skip_directories = IGNORE_FOLDERS.union(self.manager.skip_directories)
		else:
			self.skip_file_suffixes = ()
			self.skip_directories = IGNORE_FOLDERS


class ScannerTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Scanner")
		self.using_stage = bool(self.cmc.game.manager and self.cmc.game.manager.stage_path)
		self.tree_results: ttk.Treeview
		self.tree_results_data: dict[str, ProblemInfo | SimpleProblemInfo] = {}

		self.side_pane: SidePane | None = None
		self.details_pane: ResultDetailsPane | None = None

		self.scan_results: list[ProblemInfo | SimpleProblemInfo] = []
		self.queue_progress: queue.Queue[str | tuple[str, ...] | list[ProblemInfo]] = queue.Queue()
		self.thread_scan: threading.Thread | None = None
		self.dv_progress = DoubleVar()
		self.progress_check_delay = 100
		self.sv_scanning_text = StringVar()
		self.label_scanning_text: ttk.Label | None = None
		self.scan_folders: tuple[str, ...] = ("",)

		self.func_id_focus: str
		self.func_id_config: str

	def on_focus(self, _event: "Event[Misc]") -> None:
		if self.side_pane:
			self.side_pane.tkraise()
		if self.details_pane:
			self.details_pane.tkraise()

	def on_configure(self, _event: "Event[Misc]") -> None:
		if self.side_pane:
			self.side_pane.update_geometry()
		if self.details_pane:
			self.details_pane.update_geometry()

	def _switch_to(self) -> None:
		self.func_id_focus = self.cmc.root.bind("<FocusIn>", self.on_focus, "+")
		self.func_id_config = self.cmc.root.bind("<Configure>", self.on_configure, "+")

		if self.side_pane is None:
			self.side_pane = SidePane(self)

	def switch_from(self) -> None:
		self.tree_results.selection_remove(self.tree_results.selection())
		self.cmc.root.unbind("<FocusIn>", self.func_id_focus)
		self.cmc.root.unbind("<Configure>", self.func_id_config)

		if self.side_pane is not None:
			self.side_pane.destroy()
			self.side_pane = None

		if self.details_pane is not None:
			self.details_pane.destroy()
			self.details_pane = None

	def _load(self) -> bool:
		if self.cmc.game.data_path is None:
			self.loading_error = "Data folder not found"
			return False
		return True

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		style = ttk.Style(self.cmc.root)
		style.configure("Treeview", font=FONT_SMALL)
		if self.using_stage:
			self.tree_results = ttk.Treeview(self, columns=("problem", "type"), selectmode=NONE)
			self.tree_results.heading("#0", text="Mod")
			self.tree_results.heading("problem", text="Problem")
			self.tree_results.heading("type", text="Type")
			self.tree_results.column("#0", stretch=True, anchor=W)
			self.tree_results.column("problem", stretch=True, anchor=W)
			self.tree_results.column("type", minwidth=50, stretch=False, anchor=W)
		else:
			self.tree_results = ttk.Treeview(self, columns=("type",), selectmode=NONE)
			self.tree_results.heading("#0", text="Problem")
			self.tree_results.heading("type", text="Type")
			self.tree_results.column("#0", minwidth=350, stretch=True, anchor=W)
			self.tree_results.column("type", minwidth=50, stretch=False, anchor=W)

		scroll_results_y = ttk.Scrollbar(
			self,
			orient=VERTICAL,
			command=self.tree_results.yview,  # pyright: ignore[reportUnknownArgumentType]
		)
		self.tree_results.grid(column=0, row=0, rowspan=2, sticky=NSEW)
		scroll_results_y.grid(column=1, row=0, rowspan=2, sticky=NS)
		self.tree_results.configure(yscrollcommand=scroll_results_y.set)

		self.progress_bar = ttk.Progressbar(self, variable=self.dv_progress, maximum=100)
		self.progress_bar.grid(column=0, row=3, columnspan=2, sticky=EW, ipady=1)

	def start_threaded_scan(self) -> None:
		if self.side_pane is None:
			raise ValueError

		self.side_pane.button_scan.configure(state=DISABLED, text="Scanning...")
		self.tree_results.unbind("<<TreeviewSelect>>")
		self.tree_results.configure(selectmode=NONE)
		self.tree_results.delete(*self.tree_results.get_children())
		self.tree_results_data.clear()
		self.scan_results.clear()
		if self.details_pane is not None:
			self.details_pane.destroy()
			self.details_pane = None

		if self.label_scanning_text is None:
			self.label_scanning_text = ttk.Label(
				self,
				textvariable=self.sv_scanning_text,
				font=FONT,
				foreground=COLOR_NEUTRAL_2,
				justify=LEFT,
			)
			self.label_scanning_text.grid(column=0, row=2, sticky=EW, padx=5, pady=5)
		self.sv_scanning_text.set("Refreshing Overview...")
		self.cmc.refresh_tab(Tab.Overview)

		scan_settings = ScanSettings(self.side_pane)
		if scan_settings[ScanSetting.OverviewIssues] and self.cmc.overview_problems:
			self.scan_results.extend(self.cmc.overview_problems)
		if scan_settings.overview_only:
			self.dv_progress.set(100)
			self.populate_results(scan_settings)
		else:
			self.dv_progress.set(1)
			self.sv_scanning_text.set("Building mod file index...")
			self.thread_scan = threading.Thread(target=self.scan_data_files, args=(scan_settings,))
			self.thread_scan.start()
			self.cmc.root.after(self.progress_check_delay, self.check_scan_progress, scan_settings)

	def check_scan_progress(self, scan_settings: ScanSettings) -> None:
		while self.queue_progress.qsize():
			try:
				update = self.queue_progress.get()
			except queue.Empty:
				break

			if isinstance(update, tuple):
				self.scan_folders = update
				current_folder = "Data"
			elif isinstance(update, str):
				current_folder = update
				try:
					current_index = self.scan_folders.index(current_folder)
				except ValueError:
					current_index = 1
				else:
					self.sv_scanning_text.set(f"Scanning... {current_index}/{max(1, len(self.scan_folders))}: {current_folder}")
					self.dv_progress.set((current_index / len(self.scan_folders)) * 100)
			elif update:
				# list
				self.scan_results.extend(update)

		if self.thread_scan is None:
			self.dv_progress.set(100)
			self.populate_results(scan_settings)
			return
		self.cmc.root.after(self.progress_check_delay, self.check_scan_progress, scan_settings)

	def populate_results(self, scan_settings: ScanSettings) -> None:
		if self.side_pane is None:
			raise ValueError

		if self.label_scanning_text is not None:
			self.label_scanning_text.grid_forget()
			self.label_scanning_text.destroy()
			self.label_scanning_text = None
		self.sv_scanning_text.set("")

		if scan_settings[ScanSetting.OverviewIssues] and self.cmc.overview_problems and scan_settings.mod_files:
			for problem in self.cmc.overview_problems:
				if problem.mod == "OVERVIEW":
					problem.mod = scan_settings.mod_files.files.get(Path(problem.relative_path), "")
		else:
			for problem in self.cmc.overview_problems:
				if problem.mod == "OVERVIEW":
					problem.mod = ""

		for problem_info in sorted(self.scan_results, key=lambda p: p.mod):
			if isinstance(problem_info, ProblemInfo):
				if self.using_stage:
					item_text = problem_info.mod
					item_values = [problem_info.path.name, problem_info.type]
				else:
					item_text = problem_info.path.name
					item_values = [problem_info.type]

			# SimpleProblemInfo
			elif self.using_stage:
				item_text = problem_info.mod
				item_values = [problem_info.path, problem_info.type]
			else:
				item_text = problem_info.path
				item_values = [problem_info.type]

			item_id = self.tree_results.insert("", END, text=item_text, values=item_values)
			self.tree_results_data[item_id] = problem_info

		self.side_pane.button_scan.configure(state=NORMAL, text="Scan Game")
		self.tree_results.bind("<<TreeviewSelect>>", self.on_row_select)
		self.tree_results.configure(selectmode=BROWSE)

	def on_row_select(self, _event: "Event[ttk.Treeview]") -> None:
		if not _event.widget.selection():
			return

		if self.details_pane is None:
			self.details_pane = ResultDetailsPane(self)
		selection = self.tree_results.selection()[0]
		self.details_pane.set_info(self.tree_results_data[selection], using_stage=self.using_stage)

	def get_stage_paths(self, scan_settings: ScanSettings) -> list[Path]:
		manager = scan_settings.manager
		if not (manager and manager.stage_path and manager.profiles_path and manager.selected_profile and manager.overwrite_path):
			msg = (
				(
					f"Missing MO2 settings\n"
					f"Manager: {manager}\n"
					f"mods: {manager.stage_path}\n"
					f"profiles: {manager.profiles_path}\n"
					f"profile: {manager.selected_profile}\n"
					f"overwrite: {manager.overwrite_path}"
				)
				if manager
				else "Manager: None"
			)
			raise ValueError(msg)

		modlist_path = manager.profiles_path / manager.selected_profile / "modlist.txt"
		if not modlist_path.is_file():
			msg = f"File doesn't exist: {modlist_path}"
			raise FileNotFoundError(msg)

		stage_paths = [
			mod_path
			for mod in reversed(modlist_path.read_text("utf-8").splitlines())
			if mod[:1] == "+" and (mod_path := manager.stage_path / mod[1:]).is_dir()
		]
		if manager.overwrite_path.is_dir():
			stage_paths.append(manager.overwrite_path)

		return stage_paths

	def build_mod_file_list(self, scan_settings: ScanSettings) -> ModFiles:
		mod_files = ModFiles()
		if not scan_settings.using_stage or not scan_settings.manager:
			return mod_files

		for mod_path in self.get_stage_paths(scan_settings):
			mod_name = mod_path.name
			for root, folders, files in mod_path.walk(top_down=True):
				root_is_mod_path = root is mod_path
				if folders:
					last_index = len(folders) - 1
					for i, folder in enumerate(reversed(folders)):
						folder_lower = folder.lower()
						if folder_lower in scan_settings.skip_directories:
							del folders[last_index - i]

				if root_is_mod_path:
					root_relative = Path()
				else:
					root_relative = root.relative_to(mod_path)
					mod_files.folders[root_relative] = mod_name

				for file in files:
					file_lower = file.lower()
					if file_lower.endswith(scan_settings.skip_file_suffixes):
						continue

					mod_files.files[root_relative / file] = mod_name

					if root_is_mod_path:
						if file_lower.endswith((".esp", ".esl", ".esm")):
							mod_files.modules[file] = mod_name
						elif file_lower.endswith(".ba2"):
							mod_files.archives[file] = mod_name
					else:
						pass

		scan_settings.mod_files = mod_files
		return mod_files

	def scan_data_files(self, scan_settings: ScanSettings) -> None:
		problems: list[ProblemInfo] = []

		data_path = self.cmc.game.data_path
		if data_path is None:
			self.thread_scan = None
			return

		stage_path = data_path
		if scan_settings.manager and scan_settings.manager.stage_path:
			stage_path = scan_settings.manager.stage_path

		mod_files = self.build_mod_file_list(scan_settings)

		data_root_lower = "Data"
		for current_path, folders, files in data_path.walk(top_down=True):
			current_path_relative = current_path.relative_to(data_path)
			mod_name = mod_files.folders.get(current_path_relative)
			if current_path is data_path:
				self.queue_progress.put(tuple(folders))

			if current_path.parent == data_path:
				self.queue_progress.put(current_path.name)
				data_root_lower = current_path.name.lower()

				if scan_settings[ScanSetting.JunkFiles] and data_root_lower == "fomod":
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							stage_path / mod_name / current_path_relative if mod_name else current_path,
							current_path_relative,
							mod_name,
							"This is a junk folder not used by the game or mod managers.",
							SolutionType.DeleteOrIgnoreFolder,
						),
					)
					folders.clear()
					continue

				if data_root_lower not in DATA_WHITELIST:
					folders.clear()
					continue

				if scan_settings[ScanSetting.LoosePrevis] and data_root_lower == "vis":
					problems.append(
						ProblemInfo(
							ProblemType.LoosePrevis,
							stage_path / mod_name / current_path_relative if mod_name else current_path,
							current_path_relative,
							mod_name,
							"Loose previs files should be archived so they only win conflicts according to their plugin's load order.\nLoose previs files are also not supported by PJM's Previs Scripts.",
							SolutionType.ArchiveOrDeleteFolder,
						),
					)
					folders.clear()
					continue

			if folders:
				last_index = len(folders) - 1
				for i, folder in enumerate(reversed(folders)):
					folder_lower = folder.lower()
					if folder_lower in scan_settings.skip_directories:
						del folders[last_index - i]
						continue

					folder_path_full = current_path / folder
					folder_path_relative = current_path_relative / folder
					mod_name_folder = mod_files.folders.get(folder_path_relative)

					if data_root_lower == "meshes":
						if scan_settings[ScanSetting.LoosePrevis] and folder_lower == "precombined":
							problems.append(
								ProblemInfo(
									ProblemType.LoosePrevis,
									stage_path / mod_name_folder / folder_path_relative if mod_name_folder else folder_path_full,
									folder_path_relative,
									mod_name_folder,
									"Loose previs files should be archived so they only win conflicts according to their plugin's load order.\nLoose previs files are also not supported by PJM's Previs Scripts.",
									SolutionType.ArchiveOrDeleteFolder,
								),
							)
							del folders[last_index - i]
							continue

						if scan_settings[ScanSetting.ProblemOverrides] and folder_lower == "animtextdata":
							problems.append(
								ProblemInfo(
									ProblemType.AnimTextDataFolder,
									stage_path / mod_name_folder / folder_path_relative if mod_name_folder else folder_path_full,
									folder_path_relative,
									mod_name_folder,
									"The existence of unpacked AnimTextData may cause the game to crash.",
									SolutionType.ArchiveOrDeleteFolder,
								),
							)
							del folders[last_index - i]
							continue

			whitelist = DATA_WHITELIST.get(data_root_lower)
			for file in files:
				file_lower = file.lower()
				if scan_settings.skip_file_suffixes and file_lower.endswith(scan_settings.skip_file_suffixes):
					continue

				file_path_full = current_path / file
				file_path_relative = current_path_relative / file
				mod_name_file = mod_files.files.get(file_path_relative)

				if scan_settings[ScanSetting.JunkFiles] and file_lower in JUNK_FILES:
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							stage_path / mod_name_file / file_path_relative if mod_name_file else file_path_full,
							file_path_relative,
							mod_name_file,
							"This is a junk file not used by the game or mod managers.",
							SolutionType.DeleteOrIgnoreFile,
						),
					)
					continue

				if data_root_lower == "scripts":  # noqa: SIM102
					if scan_settings[ScanSetting.ProblemOverrides] and file_lower in F4SE_CRC:
						problems.append(
							ProblemInfo(
								ProblemType.F4SEOverride,
								stage_path / mod_name_file / file_path_relative if mod_name_file else file_path_full,
								file_path_relative,
								mod_name_file,
								"This is an override of an F4SE script. This could break F4SE if they aren't the\nsame version.",
								SolutionType.DeleteFile,
							),
						)
						continue

				file_split = file_lower.rsplit(".", maxsplit=1)
				if len(file_split) == 1:
					continue

				file_ext = file_split[1]

				if scan_settings[ScanSetting.WrongFormat]:
					if (whitelist and file_ext not in whitelist) or (
						file_ext == "dll" and str(current_path_relative).lower() != "f4se\\plugins"
					):
						solution = None
						if file_ext in PROPER_FORMATS:
							proper_found = [
								p.name for e in PROPER_FORMATS[file_ext] if (p := file_path_full.with_suffix(f".{e}")).is_file()
							]
							if proper_found:
								summary = f"Format not in whitelist for {data_root_lower}.\nA file with the expected format was found ({', '.join(proper_found)})."
								solution = SolutionType.DeleteOrIgnoreFile
							else:
								summary = f"Format not in whitelist for {data_root_lower}.\nA file with the expected format was NOT found ({', '.join(PROPER_FORMATS[file_ext])})."
								solution = SolutionType.ConvertDeleteOrIgnoreFile
						else:
							summary = f"Format not in whitelist for {data_root_lower}.\nUnable to determine whether the game will use this file."
							solution = SolutionType.UnknownFormat

						problems.append(
							ProblemInfo(
								ProblemType.UnexpectedFormat,
								stage_path / mod_name_file / file_path_relative if mod_name_file else file_path_full,
								file_path_relative,
								mod_name_file,
								summary,
								solution,
							),
						)
						continue

					if (
						file_ext == "ba2"
						and file_lower not in ARCHIVE_NAME_WHITELIST
						and file_path_full not in self.cmc.game.archives_enabled
					):
						ba2_name_split = file_split[0].rsplit(" - ", 1)
						no_suffix = len(ba2_name_split) == 1
						if no_suffix or ba2_name_split[1] not in self.cmc.game.ba2_suffixes:
							problems.append(
								ProblemInfo(
									ProblemType.InvalidArchiveName,
									stage_path / mod_name_file / file_path_relative if mod_name_file else file_path_full,
									file_path_relative,
									mod_name_file,
									"This is not a valid archive name and won't be loaded by the game.",
									SolutionType.RenameArchive,
									[
										f"\nValid Suffixes: {', '.join(self.cmc.game.ba2_suffixes)}",
										f"Example: {ba2_name_split[0]} - Main.ba2",
									],
								),
							)
							continue

		self.thread_scan = None
		self.queue_progress.put(problems)


class SidePane(Toplevel):
	def __init__(
		self,
		scanner_tab: ScannerTab,
	) -> None:
		super().__init__(scanner_tab.cmc.root, bd=2, relief=GROOVE)
		self.scanner_tab = scanner_tab

		self.wm_overrideredirect(boolean=True)
		self.wm_resizable(width=False, height=False)
		self.update_geometry()

		frame_scan_settings = ttk.Labelframe(self, text="Scan Settings", labelanchor=N, padding=5)
		frame_scan_settings.pack(expand=True, fill=BOTH, padx=5, pady=5)

		frame_wip_settings = ttk.Labelframe(self, text="WIP Settings", labelanchor=N, padding=5)
		if WIP_SETTINGS:
			frame_wip_settings.pack(expand=True, fill=BOTH, padx=5, pady=5)

		self.bool_vars: dict[ScanSetting, BooleanVar] = {}
		for setting in ScanSetting:
			wip = bool(WIP_SETTINGS and setting in WIP_SETTINGS)
			self.bool_vars[setting] = BooleanVar(value=not wip)
			setting_check = ttk.Checkbutton(
				frame_wip_settings if wip else frame_scan_settings,
				text=setting.value[0],
				variable=self.bool_vars[setting],
				state=DISABLED if wip else NORMAL,
				command=self.on_checkbox_toggle,
			)
			setting_check.pack(anchor=W, side=TOP)
			ToolTip(setting_check, setting.value[1])

		self.button_scan = ttk.Button(
			self,
			text="Scan Game",
			padding=5,
			command=scanner_tab.start_threaded_scan,
			style="Accent.TButton",
		)
		self.button_scan.pack(side=BOTTOM, padx=10, pady=10)

		self.grid_rowconfigure(self.grid_size()[1], weight=1)
		self.bind("<FocusIn>", self.on_focus)

	def on_checkbox_toggle(self) -> None:
		self.button_scan.configure(state=NORMAL if any(bv.get() for bv in self.bool_vars.values()) else DISABLED)
		self.scanner_tab.cmc.root.update()

	def on_focus(self, _event: "Event[Misc]") -> None:
		self.scanner_tab.cmc.root.tkraise()
		if self.scanner_tab.details_pane:
			self.scanner_tab.details_pane.tkraise()

	def update_geometry(self, _event: "Event[Misc] | None" = None) -> None:
		root_x = self.scanner_tab.cmc.root.winfo_rootx()
		root_y = self.scanner_tab.cmc.root.winfo_rooty()
		root_width = self.scanner_tab.cmc.root.winfo_width()
		root_height = self.scanner_tab.cmc.root.winfo_height()
		width = 200
		offset_y = 40
		self.wm_geometry(f"{width}x{root_height - offset_y - 5}+{root_x + root_width}+{root_y + offset_y}")
		self.update_idletasks()


class ResultDetailsPane(Toplevel):
	def __init__(
		self,
		scanner_tab: ScannerTab,
	) -> None:
		super().__init__(scanner_tab.cmc.root, bd=2, relief=GROOVE)
		self.scanner_tab = scanner_tab

		self.wm_overrideredirect(boolean=True)
		self.wm_resizable(width=False, height=False)
		self.update_geometry()
		self.wm_protocol("WM_DELETE_WINDOW", self.close)

		self.problem_info: ProblemInfo | SimpleProblemInfo
		self.sv_mod_name = StringVar()
		self.sv_file_path = StringVar()
		self.sv_problem = StringVar()
		self.sv_solution = StringVar()

		self.label_file_path: ttk.Label
		self.label_solution: ttk.Label
		self.tooltip_file_path: ToolTip | None = None
		self.tooltip_solution: ToolTip | None = None

		self.grid_columnconfigure(1, weight=1)

		start_row = 0
		if scanner_tab.cmc.game.manager and scanner_tab.cmc.game.manager.stage_path:
			start_row = 1
			ttk.Label(
				self,
				text="Mod:",
				font=FONT,
				justify=RIGHT,
			).grid(column=0, row=0, sticky=NE, padx=5, pady=5)
			ttk.Label(
				self,
				textvariable=self.sv_mod_name,
				font=FONT,
				justify=LEFT,
				foreground=COLOR_NEUTRAL_2,
			).grid(column=1, row=0, sticky=NW, padx=0, pady=5)

		ttk.Label(
			self,
			text="Path:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row, sticky=NE, padx=5, pady=5)
		ttk.Label(
			self,
			text="Summary:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row + 1, sticky=NE, padx=5, pady=5)
		ttk.Label(
			self,
			text="Solution:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row + 2, sticky=NE, padx=5, pady=5)

		self.label_file_path = ttk.Label(
			self,
			textvariable=self.sv_file_path,
			cursor="hand2",
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
		)
		self.label_file_path.grid(column=1, row=start_row, sticky=NW, padx=0, pady=5)

		ttk.Label(
			self,
			textvariable=self.sv_problem,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
		).grid(column=1, row=start_row + 1, sticky=NW, padx=0, pady=5)
		self.label_solution = ttk.Label(
			self,
			textvariable=self.sv_solution,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
			wraplength=WINDOW_WIDTH - 100,
		)
		self.label_solution.grid(column=1, row=start_row + 2, sticky=NW, padx=0, pady=5)

		self.bind("<FocusIn>", self.on_focus)

	def set_info(self, problem_info: ProblemInfo | SimpleProblemInfo, *, using_stage: bool) -> None:
		self.problem_info = problem_info
		if using_stage:
			self.sv_mod_name.set(problem_info.mod)

		self.sv_file_path.set(str(problem_info.relative_path))

		target = self.problem_info.path
		if isinstance(target, Path) and (target.exists() or target.parent.exists()):
			if not target.is_dir():
				target = target.parent
			self.label_file_path.bind("<Button-1>", lambda _: os.startfile(target))
			if self.tooltip_file_path:
				self.tooltip_file_path.msg = TOOLTIP_LOCATION
			else:
				self.tooltip_file_path = ToolTip(self.label_file_path, TOOLTIP_LOCATION)
			self.label_file_path.configure(cursor="hand2")
		else:
			self.label_file_path.unbind("<Button-1>")
			if self.tooltip_file_path:
				self.tooltip_file_path.destroy()
				self.tooltip_file_path = None
			self.label_file_path.configure(cursor="X_cursor")

		self.sv_problem.set(problem_info.summary)

		if problem_info.extra_data:
			self.sv_solution.set((problem_info.solution or "----") + f"\n{'\n'.join(problem_info.extra_data)}")
			url = problem_info.extra_data[0]

			if url.startswith("http"):
				self.label_solution.bind("<Button-1>", lambda _: webbrowser.open(url))
				self.label_solution.bind("<Button-3>", lambda _: copy_text(self.scanner_tab, url))

				tooltip_text = "Left-Click: Open URL\nRight-Click: Copy URL"
				if self.tooltip_solution:
					self.tooltip_solution.msg = tooltip_text
				else:
					self.tooltip_solution = ToolTip(self.label_solution, tooltip_text)
			else:
				self.label_solution.unbind("<Button-1>")
				self.label_solution.unbind("<Button-3>")
				if self.tooltip_solution:
					self.tooltip_solution.destroy()
					self.tooltip_solution = None
		else:
			self.sv_solution.set(problem_info.solution or "----")
			self.label_solution.unbind("<Button-1>")
			self.label_solution.unbind("<Button-3>")
			if self.tooltip_solution:
				self.tooltip_solution.destroy()
				self.tooltip_solution = None

	def on_focus(self, _event: "Event[Misc]") -> None:
		self.scanner_tab.cmc.root.tkraise()
		if self.scanner_tab.side_pane:
			self.scanner_tab.side_pane.tkraise()

	def update_geometry(self, _event: "Event[Misc] | None" = None) -> None:
		root_x = self.scanner_tab.cmc.root.winfo_rootx()
		root_y = self.scanner_tab.cmc.root.winfo_rooty()
		root_width = self.scanner_tab.cmc.root.winfo_width()
		root_height = self.scanner_tab.cmc.root.winfo_height()
		height = 200
		offset_x = 0
		self.wm_geometry(f"{root_width}x{height}+{root_x + offset_x}+{root_y + root_height}")

	def close(self) -> None:
		self.scanner_tab.details_pane = None
		self.destroy()
