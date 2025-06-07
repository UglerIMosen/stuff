# -*- coding: utf-8 -*-
"""
@author: thoe
"""
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from matplotlib import pyplot as plt

from stuff.math.functions import polynomial_function

def index_min(array):
    output = np.where(array == min(array))
    return output[0][0], min(array), output[0]

def index_max(array):
    output = np.where(array == max(array))
    return output[0][0], max(array), output[0]

def rsqr(ydat,model_dat):
    return 1-sum((np.array(ydat)-np.array(model_dat))**2)/sum((np.array(ydat)-np.mean(ydat))**2)

def polynomial_fit(xdata,ydata,order,p0=None):
    #make a polynomial fit of order. p0 is a list of initial guesses starting at lowest order
    if p0 == None:
        p0 = np.ones(order)
    else:
        if len(p0) != order:
            raise ValueError('len of p0 needs to match the specified order')
    popt, pcov = curve_fit(polynomial_function, xdata, ydata,p0=p0)
    return popt,pcov

def linear_fit_plot(datx_raw,daty_raw,plotshow=True,title=None,intercept=True,start_index=0,end_index=0):
    if start_index == 0 and end_index == 0:
        datx = datx_raw
        daty = daty_raw
    elif start_index != 0 and end_index == 0:
        datx = datx_raw[start_index:]
        daty = daty_raw[start_index:]
    elif start_index != 0 and end_index != 0:
        datx = datx_raw[start_index:end_index]
        daty = daty_raw[start_index:end_index]

    if not intercept or intercept == 0:
        def func(x,a):
            return a*x
        res = curve_fit(func,datx,daty)
        slope = res[0][0]
        s_std = np.sqrt(res[1][0][0])
        intercept = 0
        i_std = 0
        r2 = rsqr(daty,np.array(datx)*slope+intercept)
    elif type(intercept) in [int,float]:
        def func(x,a):
            return a*x+intercept
        res = curve_fit(func,datx,daty)
        slope = res[0][0]
        s_std = np.sqrt(res[1][0][0])
        intercept = intercept
        i_std = 0
        r2 = rsqr(daty,np.array(datx)*slope+intercept)
    else:
        res = linregress(datx,daty)
        slope = res.slope
        s_std = res.stderr
        intercept = res.intercept
        i_std = res.intercept_stderr
        r2 = rsqr(daty,np.array(datx)*slope+intercept)

    print('slope',slope)
    print('    +-',s_std)
    print('intercept',intercept)
    print('    +-',i_std)
    print('R2',r2)

    fig, f = plt.subplots()
    f.plot(datx_raw,daty_raw,'o',label='data')
    f.plot(datx,daty,'o',label='data')
    f.plot([0,*datx],[intercept,*np.array(datx)*slope+intercept],label=r'fit: $y = ax+b$')

    f.set_xlabel('Xdata')
    f.set_ylabel('Ydata')

    f.legend(title='$a$: '+str(round(slope,4))+'$\pm$'+str(round(s_std,4))+'\n$b$: '+str(round(intercept,4))+'$\pm$'+str(round(i_std,4))+'\n$R^2$: '+str(round(r2,4)))
    if type(title) == str:
        f.set_title(title)

    plt.draw()
    if plotshow:
        plt.show()

    return slope,intercept,s_std,i_std
