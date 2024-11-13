from tkinter import *
from tkinter import ttk

from enums import LogType
from globals import *
from utils import block_text_input


class Logger:
	def __init__(self, master: Misc) -> None:
		self._text = Text(master, wrap=WORD, height=8, font=("Cascadia Mono", 10))
		self._scroll_text_y = ttk.Scrollbar(
			master,
			command=self._text.yview,  # pyright: ignore[reportUnknownArgumentType]
			orient=VERTICAL,
		)

		self._emoji = {
			LogType.Bad: "❌ ",
			LogType.Good: "✅ ",
			LogType.Info: "💭 ",
		}

		self._text.grid(column=0, row=0, sticky=NSEW)
		self._scroll_text_y.grid(column=1, row=0, sticky=NS)

		self._text.tag_config(LogType.Good.value, foreground=COLOR_GOOD)
		self._text.tag_config(LogType.Bad.value, foreground=COLOR_BAD)
		self._text.tag_config(LogType.Info.value, foreground=COLOR_INFO)

		self._text.configure(yscrollcommand=self._scroll_text_y.set)
		self._text.bind("<Key>", block_text_input)

	def log_message(self, log_type: LogType, message: str) -> None:
		start_index = self._text.index(INSERT)
		self._text.insert(index=END, chars=f"{self._emoji[log_type]}{message}\n")
		current_line, current_column = start_index.split(".")
		end_index = f"{current_line}.{int(current_column) + len(self._emoji[log_type])}"
		self._text.tag_add(log_type.value, start_index, end_index)
		self._text.see(END)

	def clear(self) -> None:
		self._text.delete(1.0, END)
