#!/usr/bin/env python

'''
Author: John D. Anderson
Email: jander43@vols.utk.edu
Description:
    This program allows for quick visuzalition of large
    NetLogo BehaviorSpace data sets.
Attributions:
    martineau, Wed Oct 05 2016, renegade, "Heat map from data
    points in python", Mar 25, 2015 at 22:11.
    http://stackoverflow.com/a/29269645/6926917
Legal:
    Copyright 2016 John David Anderson

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
Usage:
    pyvisualize
'''

# libraries for GUI/Threads
import Tkinter
from tkFileDialog import askopenfilename
import ttk
import sys
import os
import time
import threading
import Queue
import math
import numpy as np
import primefac as pf

# libraries for data visualization
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import h5py

# custom libraries (local directory)
import square_build

# banner
banner = '''
                ______      _   _ _                 _ _
                | ___ \    | | | (_)               | (_)
                | |_/ /   _| | | |_ ___ _   _  __ _| |_ _______
                |  __/ | | | | | | / __| | | |/ _` | | |_  / _ \\
                | |  | |_| \ \_/ / \__ \ |_| | (_| | | |/ /  __/
                \_|   \__, |\___/|_|___/\__,_|\__,_|_|_/___\___|
                       __/ |
                      |___/
'''

# constants
TST = ['/count turtles', '/count turtles sky', '/count turtles pink']
LG_FONT = ('Helvetica', 23)
SM_FONT = ('Verdana', 16)
EXEC = 'exec'
COMPLR_T = '<string>'
FONTDICT = {
            'fontsize': 'small',
            'fontweight': matplotlib.rcParams['axes.titleweight'],
            'verticalalignment': 'baseline',
            'horizontalalignment': 'center'
}

# globals
COLOBARDICT = {}
WDIM = {}
SIMPORTDICT = {
                'simdat': None,
                'canvas': None,
                'mplcsize': None,
                'mplcnum': None
              }

# checking path (used if bundled with PyInstaller)
if getattr(sys, 'frozen', False):
    RTPath = os.path.dirname(sys.executable)
else:
    RTPath = os.path.dirname(os.path.abspath(__file__))


# gen/func def
def gen_list(ex_list):
    '''
    Generator to take items from object and return them.
    '''
    for val in ex_list:
        yield val


def gen_xy_list(ex_list):
    '''
    Function to take x/y item pairs and generate separate lists for each.
    '''
    x_list, y_list = [], []
    for val in ex_list:
        x_list.append(val[0])
        y_list.append(val[1])
    return x_list, y_list


def min_max(heatmap):
    '''
    Function to take a 2d list and return the minimum and maximum elements.
    Adapted from: martineau, Wed Oct 05 2016, renegade, "Heat map from data
                  points in python", Mar 25, 2015 at 22:11,
                  http://stackoverflow.com/a/29269645/6926917
    '''
    # searching for min and max elements
    hmin = min(min(elem for elem in row) for row in heatmap)
    hmax = max(max(elem for elem in row) for row in heatmap)

    # returning
    return hmin, hmax


def crange(value, minval, maxval, palette):
    '''
    Function to generate a specific color for an element in the heatmap.
    Adapted from: martineau, Wed Oct 05 2016, renegade, "Heat map from data
                  points in python", Mar 25, 2015 at 22:11,
                  http://stackoverflow.com/a/29269645/6926917
    '''
    # get max index of palette
    max_index = len(palette)-1

    # convert elem in range minval - maxval to elem in range 0 to max_index
    fval = (float(value-minval) / (maxval-minval)) * max_index

    # truncate intermediate pallette value (fval) to an int
    ival = int(fval)

    # now caculate difference between the two
    diff = fval - ival

    # now select a color tuple from the palette
    c0r, c0g, c0b = palette[ival]

    # select color tuple that is +1 of previous but not greater than max_index
    c1r, c1g, c1b = palette[min(ival+1, max_index)]

    # now get difference of two color tuples
    dr, dg, db = c1r-c0r, c1g-c0g, c1b-c0b

    # now create color set based of diff and d* values
    colorset = (c0r + diff * dr, c0g + diff * dg, c0b + diff * db)

    # convert to 0 - 255 range number sets
    color = [int(c*255) for c in colorset]

    # return color string in '#xxxxxx' format (e.g. #0000ff)
    return '#' + '%02x' % color[0] + '%02x' % color[1] + '%02x' % color[2]


