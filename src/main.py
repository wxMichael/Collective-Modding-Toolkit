import sys
from tkinter import Tk

from cm_checker import CMChecker
from helpers import Stderr
from utils import get_asset_path, load_font, set_theme

load_font(str(get_asset_path("fonts/CascadiaMono.ttf")))
root = Tk()
root.wm_withdraw()
root.update_idletasks()

sys.stderr = Stderr(root)
CMChecker(root)
set_theme(root)
root.update_idletasks()
root.wm_deiconify()
root.update_idletasks()
root.mainloop()
