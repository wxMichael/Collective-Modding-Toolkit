from tkinter import *
from tkinter import ttk

from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, DLLInfo
from utils import (
	parse_dll,
)

TAG_NEUTRAL = "neutral"
TAG_GOOD = "good"
TAG_BAD = "bad"

EMOJI_DLL_UNKNOWN = "\N{BLACK QUESTION MARK ORNAMENT}"
EMOJI_DLL_GOOD = "\N{HEAVY CHECK MARK}"
EMOJI_DLL_BAD = ""


class F4SETab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "F4SE")
		self.loading_text = "Scanning DLLs..."

		self.dll_info: dict[str, DLLInfo | None] = {}

	def _load(self) -> bool:
		if self.cmc.game.data_path is None:
			self.loading_error = "Data folder not found"
			return False

		if self.cmc.game.f4se_path is None:
			self.loading_error = "Data/F4SE/Plugins folder not found"
			return False

		self.dll_info.clear()
		for dll_file in self.cmc.game.f4se_path.glob("*.dll"):
			self.dll_info[dll_file.name] = parse_dll(dll_file)

		return True

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(2, weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)

		style = ttk.Style()
		style.configure("Treeview", font=self.cmc.FONT_SMALL)
		tree_dlls = ttk.Treeview(self, columns=("og", "ng", "user"))
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
			self,
			orient=VERTICAL,
			command=tree_dlls.yview,  # pyright: ignore[reportUnknownArgumentType]
		)

		tree_dlls.grid(column=0, row=0, rowspan=2, sticky="NSEW")
		scroll_tree_y.grid(column=1, row=0, rowspan=2, sticky="NSEW")
		tree_dlls.configure(yscrollcommand=scroll_tree_y.set)

		ttk.Label(
			self,
			text="F4SE DLLs",
			font=self.cmc.FONT,
			anchor=N,
		).grid(column=2, row=0, padx=5, pady=5)

		Message(
			self,
			text=ABOUT_F4SE_DLLS,
			font=self.cmc.FONT_SMALL,
			anchor=N,
			aspect=100,
		).grid(column=2, row=1, sticky=NSEW, padx=5)

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

				if (self.cmc.game.is_foog() and info.get("SupportsOG")) or (
					self.cmc.game.is_fong() and info.get("SupportsNG")
				):
					tags.append(TAG_GOOD)
					values.append(EMOJI_DLL_GOOD)
				else:
					tags.append(TAG_BAD)
					values.append("\N{CROSS MARK}")

			tree_dlls.insert("", END, text=dll, values=values, tags=tags)