def find_group(hdfpath, group_num, gQ, aQ):
    '''
    Function to open HDF5 file and return data associated with "group_num".
    '''
    # constants
    HDFPATH = '/' + str(group_num)

    # open hdf5 file
    with h5py.File(hdfpath, 'r') as hdf5file:

        # get attributes
        attr_list = list(gen_list(hdf5file[HDFPATH].attrs.iteritems()))

        # update attributes
        aQ.put(attr_list)
        aQ.put(None)

        # iterate over data sets
        for dset in hdf5file[HDFPATH]:

            # generate list of data items
            data_list = list(gen_list(hdf5file[HDFPATH + '/' + dset]))
            # data_list = list(parse_list(data_list))

            # create dict
            data_dict = {dset: data_list}

            # push on Q
            gQ.put(data_dict)

        # sentinel value
        gQ.put(None)

    # return
    return


def attribute_view(grp, attr_str):
    '''
    Function to generate a small Toplevel() window to view attributes of a
    simulation.
    '''
    # generate unique name
    tm = str(time.clock())
    var_num = tm.split('.')
    var_name = 'thread_{0}'.format(var_num[1])

    # string to be compiled
    attr_tplvl_str = (
        '{0} = Tkinter.Toplevel()\n'
        '{0}.title(\'Simulation {1} Attributes\')\n'
        'label = ttk.Label({0}, text=attr_str, font={2}, anchor=\'center\')\n'
        'label.pack(expand=True, fill=\'both\', side=\'top\')'
    ).format(var_name, grp, SM_FONT)

    # compile and execute code
    attr_tplvl_code = compile(attr_tplvl_str, COMPLR_T, EXEC)
    exec attr_tplvl_code


