import json
import logging
from collections import UserDict
from pathlib import Path
from typing import Any, Literal, TypedDict

from utils import is_file

logger = logging.getLogger(__name__)


class Settings(TypedDict):
	log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
	update_source: Literal["nexus", "github", "both", "none"]


DEFAULT_SETTINGS: Settings = {
	"log_level": "INFO",
	"update_source": "nexus",
}


class AppSettings(UserDict[str, Any]):
	def __init__(self) -> None:
		super().__init__(DEFAULT_SETTINGS)
		self._settings_path = Path("settings.json")
		resave = False
		if not is_file(self._settings_path):
			logger.debug("Settings : %s not found; using defaults.", self._settings_path.name)
			return

		try:
			json_content: Settings = json.loads(self._settings_path.read_text("utf-8"))
			if not isinstance(json_content, dict):  # type: ignore[reportUnnecessaryIsInstance]
				raise ValueError  # noqa: TRY004
		except:
			logger.exception("Settings : Failed to load %s. Settings will be reset.", self._settings_path.name)
			resave = True
		else:
			new_settings = [k for k in self if k not in json_content]
			if new_settings:
				logger.info("Settings : Adding new settings to JSON: %s", ", ".join(new_settings))
				resave = True

			for k, v in json_content.items():
				if k not in self:
					logger.error("Settings : Unknown setting '%s' will be removed.", k)
					resave = True
					continue

				annotation = Settings.__annotations__.get(k)
				if not annotation:
					logger.debug("Settings : '%s' has no set type", k)
					self[k] = v
				elif annotation.__class__.__name__ == "_LiteralGenericAlias":
					if v in annotation.__args__:
						logger.debug("Settings : '%s' is correct type (%s)", k, type(v).__name__)
						self[k] = v
					else:
						logger.error("Settings : '%s' has invalid value '%s'. Reset to '%s'", k, v, self[k])  # type: ignore[reportUnknownArgumentType]
						resave = True
				elif type(v) is annotation:
					logger.debug("Settings : '%s' is correct type (%s)", k, type(v).__name__)
					self[k] = v
				else:
					logger.error("Settings : '%s' has invalid type (%s) '%s'. Reset to '%s'", k, type(v).__name__, v, self[k])  # type: ignore[reportUnknownArgumentType]
					resave = True

		if resave:
			self.save()

	def save(self) -> None:
		logger.debug("Settings : Saving %s", self._settings_path.name)
		try:
			with self._settings_path.open("w", encoding="utf-8") as f:
				json.dump(self.data, f, indent="\t")
				f.write("\n")
		except:
			logger.exception("Settings : Failed to save %s", self._settings_path.name)
