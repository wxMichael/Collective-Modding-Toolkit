import logging
from enum import StrEnum
from tkinter import *
from tkinter import ttk

from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from globals import *
from helpers import CMCheckerInterface, CMCTabFrame

logger = logging.getLogger(__name__)


class UpdateMode(StrEnum):
	DontCheck = "none"
	NexusModsOnly = "nexus"
	GitHubOnly = "github"
	GitHubAndNexusMods = "both"


class LogLevel(StrEnum):
	DEBUG = "DEBUG"
	INFO = "INFO"
	ERROR = "ERROR"


class SettingsTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "Settings")

		self.sv_setting_update_source = StringVar(value=cmc.settings.dict["update_source"])
		self.sv_setting_log_level = StringVar(value=cmc.settings.dict["log_level"])

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(1, weight=0)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=0)

		options_radios = {
			"Update Channel": (
				TOOLTIP_UPDATE_SOURCE,
				1,
				0,
				self.sv_setting_update_source,
				"update_source",
				(
					("All: GitHub & Nexus Mods", UpdateMode.GitHubAndNexusMods),
					("Early: GitHub", UpdateMode.GitHubOnly),
					("Stable: Nexus Mods", UpdateMode.NexusModsOnly),
					("Never: Don't Check", UpdateMode.DontCheck),
				),
			),
			"Log Level": (
				TOOLTIP_LOG_LEVEL,
				2,
				0,
				self.sv_setting_log_level,
				"log_level",
				(
					("Debug", LogLevel.DEBUG),
					("Info", LogLevel.INFO),
					("Error", LogLevel.ERROR),
				),
			),
		}

		for name, (tooltip, column, row, var, action, options) in options_radios.items():
			frame = ttk.Labelframe(self, text=name, padding=5)
			frame.grid(column=column, row=row, padx=5, pady=5, sticky=NSEW)
			for text, value in options:
				radio = ttk.Radiobutton(
					frame,
					value=value,
					variable=var,
					text=text,
				)
				def update_setting(s: str = action, v: Variable = var) -> None:
					self.on_radio_change(s, v)
				radio.configure(command=update_setting)
				radio.pack(anchor=W, side=TOP)
				ToolTip(radio, tooltip)

	def on_radio_change(self, setting: str, variable: Variable) -> None:
		self.cmc.settings.dict[setting] = variable.get()
		self.cmc.settings.save()
