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
from scipy.optimize import curve_fit
from matplotlib import pyplot as plt
import pandas as pd

from stuff.common.stuff import progress_bar, time_stamp_str, name_of_file

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

def read_RGA_prism_dat(path,mass_name = '_amu'):
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
    name_keys = [i for i in data_dict.keys() if '_amu' in i]
    for key in name_keys:
        mass = int(re.search(r'\d+',key).group())
        data_dict[mass] = data_dict[key]
    for key in data_dict.keys():
        data_dict[key] = np.array(data_dict[key])
    return data_dict

def mass_library(compound):
    # Collection (C) 2014 copyright by the U.S. Secretary of Commerce
    # on behalf of the United States of America. All rights reserved.
    dictionary = {
        'H2'  : { 1:0.0210,  2:0.9999},
        'H2O' : {16:0.0090, 17:0.2122, 18:0.9999, 19:0.0050, 20:0.0030},
        'He'  : { 4:0.9999},
        'C'   : {12:0.9999},
        'CH4' : {12:0.0380, 13:0.1069, 14:0.2042, 15:0.8879, 16:0.9999, 17:0.0164},
        'CO'  : {12:0.0470, 16:0.0170, 28:0.9999, 29:0.0120},
        'CO2' : {12:0.0871, 16:0.0961, 22:0.0190, 28:0.0981, 29:0.0010, 44:0.9999, 45:0.0120, 46:0.0040},
        'N2'  : {14:0.1379, 28:0.9999, 29:0.0074},
        'NO'  : {14:0.0751, 15:0.0240, 16:0.0150, 30:0.9999, 31:0.0040, 32:0.0020},
        'N2O' : {14:0.1291, 15:0.0010, 16:0.0500, 28:0.1081, 29:0.0010, 30:0.3113, 31:0.0010, 44:0.9999, 45:0.0070},
        'NO2' : {14:0.0961, 16:0.2232, 30:0.9999, 46:0.3703, 47:0.0010},
        'O'   : {16:0.9999},
        'O2'  : {16:0.2180, 32:0.9999},
        'Ar'  : {20:0.1462, 36:0.0030, 38:0.0005, 40:0.9999},
    }
    
    #calculated mixes
    air = {28:1, 32:0.2085, 40:0.0094}
    dictionary['Air'] = {}
    for mass,gas in zip(air.keys(),['N2','O2','Ar']):
        for mass2 in dictionary[gas].keys():
            if mass2 in dictionary['Air'].keys():
                dictionary['Air'][mass2] += dictionary[gas][mass2]*air[mass]
            else:
                dictionary['Air'][mass2] = dictionary[gas][mass2]*air[mass]

    if compound == 'content':
        return list(dictionary.keys())
    else:
        return dictionary[compound]

def correct_air(raw_data,massname='_amu',correcting_mass=40,minimum_threshold = 1e-15):
    # correcting mass spectrum for air-leakage, usually acoording to the argon partial pressure
    corrected_data = raw_data.copy()
    if correcting_mass not in mass_library('Air').keys():
        raise ValueError('Correcting mass not present in air mass spectrum')
        return corrected_data
    if 'Air corrected' in corrected_data.keys():
        if corrected_data['Air corrected'] == True:
            print('Already air corrected')
            return corrected_data
    argon_current = raw_data[correcting_mass]
    for mass in mass_library('Air').keys():
        corrected_data[mass] = np.array(raw_data[mass])-np.array(raw_data[correcting_mass])*mass_library('Air')[mass]/mass_library('Air')[40]
        if mass != correcting_mass:
            corrected_data[mass] = [i if i > minimum_threshold else minimum_threshold for i in corrected_data[mass]]
    corrected_data['Air corrected'] = True
    return corrected_data

