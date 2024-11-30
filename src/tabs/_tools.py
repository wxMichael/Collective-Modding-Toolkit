from tkinter import *
from tkinter import ttk

from downgrader import Downgrader
from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from patcher import ArchivePatcher


class ToolsTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Tools")

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=0)
		self.grid_rowconfigure(0, weight=0)

		ttk.Button(
			self,
			text="Downgrade Manager",
			padding=5,
			command=lambda: Downgrader(self.cmc.root, self.cmc),
		).grid(column=0, row=0, sticky=EW, padx=15, pady=(15, 0))

		ttk.Button(
			self,
			text="Archive Patcher",
			padding=5,
			command=lambda: ArchivePatcher(self.cmc.root, self.cmc),
		).grid(column=0, row=1, sticky=EW, padx=15, pady=(10, 0))

		ttk.Label(
			self,
			text="Tentatively-Planned Tools:",
			font=FONT_SMALL,
		).grid(column=0, row=2, pady=(20, 0))

		ttk.Button(
			self,
			text="(WIP) File Inspector",
			padding=5,
			# command=lambda: FileInspector(self.cmc),
			state="disabled",
		).grid(column=0, row=3, sticky=EW, padx=15, pady=(10, 0))

		ttk.Button(
			self,
			text="(WIP) Complex Sorter INI Patcher",
			padding=5,
			# command=lambda: ComplexSorterPatcher(self.cmc),
			state="disabled",
		).grid(column=0, row=4, sticky=EW, padx=15, pady=(10, 0))

		ttk.Button(
			self,
			text="(WIP) Move CC to Mod Manager",
			padding=5,
			# command=lambda: CCMover(self.cmc),
			state="disabled",
		).grid(column=0, row=5, sticky=EW, padx=15, pady=(10, 0))

		ttk.Button(
			self,
			text="(WIP) Papyrus Script Compiler",
			padding=5,
			# command=lambda: PapyrusCompiler(self.cmc),
			state="disabled",
		).grid(column=0, row=6, sticky=EW, padx=15, pady=(10, 0))
