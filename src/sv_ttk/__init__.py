import tkinter as tk
from pathlib import Path
from tkinter import ttk


def apply_dark_theme(root: tk.Tk | None = None) -> None:
	style = ttk.Style(master=root)
	if not isinstance(style.master, tk.Tk):
		msg = "root must be a `tkinter.Tk` instance!"
		raise TypeError(msg)

	if not hasattr(style.master, "_sv_ttk_loaded"):
		setattr(style.master, "_sv_ttk_loaded", True)  # noqa: B010
		style.tk.call("source", str(Path(__file__).with_name("sv.tcl").absolute()))

	style.theme_use("sun-valley-dark")