class spectrum_fit(object):
    # this function can fit NIST mass spectra to 

    def __init__(self, ascii_data_set_path, 
                       run_sequence = True,
                       gasses=['H2O','CO','CO2','CH4','O2','N2','H2','Ar'], 
                       masses_to_skip=None,
                       pressure_normalization=False,
                       mass_name = '_amu'):

        self.gas_calibration = {#(a,b,std) in concentration=a qms_current*b
                                'CH4' : (5629,-0.117,0.04), #R2: 0.9466
                                'CO'  : (3812,-0.040,0.04), #R2: 0.9184
                                'CO2' : (6350,-0.065,0.01), #R2: 0.9466
                                'H2'  : ( 528, 0.176,0.01), #R2: 0.9086
                                'N2'  : (4070,-0.065,0.03), #R2: 0.9826
                                }
        
        self.data_set = read_RGA_prism_dat(ascii_data_set_path,mass_name = mass_name)
        self.data_path = ascii_data_set_path
        self.gas_list = gasses
        self.mlib = mass_library
        if 'Pressure_(mBar)' in self.data_set.keys() and pressure_normalization:
            self.pressure_normalization = pressure_normalization
        elif pressure_normalization:
            print('Cannot find any pressure data')
            self.pressure_normalization = False
        else:
            self.pressure_normalization = False
        
        self.skip = []
        if type(masses_to_skip) in [list,tuple,np.ndarray]:
            for mass in masses_to_skip:
                self.skip.append(mass)
        elif type(masses_to_skip) in [int,float]:
            self.skip.append(masses_to_skip)
        elif masses_to_skip == None:
            self.skip = []
        else:
            raise TypeError('"masses_to_skip" must be of type: list, tuple, np.ndarray, int, float, NoneType')
            print('I mean... there is plenty to choose...')
        
        self.set_max_mass()
        self.generate_gas_mass_list()

        if run_sequence:
            self.run_sequence()

    def retrieve_spectrum(self,row,data=None):
        # retrieve a single spectrum from the ascii time qms-data
        
        if data == None:
            data = self.data_set
        
        masses = [i for i in data.keys() if isinstance(i,int)]
        spectrum = []
        if 'Pressure_(mBar)' in data.keys() and self.pressure_normalization:
            for mass in masses:
                spectrum.append(data[mass][row]/data['Pressure_(mBar)'][row])
        else:
            for mass in masses:
                spectrum.append(data[mass][row])
        return [masses, spectrum]

    def set_max_mass(self):
        # finds maximum atomic mass present in the time-data
        
        spectrum = self.retrieve_spectrum(0)
        self.max_mass = max(spectrum[0])
        return self.max_mass

    def generate_gas_mass_list(self):
        #generate the list of atomic masses that will be fitted
        
        self.gas_masses = []
        for gas in self.gas_list:
            for key in self.mlib(gas).keys():
                if key not in self.gas_masses and key < self.max_mass and key not in self.skip:
                    self.gas_masses.append(key)
        self.gas_masses.sort()
        return self.gas_masses
    
    def add_gas(self,gas):
        self.gas_list.append(gas)
        self.generate_gas_mass_list()
        return self.gas_list

    def remove_gas(self,gas):
        self.gas_list.remove(gas)
        self.generate_gas_mass_list()
        return self.gas_list
    
    def generated_mass_spectrum(self,mass_list,*gas_amplitudes,gas_list=None):
        # generate a mass spectrum from amplitudes of the gasses

        if gas_list == None:
            gas_list = self.gas_list

        trial_currents = list(np.zeros(len(mass_list)))
        for mass in mass_list:
            for gas,gas_amp in zip(gas_list,gas_amplitudes):
                if mass in self.mlib(gas):
                    trial_currents[list(mass_list).index(mass)] += gas_amp*self.mlib(gas)[mass]
        return trial_currents
    
    def fit_gas_spectrum(self,spectrum,plot=False,plot_show=True):
        # fit gas amplitudes to a qms spectrum

        currents = []        
        for mass in self.gas_masses:
            currents.append(spectrum[1][spectrum[0].index(mass)])
        
        gas_amplitudes = []
        for gas in self.gas_list:
            primary_mass = max([(amplitude,mass) for mass, amplitude in self.mlib(gas).items()])
            if gas == 'CH4':
                #avoid mass 16
                gas_amplitudes.append(currents[self.gas_masses.index(15)]/self.mlib(gas)[15])
            elif gas == 'CO' and 'N2' in self.gas_list:
                gas_amplitudes.append(abs(currents[self.gas_masses.index(28)]-0.8*currents[self.gas_masses.index(14)]/self.mlib('N2')[14]))
            elif gas == 'N2' and 'CO' in self.gas_list:
                gas_amplitudes.append(0.8*currents[self.gas_masses.index(14)]/self.mlib(gas)[14])
            elif primary_mass not in self.skip:
                gas_amplitudes.append(currents[self.gas_masses.index(primary_mass[1])])
            else:
                gas_amplitudes.append(np.mean(currents))
        
        def func(x_data,*args):
            errorfunc = (np.array(self.generated_mass_spectrum(x_data,*args))-np.array(currents))/max(currents)
            return [abs(i) if i<0 else i*25 for i in errorfunc]
        
        fit = curve_fit(func,self.gas_masses,np.zeros(len(currents)),p0=gas_amplitudes,bounds=(0.0,np.inf))
        
        if plot:
            fig, f = plt.subplots()
            
            
            f.plot([spectrum[0][0]-0.5,*sum([[i,i+0.5] for i in spectrum[0]],[])],[*sum([[0,i] for i in spectrum[1]],[]),0],linestyle=':',label='Raw spectrum')
            f.plot(self.gas_masses,currents,'o',color='tab:blue',label='Data')
            f.plot(self.gas_masses,self.generated_mass_spectrum(self.gas_masses,*fit[0]),'*',color='tab:orange',label='Best fit to data')
            
            f.legend()
            f.set_xlabel('atomic mass')
            if self.pressure_normalization:
                f.set_ylabel('Detector current [A/mbar]')
            else:
                f.set_ylabel('Detector current [A]')
            
            if plot_show:
                plt.show()
            else:
                plt.draw()
        
        return fit
        
    def fit_time_data(self,echo=True):

        self.gas_currents = {}
        
        if self.pressure_normalization:
            unit = '_(A/mbar)'
        else:
            unit = '_(A)'
                    
        for gas in self.gas_list:
            self.data_set[gas+unit] = []
            self.gas_currents[gas+unit] = []

        self.gas_currents['reltime_(s)'] = self.data_set['Time Relative (sec)']
        self.gas_currents['abstime'] = self.data_set['Time Absolute (UTC)']
        self.gas_currents['datetime'] = self.data_set['Time Absolute (Date_Time)']
            
        print('\n')
        for indexation in range(len(self.data_set[list(self.data_set.keys())[0]])):
            
            fit = self.fit_gas_spectrum(self.retrieve_spectrum(indexation))
            
            for gas,fit_result in zip(self.gas_list,fit[0]):
                self.data_set[gas+unit].append(fit_result)
                self.gas_currents[gas+unit].append(fit_result)
                
            print(progress_bar(indexation/(len(self.data_set[list(self.data_set.keys())[0]])-1))+' '+str(indexation)+' out of '+str((len(self.data_set[list(self.data_set.keys())[0]])-1)),end='\r')

        print('\n')

        return self.data_set, self.gas_currents
    
    def calibrate_currents(self):
        if self.pressure_normalization:
            print('\nCalibrating gas concentration\n')
            for gas in self.gas_list:
                if gas in self.gas_calibration:
                    print('Calibration: '+gas)
                    self.gas_currents[gas+'_(%)'] = list(100*self.gas_calibration[gas][0]*np.array(self.gas_currents[gas+'_(A/mbar)'])+self.gas_calibration[gas][1])
                    self.gas_currents[gas+'_(std)'] = list(np.array(self.gas_currents[gas+'_(A/mbar)'])*self.gas_calibration[gas][2])
                    print('    - average '+gas+': '+str(round(np.mean(self.gas_currents[gas+'_(%)']),1))+'%')
                else:
                    print('Could not calibrate: '+gas)
                    print('    - missing calibration')
            print('Calibration done\n')
        else:
            print('No pressure normalisation. Cannot calibrate gas concentration\n')
        return self.gas_currents
                    
    def write_to_file(self,file_format,timestamp = None):
        if file_format not in ['.csv','csv','excel','xlsx','.xlsx']:
            raise TypeError('Not valid file format')
    
        df = pd.DataFrame(data=self.data_set)
        gdf = pd.DataFrame(data=self.gas_currents)
        if timestamp == None:
            tss = time_stamp_str()
        else:
            tss = timestamp
        
        if file_format in ['.csv','csv']:
            df.to_csv(tss+'_'+name_of_file(self.data_path)+'_all.csv')
            print('Wrote to file: '+tss+name_of_file(self.data_path)+'_all.csv')
            gdf.to_csv(tss+'_'+name_of_file(self.data_path)+'_gasfit.csv')
            print('Wrote to file: '+tss+name_of_file(self.data_path)+'_gasfit.csv')
        elif file_format in ['excel','xlsx','.xlsx']:
            df.to_excel(tss+'_'+name_of_file(self.data_path)+'_all.xlsx')
            print('Wrote to file: '+tss+name_of_file(self.data_path)+'_all.xlsx')
            gdf.to_excel(tss+'_'+name_of_file(self.data_path)+'_gasfit.xlsx')
            print('Wrote to file: '+tss+name_of_file(self.data_path)+'_gasfit.xlsx')

    def run_sequence(self):
        
        print('\n>>> Running QMS fit on file: '+self.data_path)
        timestamp = time_stamp_str()
        print('    - '+timestamp)
        
        qms_data,qms_gas_data = self.fit_time_data()
        
        print('Finished fitting')
        
        self.calibrate_currents()
        
        self.write_to_file('csv',timestamp=timestamp)
        self.write_to_file('excel',timestamp=timestamp)

        print('Finished program')
        
        return qms_data, qms_gas_data

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

