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


import ctypes
import logging
import os
import struct
import sys
import winreg
import zlib
from ctypes import byref, c_int, create_unicode_buffer, sizeof, windll, wintypes
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import TYPE_CHECKING, ClassVar, Literal, overload

import chardet
import requests
import sv_ttk
import win32api
from packaging.version import InvalidVersion, Version
from psutil import Process
from tktooltip import ToolTip  # type: ignore[reportMissingTypeStubs]

from globals import APP_VERSION, COLOR_DEFAULT, FONT, FONT_SMALL, NEXUS_LINK, scale, set_ui_scale
from mod_manager_info import ModManagerInfo

if TYPE_CHECKING:
	import io
	from collections.abc import Generator, Sequence
	from ctypes import _CDataType  # pyright: ignore[reportPrivateUsage]

	from enums import CSIDL
	# from helpers import DLLInfo

logger = logging.getLogger(__name__)

DONT_RESOLVE_DLL_REFERENCES = 0x00000001
HTTP_OK = 200
STATE_CONTROL_MASK = 0x0004

win11_24h2 = sys.getwindowsversion().build >= 26100

type Fields = Sequence[tuple[str, type[_CDataType]] | tuple[str, type[_CDataType], int]]


class F4SEPluginVersionData(ctypes.Structure):
	_fields_: ClassVar[Fields] = [
		("dataVersion", ctypes.c_uint32),
		("pluginVersion", ctypes.c_uint32),
		("name", ctypes.c_char * 256),
		("author", ctypes.c_char * 256),
		("addressIndependence", ctypes.c_uint32),
		("structureIndependence", ctypes.c_uint32),
		("compatibleVersions", ctypes.c_uint32 * 16),
		("seVersionRequired", ctypes.c_uint32),
		("reservedNonBreaking", ctypes.c_uint32),
		("reservedBreaking", ctypes.c_uint32),
		("reserved", ctypes.c_uint8 * 512),
	]


def rglob(path: Path, ext: str) -> Generator[Path]:
	if not win11_24h2:
		yield from path.rglob(f"*.{ext}")
		return

	ext = ext.lower()
	for root, _, files in path.walk():
		for file in files:
			if file.lower().endswith(f".{ext}"):
				yield root / file


def is_file(path: Path) -> bool:
	if not win11_24h2:
		return path.is_file()

	try:
		with path.open(encoding="utf-8"):
			pass
	except FileNotFoundError:
		return False
	except PermissionError:
		# Probably a folder
		try:
			_ = next(path.iterdir(), None)
		except NotADirectoryError:
			# Was a file with actual PermissionError
			return True
		except OSError:
			pass
		return False
	return True


def is_dir(path: Path) -> bool:
	if not win11_24h2:
		return path.is_dir()

	try:
		_ = next(path.iterdir(), None)
	except NotADirectoryError, FileNotFoundError:
		return False
	return True


def exists(path: Path) -> bool:
	if not win11_24h2:
		return path.exists()

	# Files
	try:
		with path.open(encoding="utf-8"):
			return True
	except FileNotFoundError:
		return False
	except PermissionError:
		# Probably a folder, check below
		pass

	# Folders
	try:
		_ = next(path.iterdir(), None)
	except PermissionError, NotADirectoryError:
		# PermissionError: Actual folder but no permission
		# NotADirectoryError: Was a file with actual PermissionError
		pass
	except OSError:
		return False
	return True


def read_text_encoded(file_path: Path) -> tuple[str, str]:
	file_bytes = file_path.read_bytes()
	encoding = chardet.detect(file_bytes)["encoding"] or "utf-8"
	return file_bytes.decode(encoding), encoding


def enable_dpi_awareness() -> None:
	try:
		windll.shcore.SetProcessDpiAwareness(1)  # System DPI aware
	except AttributeError, OSError:
		try:
			windll.user32.SetProcessDPIAware()
		except AttributeError, OSError:
			logger.debug("Could not enable DPI awareness")


