import logging
import sys
from tkinter import Tk

from app_settings import AppSettings, Settings
from cm_checker import CMChecker
from globals import APP_TITLE, APP_VERSION
from helpers import StdErr
from utils import get_asset_path, load_font, set_theme

logging.basicConfig(
	filename="cm-toolkit.log",
	format="%(levelname)s : %(message)s",
	level=logging.INFO,
)
logger = logging.getLogger()
start_message = f"Starting {APP_TITLE} v{APP_VERSION}"
logger.info("-" * len(start_message))
logger.info("%s", start_message)

settings: Settings = AppSettings()  # type: ignore[assignment]
logger.setLevel(settings["log_level"])

load_font(str(get_asset_path("fonts/CascadiaMono.ttf")))
root = Tk()
root.wm_withdraw()
root.update_idletasks()

sys.stderr = StdErr(root)
CMChecker(root, settings)
set_theme(root)
root.update_idletasks()
root.wm_deiconify()
root.update_idletasks()
root.mainloop()
