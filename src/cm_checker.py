import sys
import webbrowser
import winreg
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk

from tkextrafont import Font

import tabs
from globals import *
from helpers import (
	CMCheckerInterface,
	CMCTabFrame,
	Tab,
)
from utils import (
	check_for_update_github,
	# check_for_update_nexus,
	get_asset_path,
	get_registry_value,
)


class CMChecker(CMCheckerInterface):
	def __init__(self, window: Tk) -> None:
		self.window = window

		self.cascadia = Font(file=get_asset_path("fonts/CascadiaMono.ttf"), name="Cascadia Mono")

		self.FONT = (self.cascadia.name, 12)
		self.FONT_SMALL = (self.cascadia.name, 10)
		self.FONT_LARGE = (self.cascadia.name, 20)

		self.archives_og: set[Path] = set()
		self.archives_ng: set[Path] = set()
		self.archives_invalid: set[Path] = set()

		self.modules_invalid: set[Path] = set()
		self.modules_v95: set[Path] = set()

		self.install_type_sv = StringVar()
		self.game_path_sv = StringVar()
		self.install_type = InstallType.Unknown
		self._images: dict[str, PhotoImage] = {}
		self.find_game_paths()
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
		self.game_path_sv.set(str(value))

	@property
	def install_type(self) -> InstallType:
		return self._install_type

	@install_type.setter
	def install_type(self, value: InstallType) -> None:
		self._install_type = value
		self.install_type_sv.set(str(value))

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
		new_tab_index = int(event.widget.index("current"))  # type: ignore
		new_tab_name = str(event.widget.tab(new_tab_index, "text"))  # type: ignore
		new_tab = Tab[new_tab_name.replace(" ", "_")]

		self.tabs[new_tab].load()
		self.window.update()

	def find_game_paths(self) -> None:
		game_path_as_path = Path.cwd()
		if not is_fo4_dir(game_path_as_path):
			game_path = get_registry_value(
				winreg.HKEY_LOCAL_MACHINE,
				R"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4",
				"Installed Path",
			) or get_registry_value(
				winreg.HKEY_LOCAL_MACHINE,
				R"SOFTWARE\WOW6432Node\GOG.com\Games\1998527297",
				"path",
			)

			assert isinstance(game_path, str) or game_path is None

			if isinstance(game_path, str):
				game_path_as_path = Path(game_path)
				if not is_fo4_dir(game_path_as_path):
					game_path = None

			if game_path is None:
				game_path = filedialog.askopenfilename(
					title="Select Fallout4.exe",
					filetypes=[("Fallout 4", "Fallout4.exe")],
				)

			if not game_path:
				# None, or Empty string if filedialog cancelled
				messagebox.showerror(  # type: ignore
					"Game not found",
					"A Fallout 4 installation could not be found.",
				)
				sys.exit()

			assert isinstance(game_path, str)

			game_path_as_path = Path(game_path)
			if game_path_as_path.is_file():
				game_path_as_path = game_path_as_path.parent

		data_path: Path | None = game_path_as_path / "Data"
		assert data_path is not None
		if data_path.is_dir():
			f4se_path: Path | None = data_path / "F4SE/Plugins"
			assert f4se_path is not None
			if not f4se_path.is_dir():
				f4se_path = None
		else:
			data_path = None
			f4se_path = None

		self.game_path = game_path_as_path
		self.data_path = data_path
		self.f4se_path = f4se_path

	def refresh_tab(self, tab: Tab) -> None:
		self.tabs[tab].refresh()


def is_fo4_dir(path: Path) -> bool:
	return path.is_dir() and (path / "Fallout4.exe").is_file()