def simulation_data_portfolio(grp_name, grpQ, attrQ, controller):
    '''
    Function to generate x/y plots for all data sets for a given simulation.
    '''
    # create attribute string and make "global"
    global attr_str
    attr_str = ""
    for attr_list in iter(attrQ.get, None):
        length = len(attr_list)
        for i, attributes in enumerate(attr_list):
            tmp_str = "{0}: {1}\n".format(attributes[0], attributes[1])
            attr_str = attr_str + tmp_str

    # creating Toplevel w/ attribute button
    tplvl = Tkinter.Toplevel()
    tplvl.title('Simulation {0} Data'.format(grp_name))
    tplvl.configure(background='grey')
    attr_btn = ttk.Button(tplvl, text='attributes',
                          command=lambda: attribute_view(grp_name, attr_str))
    attr_btn.pack()

    # create canvas, frame
    tplvl_canvas = Tkinter.Canvas(tplvl)
    can_frame = Tkinter.Frame(tplvl_canvas)

    # create scrollbars / add to top level
    tplvl_yscrlbr = Tkinter.Scrollbar(tplvl_canvas, orient='vertical')
    tplvl_xscrlbr = Tkinter.Scrollbar(tplvl_canvas, orient='horizontal')

    # innercanvas for matplotlib data
    frame_innercan = Tkinter.Canvas(can_frame,
                                    yscrollcommand=tplvl_yscrlbr.set,
                                    xscrollcommand=tplvl_xscrlbr.set)

    # stor object instances in global dict
    SIMPORTDICT['simdat'] = frame_innercan
    SIMPORTDICT['canvas'] = tplvl_canvas

    # callback functions
    def on_vertical(event):
        SIMPORTDICT['simdat'].yview_scroll(-1 * event.delta, 'units')

    def on_horizontal(event):
        SIMPORTDICT['simdat'].xview_scroll(-1 * event.delta, 'units')

    def on_config(event):
        innercan = SIMPORTDICT['simdat']
        canvas = SIMPORTDICT['canvas']
        print 'innercan: ', innercan.bbox('all')
        print 'width, height: ', event.width, event.height
        scrollregion = (0, 0, int(event.width), int(event.height))

    # get data
    mplsize_list = []
    for d_index, data_dict in enumerate(iter(grpQ.get, None)):
        for dset_name, data_list in data_dict.items():

            # generate x/y lists
            x_list, y_list = gen_xy_list(data_list)

            # row/columns
            row = d_index / 3
            col = d_index % 3

            # max y-value
            ymax = int(max(y_list))
            xmax = len(y_list)

            # calculate padding
            ipadx = len(str(ymax)) * 30
            ipady = xmax - 1

            # creat figure for canvas
            fig = Figure(figsize=(2, 2), dpi=90)
            a = fig.add_subplot(111)
            a.set_title('Data: {0}'.format(dset_name), fontdict=FONTDICT)
            a.plot(x_list, y_list)
            fig_canvas = FigureCanvasTkAgg(fig, frame_innercan)
            fig_canvas.get_tk_widget().grid(row=row, column=col,
                                            ipadx=ipadx,
                                            ipady=ipady, sticky='NSEW')
            fig_canvas.show()
            width = fig_canvas.get_tk_widget().winfo_width()
            height = fig_canvas.get_tk_widget().winfo_height()

            # store width/height of fig_canvas
            entry = [width, height]

            # update list of w/h values
            mplsize_list.append(entry)

    # sort list
    mplsize_list.sort()

    # measure canvas
    can_width = int(mplsize_list[-1][0] * 3)
    can_height = int(mplsize_list[-1][1] * math.ceil((d_index+1)/3.0))

    # create scrollregion
    scrollregion = (0, 0, int(can_width), int(can_height))

    # final window/scrollbar configurations
    tplvl_yscrlbr.pack(side='right', fill='y')
    tplvl_xscrlbr.pack(side='bottom', fill='both')
    frame_innercan.pack(side='left', fill='both', expand=True)
    can_frame.pack(side='left', expand=True)
    tplvl_yscrlbr.config(command=frame_innercan.yview)
    tplvl_xscrlbr.config(command=frame_innercan.xview)
    frame_innercan.bind('<MouseWheel>', on_vertical, '+')
    frame_innercan.bind('<Shift-MouseWheel>', on_horizontal, '+')
    tplvl_canvas.pack()
    # frame_innercan.update_idletasks()
    # can_frame.update_idletasks()
    # tplvl_canvas.create_window(0, 0, anchor='nw', window=can_frame)
    # tplvl_canvas.bind_all('<Configure>', on_config)
    frame_innercan.config(scrollregion=scrollregion)

    # change dimesions
    ws = tplvl.winfo_screenwidth()
    hs = tplvl.winfo_screenheight()
    x = (ws - can_width) / 2
    y = (hs - can_height) / 2

    # adjust window size
    dims = tplvl.winfo_geometry().split('+')[0].split('x')
    tplvl.geometry('%dx%d+%d+%d' % (can_width, can_height+40, x, y))

    # # center window
    # controller.eval('tk::PlaceWindow %s center' %
    #                 tplvl.winfo_pathname(tplvl.winfo_id()))

    # return
    return


