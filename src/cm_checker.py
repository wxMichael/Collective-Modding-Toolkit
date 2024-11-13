import webbrowser
from tkinter import *
from tkinter import ttk

from tkextrafont import Font

import tabs
from enums import Tab
from game_info import GameInfo
from globals import *
from helpers import (
	CMCheckerInterface,
	CMCTabFrame,
)
from utils import (
	check_for_update_github,
	# check_for_update_nexus,
	get_asset_path,
)


class CMChecker(CMCheckerInterface):
	def __init__(self, window: Tk) -> None:
		self.window = window

		self.cascadia = Font(file=get_asset_path("fonts/CascadiaMono.ttf"), name="Cascadia Mono")

		self.FONT = (self.cascadia.name, 12)
		self.FONT_SMALLER = (self.cascadia.name, 8)
		self.FONT_SMALL = (self.cascadia.name, 10)
		self.FONT_LARGE = (self.cascadia.name, 20)

		self.install_type_sv = StringVar()
		self.game_path_sv = StringVar()
		self._images: dict[str, PhotoImage] = {}
		self.game = GameInfo(self.install_type_sv, self.game_path_sv)
		self.setup_window()

	def get_image(self, relative_path: str) -> PhotoImage:
		if relative_path not in self._images:
			self._images[relative_path] = PhotoImage(file=get_asset_path(relative_path))

		return self._images[relative_path]

	def setup_window(self) -> None:
		self.window.resizable(width=False, height=False)
		self.window.wm_attributes("-fullscreen", "false")
		self.window.iconphoto(True, self.get_image("images/icon-32.png"))  # noqa: FBT003
		self.window.title(f"{APP_TITLE} v{APP_VERSION}")

		x = (self.window.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
		y = (self.window.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
		self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
		self.window.grid_columnconfigure(0, weight=1)

		nexus_version = None  # check_for_update_nexus()
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

		self.tabs: dict[Tab, CMCTabFrame] = {
			Tab.Overview: tabs.OverviewTab(self, notebook),
			Tab.F4SE: tabs.F4SETab(self, notebook),
			Tab.Errors: tabs.ErrorsTab(self, notebook),
			Tab.Conflicts: tabs.ConflictsTab(self, notebook),
			Tab.Suggestions: tabs.SuggestionsTab(self, notebook),
			Tab.Tools: tabs.ToolsTab(self, notebook),
			Tab.About: tabs.AboutTab(self, notebook),
		}

		notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

	def on_tab_changed(self, event: "Event[ttk.Notebook]") -> None:
		new_tab_index = int(event.widget.index("current"))  # pyright: ignore[reportUnknownArgumentType]
		new_tab_name = str(event.widget.tab(new_tab_index, "text"))  # pyright: ignore[reportUnknownArgumentType]
		new_tab = Tab[new_tab_name.replace(" ", "_")]

		self.tabs[new_tab].load()
		self.window.update()

	def refresh_tab(self, tab: Tab) -> None:
		self.tabs[tab].refresh()
