import numpy as np
import re
import time

import numpy as np
from matplotlib import pyplot as plt

from scipy.optimize import curve_fit
from scipy.special import erf

def read_xrdml_wavelength(path):
    #wave_length of source
    raw_file = open(path)
    lines = raw_file.readlines()
    for index, line in enumerate(lines):
        if line.find('<usedWavelength intended="K-Alpha 1">') != -1:
            kAlpha1 = [float(value) for value in re.findall(r'\d+\.\d+',lines[index+1])]
            kAlpha2 = [float(value) for value in re.findall(r'\d+\.\d+',lines[index+2])]
            ratio_kA2_over_kA1 = [float(value) for value in re.findall(r'\d+\.\d+',lines[index+4])]
            wavelength = (ratio_kA2_over_kA1[0]*kAlpha2[0]+kAlpha1[0])/(ratio_kA2_over_kA1[0]+1)
            break
    return wavelength

def read_xrdml_pattern(path):
#read pattern 
    file = open(path)
    lines = file.readlines()

    for index, line in enumerate(lines):
        if line.find('<positions axis="2Theta" unit="deg">') != -1:
            start_angle = [float(value) for value in re.findall(r'\d+\.\d+',lines[index+1])]
            end_angle = [float(value) for value in re.findall(r'\d+\.\d+',lines[index+2])]
    
        if line.find('intensities') != -1:
            spectrum = [float(value) for value in re.findall(r'\d+',lines[index])]
            spectrum = np.array(spectrum)
    
        if line.find('<commonCountingTime unit="seconds">') != -1:
            integral_time = float(re.findall(r'\d+\.\d+',lines[index])[0])
        
        
    angle_step = (end_angle[0]-start_angle[0])/len(spectrum)
    angles = np.arange(start_angle[0],end_angle[0],angle_step)
    return angles, spectrum, integral_time

def read_xrdml_temp(path):
    raw_file = path
    lines = open(raw_file).readlines()
    for index, line in enumerate(lines):
        if line.find('<nonAmbientPoints>') != -1:
            break
    temperature = np.array([float(value) for value in re.findall(r'\d+',lines[index+2])])

    time = np.array([float(value) for value in re.findall(r'\d+',lines[index+1])])
    len_diff = len(time) - len(temperature)
    if len_diff > 0:
        time = time[0:len(time)-len_diff]
    elif len_diff < 0:
        temperature = temperature[0:len(temperature)+len_diff]

    return temperature, time

def read_xrdml_measurement_time(path):
    #creation time of data file
    raw_file = open(path)
    lines = raw_file.readlines()
    for index, line in enumerate(lines):
        if line.find('<startTimeStamp>') != -1:
            out = [int(value) for value in re.findall(r'\d+',line)]
            break
    absolute_time = time.mktime(tuple([*out,-1]))
    time_object = time.localtime(absolute_time)
    return absolute_time, time_object



class common(object):

    def __init__(self):
        self.anode = 'Cu'
        self.anode_lines = {'Cu': [1.5405980,1.5444260]}

    def inverse_length(self,angles,wavelength):
        #Bragg's law, for angles to inverse length
        angles = np.pi*np.array(angles)/180
        return 2*np.sin(angles/2)/wavelength

    def scherrer(self,angle_2theta,FWHM,broadening=0.1,formfactor = 0.9, wavelength=1.5405980):
        return formfactor*wavelength/((FWHM*np.pi/180)*np.cos(0.5*angle_2theta*np.pi/180))

    def spectral_angle_splitting(self,x_0):
        return 2*np.arcsin( (self.anode_lines[self.anode][1]/self.anode_lines[self.anode][0])*np.sin((x_0/2)*np.pi/180) )*180/np.pi

    def angle_200(self,angle_111):
        return 2*np.arcsin(2*np.sin((angle_111/2)*np.pi/180)/np.sqrt(3))*180/np.pi

    def FWHM_200(self,FWHM_111,angle_111):
        return FWHM_111*np.cos((angle_111/2)*np.pi/180)/np.cos((self.angle_200(angle_111)/2)*np.pi/180)



