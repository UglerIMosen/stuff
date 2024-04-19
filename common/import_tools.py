# -*- coding: utf-8 -*-
"""
@author: thoe
"""
import numpy as np
import re
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import openpyxl
import sys

from stuff.math.simple import isfloat

def find_file():
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use("clam")
    root.geometry("500x500")
    filepath = filedialog.askopenfilename(parent=root, initialdir="", initialfile="tmp")
    if sys.platform != 'darwin':
        root.destroy()
    return filepath

def find_directory():
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use("clam")
    root.geometry("500x500")
    path = filedialog.askdirectory(parent=root)
    if sys.platform != 'darwin':
        root.destroy()
    return path

def load_data_with_names(path, name_spacing = ', '):
    # This can open both .csv or tabulated data.
    # The data is stored in a numpy ndarray typed list, with dimensions matching the data
    #
    # It will load names as strings from the text-line before the data begins. This can be changes by "names_line", where a value of "-1" is the line before the data
    #

    file=open(path,'r')
    lines=file.readlines()

    #find lines with numbers, making a mask. Assuming this is the data
    init_chars = [line[0:2] for line in lines]
    mask = [isfloat(char) for char in init_chars]

    #finding the line with names, assuming it is the last line containing text before the data
    mask_names = list(np.diff(mask))
    names_index = mask_names.index(True)
    names = lines[names_index].split(name_spacing)
    names[-1] = names[-1][:-1] #removes the line-shift of the last name

    #reading data
    filtered_lines = np.array(lines)[mask]
    for test_index in range(len(filtered_lines)):
        error_alert_enable = True
        error_counter = 0
        error_index = []
        data_out = np.zeros(shape=(len(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",filtered_lines[test_index])),len(filtered_lines))) #the hard-coded value '-3' is probably the course of the problem
        for row,line in enumerate(filtered_lines):
            values = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",line)
            for coloumn,value in enumerate(values):
                try:
                    data_out[coloumn,row]=float(value)
                except:
                    if error_alert_enable:
                        print('In text: '+str(filtered_lines)+'; of line: '+str(row)+'of the file: '+path+'; the first error occurred')
                        error_alert_enable = False
                    error_index.append(row+1)
                    error_counter += 1

        if error_counter == 0:
            #print('Data from,  '+path+', processed with no errors')
            break
        elif error_counter != len(filtered_lines):
            print('SOME data from,  '+path+', was processed, but with errors in the following lines')
            print(error_index)
            break
        else:
            print('NO data from , '+path+', was processed on try '+str(test_index))

    data_dict = {}
    for name,data in zip(names,data_out):
        data_dict[name] = data

    return data_dict

def load_data_sheet_with_names(path, outcomment='#', name_spacing = '  ', names_line = -1):
    #This can open both .csv or tabulated data.
    #The data is stored in a numpy ndarray typed list, with dimensions matching the data
    #
    #It will load names as strings from the text-line before the data begins. This can be changes by "names_line", where a value of "-1" is the line before the data
    file=open(path,'r')
    lines=file.readlines()
    mask = [outcomment not in i for i in lines]
    mask_names = list(np.diff(mask))
    names_index = mask_names.index(True)+names_line+1
    names = lines[names_index].split(name_spacing)
    if names[0] == outcomment:
        names = names[1:]
    filtered_lines = np.array(lines)[mask]
    data_out = np.zeros(shape=(len(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",filtered_lines[0])),len(filtered_lines)))
    for row,line in enumerate(filtered_lines):
        values = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",line)
        for coloumn,value in enumerate(values):
            try:
                data_out[coloumn,row]=float(value)
            except:
                print('In text: '+str(filtered_lines)+'; of line: '+str(row)+'of the file: '+path+'; an error occurred')

    data_dict = {}
    for name,data in zip(names,data_out):
        if name[-1:] == '\n':
            name = name[:-1]
        data_dict[name] = data

    return data_dict

def load_data_sheet(path, outcomment='#'):
    #This can open both .csv or tabulated data.
    #The data is stored in a numpy ndarray typed list, with dimensions matching the data
    file=open(path,'r')
    lines=file.readlines()
    mask = [outcomment not in i for i in lines]
    filtered_lines = np.array(lines)[mask]
    data_out = np.zeros(shape=(len(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",filtered_lines[0])),len(filtered_lines)))
    for row,line in enumerate(filtered_lines):
        values = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",line)
        for coloumn,value in enumerate(values):
            try:
                data_out[coloumn,row]=float(value)
            except:
                print('In text: '+str(filtered_lines)+'; of line: '+str(row)+'of the file: '+path+'; an error occurred')
    return data_out

def load_delimited_data(path, delimiter=',',clean_names=''):
    #save data in dictionary
    file=open(path,'rb')
    lines=file.readlines()
    lengths = [len(i.decode().split(delimiter)) for i in lines]
    most_frequent_line_length = max(set(lengths),key=lengths.count)
    filtered_lines = [i.decode() for i in lines if len(i.decode().split(delimiter)) == most_frequent_line_length]

    dictionary = {}
    raw_names = filtered_lines[0].split(delimiter)
    if clean_names != '':
        names = []
        for name in raw_names:
            names.append(name.split(clean_names)[-1])
    else:
        names = raw_names
    for name in names:
        dictionary[name] = []
    for line in filtered_lines[1:]:
        for name,item in zip(names,line.split(delimiter)):
            try:
                dictionary[name].append(int(item.replace('\n','').replace('\r','')))
            except ValueError:
                try:
                    dictionary[name].append(float(item.replace('\n','').replace('\r','')))
                except ValueError:
                    dictionary[name].append(item.replace('\n','').replace('\r',''))

    return dictionary

def import_excel_data(file,sheet,column1,column2,row1,row2):
    pass