def gen_heatmap(controller, data_queue, hdfpath):
    '''
    Adapted from: martineau, Wed Oct 05 2016, renegade, "Heat map from data
                  points in python", Mar 25 2015 at 22:11,
                  http://stackoverflow.com/a/29269645/6926917
    '''
    # constants
    CDIM = 20

    # func def
    def heatmap_callback(event):
        '''
        Function called when mouse event <CLICKED> is triggered on a heatmap
        tile.
        '''
        # read mouse click event
        canvas = event.widget
        try:
            rect = canvas.find_withtag('current')[0]
        except IndexError:
            print 'IndexError: non-tile area of heatmap was clicked'
            return

        # getting group number to access data for
        grp_num = int(rect)

        # queue for thread
        grpQ = Queue.Queue()
        attrQ = Queue.Queue()

        # purely a function implementation
        find_group(hdfpath, grp_num, grpQ, attrQ)

        # plot simulation data
        simulation_data_portfolio(grp_num, grpQ, attrQ, controller)

        # return
        print 'Showing: Data Portfolio for Group {0}'.format(grp_num)

    # 2d array from HDF5 file
    heat_map = data_queue.get()

    # calculating min/max values
    # NOTE: adapted from martineau (see docstring at top of function)
    heat_min, heat_max = min_max(heat_map)

    # collor palette for heatmap
    # NOTE: adapted from martineau (see docstring at top of function)
    palette = [(0, 0, 1), (0, 0.5, 0), (0, 1, 0), (1, 0.5, 0), (1, 0, 0)]

    # rows/columns for heatmap
    rows, cols = len(heat_map), len(heat_map[0])
    cwidth, cheight = rows * CDIM, cols * CDIM

    # get data view frame
    dvf = controller.frames['DataView']

    # canvas object for heatmap
    can = Tkinter.Canvas(dvf)

    # update RootWindow's state with canvas object
    controller.canvas['DataViewCanvas'] = can

    # create inner canvas for scrolling feature
    yscrlbr = Tkinter.Scrollbar(can, orient='vertical')
    xscrlbr = Tkinter.Scrollbar(can, orient='horizontal')
    innercan = Tkinter.Canvas(can, bd=1, width=cwidth, height=cheight,
                              yscrollcommand=yscrlbr.set,
                              xscrollcommand=xscrlbr.set)

    # functions for scrolling
    def on_vertical(event):
        innercan.yview_scroll(-1 * event.delta, 'units')

    def on_horizontal(event):
        innercan.xview_scroll(-1 * event.delta, 'units')

    # populate canvas with tiles (i.e. rectangles)
    # NOTE: adapted from martineau (see docstring at top of function)
    rect_width, rect_height = cwidth // rows, cheight // cols
    for y, row in enumerate(heat_map):
        for x, temp in enumerate(row):
            x0, y0 = x * rect_width, y * rect_height
            x1, y1 = x0 + rect_width-1, y0 + rect_height-1
            color = crange(temp, heat_min, heat_max, palette)
            cr_val = (str(x), str(y))
            rect = innercan.create_rectangle(x0, y0, x1, y1,
                                             fill=color, width=0, tags=cr_val)

    # gen colorbar list
    interval = (heat_max - heat_min)/9
    cbarlist = [heat_min + i*interval for i in range(9)]
    cbarlist.append(heat_max)
    cbarlist.reverse()

    # fill dict
    COLORBARDICT = {
                    'colorbarlist': cbarlist,
                    'rwidth': rect_width,
                    'rheight': rect_height,
                    'hmin': heat_min,
                    'hmax': heat_max
    }

    # colorbar callback
    def gen_colorbar(cbardict):
        '''
        Function to create a colorbar to interpret meaning of heatmap colors.
        '''
        # get dict contents
        colorbarlist = cbardict['colorbarlist']
        rect_width = cbardict['rwidth']
        rect_height = cbardict['rheight']
        heat_min = cbardict['hmin']
        heat_max = cbardict['hmax']

        # create toplevel window
        colorbar_view = Tkinter.Toplevel()
        colorbar_view.title('')

        # create frame object
        frm = ttk.Frame(colorbar_view)
        frm.pack()

        # create canvas object
        cbarcan = Tkinter.Canvas(frm, width=rect_width, height=10*rect_height)

        # color palette for heatmap
        palette = [(0, 0, 1), (0, 0.5, 0), (0, 1, 0), (1, 0.5, 0), (1, 0, 0)]

        # populate canvas with tiles
        # NOTE: adapted from martineau (see docstring at top of function)
        x = 0
        cbar_values = 'Highest\n'
        for y, cbar in enumerate(colorbarlist):
            cbar_values += '   |\n'
            x0, y0 = x * rect_width, y * rect_height
            x1, y1 = x0 + rect_width-1, y0 + rect_height-1
            color = crange(cbar, heat_min, heat_max, palette)
            rect = cbarcan.create_rectangle(x0, y0, x1, y1, fill=color,
                                            width=0)

        cbar_values += 'Lowest'
        label = ttk.Label(frm, text=cbar_values, font={2}, anchor='center')
        label.pack(expand=True, fill='both', side='left')

        # final step
        cbarcan.pack(side='left')

    # configure colorbar button
    dvf.colorbar_button = ttk.Button(dvf.btn_frame, text='Colorbar',
                                     command=lambda: gen_colorbar(COLORBARDICT)
                                     )
    dvf.colorbar_button.pack(side='left')

    # finish configurations/packing
    yscrlbr.pack(side='right', fill='y')
    xscrlbr.pack(side='bottom', fill='both')
    innercan.pack(side='left', fill='both', expand=True)
    innercan.config(scrollregion=innercan.bbox('all'))
    # yscrlbr.config(command=innercan.yview)
    # xscrlbr.config(command=innercan.xview)
    innercan.bind('<Button-1>', heatmap_callback)
    innercan.bind_all('<MouseWheel>', on_vertical)
    innercan.bind_all('<Shift-MouseWheel>', on_horizontal)
    can.pack()  # NOTE: must call "pack()" or won't show

    # return
    return


