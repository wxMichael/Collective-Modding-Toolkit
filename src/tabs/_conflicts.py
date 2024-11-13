from tkinter import *
from tkinter import ttk

from globals import *
from helpers import CMCheckerInterface, CMCTabFrame


class ConflictsTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Conflicts")

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)
		ttk.Label(self, text="WIP", font=self.cmc.FONT_LARGE, justify=CENTER).grid()
