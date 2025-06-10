import numpy as np
from matplotlib import pyplot as plt
import matplotlib.pylab as pl
from matplotlib import cm
import os
from scipy.optimize import curve_fit

from stuff.common.filters import smooth
from stuff.common.import_tools import load_data_with_names
from stuff.math.statistics import index_min, index_max, polynomial_fit
from stuff.math.filters import eliminate_phaseshift
from stuff.math.functions import polynomial_function

def format_e(n):
    a = '%E' % n
    return a.split('E')[0].rstrip('0').rstrip('.') + 'E' + a.split('E')[1]

def IV(I,V,area='',nernst=False):
    if area == '':
        I = np.array(I)
    else:
        I = np.array(I)/area
    V = np.array(V)
    if nernst:
        return I, V
    else:
        Ip0 = np.where(np.array(I) == min(abs(I)))[0]
        Im0 = np.where(np.array(I) == -min(abs(I)))[0]
        V0 = np.mean(V[[*Ip0,*Im0]])
        return I, V-V0

def EIS_datafile(file_path):
    return EIS_data(load_data_with_names(file_path))

def fit_for_deareis(filepath,area = 1):
    file = open(filepath)
    if area != 1:
        new_filepath = filepath[:-len(filepath.split('.')[-1])-1]+'_ffd_'+str(area)+'.'+filepath.split('.')[-1]
    else:
        new_filepath = filepath[:-len(filepath.split('.')[-1])-1]+'_ffd.'+filepath.split('.')[-1]
    if os.path.exists(new_filepath):
        raise FileExistsError(f"The file '{new_filepath}' already exists.")
    else:
        new_file = open(new_filepath,'a')
        new_file.write('f,re,im\n')
        for line in file.readlines()[1:]:
            new_line = [str(float(i)*area) for i in line.split(',')]
            new_file.write(','.join(new_line)+'\n')
        new_file.close()
    return new_filepath

class IV_class(object):

    def __init__(self,I,V,area='',polynomial_order=7,calibrate=True):
        self.I = np.array(I)
        self.V = np.array(V)
        if calibrate:
            try:
                self.I, self.V = self.calibrate_I_and_V(I,V)
            except:
                print('Could not perform phase correction')
        self.area   = area
        self.I_area = self.I/self.area
        self.polyfit_IV(order=polynomial_order)
        if area != '':
            self.ASR = self.R*area
        else:
            self.ASR = ''

    def calibrate_I_and_V(self,I,V):
        return eliminate_phaseshift(I,V)

    def polyfit_IV(self,order=7):
        self.popt,self.pov = polynomial_fit(self.I,self.V,order)
        self.OCV    = self.popt[0]
        self.R      = self.popt[1]
        self.fitV   = polynomial_function(self.I,*self.popt)
        self.V_mOCV = self.V-self.OCV
        return self.I,self.fitV

    def plot(self,title='',show=True,digits=3):
        fig, f = plt.subplots()
        f.plot(self.I,self.V,label='data',marker='s',color='k')
        f.plot(self.I,self.fitV,label='fitted')
        f.plot(self.I,self.OCV+self.R*self.I,label='R: '+str(round(10**digits*self.R)/10**digits))
        f.axhline(self.OCV,label='OCV: '+str(round(10**digits*self.OCV)/10**digits))
        f.legend(title=title,frameon=0)
        f.set_ylabel('Voltage')
        f.set_xlabel('Current')
        if show:
            plt.show()
        else:
            plt.draw()

    #def IV(self,I,V,area='',nernst=False):
    #    if area == '':
    #        I = np.array(I)
    #    else:
    #        I = np.array(I)/area
    #    V = np.array(V)
    #    if nernst:
    #        return I, V
    #    else:
    #        Ip0 = np.where(np.array(I) == min(abs(I)))[0]
    #        Im0 = np.where(np.array(I) == -min(abs(I)))[0]
    #        V0 = np.mean(V[[*Ip0,*Im0]])
    #        return I, V-V0

    #def zero_current_resistance(self,I,V,based_values=10):
    #    i = np.where(abs(np.array(I))==min(abs(np.array(I))))[0][0]
    #    R = np.diff(V[i-based_values:i+based_values])/np.diff(I[i-based_values:i+based_values])
    #    return np.mean([j for j in R if j < np.inf and j > -np.inf])


