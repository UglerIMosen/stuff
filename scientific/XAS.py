import numpy as np
import re
import time

import numpy as np
from matplotlib import pyplot as plt

from scipy.optimize import minimize
from scipy.optimize import LinearConstraint
from scipy.optimize import shgo

def XANES_linear_combination_fitting(xy_data,y_references,plot=False):
    #y_reference should share x-axis with xy_data
    def best_fit_error(a):
        fit_curve = 0
        for reference, a_n in zip(y_references,a):
            fit_curve = fit_curve+a_n*np.array(reference)
        return np.sum(np.absolute(np.array(xy_data[1])-a[-1]*fit_curve))
    
    bnds = []
    for reference in y_references:
        bnds.append((0,1))
    bnds.append((0.9,1.1))
    
    con = ({'type': 'eq', 'fun': lambda a: np.sum(a[0:-1])-1})
    results = shgo(best_fit_error, bounds=bnds, constraints=con, options=({'minimize_every_iter': True}))
    
    if plot:
        a = results.x
        best_fit = 0
        for reference, a_n in zip(y_references,a):
            best_fit = best_fit+a_n*np.array(reference)
        best_fit = a[-1]*best_fit
        
        fig, f = plt.subplots()
        f.plot(xy_data[0],best_fit,label='Fit',color='tab:blue')
        f.plot(xy_data[0],xy_data[1],'.',label='Data',color='tab:red')
        f.plot(xy_data[0],best_fit,label='Fit amplitude: '+str(100*round(a[-1],2))+'%',color='white')
        count = 1
        for a_n in a[:-1]:
            f.plot(xy_data[0],best_fit,label='Ref. '+str(count)+': '+str(100*round(a_n,2))+'%',color='white')
            count += 1
        f.plot(xy_data[0],best_fit,color='tab:blue')
        f.plot(xy_data[0],xy_data[1],'.',color='tab:red')
        f.legend(frameon=0)        
        f.set_ylabel('Normalized Intensity')
        f.set_xlabel('Energy [keV]')
        plt.draw()
        plt.show()
    
    return results