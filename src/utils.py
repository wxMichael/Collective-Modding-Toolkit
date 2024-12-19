import io
import os
import struct
import sys
import winreg
import zlib
from ctypes import WinDLL, byref, c_int, create_unicode_buffer, sizeof, windll, wintypes
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import Literal, overload

import requests
import win32api
from packaging.version import InvalidVersion, Version
from psutil import Process

import sv_ttk
from enums import CSIDL
from globals import APP_VERSION, COLOR_DEFAULT, FONT, FONT_SMALL, NEXUS_LINK
from helpers import DLLInfo
from mod_manager_info import ModManagerInfo

DONT_RESOLVE_DLL_REFERENCES = 0x00000001
HTTP_OK = 200
KEY_CTRL = 12

win11_24h2 = sys.getwindowsversion().build >= 26100


def is_file(path: Path) -> bool:
	if not win11_24h2:
		return path.is_file()

	try:
		with path.open():
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
	except (NotADirectoryError, FileNotFoundError):
		return False
	return True


def exists(path: Path) -> bool:
	if not win11_24h2:
		return path.exists()

	# Files
	try:
		with path.open():
			return True
	except FileNotFoundError:
		return False
	except PermissionError:
		# Probably a folder, check below
		pass

	# Folders
	try:
		_ = next(path.iterdir(), None)
	except (PermissionError, NotADirectoryError):
		# PermissionError: Actual folder but no permission
		# NotADirectoryError: Was a file with actual PermissionError
		pass
	except OSError:
		return False
	return True


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

	for _ in range(4):
		if proc is None:
			break

		with proc.oneshot():
			if proc.name() in managers:
				manager_path = Path(proc.exe())
				manager = "Mod Organizer" if proc.name() == "ModOrganizer.exe" else "Vortex"
				manager_version = Version(".".join(str(n) for n in get_file_version(manager_path)[:3]))
				return ModManagerInfo(manager, manager_path, manager_version)
			proc = proc.parent()
	return None


def get_asset_path(relative_path: str) -> Path:
	# PyInstaller EXEs extract to a temp folder and store the path in sys._MEIPASS
	base_path = Path(str(getattr(sys, "_MEIPASS", False) or "."))
	return base_path / "assets" / relative_path


def block_text_input(event: "Event[Text]") -> str | None:
	# Block all input except CTRL+A / CTRL+C
	if event.state == KEY_CTRL and event.keysym in "AC":
		return None
	return "break"


def get_file_version(path: Path) -> tuple[int, int, int, int]:
	info = win32api.GetFileVersionInfo(str(path), "\\")
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


def parse_dll(file_path: Path) -> DLLInfo | None:
	try:
		dll = WinDLL(str(file_path), winmode=DONT_RESOLVE_DLL_REFERENCES)
		dll_info: DLLInfo = {
			"IsF4SE": hasattr(dll, "F4SEPlugin_Load"),
			"SupportsOG": hasattr(dll, "F4SEPlugin_Query"),
			"SupportsNG": hasattr(dll, "F4SEPlugin_Version"),
		}
	except OSError:
		return None
	return dll_info


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
		separator.grid(column=column, row=row, columnspan=span, padx=10, pady=10, ipady=1, sticky=EW)
	else:
		separator.grid(column=column, row=row, rowspan=span, padx=10, pady=10, ipadx=1, sticky=NS)


def set_titlebar_style(window: Misc) -> None:
	window.update()
	hwnd = windll.user32.GetParent(window.winfo_id())
	windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(c_int(1)), sizeof(c_int))
	windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), sizeof(c_int))


def set_theme(win: Tk) -> None:
	set_titlebar_style(win)
	sv_ttk.apply_dark_theme()
	style = ttk.Style(win)

	# Remove blue dotted line from focused tab
	# fmt: off
	style.layout(
		"Tab", [("Notebook.tab", {
			"sticky": NSEW,
			"children": [(
				"Notebook.padding", {
					"side": TOP,
					"sticky": NSEW,
					"children": [("Notebook.label", {
						"side": TOP,
						"sticky": "",
					})],
				},
			)]},
		)],
	)
	# fmt: on
	# style.configure("TNotebook.Tab", padding=padding)
	style.configure("Tab", font=FONT, foreground=COLOR_DEFAULT)
	style.configure("TButton", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("TCheckbutton", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("TLabelframe.Label", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("Treeview", font=FONT_SMALL, foreground=COLOR_DEFAULT)
	style.configure("Heading", font=FONT_SMALL, foreground=COLOR_DEFAULT)


def check_for_update_nexus() -> str | None:
	try:
		response = requests.get(NEXUS_LINK, timeout=10, stream=True)
		if response.status_code == HTTP_OK:
			use_next = False
			version_line = None
			for line in response.iter_lines(decode_unicode=True):
				if use_next:
					version_line = str(line).rsplit('"', 2)
					response.close()
					break

				if line.startswith('<meta property="twitter:label1" content="Version"'):
					use_next = True
					continue

			if not version_line:
				return None

			latest_version = version_line[1]
			if Version(latest_version) > Version(str(APP_VERSION)):
				return latest_version
	except (requests.RequestException, InvalidVersion, IndexError):
		pass
	return None


def check_for_update_github() -> str | None:
	url = "https://api.github.com/repos/wxMichael/Collective-Modding-Toolkit/releases/latest"
	headers = {
		"Accept": "application/vnd.github+json",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	try:
		response = requests.get(url, headers=headers, timeout=10)
	except requests.RequestException:
		return None

	if response.status_code == HTTP_OK:
		try:
			release_data = response.json()
			latest_version = str(release_data["tag_name"])
			if Version(latest_version) > Version(str(APP_VERSION)):
				return latest_version
		except (requests.JSONDecodeError, InvalidVersion):
			pass
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
