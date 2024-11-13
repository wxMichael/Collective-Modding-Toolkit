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
			padding=(10, 0),
			command=lambda: Downgrader(self.cmc),
		).grid(column=0, row=0, sticky=EW, padx=15, pady=(15, 0))

		ttk.Button(
			self,
			text="Archive Patcher",
			padding=(10, 0),
			command=lambda: ArchivePatcher(self.cmc),
		).grid(column=0, row=1, sticky=EW, padx=15, pady=(10, 0))

		ttk.Label(
			self,
			text="Tentatively-Planned Tools:",
			font=self.cmc.FONT_SMALL,
		).grid(column=0, row=2, pady=(20, 0))

		ttk.Button(
			self,
			text="(WIP) File Inspector",
			padding=(10, 0),
			# command=lambda: FileInspector(self.cmc),
			state="disabled",
		).grid(column=0, row=3, sticky=EW, padx=15, pady=(10, 0))

		ttk.Button(
			self,
			text="(WIP) Papyrus Script Compiler",
			padding=(10, 0),
			# command=lambda: PapyrusCompiler(self.cmc),
			state="disabled",
		).grid(column=0, row=4, sticky=EW, padx=15, pady=(10, 0))
