import numpy as np
import re
import time

import numpy as np
from matplotlib import pyplot as plt

from scipy.optimize import curve_fit
from scipy.special import erf

from skimage import restoration

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
    
    absolute_time = read_xrdml_measurement_time(path)[0]
    
    return temperature, time, absolute_time

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

class skewed_lorentzian_fitting(object):
    #fitting two lorenztians in the angle_vicinity of 35 to 55
    
    def __init__(self):
        self.common = common()

    def skewed_lorentz(self,x,x0,sigma,gamma,spectral_splitting=True,spectral_ratio=0.5):
        if spectral_splitting:
            return (1/(1+spectral_ratio))*(sigma/(np.pi*(sigma**2 + (x-x0)**2)))*((2/np.pi)*np.arctan(gamma*(x-x0)/sigma)+1)  +  (spectral_ratio/(1+spectral_ratio))*(sigma/(np.pi*(sigma**2 + (x-self.common.spectral_angle_splitting(x0))**2)))*((2/np.pi)*np.arctan(gamma*(x-self.common.spectral_angle_splitting(x0))/sigma)+1)
        else:
            return (sigma/(np.pi*(sigma**2 + (x-x0)**2)))*((2/np.pi)*np.arctan(gamma*(x-x0)/sigma)+1)

    def background(self,y,radius=100):
        return restoration.rolling_ball(y,radius=radius)
    
    def func(self,x,x1,sigma1,gamma1,A1,x2,sigma2,gamma2,A2):
        return A1*self.skewed_lorentz(x,x1,sigma1,gamma1)+A2*self.skewed_lorentz(x,x2,sigma2,gamma2)

    def find_FWHM(self,sigma,gamma,A):
        dat = np.linspace(-2*(sigma+gamma),2*(sigma+gamma),10000)
        angle_resolution = np.mean(np.diff(dat))
        dat1 = np.array(self.skewed_lorentz(dat,0,sigma,gamma))
        dat2 = np.array(abs(dat1-max(dat1)/2))
        sorted_dat2 = np.sort(dat2)
        first_index = np.where(dat2 == sorted_dat2[0])[0][0]
        index_array = []
        for value in sorted_dat2[1:]:
            test_index = np.where(dat2 == value)[0][0]
            if abs(test_index-first_index) > 0.009/angle_resolution:
                last_index = test_index
                break
        FWHM = abs(last_index-first_index)*angle_resolution
        if FWHM < 0.01:
            print('Peak to narrow to find FWHM')
            return None
        else:
            return FWHM

    def find_max_and_median(self,x0,sigma,gamma):
        dat = np.linspace(-10*(sigma+gamma)+x0,10*(sigma+gamma)+x0,50000)
        angle_resolution = np.mean(np.diff(dat))
        dat1 = np.array(self.skewed_lorentz(np.array(dat)-x0,0,sigma,gamma))
        maximum = dat[np.where(dat1 == max(dat1))[0][0]]
        normalisation = np.sum(dat1*angle_resolution)
        #print(normalisation)
        integral = 0
        for index in range(len(dat)):
            if np.sum(dat1[:index]*angle_resolution) > normalisation/2:
                median = dat[index]
                break
        return maximum, median

    def fit_to_data(self,dat_x,dat_y,init_guess=[42.7,0.1,0.1,0,49.76,0.1,0.1,10],plot=False,background_radius=40000):
        popt, pcov = curve_fit(self.func,dat_x,dat_y-self.background(dat_y,radius=background_radius),p0=init_guess)#,bounds=([0,0,0,0,0,0,0,0,-1e10],[180,1e10,1e10,1e10,180,1e10,1e10,1e10,1e10]))

        if plot:
                fig, f = plt.subplots()
                f.plot(dat_x,dat_y,label='Data')
                f.plot(dat_x,self.func(dat_x,*popt)+self.background(dat_y,radius=background_radius),label='best fit')
                f.plot(dat_x,self.background(dat_y,radius=background_radius),label='Background')

                f.set_xlabel(r'Diffraction Angle [2$\theta$]')
                f.set_ylabel('Intensity')
                f.legend(frameon=0)
                plt.tight_layout()
                plt.draw()

        return popt, pcov

    def pack_the_info(self,dat_x,dat_y,init_guess=[42.7,0.1,0.1,0,49.76,0.1,0.1,10],plot=False,background_radius=40000):
        popt, pcov = self.fit_to_data(dat_x,dat_y,init_guess=init_guess,plot=plot,background_radius=background_radius)

        peak1 = {}
        peak2 = {}

        peak1['popt'] = popt[0:4]
        peak2['popt'] = popt[4:8]
        
        peak1['Area'] = peak1['popt'][-1]
        peak2['Area'] = peak2['popt'][-1]

        peak1['max'], peak1['median'] = self.find_max_and_median(*peak1['popt'][0:3])
        peak2['max'], peak2['median'] = self.find_max_and_median(*peak2['popt'][0:3])
        
        peak1['FWHM'] = self.find_FWHM(*peak1['popt'][1:])
        peak2['FWHM'] = self.find_FWHM(*peak2['popt'][1:])
        
        return peak1, peak2

