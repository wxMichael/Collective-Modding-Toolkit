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
import sys
from datetime import datetime
from tkinter import Tk

from app_settings import AppSettings
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
logger.info("%s", datetime.now().strftime("%Y-%m-%d %H:%M"))

settings = AppSettings()
logger.setLevel(settings.dict["log_level"])

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
