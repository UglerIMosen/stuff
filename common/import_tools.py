# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta

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

def Read_SAC(filename, MassNumbers = np.array([-1])):
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
