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

from globals import *
from modal_window import AboutWindow

if TYPE_CHECKING:
	from collections.abc import Callable

	import tabs
	from enums import SolutionType

logger = logging.getLogger(__name__)


class AutoFixResult:  # ruff: ignore[class-as-data-structure]
	def __init__(self, *, success: bool, details: str) -> None:
		self.success = success
		self.details = details


AUTO_FIXES: dict[SolutionType, Callable[..., AutoFixResult]] = {}


def do_autofix(results_pane: tabs.ResultDetailsPane, selection: str) -> None:
	if results_pane.problem_info.autofix_result is None:
		if TYPE_CHECKING:
			assert isinstance(results_pane.problem_info.solution, SolutionType)
			assert results_pane.button_autofix is not None
		solution_func = AUTO_FIXES[results_pane.problem_info.solution]
		results_pane.button_autofix.configure(text="Fixing...", state=DISABLED)
		logger.info("Auto-Fix : Running %s", getattr(solution_func, "__name__", solution_func))
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
