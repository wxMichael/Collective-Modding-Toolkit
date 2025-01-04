import json
import logging
from pathlib import Path
from typing import Literal, TypedDict, get_args, get_origin

from utils import is_file

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path("settings.json")


class AppSettingsDict(TypedDict):
	log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
	update_source: Literal["nexus", "github", "both", "none"]
	scanner_OverviewIssues: bool
	scanner_Errors: bool
	scanner_WrongFormat: bool
	scanner_LoosePrevis: bool
	scanner_JunkFiles: bool
	scanner_ProblemOverrides: bool
	scanner_RaceSubgraphs: bool


DEFAULT_SETTINGS: AppSettingsDict = {
	"log_level": "INFO",
	"update_source": "nexus",
	"scanner_OverviewIssues": True,
	"scanner_Errors": True,
	"scanner_WrongFormat": True,
	"scanner_LoosePrevis": True,
	"scanner_JunkFiles": True,
	"scanner_ProblemOverrides": True,
	"scanner_RaceSubgraphs": True,
}


class AppSettings:
	def __init__(self) -> None:
		self.dict = DEFAULT_SETTINGS.copy()

		if not is_file(SETTINGS_PATH):
			logger.info("Settings : %s not found; using defaults.", SETTINGS_PATH.name)
			self.save()
			return

		resave = False
		try:
			json_content: AppSettingsDict = json.loads(SETTINGS_PATH.read_text("utf-8"))
			if not isinstance(json_content, dict):  # type: ignore[reportUnnecessaryIsInstance]
				# File doesn't contain a JSON Object
				raise ValueError  # noqa: TRY004
		except:
			logger.exception("Settings : Failed to load %s. Settings will be reset.", SETTINGS_PATH.name)
			resave = True
		else:
			new_settings = [k for k in self.dict if k not in json_content]
			if new_settings:
				logger.info("Settings : Adding new settings to JSON: %s", ", ".join(new_settings))
				resave = True

			for k, v in json_content.items():
				if k not in self.dict:
					logger.error("Settings : Unknown setting '%s' will be removed.", k)
					resave = True
					continue

				annotation = AppSettingsDict.__annotations__.get(k)
				if not annotation:
					logger.debug("Settings : '%s' has no set type", k)
					self.dict[k] = v
				elif get_origin(annotation) is Literal:
					if v in get_args(annotation):
						logger.debug("Settings : '%s' is correct type (%s)", k, type(v).__name__)
						self.dict[k] = v
					else:
						logger.error("Settings : '%s' has invalid value '%s'. Reset to '%s'", k, v, self.dict[k])  # type: ignore[reportUnknownArgumentType]
						resave = True
				elif type(v) is annotation:
					logger.debug("Settings : '%s' is correct type (%s)", k, type(v).__name__)
					self.dict[k] = v
				else:
					logger.error(
						"Settings : '%s' has invalid type (%s) '%s'. Reset to '%s'",
						k,
						type(v).__name__,
						v,
						self.dict[k],  # type: ignore[reportUnknownArgumentType]
					)
					resave = True

		if resave:
			self.save()

	def save(self) -> None:
		logger.debug("Settings : Saving %s", SETTINGS_PATH.name)
		try:
			with SETTINGS_PATH.open("w", encoding="utf-8") as f:
				json.dump(self.dict, f, indent="\t")
				f.write("\n")
		except:
			logger.exception("Settings : Failed to save %s", SETTINGS_PATH.name)