def apply_dpi_scaling(root: Tk) -> None:
	dpi = root.winfo_fpixels("1i")
	root.tk.call("tk", "scaling", dpi / 72)
	set_ui_scale(dpi / 96)


def load_font(font_path: str) -> None:
	# https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-addfontresourceexw
	# FR_PRIVATE = 0x10
	# FR_NOT_ENUM = 0x20
	buffer = create_unicode_buffer(font_path)
	windll.gdi32.AddFontResourceExW(byref(buffer), 0x10, 0)


def get_environment_path(location: CSIDL) -> Path:
	buf = create_unicode_buffer(wintypes.MAX_PATH)
	windll.shell32.SHGetFolderPathW(None, location, None, 0, buf)
	path = Path(buf.value)
	if not is_dir(path):
		msg = f"Folder does not exist:\n{path}"
		raise FileNotFoundError(msg)
	return path


def is_fo4_dir(path: Path) -> bool:
	return is_dir(path) and is_file(path / "Fallout4.exe")


def find_mod_manager() -> ModManagerInfo | None:
	pid = os.getppid()
	proc: Process | None = Process(pid)

	managers = {"ModOrganizer.exe", "Vortex.exe"}
	manager = None

	for _ in range(8):
		if proc is None:
			break

		with proc.oneshot():
			if proc.name() in managers:
				manager_path = Path(proc.exe())
				manager = "Mod Organizer" if proc.name() == "ModOrganizer.exe" else "Vortex"
				ver = get_file_version(manager_path)
				manager_version = Version(".".join(str(n) for n in ver[:3])) if ver else Version("0.0.0")
				return ModManagerInfo(manager, manager_path, manager_version)
			proc = proc.parent()
	return None


def get_asset_path(relative_path: str) -> Path:
	# PyInstaller EXEs extract to a temp folder and store the path in sys._MEIPASS
	base_path = Path(str(getattr(sys, "_MEIPASS", False) or "."))
	return base_path / "assets" / relative_path


def block_text_input(event: Event[Text]) -> str | None:
	# Block all input except CTRL+A / CTRL+C
	if int(event.state) & STATE_CONTROL_MASK and event.keysym.lower() in {"a", "c"}:
		return None
	return "break"


def get_file_version(path: Path) -> tuple[int, int, int, int] | None:
	try:
		info = win32api.GetFileVersionInfo(str(path), "\\")
	except:
		return None
	ms = info["FileVersionMS"]
	ls = info["FileVersionLS"]
	return (
		win32api.HIWORD(ms),
		win32api.LOWORD(ms),
		win32api.HIWORD(ls),
		win32api.LOWORD(ls),
	)


def get_crc32(file_path: Path, chunk_size: int = 65536, max_chunks: int | None = None, *, skip_ba2_header: bool = False) -> str:
	with file_path.open("rb") as f:
		checksum = 0
		chunks = 0
		if skip_ba2_header:
			f.seek(12)
		while chunk := f.read(chunk_size):
			checksum = zlib.crc32(chunk, checksum)
			if max_chunks is not None:
				chunks += 1
				if chunks >= max_chunks:
					break
	return f"{checksum:08X}"


## DEPRECIATED: Use f4se_utils.py!
## Saved for legacy use, in case old one is screwed up or something
# def parse_dll(file_path: Path) -> DLLInfo:  # this shit fucked up
# 	dll = ctypes.WinDLL(str(file_path), winmode=DONT_RESOLVE_DLL_REFERENCES)
# 	dll_info: DLLInfo = {
# 		"IsF4SE": hasattr(dll, "F4SEPlugin_Load") or hasattr(dll, "F4SEPlugin_Preload"),
# 		"SupportsOG": hasattr(dll, "F4SEPlugin_Query"),
# 		"SupportsNGAE": hasattr(dll, "F4SEPlugin_Version"),
# 		"SupportsNG": None,
# 		"SupportsAE": None,
# 		"AddrIndependentNG": None,
# 		"AddrIndependentAE": None,
# 		"StructIndependentNG": None,
# 		"StructIndependentAE": None,
# 		"SupportsCurrent": None,
# 	}

