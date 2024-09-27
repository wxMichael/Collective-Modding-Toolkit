import os
import sys
import winreg
import zlib
from ctypes import WinDLL, byref, c_int, sizeof, windll
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from typing import Literal

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


def find_game_paths() -> tuple[Path, Path | None, Path | None]:
	game_path_as_path = Path.cwd()
	if not is_fo4_dir(game_path_as_path):
		game_path = get_registry_value(
			winreg.HKEY_LOCAL_MACHINE,
			R"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4",
			"Installed Path",
		) or get_registry_value(
			winreg.HKEY_LOCAL_MACHINE,
			R"SOFTWARE\WOW6432Node\GOG.com\Games\1998527297",
			"path",
		)

		assert isinstance(game_path, str) or game_path is None

		if isinstance(game_path, str):
			game_path_as_path = Path(game_path)
			if not is_fo4_dir(game_path_as_path):
				game_path = None

		if game_path is None:
			game_path = filedialog.askopenfilename(
				title="Select Fallout4.exe",
				filetypes=[("Fallout 4", "Fallout4.exe")],
			)

		if not game_path:
			# None, or Empty string if filedialog cancelled
			messagebox.showerror(  # type: ignore
				"Game not found",
				"A Fallout 4 installation could not be found.",
			)
			sys.exit()

		assert isinstance(game_path, str)

		game_path_as_path = Path(game_path)
		if game_path_as_path.is_file():
			game_path_as_path = game_path_as_path.parent

	data_path: Path | None = game_path_as_path / "Data"
	assert data_path is not None
	if data_path.is_dir():
		f4se_path: Path | None = data_path / "F4SE/Plugins"
		assert f4se_path is not None
		if not f4se_path.is_dir():
			f4se_path = None
	else:
		data_path = None
		f4se_path = None

	return (game_path_as_path, data_path, f4se_path)


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


def is_fo4_dir(path: Path) -> bool:
	return path.is_dir() and (path / "Fallout4.exe").is_file()


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
