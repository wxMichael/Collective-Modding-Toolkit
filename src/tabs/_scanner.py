import os
import queue
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from enums import ProblemType, SolutionType
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, ProblemInfo, SolutionInfo

IGNORE_FOLDERS = {
	"Bodyslide",
	"Complex Sorter",
	"Fo4edit",
	"Robco_Patcher",
	"Source",
}

DATA_WHITELIST = {
	"F4se": None,
	"Materials": {"bgem", "bgsm", "txt"},
	"Meshes": {
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
	"Music": {"wav", "xwm"},
	"Textures": {"dds"},
	"Sound": {"cdf", "fuz", "lip", "wav", "xwm"},
	"Vis": {"uvd"},
}

JUNK_FILES = {
	"thumbs.db",
	"desktop.ini",
	".ds_store",
}

# These should be in title case
JUNK_FOLDERS_DATA_ROOT = {
	"Fomod",
}

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

RECORD_TYPES = {
	# Sound
	"mp3": "Sound Descriptor (SNDR) or Music Track (MUST) ",
}


class ScannerTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Scanner")
		self.using_stage = bool(self.cmc.game.manager and self.cmc.game.manager.stage_path)
		self.tree_results: ttk.Treeview
		self.tree_results_data: dict[str, ProblemInfo] = {}

		self.side_pane: SidePane | None = None
		self.details_pane: ResultDetailsPane | None = None

		self.scan_results: list[ProblemInfo] = []
		self.scanned_mod_paths: set[Path] = set()
		self.queue_progress: queue.Queue[tuple[int, str, list[ProblemInfo] | None]] = queue.Queue()
		self.thread_load: threading.Thread | None = None
		self.dv_progress = DoubleVar()
		self.scan_path_count = 1
		self.progress_check_delay = 100
		self.sv_scanning_text = StringVar()
		self.label_scanning_text: ttk.Label | None = None

		self.bv_scan_formats = BooleanVar(value=True)
		self.bv_scan_previs = BooleanVar(value=True)
		self.bv_scan_junk = BooleanVar(value=True)

		self.bv_scan_dds = BooleanVar(value=False)
		self.bv_scan_ba2 = BooleanVar(value=False)
		self.bv_scan_conflicts = BooleanVar(value=False)
		self.bv_scan_suggest = BooleanVar(value=False)
		self.bv_scan_bad_overrides = BooleanVar(value=False)

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
			self.tree_results = ttk.Treeview(self, columns=("problem", "info"), selectmode=NONE)
			self.tree_results.heading("#0", text="Mod")
			self.tree_results.heading("problem", text="Problem")
			self.tree_results.heading("info", text="Info")
			self.tree_results.column("#0", stretch=True, anchor=W)
			self.tree_results.column("problem", stretch=True, anchor=W)
			self.tree_results.column("info", stretch=True, anchor=W)
		else:
			self.tree_results = ttk.Treeview(self, columns=("info",), selectmode=NONE)
			self.tree_results.heading("#0", text="Problem")
			self.tree_results.heading("info", text="Info")
			self.tree_results.column("#0", width=350, stretch=True, anchor=W)
			self.tree_results.column("info", minwidth=70, stretch=True, anchor=W)

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

		scan_paths: list[Path] = []
		if self.using_stage:
			manager = self.cmc.game.manager
			if not (
				manager and manager.stage_path and manager.profiles_path and manager.selected_profile and manager.overwrite_path
			):
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
			scan_paths.append(manager.overwrite_path)
			modlist_path = manager.profiles_path / manager.selected_profile / "modlist.txt"
			if not modlist_path.is_file():
				msg = f"File doesn't exist: {modlist_path}"
				raise FileNotFoundError(msg)
			with modlist_path.open(encoding="utf-8") as modlist_file:
				modlist = [
					mod_path
					for mod in modlist_file.read().splitlines()
					if mod.startswith(("+", "*")) and (mod_path := manager.stage_path / mod[1:]).is_dir()
				]
			scan_paths.extend(modlist)

		self.scan_path_count = len(scan_paths) + 1
		self.thread_load = threading.Thread(target=self.threaded_scan, args=(scan_paths, ScanSettings(self)))
		self.thread_load.start()
		self.cmc.root.after(self.progress_check_delay, self.check_scan_progress)

	def threaded_scan(self, scan_paths: list[Path], scan_settings: "ScanSettings") -> None:
		if self.cmc.game.data_path is None:
			return

		loaded_count = 0
		if scan_paths:
			for path in scan_paths:
				self.queue_progress.put((loaded_count, path.name, None))
				results = self.scan_data_path(scan_settings, path, self.scanned_mod_paths)
				loaded_count += 1
				self.queue_progress.put((loaded_count, path.name, results))

		self.queue_progress.put((loaded_count, "Unmanaged Files", None))
		results = self.scan_data_path(
			scan_settings,
			self.cmc.game.data_path,
			self.scanned_mod_paths,
			is_data_folder=True,
		)
		self.queue_progress.put((loaded_count, "Unmanaged Files", results))
		self.thread_load = None

	def check_scan_progress(self) -> None:
		while self.queue_progress.qsize():
			try:
				loaded_count, path_name, results = self.queue_progress.get()
			except queue.Empty:
				break
			else:
				self.sv_scanning_text.set(f"Scanning Data... {loaded_count}/{self.scan_path_count}: {path_name}")
				self.dv_progress.set((loaded_count / self.scan_path_count) * 100)
				if results:
					self.scan_results.extend(results)

		if self.thread_load is None:
			self.dv_progress.set(100)
			self.populate_results()
			return
		self.cmc.root.after(self.progress_check_delay, self.check_scan_progress)

	def populate_results(self) -> None:
		if self.side_pane is None:
			raise ValueError

		if self.label_scanning_text is not None:
			self.label_scanning_text.grid_forget()
			self.label_scanning_text.destroy()
			self.label_scanning_text = None
		self.sv_scanning_text.set("")

		for problem_info in sorted(self.scan_results, key=lambda p: p.mod):
			if self.using_stage:
				item_text = problem_info.mod
				item_values = [problem_info.path.name, problem_info.summary]
			else:
				item_text = problem_info.path.name
				item_values = [problem_info.summary]
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

	def scan_data_path(
		self,
		scan_settings: "ScanSettings",
		data_path: Path,
		scanned_mod_paths: set[Path],
		*,
		is_data_folder: bool = False,
	) -> list[ProblemInfo]:
		problems: list[ProblemInfo] = []
		manager = self.cmc.game.manager
		skip_file_suffixes = manager.skip_file_suffixes if manager else ()
		skip_directories = IGNORE_FOLDERS.union(manager.skip_directories) if manager else IGNORE_FOLDERS

		data_root_titlecase = "<Data>"
		mod_name = None if is_data_folder else data_path.name
		for root, folders, files in data_path.walk(top_down=True):
			if root.parent == data_path:
				data_root_titlecase = root.name.title()

				if scan_settings.junk and data_root_titlecase in JUNK_FOLDERS_DATA_ROOT:
					relative_path = root.relative_to(data_path)
					if not is_data_folder:
						scanned_mod_paths.add(relative_path)
					elif relative_path in scanned_mod_paths:
						folders.clear()
						continue
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							root,
							relative_path,
							mod_name,
							"Junk Folder",
							SolutionInfo(
								SolutionType.DeleteOrIgnoreFile,
								f"{root.name} is a junk folder not used by the game or mod managers.\nIt can either be deleted or ignored.",
							),
						),
					)
					folders.clear()
					continue

				if data_root_titlecase not in DATA_WHITELIST:
					folders.clear()
					continue

				if scan_settings.previs and data_root_titlecase == "Vis":
					relative_path = root.relative_to(data_path)
					if not is_data_folder:
						scanned_mod_paths.add(relative_path)
					elif relative_path in scanned_mod_paths:
						folders.clear()
						continue
					problems.append(
						ProblemInfo(
							ProblemType.LoosePrevis,
							root,
							relative_path,
							mod_name,
							"Loose previs folder found",
							SolutionInfo(
								None,
								"Loose previs files should be packed so they only win conflicts according to their plugin's load order, or deleted if unnecessary due to later previs plugins.",
							),
						),
					)
					folders.clear()
					continue

			for index, folder in reversed(list(enumerate(folders))):
				folder_lower = folder.lower()
				if folder_lower in skip_directories:
					del folders[index]
					continue

				if data_root_titlecase == "Meshes":
					full_path = root / folder
					relative_path = full_path.relative_to(data_path)
					if scan_settings.previs and folder_lower == "precombined":
						if not is_data_folder:
							scanned_mod_paths.add(relative_path)
						elif relative_path in scanned_mod_paths:
							del folders[index]
							continue
						problems.append(
							ProblemInfo(
								ProblemType.LoosePrevis,
								full_path,
								relative_path,
								mod_name,
								"Loose previs folder found",
								SolutionInfo(
									None,
									"Loose previs files should be packed so they only win conflicts according to their plugin's load order, or deleted if unnecessary due to later previs plugins.",
								),
							),
						)
						del folders[index]
						continue

					if folder_lower == "animtextdata":
						if not is_data_folder:
							scanned_mod_paths.add(relative_path)
						elif relative_path in scanned_mod_paths:
							del folders[index]
							continue
						problems.append(
							ProblemInfo(
								ProblemType.AnimTextDataFolder,
								full_path,
								relative_path,
								mod_name,
								"Loose AnimTextData folder found",
								SolutionInfo(
									SolutionType.ArchiveOrDelete,
									"The existence of unpacked AnimTextData may cause the game to crash.\nThe folder should be packed in a BA2 or deleted.",
								),
							),
						)
						del folders[index]
						continue

			whitelist = DATA_WHITELIST.get(data_root_titlecase)
			for file in files:
				file_lower = file.lower()
				if skip_file_suffixes and file_lower.endswith(skip_file_suffixes):
					continue

				full_path = root / file
				relative_path = full_path.relative_to(data_path)
				if not is_data_folder:
					scanned_mod_paths.add(relative_path)
				elif relative_path in scanned_mod_paths:
					continue

				if scan_settings.junk and file_lower in JUNK_FILES:
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							full_path,
							relative_path,
							mod_name,
							"Junk File",
							SolutionInfo(
								SolutionType.DeleteOrIgnoreFile,
								f"{full_path.name} is a junk file not used by the game or mod managers.\nIt can either be deleted or ignored.",
							),
						),
					)
					continue

				file_split = file_lower.rsplit(".", maxsplit=1)
				if len(file_split) == 1:
					continue

				file_ext = file_split[1]

				if scan_settings.formats:
					if (whitelist and file_ext not in whitelist) or (
						file_ext == "dll" and str(root.relative_to(data_path)).lower() != "f4se\\plugins"
					):
						solution = None
						if file_ext in PROPER_FORMATS:
							msg_delete_or_ignore = f"If {full_path.name} is not referenced by any plugin's {RECORD_TYPES.get(file_ext, '')}records, it can likely be deleted or ignored."
							proper_found = [
								p.name for e in PROPER_FORMATS[file_ext] if (p := full_path.with_suffix(f".{e}")).is_file()
							]
							if proper_found:
								msg_found = f"Expected format found ({', '.join(proper_found)})."
							else:
								msg_found = f"Expected format NOT found ({', '.join(PROPER_FORMATS[file_ext])}).\nThis file may need to be converted and relevant plugins updated for the new file name."
							solution = SolutionInfo(
								SolutionType.DeleteOrIgnoreFile,
								f"{msg_found}\n{msg_delete_or_ignore}",
							)
						else:
							solution = SolutionInfo(
								None,
								"Format not in whitelist. Unable to determine whether the game will use this file.\nIf this file type is expected here, please report it.",
							)

						problems.append(
							ProblemInfo(
								ProblemType.UnexpectedFormat,
								full_path,
								relative_path,
								mod_name,
								f"Unexpected format in {data_root_titlecase}",
								solution,
							),
						)
						continue

					if (
						file_ext == "ba2"
						and file_lower not in ARCHIVE_NAME_WHITELIST
						and full_path not in self.cmc.game.archives_enabled
					):
						ba2_name_split = file_split[0].rsplit(" - ", 1)
						no_suffix = len(ba2_name_split) == 1
						if no_suffix or ba2_name_split[1] not in self.cmc.game.ba2_suffixes:
							problems.append(
								ProblemInfo(
									ProblemType.InvalidArchiveName,
									full_path,
									relative_path,
									mod_name,
									"Invalid Archive Name",
									SolutionInfo(
										SolutionType.RenameArchive,
										(
											"This is not a valid archive name and won't be loaded by the game.\n"
											"Archives must be named the same as a plugin with an added suffix\n\n"
											f"Valid Suffixes: {', '.join(self.cmc.game.ba2_suffixes)}\n"
											f"Example: {ba2_name_split if no_suffix else ba2_name_split[0]} - Main.ba2"
										),
									),
								),
							)
							continue
		return problems


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

		check_scan_formats = ttk.Checkbutton(
			frame_scan_settings,
			text="Wrong File Formats",
			variable=self.scanner_tab.bv_scan_formats,
		)
		check_scan_previs = ttk.Checkbutton(
			frame_scan_settings,
			text="Loose Previs",
			variable=self.scanner_tab.bv_scan_previs,
		)
		check_scan_junk = ttk.Checkbutton(
			frame_scan_settings,
			text="Junk Files",
			variable=self.scanner_tab.bv_scan_junk,
		)

		frame_wip_settings = ttk.Labelframe(self, text="WIP Settings", labelanchor=N, padding=5)
		frame_wip_settings.pack(expand=True, fill=BOTH, padx=5, pady=5)

		check_scan_dds = ttk.Checkbutton(
			frame_wip_settings,
			text="DDS Checks",
			variable=self.scanner_tab.bv_scan_dds,
			state=DISABLED,
		)
		check_scan_ba2 = ttk.Checkbutton(
			frame_wip_settings,
			text="BA2 Contents",
			variable=self.scanner_tab.bv_scan_ba2,
			state=DISABLED,
		)
		check_scan_conflicts = ttk.Checkbutton(
			frame_wip_settings,
			text="Mod Conflicts",
			variable=self.scanner_tab.bv_scan_conflicts,
			state=DISABLED,
		)
		check_scan_suggest = ttk.Checkbutton(
			frame_wip_settings,
			text="Suggestions",
			variable=self.scanner_tab.bv_scan_suggest,
			state=DISABLED,
		)
		check_scan_bad_overrides = ttk.Checkbutton(
			frame_wip_settings,
			text="Problem Overrides",
			variable=self.scanner_tab.bv_scan_bad_overrides,
			state=DISABLED,
		)

		self.button_scan = ttk.Button(
			self,
			text="Scan Game",
			padding=5,
			command=scanner_tab.start_threaded_scan,
			style="Accent.TButton",
		)

		check_scan_formats.pack(anchor=W, side=TOP)
		check_scan_previs.pack(anchor=W, side=TOP)

		check_scan_dds.pack(anchor=W, side=TOP)
		check_scan_ba2.pack(anchor=W, side=TOP)
		check_scan_junk.pack(anchor=W, side=TOP)
		check_scan_conflicts.pack(anchor=W, side=TOP)
		check_scan_suggest.pack(anchor=W, side=TOP)
		check_scan_bad_overrides.pack(anchor=W, side=TOP)

		self.button_scan.pack(side=BOTTOM, padx=10, pady=10)

		ToolTip(check_scan_formats, TOOLTIP_SCAN_FORMATS)
		ToolTip(check_scan_dds, TOOLTIP_SCAN_DDS)
		ToolTip(check_scan_ba2, TOOLTIP_SCAN_BA2)
		ToolTip(check_scan_previs, TOOLTIP_SCAN_PREVIS)
		ToolTip(check_scan_junk, TOOLTIP_SCAN_JUNK)
		ToolTip(check_scan_conflicts, TOOLTIP_SCAN_CONFLICTS)
		ToolTip(check_scan_suggest, TOOLTIP_SCAN_SUGGEST)
		ToolTip(check_scan_bad_overrides, TOOLTIP_SCAN_BAD_OVERRIDES)

		self.grid_rowconfigure(self.grid_size()[1], weight=1)
		self.bind("<FocusIn>", self.on_focus)

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

		self.problem_info: ProblemInfo
		self.sv_mod_name = StringVar()
		self.sv_file_path = StringVar()
		self.sv_problem = StringVar()
		self.sv_solution = StringVar()

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
			text="File:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row, sticky=NE, padx=5, pady=5)
		ttk.Label(
			self,
			text="Problem:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row + 1, sticky=NE, padx=5, pady=5)
		ttk.Label(
			self,
			text="Solution:",
			font=FONT_SMALL,
			justify=RIGHT,
		).grid(column=0, row=start_row + 2, sticky=NE, padx=5, pady=5)

		label_file_path = ttk.Label(
			self,
			textvariable=self.sv_file_path,
			cursor="hand2",
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
		)
		label_file_path.grid(column=1, row=start_row, sticky=NW, padx=0, pady=5)

		label_file_path.bind("<Button-1>", lambda _: os.startfile(self.problem_info.path.parent))
		ToolTip(label_file_path, TOOLTIP_LOCATION)

		ttk.Label(
			self,
			textvariable=self.sv_problem,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
		).grid(column=1, row=start_row + 1, sticky=NW, padx=0, pady=5)
		ttk.Label(
			self,
			textvariable=self.sv_solution,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
			wraplength=WINDOW_WIDTH - 100,
		).grid(column=1, row=start_row + 2, sticky=NW, padx=0, pady=5)

		self.bind("<FocusIn>", self.on_focus)

	def set_info(self, problem_info: ProblemInfo, *, using_stage: bool) -> None:
		self.problem_info = problem_info
		if using_stage:
			self.sv_mod_name.set(problem_info.mod)
		self.sv_file_path.set(problem_info.relative_path.as_posix())
		self.sv_problem.set(problem_info.summary)
		self.sv_solution.set(problem_info.solution.info if problem_info.solution else "No solution found.")

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


class ScanSettings:
	def __init__(self, scanner_tab: ScannerTab) -> None:
		self.formats = scanner_tab.bv_scan_formats.get()
		self.previs = scanner_tab.bv_scan_previs.get()
		self.junk = scanner_tab.bv_scan_junk.get()

		self.dds = scanner_tab.bv_scan_dds.get()
		self.ba2 = scanner_tab.bv_scan_ba2.get()
		self.conflicts = scanner_tab.bv_scan_conflicts.get()
		self.suggest = scanner_tab.bv_scan_suggest.get()
		self.bad_overrides = scanner_tab.bv_scan_bad_overrides.get()
