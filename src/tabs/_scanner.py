import os
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from autofixes import AUTO_FIXES, do_autofix
from enums import ProblemType, SolutionType, Tab, Tool
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, ProblemInfo, SimpleProblemInfo
from modal_window import TreeWindow
from scan_settings import (
	DATA_WHITELIST,
	JUNK_FILE_SUFFIXES,
	JUNK_FILES,
	PROPER_FORMATS,
	ModFiles,
	ScanSetting,
	ScanSettings,
)
from utils import (
	copy_text,
	copy_text_button,
	exists,
	is_dir,
	is_file,
	read_text_encoded,
	rglob,
)


class ScannerTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Scanner")
		self.using_stage: bool = bool(self.cmc.game.manager and self.cmc.game.manager.stage_path)
		self.tree_results: ttk.Treeview
		self.tree_results_data: dict[str, ProblemInfo | SimpleProblemInfo] = {}

		self.side_pane: SidePane | None = None
		self.details_pane: ResultDetailsPane | None = None

		self.scan_results: list[ProblemInfo | SimpleProblemInfo] = []
		self.queue_progress: queue.Queue[str | tuple[str, ...] | list[ProblemInfo | SimpleProblemInfo]] = queue.Queue()
		self.thread_scan: threading.Thread | None = None
		self.dv_progress = DoubleVar()
		self.progress_check_delay = 100
		self.sv_scanning_text = StringVar()
		self.label_scanning_text: ttk.Label | None = None
		self.scan_folders: tuple[str, ...] = ("",)
		self.sv_results_info = StringVar()

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

	def set_expanded(self, *, expanded: bool) -> None:
		for ch in self.tree_results.get_children():
			self.tree_results.item(ch, open=expanded)

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)

		frame_tree_controls = ttk.Frame(self, padding=0)
		frame_tree_controls.grid(column=0, row=0, columnspan=2, sticky=EW, padx=5, pady=5)

		button_collapse = ttk.Button(
			frame_tree_controls,
			text="Collapse All",
			padding=0,
			state=NORMAL,
			command=lambda: self.set_expanded(expanded=False),
		)
		button_expand = ttk.Button(
			frame_tree_controls,
			text="Expand All",
			padding=0,
			state=NORMAL,
			command=lambda: self.set_expanded(expanded=True),
		)
		button_collapse.pack(side=LEFT, anchor=W, padx=(0, 5))
		button_expand.pack(side=LEFT, anchor=W, padx=(0, 5))

		label_results_info = ttk.Label(
			frame_tree_controls,
			textvariable=self.sv_results_info,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=RIGHT,
		)
		label_results_info.pack(side=RIGHT, anchor=E, padx=(0, 5))

		style = ttk.Style(self.cmc.root)
		style.configure("Treeview", font=FONT_SMALL)
		if self.using_stage:
			self.tree_results = ttk.Treeview(self, columns=("mod",), selectmode=NONE, show="tree")
			self.tree_results.heading("#0", text="Problem")
			self.tree_results.column("#0", minwidth=400, stretch=True, anchor=W)
			self.tree_results.column("mod", stretch=True, anchor=E)
		else:
			self.tree_results = ttk.Treeview(self, selectmode=NONE, show="tree")
			self.tree_results.column("#0", minwidth=400, stretch=True, anchor=W)

		scroll_results_y = ttk.Scrollbar(
			self,
			orient=VERTICAL,
			command=self.tree_results.yview,  # pyright: ignore[reportUnknownArgumentType]
		)
		self.tree_results.grid(column=0, row=1, rowspan=2, sticky=NSEW)
		scroll_results_y.grid(column=1, row=1, rowspan=2, sticky=NS)
		self.tree_results.configure(yscrollcommand=scroll_results_y.set)

		self.progress_bar = ttk.Progressbar(self, variable=self.dv_progress, maximum=100)
		self.progress_bar.grid(column=0, row=4, columnspan=2, sticky=EW, ipady=1)

	def start_threaded_scan(self) -> None:
		if self.side_pane is None:
			raise ValueError

		self.side_pane.button_scan.configure(state=DISABLED, text="Scanning...")
		self.tree_results.unbind("<<TreeviewSelect>>")
		self.tree_results.configure(selectmode=NONE)
		self.tree_results.delete(*self.tree_results.get_children())
		self.tree_results_data.clear()
		self.scan_results.clear()
		self.sv_results_info.set("")
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
			self.label_scanning_text.grid(column=0, row=3, sticky=EW, padx=5, pady=5)
		self.sv_scanning_text.set("Refreshing Overview...")
		self.cmc.refresh_tab(Tab.Overview)

		scan_settings = ScanSettings(self.side_pane)
		if scan_settings[ScanSetting.OverviewIssues] and self.cmc.overview_problems:
			self.scan_results.extend(self.cmc.overview_problems)
		self.dv_progress.set(1)
		if not scan_settings.skip_data_scan:
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
		self.sv_results_info.set(f"{len(self.scan_results)} Results ~ Select an item for details")

		if scan_settings[ScanSetting.OverviewIssues] and self.cmc.overview_problems and scan_settings.mod_files:
			for problem in self.cmc.overview_problems:
				if problem.mod == "OVERVIEW":
					problem.mod = scan_settings.mod_files.files.get(Path(problem.relative_path), [""])[0]
		else:
			for problem in self.cmc.overview_problems:
				if problem.mod == "OVERVIEW":
					problem.mod = ""

		groups = {p.type for p in self.scan_results}

		for group in groups:
			group_id = self.tree_results.insert("", END, text=group, open=True)
			for problem_info in sorted(self.scan_results, key=lambda p: p.type + p.mod):
				if problem_info.type != group:
					continue
				if isinstance(problem_info, ProblemInfo):
					if self.using_stage:
						item_text = problem_info.path.name
						item_values = [problem_info.mod]
					else:
						item_text = problem_info.path.name
						item_values = []

				# SimpleProblemInfo
				elif self.using_stage:
					item_text = problem_info.path
					item_values = [problem_info.mod]
				else:
					item_text = problem_info.path
					item_values = []

				item_id = self.tree_results.insert(group_id, END, text=item_text, values=item_values)
				self.tree_results_data[item_id] = problem_info

		self.side_pane.button_scan.configure(state=NORMAL, text="Scan Game")
		self.tree_results.bind("<<TreeviewSelect>>", self.on_row_select)
		self.tree_results.configure(selectmode=BROWSE)

	def on_row_select(self, _event: "Event[ttk.Treeview]") -> bool:
		if not _event.widget.selection():
			return False

		selection = self.tree_results.selection()[0]
		if selection in self.tree_results_data:
			if self.details_pane is None:
				self.details_pane = ResultDetailsPane(self)
			self.details_pane.set_info(selection, using_stage=self.using_stage)
			return True
		return False

	def get_stage_paths(self, scan_settings: ScanSettings) -> list[Path]:  # noqa: PLR6301
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
		if not is_file(modlist_path):
			msg = f"File doesn't exist: {modlist_path}"
			raise FileNotFoundError(msg)

		stage_paths = [
			mod_path
			for mod in reversed(modlist_path.read_text("utf-8").splitlines())
			if mod[:1] == "+" and is_dir(mod_path := manager.stage_path / mod[1:])
		]
		if is_dir(manager.overwrite_path):
			stage_paths.append(manager.overwrite_path)

		return stage_paths

	def build_mod_file_list(self, scan_settings: ScanSettings) -> ModFiles:
		mod_files = ModFiles()
		if not scan_settings.using_stage or not scan_settings.manager or scan_settings.manager.name != "Mod Organizer":
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
					mod_files.folders[root_relative] = (mod_name, root)

				for file in files:
					file_lower = file.lower()
					if file_lower.endswith(scan_settings.skip_file_suffixes):
						continue

					full_path = root / file

					mod_files.files[root_relative / file] = (mod_name, full_path)

					if root_is_mod_path:
						if file_lower.endswith((".esp", ".esl", ".esm")):
							mod_files.modules[file] = (mod_name, full_path)
						elif file_lower.endswith(".ba2"):
							mod_files.archives[file] = (mod_name, full_path)
					else:
						pass

		scan_settings.mod_files = mod_files
		return mod_files

	def scan_data_files(self, scan_settings: ScanSettings) -> None:
		problems: list[ProblemInfo | SimpleProblemInfo] = []

		data_path = self.cmc.game.data_path
		if data_path is None:
			self.thread_scan = None
			return

		if scan_settings[ScanSetting.Errors]:  # noqa: SIM102
			if scan_settings.manager and Tool.ComplexSorter in scan_settings.manager.executables:
				for tool_path in scan_settings.manager.executables[Tool.ComplexSorter]:
					for ini_path in rglob(tool_path.parent, "ini"):
						ini_text, _ = read_text_encoded(ini_path)
						ini_lines = ini_text.splitlines(keepends=True)
						error_found = False
						for ini_line in ini_lines:
							if not ini_line.startswith(";") and (
								'FindNode OBTS(FindNode "Addon Index"' in ini_line
								or "FindNode OBTS(FindNode 'Addon Index'" in ini_line
							):
								error_found = True
								break

						if error_found:
							problems.append(
								ProblemInfo(
									ProblemType.ComplexSorter,
									ini_path,
									ini_path.relative_to(tool_path.parent),
									tool_path.parent.name,
									"INI uses an outdated field name. xEdit 4.1.5g changed the name of 'Addon Index' to 'Parent Combination Index'. Using outdated INIs with xEdit 4.1.5g+ results in broken output that may crash the game.",
									SolutionType.ComplexSorterFix,
								),
							)
							continue

		if scan_settings[ScanSetting.RaceSubgraphs]:
			self.queue_progress.put("Race Subgraph Records")
			sadd_modules: list[tuple[int, Path]] = []
			sadd_total = 0
			sadd_bytes = b"\x00\x53\x41\x44\x44"
			for module_path in self.cmc.game.modules_enabled:
				try:
					module_bytes = module_path.read_bytes()
				except OSError:
					continue
				sadd_count = module_bytes.count(sadd_bytes)
				if sadd_count:
					sadd_modules.append((sadd_count, module_path))
					sadd_total += sadd_count

			if sadd_total > RACE_SUBGRAPH_THRESHOLD:
				problems.append(
					SimpleProblemInfo(
						f"{sadd_total} SADD Records from {len(sadd_modules)} modules",
						"Race Subgraph Record Count",
						INFO_SCAN_RACE_SUBGRAPHS,
						"IF you are experiencing stutter when moving between cells, removing some of these mods could alleviate performance issues.\nMerging them may also reduce stutter.",
						file_list=sadd_modules,
					),
				)

		if scan_settings.skip_data_scan:
			self.thread_scan = None
			self.queue_progress.put(problems)
			return

		mod_files = self.build_mod_file_list(scan_settings)

		data_root_lower = "Data"
		for current_path, folders, files in data_path.walk(top_down=True):
			current_path_relative = current_path.relative_to(data_path)
			mod_name, mod_path = mod_files.folders.get(current_path_relative) or ("", current_path)
			if current_path is data_path:
				self.queue_progress.put(tuple(folders))

			if current_path.parent == data_path:
				self.queue_progress.put(current_path.name)
				data_root_lower = current_path.name.lower()

				if scan_settings[ScanSetting.JunkFiles] and data_root_lower == "fomod":
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							mod_path,
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
							mod_path,
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
					mod_name_folder, mod_path_folder = mod_files.folders.get(folder_path_relative) or ("", folder_path_full)

					if data_root_lower == "meshes":
						if scan_settings[ScanSetting.LoosePrevis] and folder_lower == "precombined":
							problems.append(
								ProblemInfo(
									ProblemType.LoosePrevis,
									mod_path_folder,
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
									mod_path_folder,
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
				mod_name_file, mod_path_file = mod_files.files.get(file_path_relative) or ("", file_path_full)

				if scan_settings[ScanSetting.JunkFiles] and (file_lower in JUNK_FILES or file_lower.endswith(JUNK_FILE_SUFFIXES)):
					problems.append(
						ProblemInfo(
							ProblemType.JunkFile,
							mod_path_file,
							file_path_relative,
							mod_name_file,
							"This is a junk file not used by the game or mod managers.",
							SolutionType.DeleteOrIgnoreFile,
						),
					)
					continue

				if data_root_lower == "scripts" and current_path.parent == data_path:  # noqa: SIM102
					if mod_name_file and scan_settings[ScanSetting.ProblemOverrides] and file_lower in F4SE_CRC:
						problems.append(
							ProblemInfo(
								ProblemType.F4SEOverride,
								mod_path_file,
								file_path_relative,
								mod_name_file,
								"This is an override of an F4SE script. This could break F4SE if they aren't the same version or this mod isn't intended to override F4SE files.",
								"Check if this mod is supposed to override F4SE Scripts.\nIf this is a script extender/library or requires one, this is likely intentional but it must support your game version explicitly.\nOtherwise, this mod or file may need to be deleted.",
							),
						)
						continue

				file_split = file_lower.rsplit(".", maxsplit=1)
				if len(file_split) == 1:
					continue

				file_ext = file_split[1]

				if scan_settings[ScanSetting.Errors]:  # noqa: SIM102
					if data_root_lower == "complex sorter" and file_ext == "ini":
						ini_text, _ = read_text_encoded(file_path_full)
						ini_lines = ini_text.splitlines(keepends=True)
						error_found = False
						for ini_line in ini_lines:
							if not ini_line.startswith(";") and (
								'FindNode OBTS(FindNode "Addon Index"' in ini_line
								or "FindNode OBTS(FindNode 'Addon Index'" in ini_line
							):
								error_found = True
								break
						if error_found:
							problems.append(
								ProblemInfo(
									ProblemType.ComplexSorter,
									mod_path_file,
									file_path_relative,
									mod_name_file,
									"INI uses an outdated field name. xEdit 4.1.5g changed the name of 'Addon Index' to 'Parent Combination Index'. Using outdated INIs with xEdit 4.1.5g+ results in broken output that may crash the game.",
									SolutionType.ComplexSorterFix,
								),
							)
							continue

				if scan_settings[ScanSetting.WrongFormat]:
					if (whitelist and file_ext not in whitelist) or (
						file_ext == "dll" and str(current_path_relative).lower() != "f4se\\plugins"
					):
						solution = None
						if file_ext in PROPER_FORMATS:
							proper_found = [
								p.name for e in PROPER_FORMATS[file_ext] if is_file(p := file_path_full.with_suffix(f".{e}"))
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
								mod_path_file,
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
									mod_path_file,
									file_path_relative,
									mod_name_file,
									"This is not a valid archive name and won't be loaded by the game.",
									SolutionType.RenameArchive,
									extra_data=[
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

		self.bool_vars: dict[ScanSetting, BooleanVar] = {}
		for setting in ScanSetting:
			self.bool_vars[setting] = BooleanVar(value=True)
			setting_check = ttk.Checkbutton(
				frame_scan_settings,
				text=setting.value[0],
				variable=self.bool_vars[setting],
				state=NORMAL,
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
		self.button_files: ttk.Button | None = None
		self.button_autofix: ttk.Button | None = None
		self.button_copy: ttk.Button | None = None

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
			text="Problem:",
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

		wraplength = WINDOW_WIDTH - 200

		self.label_file_path = ttk.Label(
			self,
			textvariable=self.sv_file_path,
			cursor="hand2",
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
			wraplength=wraplength,
		)
		self.label_file_path.grid(column=1, row=start_row, sticky=NW, padx=0, pady=5)

		ttk.Label(
			self,
			textvariable=self.sv_problem,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
			wraplength=wraplength,
		).grid(column=1, row=start_row + 1, sticky=NW, padx=0, pady=5)

		self.label_solution = ttk.Label(
			self,
			textvariable=self.sv_solution,
			font=FONT_SMALL,
			foreground=COLOR_NEUTRAL_2,
			justify=LEFT,
			wraplength=wraplength,
		)
		self.label_solution.grid(column=1, row=start_row + 2, sticky=NW, padx=0, pady=5)

		self.bind("<FocusIn>", self.on_focus)

		self.frame_buttons = ttk.Frame(self)
		self.frame_buttons.grid(column=2, row=0, rowspan=10, sticky=NSEW)

	def copy_details(self) -> None:
		if not self.button_copy:
			return

		if self.scanner_tab.cmc.game.manager and self.scanner_tab.cmc.game.manager.stage_path:
			mod = f"Mod: {self.sv_mod_name.get()}\n"
		else:
			mod = ""

		details = (
			f"{mod}Problem: {self.sv_file_path.get()}\nSummary: {self.sv_problem.get()}\nSolution: {self.sv_solution.get()}\n"
		)
		copy_text_button(self.button_copy, details)

	def set_info(self, selection: str, *, using_stage: bool) -> None:
		self.problem_info = self.scanner_tab.tree_results_data[selection]
		if using_stage:
			self.sv_mod_name.set(self.problem_info.mod or "N/A")

		self.sv_file_path.set(str(self.problem_info.relative_path))

		target = self.problem_info.path
		if isinstance(target, Path) and (exists(target) or exists(target.parent)):
			if not is_dir(target):
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

		self.sv_problem.set(self.problem_info.summary)

		if self.problem_info.extra_data:
			extra = "\n".join(self.problem_info.extra_data)
			self.sv_solution.set((self.problem_info.solution or "Solution not found.") + f"\n{extra}")
			url = self.problem_info.extra_data[0]

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
			self.sv_solution.set(self.problem_info.solution or "Solution not found.")
			self.label_solution.unbind("<Button-1>")
			self.label_solution.unbind("<Button-3>")
			if self.tooltip_solution:
				self.tooltip_solution.destroy()
				self.tooltip_solution = None

		if self.button_files:
			self.button_files.destroy()
			self.button_files = None

		if self.button_autofix:
			self.button_autofix.destroy()
			self.button_autofix = None

		if self.button_copy is None:
			self.button_copy = ttk.Button(
				self.frame_buttons,
				text="Copy Details",
				command=self.copy_details,
				padding=(0, 5),
			)

			self.button_copy.pack(side=TOP, anchor=E, fill=X, padx=5, pady=(5, 0))

		if isinstance(self.problem_info, SimpleProblemInfo) and self.problem_info.file_list:
			if self.problem_info.problem == "Race Subgraph Record Count":
				tree_title = "Race Animation Subgraph Records"
				tree_text = INFO_SCAN_RACE_SUBGRAPHS.replace("\n", " ").replace(". ", ".\n", 1)
			else:
				tree_title = "Files"
				tree_text = ""

			self.button_files = ttk.Button(
				self.frame_buttons,
				text="File List",
				command=lambda: TreeWindow(
					self.scanner_tab.cmc.root,
					self.scanner_tab.cmc,
					400,
					500,
					tree_title,
					tree_text,
					("Records", " Module"),
					self.problem_info.file_list,
				),
				padding=(0, 5),
			)
			self.button_files.pack(side=TOP, anchor=E, fill=X, padx=5, pady=(5, 0))

		if self.problem_info.solution in AUTO_FIXES:
			if self.problem_info.autofix_result is None:
				text = "Auto-Fix"
				style = "Accent.TButton"
			elif self.problem_info.autofix_result.success:
				text = "Fixed!"
				style = "TButton"
			else:
				text = "Fix Failed"
				style = "TButton"

			self.button_autofix = ttk.Button(
				self.frame_buttons,
				padding=(0, 5),
				command=lambda: do_autofix(self, selection),
				text=text,
				style=style,
			)
			self.button_autofix.pack(side=TOP, anchor=E, fill=X, padx=5, pady=(5, 0))

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
