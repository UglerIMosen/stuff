import numpy as np
from matplotlib import pyplot as plt
import matplotlib.pylab as pl
from matplotlib import cm

def format_e(n):
    a = '%E' % n
    return a.split('E')[0].rstrip('0').rstrip('.') + 'E' + a.split('E')[1]

class EIS_figure(object):

    def __init__(self):
        self.figure_size = (8,10)
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

    def aesthetics(self,figure,ax):
        figure.set_size_inches(self.figure_size[0],self.figure_size[1])
        ax.set_xlabel(r"Z' ["+self.unit+"]")
        ax.set_ylabel(r"Z'' ["+self.unit+"]")
        ax = self.set_equal_aspect(ax)
        plt.gca().invert_yaxis()
        ax.grid(visible=True)
        ax.legend()#frameon=0,ncol=1)                
        return figure, ax
        
    def plot(self, data_set, label='',color='k',freq_annotation=False):
        for key in data_set.keys():
            if 'R' in key:
                R_key = key
            if 'F' in key:
                F_key = key
            if 'I' in key:
                I_key = key
        
        self.ax.plot(data_set[R_key],data_set[I_key],color=color,label=label)
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
        
    def draw(self):
        self.aesthetics(self.figure,self.ax)
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
    
    def find_keys(self):
        for key in self.data.keys():
            if 'R' in key:
                R_key = key
            if 'F' in key:
                F_key = key
            if 'I' in key:
                I_key = key
        return R_key, I_key, F_key
        
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
        
    def find_Rtot(self):
        return self.Real[0], 0
    
    def find_Rp(self):
        return self.Rtot-self.Rs, np.nan
    
    def Nyquist(self,color='k',freq_annotation=False,R_annotation=False,legend=False,subfigure=False):
        figure = EIS_figure()
        figure.plot(self.data,freq_annotation=freq_annotation,color=color)
        if R_annotation:
            Rs = self.find_Rs()
            Rtot = self.find_Rtot()
            if legend:
                figure.ax.plot(Rs[0],self.Imag[Rs[1]],'s',label='Rs',color=color)
                figure.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',label='Rtot',color=color)
            else:
                figure.ax.plot(Rs[0],self.Imag[Rs[1]],'s',color=color)
                figure.ax.plot(Rtot[0],self.Imag[Rtot[1]],'o',color=color)
        figure.draw()

