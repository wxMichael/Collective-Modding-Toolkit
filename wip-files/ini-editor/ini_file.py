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


import string
from enum import Enum, auto
from pathlib import Path


class INIPart(Enum):
	Section = auto()
	Setting = auto()
	Value = auto()
	Comment = auto()
	Whitespace = auto()
	Assignment = auto()


class INIFile:
	def __init__(self, ini_path: Path) -> None:
		if not ini_path.is_file():
			raise FileNotFoundError(ini_path)
		self.ini_path = ini_path

		self.raw_content = ""
		self.lines: list[str] = []

		self.settings: dict[str, dict[str, tuple[str | None, int, int]]] = {}
		self.line_parts: list[list[tuple[INIPart, str | None]]] = []
		self.parse()


	def add_value(self, line_stripped: str, section: str | None, setting: str | None, value: str) -> None:
		whitespace = None
		if value[-1] in string.whitespace:
			for char_index, char in enumerate(reversed(value)):
				if char not in string.whitespace:
					whitespace = value[-char_index:]
					break

		v = value.strip() or None
		if not section:
			msg = f"Line {len(self.lines)}: Setting outside of sections:\n{line_stripped}"
			raise SyntaxError(msg)
		if not setting:
			msg = f"Line {len(self.lines)}: Value without setting name:\n{line_stripped}"
			raise SyntaxError(msg)
		self.line_parts[-1].append((INIPart.Value, v))
		self.settings[section][setting] = (v, len(self.line_parts) - 1, len(self.line_parts[-1]) - 1)
		if whitespace is not None:
			self.line_parts[-1].append((INIPart.Whitespace, whitespace))

	def parse(self) -> None:
		self.lines.clear()
		with self.ini_path.open() as ini_file:
			section: str | None = None
			setting: str | None = None
			ini_part: INIPart | None = None
			start_index = -1
			for line in ini_file:
				self.line_parts.append([])
				line_stripped = line.strip()
				self.lines.append(line_stripped)
				if not line:
					continue

				for index, token in enumerate(line_stripped):
					if ini_part == INIPart.Whitespace and token not in string.whitespace:
						self.line_parts[-1].append((INIPart.Whitespace, line_stripped[start_index : index]))
						ini_part = None
						start_index = -1

					if ini_part == INIPart.Value:
						if token == ";":
							self.add_value(line_stripped, section, setting, line_stripped[start_index:index])
							ini_part = None
							start_index = -1

						else:
							continue

					if ini_part is None:
						if token == "[":
							ini_part = INIPart.Section
							start_index = index
							continue
						if token == "]":
							msg = f"Line {len(self.lines)}: Unexpected closing brace:\n{line_stripped}"
							raise SyntaxError(msg)
						if token == ";":
							self.line_parts[-1].append((INIPart.Comment, line_stripped[index:]))
							ini_part = None
							start_index = -1
							break
						if token in string.whitespace:
							ini_part = INIPart.Whitespace
							start_index = index
							continue
						if token == "=":
							msg = f"Line {len(self.lines)}: Assignment without setting name:\n{line_stripped}"
							raise SyntaxError(msg)

						ini_part = INIPart.Setting
						start_index = index
						continue

					if ini_part == INIPart.Section:
						if token == "]":
							section = line_stripped[start_index : index + 1]
							if not section[1:-1].strip():
								msg = f"Line {len(self.lines)}: Empty section name:\n{line_stripped}"
								raise SyntaxError(msg)
							if section not in self.settings:
								self.settings[section] = {}
							self.line_parts[-1].append((INIPart.Section, section))
							ini_part = None
							start_index = -1
							continue
						if token == "[":
							msg = f"Line {len(self.lines)}: Bracket within section name:\n{line_stripped}"
							raise SyntaxError(msg)
						continue

					if ini_part == INIPart.Setting:
						if token == "=":
							setting = line_stripped[start_index : index]
							self.line_parts[-1].append((INIPart.Setting, setting))
							self.line_parts[-1].append((INIPart.Assignment, token))
							ini_part = INIPart.Value
							start_index = index + 1
							continue
						if token == ";":
							msg = f"Line {len(self.lines)}: Setting name without assignment:\n{line_stripped}"
							raise SyntaxError(msg)
						if token in {"[", "]"}:
							msg = f"Line {len(self.lines)}: Bracket within setting name:\n{line_stripped}"
							raise SyntaxError(msg)
						continue

				# End of line
				if ini_part == INIPart.Section:
					msg = f"Line {len(self.lines)}: Section without closing brace:\n{line_stripped}"
					raise SyntaxError(msg)
				if ini_part == INIPart.Setting:
					msg = f"Line {len(self.lines)}: Setting name without assignment:\n{line_stripped}"
					raise SyntaxError(msg)
				if ini_part == INIPart.Value:
					self.add_value(line_stripped, section, setting, line_stripped[start_index:])
					ini_part = None
					start_index = -1
					# continue
				if ini_part is None:
					self.line_parts[-1].append((INIPart.Whitespace, "\n"))