def update_progbar(progress, Q, popup, controller):
    '''
    Function to update the progressbar while CSV is converted to HDF5.
    '''
    progress["value"] = Q.get()
    if progress["maximum"] == progress["value"]:
        print "CONVERSION FINISHED!!!!"
        popup.destroy()
        return
    controller.after(100, update_progbar, progress, Q, popup, controller)


def csv_linesum(fname):
    '''
    Function to count lines in CSV file
    '''
    with open(fname, 'rU') as f:
        for i, l in enumerate(f):
            pass
        return i


def hdf5_linesum(hdfpath):
    '''
    Function to count the number of lines in an HDF5 file.
    '''
    with h5py.File(hdfpath, 'r') as hdf5file:
        for count, __ in enumerate(hdf5file):
            pass
        return count+1


def gen_hdf5_dnames(hdfpath):
    '''
    Generator to return list of data names from the HDF5 file.
    '''
    with h5py.File(hdfpath, 'r') as hdf5file:
        for grp in hdf5file:
            for dset in hdf5file['/' + grp]:
                yield dset
            return


def get_filename(filepath):
    '''
    Function to extract filename from a full path.
    '''
    path_list = filepath.split('/')
    filename = path_list[len(path_list)-1]
    return filename


def csv2hdf5(fpath, Q):
    '''
    Function to convert CSV data to HDF5.
    '''
    # limited scope libraries
    import csv

    # function to creat yourfile.hdf5 save path
    def hdf5_path(argv):
        argname = argv.split('/')
        csvname = argname[len(argname)-1].rsplit('.', 1)
        h5name = csvname[0] + ".hdf5"
        pathname = ''
        for i, folder in enumerate(argname):
            if i == len(argname)-1:
                return pathname + h5name
            pathname += folder + '/'

    # check for empty arg
    if fpath == '':
        sys.exit()

    # find line number
    numline = csv_linesum(fpath)

    # lists/dicts/containers for data
    atlst = []
    datasets = {}

    # getting path/name of hdf5 file
    h5name = hdf5_path(fpath)

    # open "TABLE" csv file and copy to HDF5 file
    with open(fpath, 'rU') as csvfile,  h5py.File(h5name, 'w') as hdf5:

        # main loop
        for i, line in enumerate(csv.reader(csvfile)):

            # push increment to queue (NOTE: for progressbar)
            Q.put(i)

            # pulling dataset names and attributes
            if i == 6:
                atlst = [row for j, row in enumerate(line) if j < 17]
                datasets = {line[x]: x for x in range(18, len(list(line)))}

            if i > 6:
                if line[0] in hdf5:
                    grp = hdf5[line[0]]
                    for dset_name in grp:
                        dset = grp[dset_name]
                        newsize = dset.len()
                        dset.resize((newsize+1, 2))
                        dset[newsize, 0] = int(line[17])
                        dset[newsize, 1] = float(line[datasets[dset_name]])
                    continue

                # else create new group
                grp = hdf5.create_group(line[0])
                for attr, row in zip(atlst, line):
                    grp.attrs[attr] = row
                for name, index in datasets.iteritems():
                    inlist = [int(line[17]), float(line[index])]
                    grp.create_dataset(name, (1, 2), maxshape=(None, 2),
                                       data=inlist)