class EIS_figure(object):

    def __init__(self):
        self.figure_size = (8,5)
        self.unit = '$\Omega$ cm$^2$'
        self.figure, self.ax = plt.subplots()

    def set_equal_aspect(self,ax):
        plt.gca().set_aspect('equal', adjustable='box')
        x_length = abs(np.diff(ax.axes.get_xlim())[0])
        y_length = abs(np.diff(ax.axes.get_ylim())[0])
        x_over_y = x_length/y_length

        fig = ax.figure
        h, w = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).height, ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width
        area = h*w
        h = np.sqrt(area/x_over_y)
        w = np.sqrt(area*x_over_y)
        if h > w:
            fig.set_size_inches(w*(1/x_over_y)**(1/3), h, forward=True)
        else:
            fig.set_size_inches(w, h*(x_over_y)**(1/3), forward=True)

        return ax

    def aesthetics(self,figure,ax,title='',grid=True):
        figure.set_size_inches(self.figure_size[0],self.figure_size[1])
        ax.set_xlabel(r"Z' ["+self.unit+"]")
        ax.set_ylabel(r"Z'' ["+self.unit+"]")
        ax = self.set_equal_aspect(ax)
        plt.gca().invert_yaxis()
        ax.grid(visible=grid)
        ax.legend(title=title)#frameon=0,ncol=1)
        return figure, ax

    def man_aesthetics(self,figure,ax,xlim,ylim,title='',grid=True,size=''):
        if type(size) == list:
            figure.set_size_inches(size[0],size[1])
        else:
            figure.set_size_inches(self.figure_size[0],self.figure_size[1])
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(r"Z' ["+self.unit+"]")
        ax.set_ylabel(r"Z'' ["+self.unit+"]")
        plt.gca().set_aspect('equal')
        plt.gca().invert_yaxis()
        ax.grid(visible=grid)
        ax.legend(title=title)#frameon=0,ncol=1)
        return figure, ax

    def plot(self, data_set, label='',color='k',freq_annotation=False,linestyle='-'):
        for key in data_set.keys():
            if 'R' in key:
                R_key = key
            if 'F' in key:
                F_key = key
            if 'I' in key:
                I_key = key

        self.ax.plot(data_set[R_key],data_set[I_key],color=color,label=label,linestyle=linestyle)
        if freq_annotation:
            potens = 0.001
            for F in data_set[F_key]:
                if round(F*potens) != 0:
                    potens = 1/potens
                    break
                potens = potens*10

            for Re,Im,F in zip(data_set[R_key],data_set[I_key],data_set[F_key]):
                if F > potens:
                    self.ax.text(Re,Im,format_e(potens)+' Hz')
                    potens = potens*10

    def draw(self,grid=True,legend_title=''):
        self.aesthetics(self.figure,self.ax,grid=grid,title=legend_title)
        plt.tight_layout()
        plt.draw()

