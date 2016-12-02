#!/usr/bin/env python

import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk

root = Tk.Tk()
root.wm_title("Embedding in TK")

f = Figure(figsize=(5, 4), dpi=100)
a = f.add_subplot(111)
t = arange(0.0, 3.0, 0.01)
s = sin(2*pi*t)

a.plot(t, s)

outcan = Tk.Canvas(root)
outcan.pack()

# create scrollbars / add to top level
tplvl_yscrlbr = Tk.Scrollbar(outcan, orient='vertical')
tplvl_xscrlbr = Tk.Scrollbar(outcan, orient='horizontal')

# innercanvas for matplotlib data
outcan.config(yscrollcommand=tplvl_yscrlbr.set,
              xscrollcommand=tplvl_xscrlbr.set)

tplvl_yscrlbr.pack(side='right', fill='y')
tplvl_xscrlbr.pack(side='bottom', fill='both')
tplvl_yscrlbr.config(command=outcan.yview)
tplvl_xscrlbr.config(command=outcan.xview)


for i in range(3):

    # row/columns
    row = i / 3
    col = i % 3

    # a tk.DrawingArea
    canvas = FigureCanvasTkAgg(f, master=outcan)
    canvas.show()

    # grid overrides the automatic 'sizing' of the window
    canvas.get_tk_widget().grid(row=row, column=col, sticky='NSEW')


Tk.mainloop()
# If you put root.destroy() here, it will cause an error if
# the window is closed with the window manager.
