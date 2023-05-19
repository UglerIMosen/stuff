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
        self.ax.plot(data_set['Real'],data_set['Imag'],color=color,label=label)
        if freq_annotation:
            potens = 0.001
            for F in data_set['Frequency (Hz)']:
                if round(F*potens) != 0:
                    potens = 1/potens
                    break
                potens = potens*10
            
            for Re,Im,F in zip(data_set['Real'],data_set['Imag'],data_set['Frequency (Hz)']):
                if F > potens:
                    self.ax.text(Re,Im,format_e(potens)+' Hz')
                    potens = potens*10
        
    def draw(self):
        self.aesthetics(self.figure,self.ax)
        plt.tight_layout()
        plt.draw()