class new_xrd_fitting(object):
    #This function is written for a particular data set, and should be usd with caution

    def __init__(self):
        self.common = common()
        self.spectral_ratio = 0.5
        self.bgk_ball_radius = 100

    def lorentz(self,x,x_0,FWHM,spectral_splitting=True): #gamma = (FWHM/2)
        if spectral_splitting:
            return (1/(1+self.spectral_ratio))*(1/(np.pi*(FWHM/2)*(1+((x-x_0)/((FWHM/2)))**2))) + (self.spectral_ratio/(1+self.spectral_ratio))*(1/(np.pi*(FWHM/2)*(1+((x-self.common.spectral_angle_splitting(x_0))/((FWHM/2)))**2)))
        else:
            return 1/(np.pi*(FWHM/2)*(1+((x-x_0)/((FWHM/2)))**2))

    def gaussian(self,x,x_0,FWHM,spectral_splitting=True): #sigma = (FWHM/(2*np.sqrt(2*np.log(2))))
        if spectral_splitting:
            return (1/(1+self.spectral_ratio))*(1/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-x_0)**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2)) + (1/(1+self.spectral_ratio))*(1/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-self.common.spectral_angle_splitting(x_0))**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2))
        else:
            return (1/((FWHM/(2*np.sqrt(2*np.log(2))))*np.sqrt(2*np.pi)))*np.exp(-(x-x_0)**2 / (2*(FWHM/(2*np.sqrt(2*np.log(2))))**2))

    def pseudo_voigt(self,x,x_0,FWHM,n):
        return (1-n)*self.lorentz(x,x_0,FWHM)+n*self.gaussian(x,x_0,FWHM)

    def background(self,y,radius=100):
        self.bgk_ball_radius = radius
        return restoration.rolling_ball(y,radius=radius)
    
    def fcc(self,x,x_1,FWHM_1,I_1,I_ratio,n):
        return I_1*self.pseudo_voigt(x,x_1,FWHM_1,n)+I_1*I_ratio*self.pseudo_voigt(x,self.common.angle_200(x_1),self.common.FWHM_200(FWHM_1,x_1),n)

    def bcc(self,x,x_1,FWHM_1,I_1,n):
        return I_1*self.pseudo_voigt(x,x_1,FWHM_1,n)
    
    def func(self,x,x_1,FWHM_1,I_1,I_ratio_1,x_2,FWHM_2,I_2,x_3,FWHM_3,I_3,n,a):
        #return self.fcc(x,x_1,FWHM_1,I_1,I_ratio_1,n)+self.fcc(x,x_2,FWHM_2,I_2,I_ratio_2,n)+I_3*self.pseudo_voigt(x,x_3,FWHM_3,n)+a
        return self.fcc(x,x_1,FWHM_1,I_1,I_ratio_1,n)+self.fcc(x,x_2,FWHM_2,I_2,I_ratio_1,n)+I_3*self.pseudo_voigt(x,x_3,FWHM_3,n)+a

    def fit_to_data(self,pattern,plot=False,init_guess=[42.6, 2.0, 10, 0.44, 43.25, 1.0, 10, 44.3, 0.9, 10, 0.1],lower_bound=None,upper_bound=None,bgk_radius=100):
        background = self.background(pattern[1],radius=bgk_radius)
        y_data = np.array(pattern[1])-np.array(background)
        
        if lower_bound == None and upper_bound == None:
            popt, pcov = curve_fit(self.func,np.array(pattern[0]),y_data,p0=[*init_guess,0])
        else:
            popt, pcov = curve_fit(self.func,np.array(pattern[0]),y_data,p0=[*init_guess,0],bounds=([*lower_bound,-1e10],[*upper_bound,1e10]))
                
        class result:
            def __init__(self):
                self.popt = popt
                self.pcov = pcov
                self.bgk_data = background
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

        if plot:
            fig, f = plt.subplots()
            f.plot(pattern[0],pattern[1],label='Data')
            f.plot(pattern[0],self.func(pattern[0],*popt)+res.bgk_data,label='best fit')

            f.set_xlabel(r'2$\theta$ Diffraction angle [$^{\circ}$]')
            f.set_ylabel('Intensity [cts/s]')
            f.legend(frameon=0)
            plt.tight_layout()
            plt.draw()


            fig, f = plt.subplots()
            f.plot(pattern[0],pattern[1],label='Data')
            f.plot(pattern[0],self.func(pattern[0],*popt)+res.bgk_data,label='best fit')
            f.plot(pattern[0],self.fcc(pattern[0],*popt[0:4],popt[-2])+res.bgk_data+popt[-1],label='Primary FCC')
            f.plot(pattern[0],self.fcc(pattern[0],*popt[4:7],popt[3],popt[-2])+res.bgk_data+popt[-1],label='Shoulder FCC')
            f.plot(pattern[0],self.bcc(pattern[0],*popt[7:10],popt[-2])+res.bgk_data+popt[-1],label='BCC')
            f.plot(pattern[0],res.bgk_data+popt[-1],label='background')
            f.set_xlabel(r'2$\theta$ Diffraction angle [$^{\circ}$]')
            f.set_ylabel('Intensity [cts/s]')
            f.legend(frameon=0)
            plt.tight_layout()
            plt.draw()    

        return res

class xrd_fitting(object):
    #This function is written for a particular purpose, and shouldn't be used

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

        if plot:
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
            f.plot(pattern[0],self.fcc(pattern[0],*popt[0:4],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='Primary FCC')
            f.plot(pattern[0],self.fcc(pattern[0],*popt[4:8],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='Shoulder FCC')
            f.plot(pattern[0],self.bcc(pattern[0],*popt[8:11],popt[-1])+self.background(pattern[0],*popt[11:-1]),label='BCC')
            f.plot(pattern[0],self.background(pattern[0],*popt[11:-1]),label='background')
            f.set_xlabel(r'Diffraction Angle [$^{\circ}$2$\theta$]')
            f.set_ylabel('Intensity [cts/s]')
            f.legend(frameon=0)
            plt.tight_layout()
            plt.draw()    

        return res