# 	if dll_info["SupportsNGAE"]:
# 		sym = ctypes.cast(
# 			dll.F4SEPlugin_Version,
# 			POINTER(F4SEPluginVersionData),
# 		)
# 		v = sym.contents

# 		dll_info["AddrIndependent"] = bool(0b110 & v.addressIndependence)
# 		dll_info["StructIndependent"] = bool(0b110 & v.structureIndependence)

# 		if 0x010A3D40 in v.compatibleVersions or 0x010A3D80 in v.compatibleVersions:
# 			dll_info["SupportsNG"] = True

# 		if any(n > 0x010B0890 for n in v.compatibleVersions):
# 			dll_info["SupportsAE"] = True

# 		# dll_info["SupportsCurrent"] = v.IsSupportVersion(version)

# 	return dll_info


def ver_to_str(version: str | tuple[int, int, int, int]) -> str:
	if isinstance(version, str):
		return version

	return ".".join(map(str, version))


def get_registry_value(key: int, subkey: str, value_name: str) -> str | None:
	try:
		with winreg.OpenKey(key, subkey) as reg_handle:
			value, value_type = winreg.QueryValueEx(reg_handle, value_name)

		if value and value_type == winreg.REG_SZ and isinstance(value, str):
			return value

	except OSError:
		pass

	return None


def add_tooltip(widget: Misc, msg: str) -> None:
	def on_first_enter(event: Event[Misc]) -> None:
		widget.unbind("<Enter>", func_id)
		tip = ToolTip(widget, msg)  # ty: ignore[invalid-argument-type]
		tip.on_enter(event)

	func_id = widget.bind("<Enter>", on_first_enter, "+")


def copy_text(widget: ttk.Widget, text: str) -> None:
	widget.clipboard_clear()
	widget.clipboard_append(text)


def copy_text_button(button: ttk.Button, text: str) -> None:
	button.master.clipboard_clear()
	button.master.clipboard_append(text)
	original_text = button.cget("text")
	button.config(text="Copied!", state=DISABLED)
	button.master.after(3000, lambda: button.config(text=original_text, state=NORMAL))


def add_separator(master: Misc, orient: Literal["horizontal", "vertical"], column: int, row: int, span: int) -> None:
	separator = ttk.Separator(master, orient=orient)
	if orient == HORIZONTAL:
		separator.grid(column=column, row=row, columnspan=span, padx=scale(10), pady=scale(10), ipady=scale(1), sticky=EW)
	else:
		separator.grid(column=column, row=row, rowspan=span, padx=scale(10), pady=scale(10), ipadx=scale(1), sticky=NS)


def set_titlebar_style(window: Misc) -> None:
	window.update()
	hwnd = windll.user32.GetParent(window.winfo_id())
	windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(c_int(1)), sizeof(c_int))
	windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), sizeof(c_int))


def apply_green_accent(win: Tk) -> None:
	"""Recolor sv_ttk's blue accent to green."""
	sprite_sheet = get_asset_path("sv_ttk/spritesheet_dark_green.png").absolute().as_posix()
	win.tk.eval(
		f"""
		set ns ttk::theme::sv_dark
		array set ${{ns}}::colors {{-selbg "#05b62e" -accent "#57ff64"}}
		image create photo sv_green_sheet -file {{{sprite_sheet}}} -format png
		foreach {{name x y w h}} $::spriteinfo {{
			[set ${{ns}}::I($name)] copy sv_green_sheet -from $x $y [expr {{$x+$w}}] [expr {{$y+$h}}] -compositingrule set
		}}
		ttk::style map Accent.TButton -foreground [list pressed "#252525" disabled "#a5a5a5"]
		ttk::style map Toggle.TButton -foreground [list {{selected disabled}} "#a5a5a5" {{selected pressed}} "#d0d0d0" selected "#000000" pressed "#252525" disabled "#7a7a7a"]
		rename configure_colors sv_configure_colors
		proc configure_colors {{}} {{
			if {{![info exists ::sv_colors_configured]}} {{
				set ::sv_colors_configured 1
				sv_configure_colors
			}}
		}}
		configure_colors
		"""
	)


