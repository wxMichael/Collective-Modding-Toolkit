import webbrowser
from tkinter import *
from tkinter import ttk

import tabs
from enums import Tab
from game_info import GameInfo
from globals import *
from helpers import (
	CMCheckerInterface,
	CMCTabFrame,
	PCInfo,
)
from utils import (
	check_for_update_github,
	check_for_update_nexus,
	get_asset_path,
)


class CMChecker(CMCheckerInterface):
	def __init__(self, root: Tk) -> None:
		self.root = root
		self.pc = PCInfo()
		self.install_type_sv = StringVar()
		self.game_path_sv = StringVar()
		self.specs_sv_1 = StringVar(value=f"{self.pc.os}\n{self.pc.ram}GB RAM")
		self.specs_sv_2 = StringVar(value=f"{self.pc.cpu}\n{self.pc.gpu} {self.pc.vram}GB")
		self._images: dict[str, PhotoImage] = {}
		self.game = GameInfo(self.install_type_sv, self.game_path_sv)
		self.current_tab: CMCTabFrame | None = None
		self.overview_problems = []
		self.processing_data = False
		self.setup_window()

	def get_image(self, relative_path: str) -> PhotoImage:
		if relative_path not in self._images:
			self._images[relative_path] = PhotoImage(file=get_asset_path(relative_path))

		return self._images[relative_path]

	def on_close(self) -> None:
		if self.processing_data:
			return
		self.root.destroy()

	def setup_window(self) -> None:
		self.root.wm_resizable(width=False, height=False)
		self.root.wm_attributes("-fullscreen", "false")
		self.root.wm_iconphoto(True, self.get_image("images/icon-32.png"))  # noqa: FBT003
		self.root.wm_title(f"{APP_TITLE} v{APP_VERSION}")
		self.root.wm_protocol("WM_DELETE_WINDOW", self.on_close)

		x = (self.root.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
		y = (self.root.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
		self.root.wm_geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
		self.root.grid_columnconfigure(0, weight=1)

		nexus_version = check_for_update_nexus()
		github_version = check_for_update_github()
		if nexus_version or github_version:
			update_frame = ttk.Frame(self.root)
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
				padding=5,
				font=FONT,
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
					padding=0,
					font=(*FONT, "bold underline"),
				)
				hyperlink_label_nexus.grid_configure(column=column, row=0, sticky=NSEW)
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
					font=FONT,
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
					font=(*FONT, "bold underline"),
				)
				hyperlink_label_github.grid(column=column, row=0, sticky=NSEW)
				hyperlink_label_github.bind("<Button-1>", lambda _: webbrowser.open(GITHUB_LINK))

			update_frame.grid_columnconfigure(0, weight=1)
			update_frame.grid_columnconfigure(column, weight=1)
			update_frame.grid_rowconfigure(0, weight=1)

		notebook = ttk.Notebook(self.root)
		notebook.grid(sticky=NSEW)

		self.root.grid_rowconfigure(self.root.grid_size()[1] - 1, weight=1)

		self.tabs: dict[Tab, CMCTabFrame] = {
			Tab.Overview: tabs.OverviewTab(self, notebook),
			Tab.F4SE: tabs.F4SETab(self, notebook),
			Tab.Scanner: tabs.ScannerTab(self, notebook),
			Tab.Tools: tabs.ToolsTab(self, notebook),
			Tab.About: tabs.AboutTab(self, notebook),
		}

		notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
		self.root.bind("<Escape>", lambda _: self.root.destroy())
		self.root.bind("<Unmap>", self.on_minimize)
		self.root.bind("<Map>", self.on_restore)

	def on_minimize(self, _event: "Event[Misc]") -> None:
		if self.root.wm_state() != "iconic":
			return
		scanner_tab = self.tabs[Tab.Scanner]
		if scanner_tab.is_loaded and isinstance(scanner_tab, tabs.ScannerTab):
			if scanner_tab.side_pane:
				scanner_tab.side_pane.wm_state("withdrawn")
			if scanner_tab.details_pane:
				scanner_tab.details_pane.wm_state("withdrawn")

	def on_restore(self, _event: "Event[Misc]") -> None:
		if self.root.wm_state() != "normal":
			return
		scanner_tab = self.tabs[Tab.Scanner]
		if scanner_tab.is_loaded and isinstance(scanner_tab, tabs.ScannerTab):
			if scanner_tab.side_pane:
				scanner_tab.side_pane.wm_state("normal")
			if scanner_tab.details_pane:
				scanner_tab.details_pane.wm_state("normal")

	def on_tab_changed(self, event: "Event[ttk.Notebook]") -> None:
		if self.current_tab is not None:
			self.current_tab.switch_from()
		new_tab_index = int(event.widget.index("current"))  # pyright: ignore[reportUnknownArgumentType]
		new_tab_name = str(event.widget.tab(new_tab_index, "text"))  # pyright: ignore[reportUnknownArgumentType]
		new_tab = Tab[new_tab_name.replace(" ", "_")]
		self.current_tab = self.tabs[new_tab]

		self.tabs[new_tab].load()
		self.root.update()

	def refresh_tab(self, tab: Tab) -> None:
		self.tabs[tab].refresh()