def read_hdf5(hdf5path, Q, datapath):
    '''
    Function to read data from HDF5 file and pass to a Queue.
    '''
    # dictionary for data
    data_dict = {}

    # NOTE: here is where you can implement "choose your heatmap variable"
    #      where they will choose a dataset and time point to compare
    #      simulations ...

    # open hdf5 file
    with h5py.File(hdf5path, 'r') as hdf5file:
        for grp in hdf5file:
            fullpath = '/' + grp + datapath
            count_turtles_dataset = hdf5file[fullpath][100]
            data_dict[int(grp)] = count_turtles_dataset[1]

    # list for 2D array
    ls_2d_array = list(gen_list(data_dict.values()))

    # #NOTE: this only works for numbers with square roots
    # # Rows/Columns for 2D array
    # columns = int(math.sqrt(len(data_dict)))
    # rows = columns
    #
    # # convert to 2D
    # data_array = np.array(ls_2d_array).reshape(columns,rows)

    # building heatmap
    list_rows = square_build.square_builder(len(ls_2d_array))

    # heatmap list
    data_array = square_build.square_list(list_rows, ls_2d_array)

    # pass to Thread Queue
    Q.put(data_array)


def get_csv(controller):
    '''
    Function to grab path to CSV file, get number of lines, and start prog bar.
    '''
    # choose csvfile
    csvpath = askopenfilename()

    # error check
    if csvpath == '':
        print 'No File Selected'
        return

    # count lines
    maxprogress = csv_linesum(csvpath)

    # get file name
    csv_name = get_filename(csvpath)

    # error check
    if not csv_name.lower().endswith('csv'):
        print 'Non-CSV File Selected'
        return

    # generate unique name
    tm = str(time.clock())
    var_num = tm.split('.')
    var_name = 'thread_{0}'.format(var_num[1])

    # open Progressbar with exec() function
    exec("%s=Tkinter.Toplevel()" % var_name)
    exec("%s.title(\'Conversion Progress\')" % var_name)
    exec("%s.geometry(\'500x75\')" % var_name)
    exec("progress = ttk.Progressbar(%s,orient=\'horizontal\',"
         "mode=\'determinate\')"
         % var_name)
    progress.pack(expand=True, fill='both', side='top')
    progress["maximum"] = maxprogress
    progress["value"] = 0
    status = 'Converting: {0}'.format(csv_name)
    exec("label = ttk.Label(%s,text=status,font=%s,anchor=\'center\')"
         % (var_name, LG_FONT))
    label.pack(expand=True, fill='both', side='top')

    # center window
    exec("controller.eval(\'tk::PlaceWindow %%s center\' %% "
         "%s.winfo_pathname(%s.winfo_id()))"
         % ((var_name,)*2))

    # queue for thread values
    Q = Queue.LifoQueue()

    # run conversion thread
    my_thread = threading.Thread(target=csv2hdf5, args=(csvpath,  Q))
    my_thread.start()

    # start controller.after cycle
    exec("update_progbar(progress, Q, %s, controller)" % var_name)


def get_hdf5(controller):
    '''
    Function to allow selecting of HDF5 file, generating heatmap for file (by
    calling gen_heatmap()), and navigating GUI page from the "MainView" page
    to the "DataView" page.
    '''
    # choose HDF5 file
    hdfpath = askopenfilename()

    # error check
    if hdfpath == '':
        print 'No File Selected'
        return

    # get file name
    hdf_name = get_filename(hdfpath)

    # error check
    if not hdf_name.lower().endswith(('hdf5', 'h5')):
        print 'Non-HDF File Selected'
        return

    # get dataset names
    dnames = [dset for dset in gen_hdf5_dnames(hdfpath)]

    # offer user choice of dataset for heatmap coloring
    h = HeatmapDataSource(controller, dnames, hdfpath)

    # # count lines
    # maxprogress = hdf5_linesum(hdfpath)


def back_to_main(controller):
    '''
    Function that removes current GUI objects to navigate back to main page.
    '''
    controller.canvas['DataViewCanvas'].destroy()
    controller.frames['DataView'].colorbar_button.destroy()
    controller.show_frame('MainView')


