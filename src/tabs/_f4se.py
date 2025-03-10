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
TAG_NOTE = "note"

EMOJI_DLL_UNKNOWN = "\N{BLACK QUESTION MARK ORNAMENT}"
EMOJI_DLL_GOOD = "\N{HEAVY CHECK MARK}"
EMOJI_DLL_BAD = ""
EMOJI_DLL_NOTE = "\N{WARNING SIGN}"
DLL_OGNG_WHITELIST = (
	"AchievementsModsEnablerLoader.dll",
	"BetterConsole.dll",
	"Buffout4.dll",
	"ClockWidget.dll",
	"FloatingDamage.dll",
	"GCBugFix.dll",
	"HUDPlusPlus.dll",
	"IndirectFire.dll",
	"MinimalMinimap.dll",
	"MoonRotationFix.dll",
	"mute_on_focus_loss.dll",
	"SprintStutteringFix.dll",
	"UnlimitedFastTravel.dll",
	"WeaponDebrisCrashFix.dll",
	"x-cell-fo4.dll",
)

logger = logging.getLogger(__name__)


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
			if not self.cmc.game.manager:
				self.loading_error += "\nTry launching via your mod manager."
			return False

		self.dll_info.clear()
		for dll_file in self.cmc.game.f4se_path.iterdir():
			if dll_file.suffix.lower() == ".dll" and not dll_file.name.startswith("msdia"):
				logger.debug("Scanning %s", dll_file.name)
				self.dll_info[dll_file.name] = parse_dll(dll_file)

		return True

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(2, weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)

		tree_dlls = ttk.Treeview(self, columns=("og", "ng", "user"))
		tree_dlls.heading("#0", text="DLL")
		tree_dlls.heading("og", text="OG")
		tree_dlls.heading("ng", text="NG")
		tree_dlls.heading("user", text="Your Game")

		tree_dlls.column("#0", width=300, stretch=False, anchor=E)
		tree_dlls.column("og", width=60, stretch=False, anchor=CENTER)
		tree_dlls.column("ng", width=60, stretch=False, anchor=CENTER)
		tree_dlls.column("user", width=80, stretch=False, anchor=CENTER)

		tree_dlls.tag_configure(TAG_NEUTRAL, foreground=COLOR_NEUTRAL_1)
		tree_dlls.tag_configure(TAG_GOOD, foreground=COLOR_GOOD)
		tree_dlls.tag_configure(TAG_BAD, foreground=COLOR_BAD)
		tree_dlls.tag_configure(TAG_NOTE, foreground="yellow")

		scroll_tree_y = ttk.Scrollbar(
			self,
			orient=VERTICAL,
			command=tree_dlls.yview,  # pyright: ignore[reportUnknownArgumentType]
		)

		tree_dlls.grid(column=0, row=0, rowspan=2, sticky=NS)
		scroll_tree_y.grid(column=1, row=0, rowspan=2, sticky=NS)
		tree_dlls.configure(yscrollcommand=scroll_tree_y.set)

		ttk.Label(
			self,
			text="F4SE DLLs",
			font=FONT,
			anchor=N,
		).grid(column=2, row=0, padx=5, pady=5)

		text_about_f4se = Text(
			self,
			font=FONT_SMALL,
			wrap=CHAR,
			relief=FLAT,
		)
		text_about_f4se.insert(END, ABOUT_F4SE_DLLS)
		text_about_f4se.tag_add(TAG_NEUTRAL, "2.0", "2.18")
		text_about_f4se.tag_add(TAG_GOOD, "6.0", "6.1")
		text_about_f4se.tag_add(TAG_BAD, "8.0", "8.1")
		text_about_f4se.tag_add(TAG_NEUTRAL, "10.0", "10.1")
		text_about_f4se.tag_add(TAG_NOTE, "14.0", "14.1")
		text_about_f4se.tag_configure(TAG_GOOD, foreground=COLOR_GOOD)
		text_about_f4se.tag_configure(TAG_BAD, foreground=COLOR_BAD)
		text_about_f4se.tag_configure(TAG_NEUTRAL, foreground=COLOR_NEUTRAL_2)
		text_about_f4se.tag_configure(TAG_NOTE, foreground="yellow")
		text_about_f4se.configure(state=DISABLED)
		text_about_f4se.grid(column=2, row=1, sticky=NSEW, padx=0)

		tag: str | None = None
		for dll, info in self.dll_info.items():
			values: list[str] = []
			if info is None or not info["IsF4SE"]:
				tag = TAG_NEUTRAL
				values = [EMOJI_DLL_UNKNOWN] * 3
			else:
				og = EMOJI_DLL_GOOD if info.get("SupportsOG") else EMOJI_DLL_BAD
				ng = EMOJI_DLL_GOOD if info.get("SupportsNG") else EMOJI_DLL_BAD
				cg = (
					EMOJI_DLL_NOTE
					if (info.get("SupportsOG") and info.get("SupportsNG"))
					else EMOJI_DLL_GOOD
					if (self.cmc.game.is_foog() and info.get("SupportsOG"))
					or (self.cmc.game.is_fong() and info.get("SupportsNG"))
					else "\N{CROSS MARK}"
				)
				if cg == EMOJI_DLL_NOTE and dll in DLL_OGNG_WHITELIST:
					cg = EMOJI_DLL_GOOD
				values = [og, ng, cg]
				tag = TAG_NOTE if cg == EMOJI_DLL_NOTE else TAG_GOOD if cg == EMOJI_DLL_GOOD else TAG_BAD

			tree_dlls.insert("", END, text=dll, values=values, tags=tag)
