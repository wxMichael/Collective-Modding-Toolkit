from tkinter import Tk

from cm_checker import CMChecker
from utils import set_theme

root = Tk()
root.withdraw()
root.update()
CMChecker(root)
set_theme(root)
root.update()
root.deiconify()
root.mainloop()
