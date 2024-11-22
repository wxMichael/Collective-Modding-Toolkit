import webbrowser
from tkinter import *
from tkinter import ttk

from globals import *
from helpers import CMCheckerInterface, CMCTabFrame
from utils import (
	add_separator,
	copy_text_button,
)


class AboutTab(CMCTabFrame):
	def __init__(self, cmc: CMCheckerInterface, notebook: ttk.Notebook) -> None:
		super().__init__(cmc, notebook, "About")

	def _build_gui(self) -> None:
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)

		ttk.Label(
			self,
			text="\n".join(APP_TITLE.rsplit(maxsplit=1)),
			font=self.cmc.FONT_LARGE,
			justify=CENTER,
		).grid(column=0, row=0, pady=10)

		ttk.Label(
			self,
			compound="image",
			image=self.cmc.get_image("images/icon-256.png"),
		).grid(column=0, row=1, sticky=NS, pady=(0, 20))

		frame_about_text = ttk.Frame(self)
		frame_about_text.grid(column=1, row=0, rowspan=2, padx=(0, 20))

		ttk.Label(
			frame_about_text,
			text=f"v{APP_VERSION}\n\nCreated by wxMichael for the\nCollective Modding Community",
			font=self.cmc.FONT,
			justify=CENTER,
		).grid(column=0, row=1, rowspan=2, pady=10)

		frame_nexus = ttk.Frame(frame_about_text)
		frame_nexus.grid(column=0, row=3, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_nexus,
			compound="image",
			image=self.cmc.get_image("images/logo-nexusmods.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_nexus, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_nexus,
			text="Open Link",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(NEXUS_LINK),
		).grid(column=2, row=0, padx=0, pady=5)

		button_nexus_copy = ttk.Button(frame_nexus, text="Copy Link", padding=0, width=12)
		button_nexus_copy.configure(command=lambda: copy_text_button(button_nexus_copy, NEXUS_LINK))
		button_nexus_copy.grid(column=2, row=1, padx=0, pady=5)

		frame_discord = ttk.Frame(frame_about_text)
		frame_discord.grid(column=0, row=4, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_discord,
			compound="image",
			image=self.cmc.get_image("images/logo-discord.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_discord, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_discord,
			text="Open Invite",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(DISCORD_INVITE),
		).grid(column=2, row=0, padx=0, pady=5)

		button_discord_copy = ttk.Button(frame_discord, text="Copy Invite", padding=0, width=12)
		button_discord_copy.configure(command=lambda: copy_text_button(button_discord_copy, DISCORD_INVITE))
		button_discord_copy.grid(column=2, row=1, padx=0, pady=5)

		frame_github = ttk.Frame(frame_about_text)
		frame_github.grid(column=0, row=5, pady=(10, 0), sticky=E)

		ttk.Label(
			frame_github,
			compound="image",
			image=self.cmc.get_image("images/logo-github.png"),
		).grid(column=0, row=0, rowspan=2)

		add_separator(frame_github, VERTICAL, 1, 0, 2)

		ttk.Button(
			frame_github,
			text="Open Link",
			padding=0,
			width=12,
			command=lambda: webbrowser.open(GITHUB_LINK),
		).grid(column=2, row=0, padx=0, pady=5)

		button_github_copy = ttk.Button(frame_github, text="Copy Link", padding=0, width=12)
		button_github_copy.configure(command=lambda: copy_text_button(button_github_copy, GITHUB_LINK))
		button_github_copy.grid(column=2, row=1, padx=0, pady=5)
