import stat
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import final

from enums import ArchiveVersion, LogType, Magic
from globals import *
from helpers import CMCheckerInterface

from ._base import PatcherBase


@final
class ArchivePatcher(PatcherBase):
	def __init__(self, parent: Wm, cmc: CMCheckerInterface) -> None:
		self.desired_version = IntVar(value=ArchiveVersion.OG)
		super().__init__(parent, cmc, "Archive Patcher")

	@property
	def about_title(self) -> str:
		return ABOUT_ARCHIVES_TITLE

	@property
	def about_text(self) -> str:
		return ABOUT_ARCHIVES

	@property
	def filter_text(self) -> str:
		if self.desired_version.get() == ArchiveVersion.OG:
			return PATCHER_FILTER_NG
		return PATCHER_FILTER_OG

	@property
	def files_to_patch(self) -> set[Path]:
		files = self.cmc.game.archives_ng if self.desired_version.get() == ArchiveVersion.OG else self.cmc.game.archives_og
		if not self.name_filter:
			return files
		return {file for file in files if self.name_filter in file.name.casefold()}

	def build_gui_secondary(self) -> None:
		frame_radio = ttk.Labelframe(self.frame_top, text="Desired Version")
		frame_radio.pack(side=LEFT, ipadx=5, ipady=5, padx=5, pady=5)

		radio_og = ttk.Radiobutton(
			frame_radio,
			text="v1 (OG)",
			variable=self.desired_version,
			value=ArchiveVersion.OG,
			command=self.on_radio_change,
		)
		radio_ng = ttk.Radiobutton(
			frame_radio,
			text="v8 (NG)",
			variable=self.desired_version,
			value=ArchiveVersion.NG,
			command=self.on_radio_change,
		)
		radio_og.grid(column=0, row=0, padx=5)
		radio_ng.grid(column=1, row=0, padx=5)

		self.label_filter = ttk.Label(self.frame_top, text=self.filter_text, foreground=COLOR_NEUTRAL_2)
		self.label_filter.pack(side=LEFT, padx=10, fill=Y)

		ttk.Label(
			self.frame_middle,
			text="Name Filter:",
			foreground=COLOR_DEFAULT,
		).grid(column=0, row=0, sticky=NSEW, padx=5, pady=5)
		self.text_filter = ttk.Entry(self.frame_middle)
		self.text_filter.grid(column=1, row=0, sticky=NSEW)

		def on_key_release(event: "Event[ttk.Entry]") -> None:
			text = event.widget.get()
			self.name_filter = event.widget.get().casefold() if text else None
			self.logger.clear()
			self.populate_tree()

		self.text_filter.bind("<KeyRelease>", on_key_release)

	def patch_files(self) -> None:
		patched = 0
		failed = 0

		if self.desired_version.get() == ArchiveVersion.OG:
			old_bytes = [b"\x07", b"\x08"]
			new_bytes = b"\x01"
		else:
			old_bytes = [b"\x01"]
			new_bytes = b"\x08"

		file_to_patch = list(self.files_to_patch)

		if not file_to_patch:
			self.logger.log_message(LogType.Info, "Nothing to do!")
			return

		for ba2_file in list(self.files_to_patch):
			try:
				if ba2_file.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
					ba2_file.chmod(stat.S_IWRITE)
				with ba2_file.open("r+b") as f:
					if f.read(4) != Magic.BTDX:
						self.logger.log_message(LogType.Bad, f"Unrecognized format: {ba2_file.name}")
						failed += 1
						continue

					f.seek(4)
					current_bytes = f.read(1)
					if current_bytes == new_bytes:
						self.logger.log_message(LogType.Bad, f"Skipping already-patched archive: {ba2_file.name}")
						failed += 1
						continue

					if current_bytes not in old_bytes:
						self.logger.log_message(
							LogType.Bad,
							f"Unrecognized version [{current_bytes.hex()}]: {ba2_file.name}",
						)
						failed += 1
						continue

					f.seek(4)
					f.write(new_bytes)

			except OSError:
				self.logger.log_message(LogType.Bad, f"Failed patching: {ba2_file.name}")
				failed += 1

			else:
				self.logger.log_message(LogType.Good, f"Patched to v{self.desired_version.get()}: {ba2_file.name}")
				patched += 1

		self.logger.log_message(LogType.Info, f"Patching complete. {patched} Successful, {failed} Failed.")

	def on_radio_change(self) -> None:
		self.logger.clear()
		self.label_filter.configure(text=self.filter_text)
		self.populate_tree()