class EIS_data(object):

    def __init__(self,data_set):
        self.data   = data_set
        self.keys   = self.find_keys()
        self.Real   = data_set[self.keys[0]]
        self.Imag   = data_set[self.keys[1]]
        self.Freq   = data_set[self.keys[2]]
        self.Rs     = self.find_Rs()[0]
        self.Rtot   = self.find_Rtot()[0]
        self.Rp     = self.find_Rp()[0]

        self.normalized = 'NO'

    def find_keys(self):
        for key in self.data.keys():
            if 'R' in key:
                R_key = key
            if 'F' in key:
                F_key = key
            if 'I' in key:
                I_key = key
        return R_key, I_key, F_key

    def limit_data(self,start,end):
        self.Real = self.Real[start:end]
        self.Imag = self.Imag[start:end]
        self.Freq = self.Freq[start:end]

    def find_Rs(self):
        if np.diff(self.Imag)[-1] > 0:
            sign = 1
        elif np.diff(self.Imag)[-1] < 0:
            sign = -1
        for i in range(1,len(self.Imag)):
            if sign*np.diff(self.Imag)[-i] < 0:
                break
        i = i-1

        lower_limit = min(self.Imag[0:-i])
        upper_limit = max(self.Imag[0:-i])
        if upper_limit < 0:
            upper_limit = 0
        for j in range(len(self.Imag[-i:])):
            if self.Imag[-i:][j] > upper_limit or self.Imag[-i:][j] < lower_limit:
                Rs_index = j
                break
        return self.Real[-i:][j], j-i

    def simpleRs(self):
        pass

    def find_Rtot(self):
        return self.Real[0], 0

    def find_Rp(self):
        return self.Rtot-self.Rs, np.nan

    def normalize(self,area,norm_unit = ''):
        self.Real = self.Real*area
        self.Imag = self.Imag*area
        self.unit = norm_unit
        self.normalization_area = area
        self.Rs     = self.find_Rs()[0]
        self.Rtot   = self.find_Rtot()[0]
        self.Rp     = self.find_Rp()[0]

        self.normalized = 'YES'
        return self.Freq,self.Real,self.Imag

    def Nyquist(self,color='k',linestyle='-',freq_annotation=False,R_annotation=False,legend=False,subfigure=False):
        figure = EIS_figure()
        try:
            figure.unit = self.unit
        except AttributeError:
            print('No unit. Using Eis figure object unit: ', EIS_fig.unit)

        if R_annotation:
            Rs = self.find_Rs()
            Rtot = self.find_Rtot()
            if legend:
                figure.ax.plot(Rs[0],self.Imag[Rs[1]],'s',label='Rs',color=color,linestyle=linestyle)
                figure.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',label='Rtot',color=color,linestyle=linestyle)
            else:
                figure.ax.plot(Rs[0],self.Imag[Rs[1]],'s',color=color,linestyle=linestyle)
                figure.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',color=color,linestyle=linestyle)
        figure.plot(self.data,freq_annotation=freq_annotation,color=color,linestyle=linestyle)
        figure.draw()

    def Nyquist_curve(self,EIS_fig,color='k',label='',freq_annotation=False,R_annotation=False,legend=False,linestyle='-'):
        #used to generate plots with multiple graphs. The point is to feed the
        #"figure object" as "EIS_fig", which is then returned with the new nyquist-graph

        try:
            EIS_fig.unit = self.unit
        except AttributeError:
            print('No unit. Using Eis figure object unit: ', EIS_fig.unit)

        if R_annotation:
            Rs = self.find_Rs()
            Rtot = self.find_Rtot()
            if legend:
                EIS_fig.ax.plot(Rs[0],self.Imag[Rs[1]],'s',label='Rs',color=color)
                EIS_fig.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',label='Rtot',color=color)
            else:
                EIS_fig.ax.plot(Rs[0],self.Imag[Rs[1]],'s',color=color)
                EIS_fig.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',color=color)
        EIS_fig.plot({'R' : self.Real, 'I' : self.Imag, 'F' : self.Freq}, freq_annotation=freq_annotation,color=color,label=label,linestyle=linestyle)
        return EIS_fig

class ADIS_cal(object):

    def __init__(self,EIS_data_1,EIS_data_2):
        self.R = EIS_data_1.Real-EIS_data_2.Real
        self.I = EIS_data_1.Imag-EIS_data_2.Imag
        self.F = EIS_data_1.Freq

    def Real(self):
        return self.F, self.R

    def Imag(self):
        return self.F, self.I

    def dReal(self,smoothing=10):
        return self.F[1:], smooth(np.diff(self.R)/np.diff(np.log10(self.F)),smoothing)

    def dImag(self,smoothing=10):
        return self.F[1:], smooth(np.diff(self.I)/np.diff(np.log10(self.F)),smoothing)
