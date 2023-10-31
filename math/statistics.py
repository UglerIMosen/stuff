# -*- coding: utf-8 -*-
"""
@author: thoe
"""
from scipy.stats import linregress
from scipy.optimize import curve_fit

import numpy as np
from matplotlib import pyplot as plt

def rsqr(ydat,model_dat):
    return 1-sum((np.array(ydat)-np.array(model_dat))**2)/sum((np.array(ydat)-np.mean(ydat))**2)


def linear_fit_plot(datx,daty,plotshow=True,title=None,intercept_zero=False):
    if intercept_zero:
        def func(x,a):
            return a*x
        res = curve_fit(f,datx,daty)
        slope = res[0][0]
        s_std = np.sqrt(res[1][0])
        intercept = 0
        i_std = 0
        r2 = rsqr(daty,np.array(datx)*slope+intercept)        
    else:
        res = linregress(datx,daty)
        slope = res.slope
        s_std = res.stderr
        intercept = res.intercept
        i_std = res.intercept_stderr
        r2 = r_squared(daty,np.array(datx)*slope+intercept)
        
    fig, f = plt.subplots()
    f.plot(datx,daty,'o',label='data')
    f.plot(datx,np.array(datx)*slope+intercept,label=r'fit: $y = ax+b$')
    
    f.set_xlabel('Xdata')
    f.set_ylabel('Ydata')
    
    f.legend(title='$a$: '+str(round(slope,4))+'$\pm$'+str(round(s_std,4))+
                  '\n$b$: '+str(round(intercept,4))+'$\pm$'+str(round(i_std,4))+
                '\n$R^2$: '+str(round(r2,4))
            ) 
    if type(title) == str:
        f.set_title(title)
    
    plt.draw()
    if plotshow:
        plt.show()
    
    return slope,intercept,s_std,i_std

