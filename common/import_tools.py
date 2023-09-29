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
import sys

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