class xrd_fitting(object):

    def __init__(self):
        self.common = common()
        self.spectral_ratio = 0.5

    def lorentz(self,x,x_0,FWHM,spectral_splitting=True): #gamma = (FWHM/2)
        if spectral_splitting:
            return (1/(np.pi*(FWHM/2)*(1+((x-x_0)/((FWHM/2)))**2)) + self.spectral_ratio/(np.pi*(FWHM/2)*(1+((x-self.common.spectral_angle_splitting(x_0))/((FWHM/2)))**2)))/(1+self.spectral_ratio)
        else:
            return 1/(np.pi*(FWHM/2)*(1+((x-x_0)/((FWHM/2)))**2))

    def gaussian(self,x,x_0,FWHM,spectral_splitting=True): #sigma = (FWHM/(2*np.sqrt(2*np.log(2))))
        if spectral_splitting:
            return ((1/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-x_0)**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2)) + (self.spectral_ratio/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-self.common.spectral_angle_splitting(x_0))**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2)))/(1+self.spectral_ratio)
        else:
            return (1/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-x_0)**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2))

    def pseudo_voigt(self,x,x_0,FWHM,n):
        return (1-n)*self.lorentz(x,x_0,FWHM)+n*self.gaussian(x,x_0,FWHM)

    def background(self,x,a,b,c):
        return a+b*erf(0.2*(x-c-44))
    
    def fcc(self,x,x_1,FWHM_1,I_1,I_ratio,n):
        return I_1*self.pseudo_voigt(x,x_1,FWHM_1,n)+I_1*I_ratio*self.pseudo_voigt(x,self.common.angle_200(x_1),self.common.FWHM_200(FWHM_1,x_1),n)

    def bcc(self,x,x_1,FWHM_1,I_1,n):
        return I_1*self.pseudo_voigt(x,x_1,FWHM_1,n)
    
    def func(self,x,x_1,FWHM_1,I_1,I_ratio_1,x_2,FWHM_2,I_2,I_ratio_2,x_3,FWHM_3,I_3,slope_0,slope_1,slope_2,n):
        return self.fcc(x,x_1,FWHM_1,I_1,I_ratio_1,n)+self.fcc(x,x_2,FWHM_2,I_2,I_ratio_2,n)+I_3*self.pseudo_voigt(x,x_3,FWHM_3,n)+self.background(x,slope_0,slope_1,slope_2)

    def fit_to_data(self,pattern,plot=False,init_guess=[42.8, 2,   1000,   0.44, 43.6, 2,   1000,   0.44, 44.4, 0.5, 10000,  5000,  1000,  0.1, 0.1],lower_bound=None,upper_bound=None):
        if lower_bound == None and upper_bound == None:
            popt, pcov = curve_fit(self.func,np.array(pattern[0]),np.array(pattern[1]),p0=init_guess)
        else:
            popt, pcov = curve_fit(self.func,np.array(pattern[0]),np.array(pattern[1]),p0=init_guess,bounds=(lower_bound,upper_bound))
                
        class result:
            def __init__(self):
                self.popt = popt
                self.pcov = pcov
                self.background = [popt[-3],popt[-2],popt[-1],]
                self.dict = {}
                self.fcc = 0
                self.bcc = 0
            
            def write_fcc(self,angle,FWHM,intensity,intensity_ratio):
                name = 'fcc '+str(self.fcc)
                self.fcc += 1
                self.dict[name] = {}
                self.dict[name]['angle'] = angle
                self.dict[name]['FWHM'] = FWHM
                self.dict[name]['I'] = intensity
                self.dict[name]['I_ratio'] = intensity_ratio            

            def write_bcc(self,angle,FWHM,intensity):
                name = 'bcc '+str(self.bcc)
                self.bcc += 1
                self.dict[name] = {}
                self.dict[name]['angle'] = angle
                self.dict[name]['FWHM'] = FWHM
                self.dict[name]['I'] = intensity
    
        res = result()
    
        res.write_fcc(*popt[0:4])
        res.write_fcc(*popt[4:8])
        res.write_bcc(*popt[8:11])

        if plot == True:
            fig, f = plt.subplots()
            f.plot(pattern[0],pattern[1],label='Data')
            f.plot(pattern[0],self.func(pattern[0],*popt),label='best fit')

            f.set_xlabel(r'Diffraction Angle [2$\theta$]')
            f.set_ylabel('Intensity')
            f.legend(frameon=0)
            plt.tight_layout()
            plt.draw()


            fig, f = plt.subplots()
            f.plot(pattern[0],pattern[1],label='Data')
            f.plot(pattern[0],self.func(pattern[0],*popt),label='best fit')
            f.plot(pattern[0],self.fcc(pattern[0],*popt[0:4],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='fcc 1')
            f.plot(pattern[0],self.fcc(pattern[0],*popt[4:8],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='fcc 2')
            f.plot(pattern[0],self.bcc(pattern[0],*popt[8:11],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='bcc 1')
            f.plot(pattern[0],self.background(pattern[0],*popt[11:-1]),label='background')
            f.set_xlabel(r'Diffraction Angle [2$\theta$]')
            f.set_ylabel('Intensity')
            f.legend(frameon=0)
            plt.tight_layout()
            plt.draw()    

        return res