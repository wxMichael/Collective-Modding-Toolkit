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


import logging
from tkinter import *
from typing import TYPE_CHECKING

from enums import SolutionType
from globals import *
from helpers import ProblemInfo, SimpleProblemInfo
from modal_window import AboutWindow
from utils import read_text_encoded

if TYPE_CHECKING:
	import tabs

logger = logging.getLogger(__name__)


class AutoFixResult:
	def __init__(self, *, success: bool, details: str) -> None:
		self.success = success
		self.details = details


def autofix_complex_sorter(problem_info: ProblemInfo | SimpleProblemInfo) -> AutoFixResult:
	if isinstance(problem_info, SimpleProblemInfo):
		return AutoFixResult(
			success=False,
			details="Unsupported Problem Type",
		)

	try:
		ini_text, ini_encoding = read_text_encoded(problem_info.path)
		ini_text = ini_text.replace("\r\n", "\n")
		while "\n\n\n" in str(ini_text):
			ini_text = ini_text.replace("\n\n", "\n")
		ini_lines = ini_text.splitlines()
	except FileNotFoundError:
		logger.exception("Auto-Fix : %s : Failed", problem_info.path)
		return AutoFixResult(
			success=False,
			details=f"File Not Found: {problem_info.path}",
		)
	except PermissionError:
		logger.exception("Auto-Fix : %s : Failed", problem_info.path)
		return AutoFixResult(
			success=False,
			details=f"File Access Denied: {problem_info.path}",
		)
	except OSError:
		logger.exception("Auto-Fix : %s : Failed", problem_info.path)
		return AutoFixResult(
			success=False,
			details=f"OSError: {problem_info.path}",
		)

	lines_fixed = 0
	for i, ini_line in enumerate(ini_lines):
		if ini_line.startswith(";"):
			continue

		if 'FindNode OBTS(FindNode "Addon Index"' in ini_line or "FindNode OBTS(FindNode 'Addon Index'" in ini_line:
			ini_lines[i] = ini_line.replace(
				'FindNode OBTS(FindNode "Addon Index"',
				'FindNode OBTS(FindNode "Parent Combination Index"',
			).replace(
				"FindNode OBTS(FindNode 'Addon Index'",
				"FindNode OBTS(FindNode 'Parent Combination Index'",
			)
			lines_fixed += 1
			logger.info(
				'Auto-Fix : %s : Line %s : Updated "Addon Index" to "Parent Combination Index"',
				problem_info.path.name,
				i + 1,
			)

	if lines_fixed:
		try:
			problem_info.path.write_text("\n".join(ini_lines) + "\n", ini_encoding)
		except PermissionError:
			logger.exception("Auto-Fix : %s : Failed", problem_info.path.name)
			result = AutoFixResult(
				success=False,
				details=f"File Access Denied: {problem_info.path}",
			)
		except OSError:
			logger.exception("Auto-Fix : %s : Failed", problem_info.path.name)
			result = AutoFixResult(
				success=False,
				details=f"OSError: {problem_info.path}",
			)
		else:
			logger.info("Auto-Fix : %s : %s Lines Fixed", problem_info.path.name, lines_fixed)
			result = AutoFixResult(
				success=True,
				details=f'All references to "Addon Index" updated to "Parent Combination Index".\nINI Lines Fixed: {lines_fixed}',
			)
		return result

	logger.error("Auto-Fix : %s : No fixes were needed.", problem_info.path.name)
	return AutoFixResult(
		success=True,
		details="No fixes were needed.",
	)


AUTO_FIXES = {
	SolutionType.ComplexSorterFix: autofix_complex_sorter,
}


def do_autofix(results_pane: "tabs.ResultDetailsPane", selection: str) -> None:
	if results_pane.problem_info.autofix_result is None:
		if TYPE_CHECKING:
			assert isinstance(results_pane.problem_info.solution, SolutionType)
			assert results_pane.button_autofix is not None
		solution_func = AUTO_FIXES[results_pane.problem_info.solution]
		results_pane.button_autofix.configure(text="Fixing...", state=DISABLED)
		logger.info("Auto-Fix : Running %s", solution_func.__name__)
		results_pane.problem_info.autofix_result = solution_func(results_pane.problem_info)
		if results_pane.problem_info.autofix_result.success:
			results_pane.button_autofix.configure(text="Fixed!", style="TButton", state=NORMAL)
			results_pane.scanner_tab.tree_results.item(
				selection,
				image=results_pane.scanner_tab.cmc.get_image("images/check-20.png"),
			)
		else:
			results_pane.button_autofix.configure(text="Fix Failed", style="TButton", state=NORMAL)

	AboutWindow(
		results_pane.scanner_tab.cmc.root,
		results_pane.scanner_tab.cmc,
		500,
		300,
		"Auto-Fix Results",
		results_pane.problem_info.autofix_result.details,
	)
