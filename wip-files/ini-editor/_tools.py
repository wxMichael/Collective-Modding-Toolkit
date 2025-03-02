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


import webbrowser
from collections.abc import Callable
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from downgrader import Downgrader
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from ini_file import INIFile, INIPart
from modal_window import ModalWindow
from patcher import ArchivePatcher


NEW_TAB_STRINGS = ("hotkey",)
layout = {
	"General": {
		"[CreationKit]": (0, 0, 4),
		"[PreCombined]": (1, 1, 1),
		"[Animation]": (1, 2, 1),
		"[FaceGen]": (1, 3, 1),
		"[Log]": (1, 4, 1),
	},
	"[Hotkeys]": {},
}

from random import randint


class CKPEINIEditor(ModalWindow):
	def __init__(self, parent: Wm, cmc: CMCheckerInterface) -> None:
		super().__init__(parent, cmc, "CKPE INI Editor", 700, 600)
		self.win_width = 700
		self.win_height = 600
		self.variables: dict[str, dict[str, Variable]] = {}
		self.load_ini()
		self.build_gui()

	def load_ini(self) -> None:
		ini_path = self.cmc.game.game_path / "CreationKitPlatformExtended.ini"
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)
		if not ini_path.is_file():
			label_error = ttk.Label(
				self,
				text="CreationKitPlatformExtended.ini not found!\nPlease reinstall CKPE.",
				font=FONT,
				foreground=COLOR_BAD,
				justify=CENTER,
				anchor=CENTER,
			)
			label_error.grid(sticky=NSEW, padx=10, pady=10)
			return

		notebook = ttk.Notebook(self)
		notebook.grid(sticky=NSEW)
		frame_main = ttk.Frame(self)
		notebook.add(frame_main, text="Main")

		ini = INIFile(ini_path)
		column_height = 0
		current_column = 0
		current_row = -1
		for i, section in enumerate(ini.settings):
			section_lower = section.lower()
			if any(s in section_lower for s in NEW_TAB_STRINGS):
				frame_section: ttk.Widget = ttk.Frame(notebook)
				notebook.add(frame_section, text=section)
			else:
				frame_section = ttk.Labelframe(
					frame_main,
					text=section,
					padding=5,
				)
				style = ttk.Style()
				style_name = f"RandomBG{i}.TFrame"
				style.configure(style_name, background=f"#{randint(0, 0xFFFFFF):06x}")
				frame_section.configure(style=style_name)
			self.variables[section] = {}
			if not ini.settings[section]:
				ttk.Label(frame_section, text="<No Settings>").grid(column=0, row=0, sticky=NSEW)
				continue

			for setting in ini.settings[section]:
				if setting[0] == "b":
					variable: Variable = BooleanVar(value=bool(ini.settings[section][setting][0] == "true"))
					setting_widget: ttk.Widget = ttk.Checkbutton(
						frame_section,
						text=setting,
						variable=variable,
					)
					self.variables[section][setting] = variable
				else:
					setting_widget = ttk.Label(
						frame_section,
						text=f"{setting} = {ini.settings[section][setting][0]}",
						font=FONT_SMALL,
						justify=LEFT,
						foreground=COLOR_DEFAULT,
						anchor=W,
					)
				setting_widget.pack(side=TOP, anchor=W)  # .grid(column=0, row=frame_section.size()[1], sticky=W)
				for ini_part in ini.line_parts[ini.settings[section][setting][1]][ini.settings[section][setting][2] :]:
					if ini_part[0] == INIPart.Comment:
						if ini_part[1]:
							ToolTip(setting_widget, ini_part[1])
						break

			if isinstance(frame_section, ttk.Labelframe):
				current_row += 1
				frame_section.grid(column=current_column, row=current_row, sticky=NW)
				frame_section.update_idletasks()
				section_height = frame_section.winfo_height()
				if column_height + section_height <= self.win_height:
					column_height += section_height
				else:
					current_column += 1
					current_row = 0
					column_height = 0
					frame_section.grid(column=current_column, row=current_row, sticky=NW)
					frame_section.update_idletasks()

	def build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)


class ToolsTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Tools")

	def add_tool_button(
		self, frame: ttk.Labelframe, text: str, action: str | Callable[[], ModalWindow] | None = None, tooltip: str | None = None
	) -> None:
		row = len(frame.children)
		new_button = ttk.Button(frame, text=text)
		new_button.grid(column=0, row=row, sticky=EW, padx=(10, 0), pady=5)
		if action is None:
			new_button.configure(state=DISABLED)
		elif isinstance(action, str):
			new_button.configure(command=lambda: webbrowser.open(action))
		else:
			new_button.configure(command=action)

		if tooltip is not None:
			image_info = self.cmc.get_image("images/info-16.png")
			padding_y = image_info.height() // 2 - 1
			new_button_info = ttk.Label(
				frame,
				compound="image",
				image=image_info,
				justify=CENTER,
			)
			new_button_info.grid(column=1, row=row, sticky=NSEW, padx=(5, 0), pady=(padding_y, 0))
			ToolTip(new_button_info, tooltip)

	def _build_gui(self) -> None:
		tool_buttons = {
			"Toolkit Utilities": (
				(
					"Downgrade Manager",
					lambda: Downgrader(self.cmc.root, self.cmc),
				),
				(
					"Archive Patcher",
					lambda: ArchivePatcher(self.cmc.root, self.cmc),
				),
				(
					"CKPE INI Editor",
					lambda: CKPEINIEditor(self.cmc.root, self.cmc),
				),
			),
			"Other CM Authors' Tools": (
				(
					"Bethini Pie",
					"https://www.nexusmods.com/site/mods/631",
					"Bethini Pie (Performance INI Editor) makes editing INI config files simple.",
				),
				(
					"CLASSIC Crash Log Scanner",
					"https://www.nexusmods.com/fallout4/mods/56255",
					"Scans Buffout crash logs for key indicators of crashes.\nYou can also post crash logs to the CM Discord for assistance.",
				),
				(
					"  Vault-Tec Enhanced\nFaceGen System (VEFS)",
					"https://www.nexusmods.com/fallout4/mods/86374",
					"Automates the process of generating FaceGen models and textures with xEdit/CK.",
				),
			),
			"Other Useful Tools": (
				(
					"xEdit / FO4Edit",
					"https://github.com/TES5Edit/TES5Edit#xedit",
					"Module editor and conflict detector for Bethesda games.\nFO4Edit/SSEEdit are xEdit, renamed to auto-set a game mode.",
				),
				(
					"Creation Kit Platform\n   Extended (CKPE)",
					"https://www.nexusmods.com/fallout4/mods/51165",
					"Various patches and bug fixes for the Creation Kit to make life easier.",
				),
				(
					"Cathedral Assets\nOptimizer (CAO)",
					"https://www.nexusmods.com/fallout4/mods/71588",
					"An automation tool used to optimize BSAs, meshes, textures and animations.",
				),
				(
					"DDS Texture Scanner",
					"https://www.nexusmods.com/fallout4/mods/71588",
					"Sniff out textures that might CTD your game. With BA2 support.",
				),
				(
					"Unpackrr",
					"https://www.nexusmods.com/fallout4/mods/82082",
					"Batch unpacks small BA2 files to stay below the limit.",
				),
				(
					"IceStorm's Texture Tools",
					"https://storage.icestormng-mods.de/s/QG43aExydefeGXy",
					"Converts textures from various formats into a Fallout 4 compatible format.",
				),
				(
					"CapFrameX",
					"https://www.capframex.com/",
					"Benchmarking tool - Record FPS, frametime, and sensors; analyse and plot the results.",
				),
			),
		}

		for i, (column, buttons) in enumerate(tool_buttons.items()):
			self.grid_columnconfigure(i, weight=1, pad=5)
			frame_column = ttk.Labelframe(self, text=column, labelanchor=N, padding=5)
			frame_column.grid(column=i, row=0, sticky=NSEW, padx=5, pady=5)
			for button in buttons:
				self.add_tool_button(frame_column, *button)  # type: ignore[reportArgumentType]

		frame_toolkit = next(w for w in self.children.values() if isinstance(w, ttk.Labelframe))
		label_planned = ttk.Label(frame_toolkit, text="Planned Tools:", font=FONT_SMALL)
		label_planned.grid(column=0, row=len(frame_toolkit.children) - 1, pady=(10, 0))

		self.add_tool_button(frame_toolkit, "File Inspector")
		self.add_tool_button(frame_toolkit, "Complex Sorter\n  INI Patcher")
		self.add_tool_button(frame_toolkit, "Move CC to\nMod Manager")
		self.add_tool_button(frame_toolkit, "Papyrus Script\nCompiler")
