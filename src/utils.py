import io
import os
import struct
import sys
import winreg
import zlib
from ctypes import WinDLL, byref, c_int, sizeof, windll
from pathlib import Path
from tkinter import *
from tkinter import ttk
from typing import Literal, overload

import requests
import sv_ttk
import win32api
from packaging.version import InvalidVersion, Version
from psutil import Process

from globals import APP_VERSION, NEXUS_LINK
from helpers import DLLInfo

DONT_RESOLVE_DLL_REFERENCES = 0x00000001
HTTP_OK = 200
KEY_CTRL = 12


def find_mod_manager() -> str | None:
	pid = os.getppid()
	proc: Process | None = Process(pid)

	managers = ("ModOrganizer.exe", "Vortex.exe")
	manager = None

	for _ in range(4):
		if proc is None:
			break

		if proc.name() in managers:
			manager = proc.name().rsplit(".")[0]
			if manager == "ModOrganizer":
				manager = "Mod Organizer"
			break

		proc = proc.parent()

	return manager


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


def get_crc32(
	file_path: Path,
	chunk_size: int = 65536,
	max_chunks: int | None = None,
	*,
	skip_ba2_header: bool = False,
) -> str:
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

	else:
		return dll_info


def ver_to_str(version: str | tuple[int, int, int, int]) -> str:
	if isinstance(version, str):
		return version

	return ".".join(map(str, version))


def get_registry_value(key: int, subkey: str, value_name: str) -> str | None:
	try:
		with winreg.OpenKey(key, subkey) as reg_handle:
			value, value_type = winreg.QueryValueEx(reg_handle, value_name)

		if value and value_type == winreg.REG_SZ:
			assert isinstance(value, str)
			return str(value)

	except OSError:
		pass

	return None


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
	sv_ttk.set_theme("dark")
	style = ttk.Style(win)

	# Remove blue dotted line from focused tab
	# fmt: off
	style.layout(
		"Tab", [( "Notebook.tab", {
			"sticky": NSEW,
			"children": [(
				"Notebook.padding", {
					"side": TOP,
					"sticky": NSEW,
					"children": [("Notebook.label", {"side": TOP, "sticky": ""})],
				},
			)]},
		)],
	)
	# fmt: on


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
		# "Authorization": "Bearer <TOKEN>",
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
