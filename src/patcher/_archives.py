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
		return "About Archives"

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
		if self.desired_version.get() == ArchiveVersion.OG:
			return self.cmc.game.archives_ng
		return self.cmc.game.archives_og

	def build_gui_secondary(self, frame_top: ttk.Frame) -> None:
		frame_radio = ttk.Labelframe(frame_top, text="Desired Version")
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

		self.label_filter = ttk.Label(frame_top, text=PATCHER_FILTER_NG, foreground=COLOR_NEUTRAL_2)
		self.label_filter.pack(side=LEFT, padx=10, fill=Y)

	def patch_files(self) -> None:
		patched = 0
		failed = 0

		if self.desired_version.get() == ArchiveVersion.OG:
			archives_from = self.cmc.game.archives_ng
			old_bytes = [b"\x07", b"\x08"]
			new_bytes = b"\x01"
		else:
			archives_from = self.cmc.game.archives_og
			old_bytes = [b"\x01"]
			new_bytes = b"\x08"

		if not archives_from:
			self.logger.log_message(LogType.Info, "Nothing to do!")
			return

		for ba2_file in list(archives_from):
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
