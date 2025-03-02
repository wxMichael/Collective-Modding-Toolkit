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
import sys
import webbrowser
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

import tabs
from app_settings import AppSettings
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

logger = logging.getLogger(__name__)


class CMChecker(CMCheckerInterface):
	def __init__(self, root: Tk, settings: AppSettings) -> None:
		self.root = root
		self.settings = settings
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
		self.check_for_updates()

	def get_image(self, relative_path: str) -> PhotoImage:
		if relative_path not in self._images:
			self._images[relative_path] = PhotoImage(file=get_asset_path(relative_path))

		return self._images[relative_path]

	def on_close(self) -> None:
		if self.processing_data:
			return
		sys.stderr = sys.__stderr__
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
		self.root.grid_rowconfigure(1, weight=1)

		notebook = ttk.Notebook(self.root)
		notebook.grid(column=0, row=1, sticky=NSEW)

		self.tabs: dict[Tab, CMCTabFrame] = {
			Tab.Overview: tabs.OverviewTab(self, notebook),
			Tab.F4SE: tabs.F4SETab(self, notebook),
			Tab.Scanner: tabs.ScannerTab(self, notebook),
			Tab.Tools: tabs.ToolsTab(self, notebook),
			Tab.Settings: tabs.SettingsTab(self, notebook),
			Tab.About: tabs.AboutTab(self, notebook),
		}

		notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
		self.root.bind("<Escape>", lambda _: self.root.destroy())
		self.root.bind("<Unmap>", self.on_minimize)
		self.root.bind("<Map>", self.on_restore)

	def check_for_updates(self) -> None:
		update_source = self.settings.dict["update_source"]
		if update_source == "none":
			return

		nexus_version = check_for_update_nexus() if update_source in {"nexus", "both"} else None
		github_version = check_for_update_github() if update_source in {"github", "both"} else None
		if not (nexus_version or github_version):
			return

		update_frame = ttk.Frame(self.root, style="Update.TFrame")
		update_frame.grid(column=0, row=0, sticky=NSEW)

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
		).grid(column=column, row=0, sticky=E)

		if nexus_version:
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
			hyperlink_label_nexus.grid(column=column, row=0, sticky=W)
			hyperlink_label_nexus.bind("<Button-1>", lambda _: webbrowser.open(NEXUS_LINK))
			ToolTip(hyperlink_label_nexus, "Open Nexus Mods")

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
			).grid(column=column, row=0, sticky=W)

		if github_version:
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
			hyperlink_label_github.grid(column=column, row=0, sticky=W)
			hyperlink_label_github.bind("<Button-1>", lambda _: webbrowser.open(GITHUB_LINK))
			ToolTip(hyperlink_label_github, "Open GitHub")

		update_frame.grid_columnconfigure(0, weight=1)
		update_frame.grid_columnconfigure(column, weight=1)
		update_frame.grid_rowconfigure(0, weight=1)

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
		logger.debug("Refresh Tab : %s", tab)
		self.tabs[tab].refresh()
