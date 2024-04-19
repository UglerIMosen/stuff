# -*- coding: utf-8 -*-
"""
@author: thoe
"""

print('Opening QMS fitting')
print('v1.0 (November 2023)')
print('(c) DynElectro ApS - 2023')

import os
from tkinter import *
from stuff.common.import_tools import find_file
from stuff.scientific.QMS import spectrum_fit
import numpy as np
from matplotlib import pyplot as plt

fit_tool = spectrum_fit()

class Checkbar(Frame):

    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        Frame.__init__(self, parent)
        self.vars = []
        for pick in picks:
            var = IntVar()
            chk = Checkbutton(self, text=pick, variable=var)
            chk.pack(side=side, anchor=anchor, expand=YES)
            self.vars.append(var)

    def state(self):
        return map((lambda var: var.get()), self.vars)

    def __getitem__(self,key):
        return self.vars[key].get()

root = Tk()
gas_list = Checkbar(root, fit_tool.mlib('content'))
gas_list.pack(side=TOP,  fill=X)
gas_list.config(relief=GROOVE, bd=2)
label2=Label(root,bg='white',text='')
label2.pack(side=LEFT)
label=Label(root,bg='white',text='')
label.pack(side=BOTTOM)

def button_run():
    if fit_tool.data_present:
        fit_tool.gas_list = list(np.array(fit_tool.mlib('content'))[[i==1 for i in list(gas_list.state())]])
        fit_tool.generate_gas_mass_list()
        fit_tool.run_sequence()
    else:
        global label
        label.destroy()
        label=Label(root,bg='white',text='ERROR: no data is loaded')
        label.pack(side=BOTTOM)

def load_file():
    file_path = find_file()

    if '.dat' not in file_path:
        file_path = 'ERROR: file is not a .dat file'
    else:
        fit_tool.load_data(file_path)

    global label2
    label2.destroy()
    label2=Label(root,bg='white',text=file_path)
    label2.pack(side=LEFT)

def button_plot_raw():
    if fit_tool.data_present:
        fit_tool.gas_list = list(np.array(fit_tool.mlib('content'))[[i==1 for i in list(gas_list.state())]])
        fit_tool.generate_gas_mass_list()

        fig, f = plt.subplots()
        for mass in fit_tool.gas_masses:
            f.plot(fit_tool.data_set['Time Relative (sec)'],np.array(fit_tool.data_set[mass])/np.array(fit_tool.data_set['Pressure_(mBar)']),label=str(mass))
        f.set_xlabel('Time [s]')
        f.set_ylabel('Current [A/mbar]')
        f.set_yscale('log')
        f.legend(title='Atomic mass')
        plt.tight_layout()
        plt.show()
    else:
        global label
        label.destroy()
        label=Label(root,bg='white',text='ERROR: no data is loaded')
        label.pack(side=BOTTOM)


def button_plot_fit():
    if fit_tool.fit_complete:
        fit_tool.gas_list = list(np.array(fit_tool.mlib('content'))[[i==1 for i in list(gas_list.state())]])
        fit_tool.generate_gas_mass_list()

        fig, f = plt.subplots()
        for gas in fit_tool.gas_list:
            if gas+'_(A/mbar)' in fit_tool.gas_currents.keys():
                f.plot(fit_tool.gas_currents['reltime_(s)'],fit_tool.data_set[gas+'_(A/mbar)'],label=gas)
        f.set_xlabel('Time [s]')
        f.set_ylabel('Current [A/mbar]')
        f.set_yscale('log')
        f.legend(title='Atomic mass')
        plt.tight_layout()
        plt.show()

    else:
        global label
        label.destroy()
        label=Label(root,bg='white',text='ERROR: no data fitted')
        label.pack(side=BOTTOM)



Button(root, text='Fitted data', command=button_plot_fit).pack(side=RIGHT)
Button(root, text='Run', command=button_run).pack(side=RIGHT)
Button(root, text='Raw data', command=button_plot_raw).pack(side=RIGHT)
Button(root, text='Load', command=load_file).pack(side=RIGHT)
root.mainloop()