# class def
class RootWindow(Tkinter.Tk):
    '''
    Class for main Tkinter root object.
    '''
    # constructor
    def __init__(self, *args, **kwargs):
        # instantiate Tk() object
        Tkinter.Tk.__init__(self, *args, **kwargs)
        self.title('PyVisualize')
        rootframe = ttk.Frame(self)
        rootframe.pack(side='top', fill='both', expand=True)
        rootframe.grid_rowconfigure(0, weight=1)
        rootframe.grid_columnconfigure(0, weight=1)

        # dictionary of frame objects
        self.frames = {}

        # dictionary of canvas objects
        # NOTE: to be filled by gen_heatmap()
        self.canvas = {}

        # populate frames dict
        frame_list = ('DataView', 'MainView')
        for frame in frame_list:
            exec('obj_frame = %s(rootframe,self)' % frame)
            exec('self.frames[\'%s\'] = obj_frame' % frame)
            obj_frame.grid(row=0, column=0, stick='nsew')

        # print banner
        print banner

        # show frame
        self.show_frame('MainView')

        # center window
        self.eval('tk::PlaceWindow %s center' %
                  self.winfo_pathname(self.winfo_id()))

    def show_frame(self, cont):
        select_frame = self.frames[cont]
        select_frame.tkraise()
        print 'Showing: {0}'.format(cont)


class MainView(ttk.Frame):
    '''
    Class for main GUI menu, showing options (e.g. convert CSV -> HDF5)
    '''
    # constructor
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent, padding=((24,)*4))
        self.grid(column=5, row=12, sticky='nsew')

        # loading python image
        self.gif = Tkinter.PhotoImage(file=RTPath + '/media/python_dark.gif')
        self.py_logo = ttk.Label(self, image=self.gif)
        self.py_logo.pack(pady=20)

        # frame for grouping buttons
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack()

        # convert file.csv to file.hdf5
        self.csv_2_hdf5_button = ttk.Button(self.btn_frame,
                                            text='Convert CSV -> HDF5',
                                            command=lambda: get_csv(controller)
                                            ).pack(side='left', padx=5)

        # open and view file.hdf5 contents
        self.view_hdf5_button = ttk.Button(self.btn_frame, text='Open HDF5',
                                           command=lambda: get_hdf5(controller)
                                           ).pack(side='left', padx=5)


class DataView(ttk.Frame):
    '''
    Class that enables the viewing of the heatmap of NetLogo simulation data.
    '''
    # constructor
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.pack()

        # self.scrlbar = Tkinter.Scrollbar(self, orient='vertical')
        # self.scrlbar.config(command=file_list.yview)
        # self.scrlbar.pack(side='right', fill='y')

        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack()

        # button back to main view
        self.back_button = ttk.Button(self.btn_frame, text='<- Back',
                                      command=lambda: back_to_main(controller))
        self.back_button.pack(side='left')

        # colorbar for heatmap
        self.colorbar_button = None


class HeatmapDataSource(Tkinter.Toplevel):
    '''
    Class for choosing data source for heatmap.
    '''
    # constructor
    def __init__(self, root, dlist, filepath):
        # create toplevel window
        Tkinter.Toplevel.__init__(self, root)
        self.title('Heatmap Data Source')

        # create variable
        self.var = Tkinter.StringVar()

        # store hdfpath
        self.hdfpath = filepath

        # store root window
        self.root = root

        # loop over dlist to create checkboxes
        for text in dlist:
            c = Tkinter.Radiobutton(
                self, text=text.strip('/'),
                variable=self.var,
                value=text)
            c.pack(anchor='w')

        # create submit button
        self.submit = ttk.Button(self, text='submit',
                                 command=lambda: self.get_choice())
        self.submit.pack(side='bottom')

        # center window
        self.root.eval('tk::PlaceWindow %s center' %
                       self.winfo_pathname(self.winfo_id()))

    def get_choice(self):
        '''
        Function to flip 'pressed' flag.
        '''
        # check for empty var
        datapath = self.var.get()
        if datapath is not '':
            # generate heatmap canvas
            # NOTE: Need to refactor WITHOUT threads ...
            dataQ = Queue.Queue()
            readhdf5_thread = threading.Thread(target=read_hdf5,
                                               args=(self.hdfpath, dataQ,
                                                     '/'+datapath))
            readhdf5_thread.start()

            # generate heatmap
            gen_heatmap(self.root, dataQ, self.hdfpath)

            # show 'DataView' page
            self.root.show_frame('DataView')

            # then close window
            self.destroy()


# executable
if __name__ == '__main__':
    # launch
    app = RootWindow()
    app.mainloop()
