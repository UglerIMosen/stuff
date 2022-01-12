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
import time

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
  
def load_qms_asc(path):
    if path[-4:] == '.asc':
        raw_file = open(path)
    else:
        raw_file = open(path+'.asc')
    lines = raw_file.readlines()

    mass_keys = []
    for line in lines[10:]:
            vector = line.split("\t")
            if vector[0] == '\n':
                break
            mass_keys.append(vector[1])

            mass_data = {}
    mass_data['cycle'] = []
    mass_data['date']  = []
    mass_data['clock'] = []
    mass_data['time']  = []
    for key in mass_keys:
        mass_data[key] = []

    for line in lines:
        vector = line.split("\t")
        if vector[0].isdigit():
            #write vector to new vector
            mass_data['cycle'].append(float(vector[0]))
            mass_data['date'].append(vector[1])
            mass_data['clock'].append(vector[2])
            mass_data['time'].append(float(vector[3]))
            for key, value in zip(mass_keys, vector[4:-1]):
                mass_data[key].append(float(value))
    for key in mass_data.keys():
        mass_data[key] = np.array(mass_data[key])
    return mass_data, mass_keys

def read_SAC(filename, MassNumbers = np.array([-1])):
    f = open(filename, "r")
    NbCycle = np.fromfile(f, dtype=np.uint16, count=1, offset=100)
    Cycle_list = np.arange(1, NbCycle)

    f = open(filename, "r")
    Scan_Width = np.fromfile(f, dtype=np.uint16, count=1, offset=345)

    f = open(filename, "r")
    Steps = np.fromfile(f, dtype=np.uint16, count=1, offset=347)

    f = open(filename, "r")
    NbPts = np.fromfile(f, dtype=np.uint16, count=1, offset=386)

    f = open(filename, "r")
    First_u = np.fromfile(f, dtype=np.float32, count=1, offset=341)

    f = open(filename, "r")
    u_start = np.fromfile(f, dtype=np.float32, count=1, offset=348)

    f = open(filename, "r")
    u_end = np.fromfile(f, dtype=np.float32, count=1, offset=352)

    f = open(filename, "r")
    Units_I = str(np.fromfile(f, dtype="c", count=1, offset=234)[0]).split("'")[1]

    f = open(filename, "r")
    Units_u = str(np.fromfile(f, dtype="c", count=1, offset=263)[0]).split("'")[1]

    f = open(filename, "r")
    UTC = np.fromfile(f, dtype=np.uint32, count=1, offset=194)

    Start_time = datetime.fromtimestamp(UTC[0])

    Cal_NbPts = Scan_Width * Steps

    u = np.zeros(NbPts[0]+1)

    u[0] = First_u
    for i in range(1, int(Cal_NbPts)+1):
        u[i] = u[i-1] + (1/Steps)

    f = open(filename, "r")
    time_cycle_all = np.fromfile(f, dtype=np.uint32, offset=0)
    taille = len(time_cycle_all)

    j = 0
    time_cycle = np.zeros(NbCycle[0])

    for i in np.arange(96, taille, Cal_NbPts + 3):
        j = j + 1
        time_cycle[j-1] = time_cycle_all[i-1]
    
    Time = np.array([])

    for i in range(len(time_cycle)):
        Time = np.append(Time, Start_time + timedelta(seconds=time_cycle[i]))

    f = open(filename, "r")
    data_cycle_all = np.fromfile(f, dtype=np.float32, offset=0)

    dec = 96
    l = 0
    if np.any(MassNumbers == -1):
        s = (NbPts[0]+1, NbCycle[0])
        data_cycle = np.zeros(s)

        for k in range(NbCycle[0]):
            for i in range(Cal_NbPts[0]):
                data_cycle[i, k] = data_cycle_all[dec + i + 2 + l]
            l = l + 3 + Cal_NbPts[0]
    else:
        s = (len(MassNumbers), NbCycle[0])
        data_cycle = np.zeros(s)

        for k in range(NbCycle[0]):
            p = 0
            for i in MassNumbers:
                data_cycle[p, k] = data_cycle_all[dec + int(i*32) + 2 + l]
                p = p +1
            l = l + 3 + Cal_NbPts[0]
    f.close()
    return data_cycle, Time, u, time_cycle, Start_time

def read_RGA_prism_dat(path):
    #TAkes a data-file, read the lines, split the lines in '\t', and makes a differential analysis on, when the data starts. It reads the first line as names, and the rest as the data.
    file=open(path,'r')
    lines=file.readlines()
    length = [len(i.split('\t')) for i in lines]
    name_line = np.where(np.diff(length)==max(np.diff(length)))[0][0]+1
    data_dict = {}
    for key in lines[name_line].split('\t'):
        data_dict[key] = []
    for line in lines[name_line+1:]:
        values = line.split('\t')
        for key,value in zip(lines[name_line].split('\t'),values):
            try:
                data_dict[key].append(float(value))
            except:
                data_dict[key].append(value)
    return data_dict

if __name__ == '__main__':
    file = find_file()
    masses = [1.41, 2.38, 4, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26, 28, 29, 30, 32, 36, 40, 44, 46]
    spacing = '    '
    if file[-4:] != '.sac':
        print('The file loaded is not a .sac file')
    else:
        data = read_SAC(file, MassNumbers = masses)
        output_file = open(file[:-4]+' '+time.ctime().replace(':','')+'.txt','w+')
        print('Writing to '+file[:-4]+' '+time.ctime()+'.txt')
        output_file.write('#Data acquisition on '+str(data[4])+'\n')
        string_to_write = '#Time[s]'
        for mass in masses:
            string_to_write = string_to_write+spacing+str(mass)
        output_file.write(string_to_write+'\n')
        print(' ')
        length = len(data[3])
        for index in range(length):
            string_to_write = str(data[3][index])
            for point_list in data[0]:
                string_to_write = string_to_write + spacing + str(point_list[index])
            output_file.write(string_to_write+'\n')
            print(str(round(100*index/length))+'%',end='\r')
        output_file.close()
        print(' ')
        print('Job finished')
        
        
        
        
        
        
        
        
        
        
        