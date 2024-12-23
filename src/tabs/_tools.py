import webbrowser
from collections.abc import Callable
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from downgrader import Downgrader
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from modal_window import ModalWindow
from patcher import ArchivePatcher


class ToolsTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Tools")

	def add_tool_button(
		self,
		frame: ttk.Labelframe,
		text: str,
		action: str | Callable[[], ModalWindow] | None = None,
		tooltip: str | None = None,
	) -> None:
		row = len(frame.children)
		new_button = ttk.Button(frame, text=text)
		new_button.grid(column=0, row=row, sticky=EW, padx=(10, 0), pady=5)
		if action is None:
			new_button.configure(state=DISABLED)
		elif isinstance(action, str):
			new_button.configure(command=lambda: webbrowser.open(action))
			if "nexusmods" in action:
				ToolTip(new_button, "View on Nexus Mods")
			elif "github" in action:
				ToolTip(new_button, "View on GitHub")
			else:
				ToolTip(new_button, "Open website")
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
			),
			"Other CM Authors' Tools": (
				(
					"Bethini Pie",
					"https://www.nexusmods.com/site/mods/631",
					"Bethini Pie (Performance INI Editor) makes editing INI config files simple.\nDiscord channel: #bethini-doubleyou-etc",
				),
				(
					"CLASSIC Crash Log Scanner",
					"https://www.nexusmods.com/fallout4/mods/56255",
					"Scans Buffout crash logs for key indicators of crashes.\nYou can also post crash logs to the CM Discord for assistance.\nDiscord channel: #fo4-crash-logs",
				),
				(
					"  Vault-Tec Enhanced\nFaceGen System (VEFS)",
					"https://www.nexusmods.com/fallout4/mods/86374",
					"Automates the process of generating FaceGen models and textures with xEdit/CK.\nDiscord channel: #bethini-doubleyou-etc",
				),
				(
					"PJM's Precombine/Previs\n    Patching Scripts",
					"https://www.nexusmods.com/fallout4/mods/69978",
					"Scripts to find precombine/previs (flickering/occlusion) errors in your mod list, and optionally generate a patch to fix those problems.",
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
					"https://www.nexusmods.com/skyrimspecialedition/mods/23316",
					"An automation tool used to optimize BSAs, meshes, textures and animations.",
				),
				(
					"DDS Texture Scanner",
					"https://www.nexusmods.com/fallout4/mods/71588",
					"Sniff out textures that might CTD your game. With BA2 support.\nDiscord channel: #nistonmakemod",
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
		self.add_tool_button(frame_toolkit, "Papyrus Script\n   Compiler")
