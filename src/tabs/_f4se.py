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

import f4se_utils
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame, DLLInfo

TAG_NEUTRAL = "neutral"
TAG_GOOD = "good"
TAG_BAD = "bad"
TAG_NOTE = "note"
TAG_INDIE = "independent"

EMOJI_DLL_UNKNOWN = "\N{BLACK QUESTION MARK ORNAMENT}"
EMOJI_DLL_GOOD = "\N{HEAVY CHECK MARK}"
EMOJI_DLL_BAD = ""
EMOJI_DLL_NOTE = "\N{WARNING SIGN}"
EMOJI_DLL_INDIE = "\N{HEAVY ASTERISK}"

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

		try:
			game_version = self.cmc.game.load_game_version()
		except Exception:
			logger.exception("Failed to read Fallout4.exe version")
			self.loading_error = "Unable to read the version of Fallout4.exe"
			return False

		self.dll_info.clear()
		for dll_file in self.cmc.game.f4se_path.iterdir():
			if dll_file.suffix.lower() == ".dll" and not dll_file.name.startswith("msdia"):
				logger.debug("Scanning %s", dll_file.name)
				# TODO: make this actually scan the game
				try:
					self.dll_info[dll_file.name] = f4se_utils.parse_dll(dll_file, game_version)
				except OSError:
					logger.exception("Failed to load %s", dll_file.name)
					self.dll_info[dll_file.name] = None
		return True

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(2, weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)

		tree_dlls = ttk.Treeview(self, columns=("og", "ng", "ae", "user"))
		tree_dlls.heading("#0", text="DLL")
		tree_dlls.heading("og", text="OG")
		tree_dlls.heading("ng", text="NG")
		tree_dlls.heading("ae", text="AE")
		tree_dlls.heading("user", text="Your Game")

		tree_dlls.column("#0", width=scale(240), stretch=False, anchor=E)
		tree_dlls.column("og", width=scale(60), stretch=False, anchor=CENTER)
		tree_dlls.column("ng", width=scale(60), stretch=False, anchor=CENTER)
		tree_dlls.column("ae", width=scale(60), stretch=False, anchor=CENTER)
		tree_dlls.column("user", width=scale(80), stretch=False, anchor=CENTER)

		tree_dlls.tag_configure(TAG_NEUTRAL, foreground=COLOR_NEUTRAL_1)
		tree_dlls.tag_configure(TAG_GOOD, foreground=COLOR_GOOD)
		tree_dlls.tag_configure(TAG_BAD, foreground=COLOR_BAD)
		tree_dlls.tag_configure(TAG_NOTE, foreground=COLOR_NOTE)
		tree_dlls.tag_configure(TAG_INDIE, foreground=COLOR_INDIE)

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
		).grid(column=2, row=0, padx=scale(5), pady=scale(5))

		text_about_f4se = Text(
			self,
			font=FONT_SMALL,
			wrap=CHAR,
			relief=FLAT,
		)
		text_about_f4se.insert(END, ABOUT_F4SE_DLLS)
		text_about_f4se.tag_add(TAG_NEUTRAL, "2.0", "2.18")
		text_about_f4se.tag_add(TAG_GOOD, "6.0", "6.1")
		text_about_f4se.tag_add(TAG_INDIE, "8.0", "8.1")
		text_about_f4se.tag_add(TAG_NEUTRAL, "10.0", "10.1")
		text_about_f4se.tag_add(TAG_NOTE, "14.0", "14.1")
		text_about_f4se.tag_configure(TAG_GOOD, foreground=COLOR_GOOD)
		text_about_f4se.tag_configure(TAG_INDIE, foreground=COLOR_INDIE)
		text_about_f4se.tag_configure(TAG_NEUTRAL, foreground=COLOR_NEUTRAL_2)
		text_about_f4se.tag_configure(TAG_NOTE, foreground=COLOR_NOTE)
		text_about_f4se.configure(state=DISABLED)
		text_about_f4se.grid(column=2, row=1, sticky=NSEW, padx=0)

		tag: str | None = None
		for dll, info in self.dll_info.items():
			values: list[str] = []
			if info is None or not info["IsF4SE"]:
				tag = TAG_NEUTRAL
				values = [EMOJI_DLL_UNKNOWN] * len(tree_dlls["columns"])
			else:
				og = EMOJI_DLL_GOOD if info.get("SupportsOG") else EMOJI_DLL_BAD

				supports_ngae = info.get("SupportsNGAE")
				supports_ng = info.get("SupportsNG")
				supports_ae = info.get("SupportsAE")
				supports_game = info.get("SupportsCurrent")
				is_addrindependent_ng = info.get("AddrIndependentNG")
				is_structindependent_ng = info.get("StructIndependentNG")
				is_addrindependent_ae = info.get("AddrIndependentAE")
				is_structindependent_ae = info.get("StructIndependentAE")

				if supports_ngae:
					ng = (
						EMOJI_DLL_INDIE
						if is_addrindependent_ng and is_structindependent_ng
						else EMOJI_DLL_GOOD
						if supports_ng and supports_game
						else EMOJI_DLL_NOTE
						if supports_ng
						else EMOJI_DLL_BAD
					)
					ae = (
						EMOJI_DLL_INDIE
						if is_addrindependent_ae and is_structindependent_ae
						else EMOJI_DLL_GOOD
						if supports_ae and supports_game
						else EMOJI_DLL_NOTE
						if supports_ae
						else EMOJI_DLL_BAD
					)
				else:
					ng = EMOJI_DLL_BAD
					ae = EMOJI_DLL_BAD

				cg = "\N{CROSS MARK}"
				if self.cmc.game.is_fongae():
					if supports_game:
						cg = EMOJI_DLL_GOOD
					elif self.cmc.game.is_foae():
						cg = EMOJI_DLL_INDIE if is_addrindependent_ae and is_structindependent_ae else "\N{CROSS MARK}"
					elif self.cmc.game.is_fong():
						cg = EMOJI_DLL_INDIE if is_addrindependent_ng and is_structindependent_ng else "\N{CROSS MARK}"
					else:
						cg = EMOJI_DLL_NOTE
				elif self.cmc.game.is_foog():
					cg = EMOJI_DLL_GOOD if info.get("SupportsOG") else "\N{CROSS MARK}"

				values = [og, ng, ae, cg]
				tag = (
					TAG_INDIE
					if cg == EMOJI_DLL_INDIE
					else TAG_NOTE
					if cg == EMOJI_DLL_NOTE
					else TAG_GOOD
					if cg == EMOJI_DLL_GOOD
					else TAG_BAD
				)

			tree_dlls.insert("", END, text=dll, values=values, tags=tag)