def set_theme(win: Tk) -> None:
	set_titlebar_style(win)
	sv_ttk.set_theme("dark", win)
	apply_green_accent(win)
	style = ttk.Style(win)

	style.layout("TNotebook", [("Notebook.background", {"children": [("TNotebook.Tab", {"sticky": NSEW})]})])
	style.configure("TNotebook", background="#2f2f2f")

	# Remove blue dotted line from focused tab
	# fmt: off
	style.layout(
		"Tab", [("Notebook.tab", {
			"sticky": NSEW,
			"children": [("Notebook.padding", {
				"side": TOP,
				"sticky": NSEW,
				"children": [("Notebook.label", {
					"side": TOP,
					"sticky": "",
				})],
			})],
		})],
	)
	# fmt: on
	# style.configure("TNotebook.Tab", padding=padding)
	style.configure("Tab", font=FONT, foreground=COLOR_DEFAULT)
	style.configure("TButton", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("TCheckbutton", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("TRadiobutton", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("TLabelframe.Label", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("Treeview", font=FONT_SMALL, foreground=COLOR_DEFAULT, rowheight=scale(25))
	style.configure("Heading", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("Update.TFrame", background="pale green")


def check_for_update_nexus() -> str | None:
	logger.debug("Update Check : Nexus Mods")
	try:  # ruff: ignore[too-many-statements-in-try-clause]
		response = requests.get(NEXUS_LINK, timeout=5, stream=True)
		if response.status_code == HTTP_OK:
			use_next = False
			version_line = None
			for line in response.iter_lines(decode_unicode=True):
				if TYPE_CHECKING:
					assert isinstance(line, str)
				if use_next:
					version_line = line.rsplit('"', 2)
					response.close()
					break

				if line.lstrip().startswith('<meta property="twitter:label1" content="Version"'):
					use_next = True
					continue

			if not version_line:
				logger.error("Update Check : Nexus Mods : Failed")
				return None

			latest_version = version_line[1]
			if Version(latest_version) > Version(str(APP_VERSION)):
				logger.info("Update Check : Nexus Mods : Update Available : v%s", latest_version)  # TODO: test variable
				return latest_version
	except requests.RequestException, InvalidVersion, IndexError:
		logger.exception("Update Check : Nexus Mods : Failed")  # TODO: Reasons
		return None

	logger.debug("Update Check : Nexus Mods : No Updates")
	return None


def check_for_update_github() -> str | None:
	logger.debug("Update Check : GitHub")
	url = "https://api.github.com/repos/wxMichael/Collective-Modding-Toolkit/releases/latest"
	headers = {
		"Accept": "application/vnd.github+json",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	try:
		response = requests.get(url, headers=headers, timeout=5)
	except requests.RequestException:
		logger.exception("Update Check : GitHub : Failed")
		return None

	if response.status_code == HTTP_OK:
		try:
			release_data = response.json()
			latest_version = str(release_data["tag_name"])
			if Version(latest_version) > Version(str(APP_VERSION)):
				logger.info("Update Check : GitHub : Update Available : v%s", latest_version)
				return latest_version
		except requests.JSONDecodeError, InvalidVersion:
			logger.exception("Update Check : GitHub : Failed")
			return None

	logger.debug("Update Check : GitHub : No Updates")
	return None


@overload
def read_uint(source: io.BufferedIOBase) -> int: ...
@overload
def read_uint(source: io.BufferedIOBase, count: int) -> tuple[int, ...]: ...
def read_uint(source: io.BufferedIOBase, count: int = 1) -> int | tuple[int, ...]:
	if count < 1:
		raise ValueError
	uints: tuple[int, ...] = struct.unpack(f"<{count}I", source.read(count * 4))
	if len(uints) != count:
		raise SyntaxError
	if count == 1:
		return uints[0]
	return uints
