import numpy as np
import re
import time

import numpy as np
from matplotlib import pyplot as plt

from scipy.optimize import minimize
from scipy.optimize import LinearConstraint
from scipy.optimize import shgo

import warnings

from stuff.common.filters import derivative, smooth

def find_binding_energy(edge,smooth_pts=1):
    dev_edge = derivative([edge[0],smooth(edge[1],smooth_pts)])
    dev2_edge = derivative([dev_edge[0][smooth_pts:-smooth_pts],dev_edge[1][smooth_pts:-smooth_pts]])
    #edge_2nd_dev_min = (dev_edge[0][np.where(dev_edge[1] == max(dev_edge[1]))[0][0]]+dev_edge[0][np.where(dev_edge[1] == min(dev_edge[1]))[0][0]])/2
    edge_2nd_dev_min = dev_edge[0][np.where(dev2_edge[1] == min(dev2_edge[1]))[0][0]]
    return edge_2nd_dev_min

def calibrate_edge(edge,ref_edge,smooth_pts=1):
    #This function calibrates by the average between the minimum and maximum of the first derivative. This is more alternative than taking the minimum of the second derivative. But in terms of real data, the second derivative can be very very noisy. This solution should be close.
    #dev_edge = derivative(edge)
    #edge_2nd_dev_min = (dev_edge[0][np.where(dev_edge[1] == max(dev_edge[1]))[0][0]]+dev_edge[0][np.where(dev_edge[1] == min(dev_edge[1]))[0][0]])/2
    edge_2nd_dev_min = find_binding_energy(edge,smooth_pts=1)
    ref_2nd_dev_min = find_binding_energy(ref_edge,smooth_pts=1)
    #dev_ref = derivative(ref_edge)
    #ref_2nd_dev_min = (dev_ref[0][np.where(dev_ref[1] == max(dev_ref[1]))[0][0]]+dev_ref[0][np.where(dev_ref[1] == min(dev_ref[1]))[0][0]])/2
    return ref_2nd_dev_min-edge_2nd_dev_min

def normalise_fluorescence(edge,pre_edge_energy = -0.05, extended_edge_energy = 0.03,smooth_pts=1):
    bnd_energy = find_binding_energy(edge,smooth_pts=1)
    pre_edge = np.where(edge[0] < bnd_energy+pre_edge_energy)
    extended_edge = np.where(edge[0] > bnd_energy+extended_edge_energy)

    dat_x = edge[0][extended_edge[0][0]:extended_edge[0][-1]]
    dat_y = edge[1][extended_edge[0][0]:extended_edge[0][-1]]
    slope = np.polyfit(dat_x,dat_y,1)[0]
    def normalisation_func(x):
        if x < bnd_energy:
            return 0
        elif x >= bnd_energy:
            return (x-bnd_energy)*slope
    normal_intensity = [i-normalisation_func(j) for i,j in zip(edge[1],edge[0])]

    pre_edge_y = normal_intensity[pre_edge[0][0]:pre_edge[0][-1]]
    extended_edge_y = normal_intensity[extended_edge[0][0]:extended_edge[0][-1]]
    parameters = [np.mean(pre_edge_y),1/(np.mean(extended_edge_y)-np.mean(pre_edge_y))]    
    intensity = (np.array(normal_intensity)-parameters[0])*parameters[1]
    return [edge[0], intensity]

def XANES_linear_combination_fitting(xy_data,y_references,plot=False,references_names=[],amplitude_bnds = (0.9,1.1)):
    #y_reference should share x-axis with xy_data
    def best_fit_error(a):
        fit_curve = 0
        for reference, a_n in zip(y_references,a):
            fit_curve = fit_curve+a_n*np.array(reference)
        return np.sum(np.absolute(np.array(xy_data[1])-a[-1]*fit_curve))
    
    bnds = []
    for reference in y_references:
        bnds.append((0,1))
    bnds.append(amplitude_bnds)
    
    con = ({'type': 'eq', 'fun': lambda a: np.sum(a[0:-1])-1})
    results = shgo(best_fit_error, bounds=bnds, constraints=con, options=({'minimize_every_iter': True}))

    a = results.x
    best_fit = 0
    for reference, a_n in zip(y_references,a):
        best_fit = best_fit+a_n*np.array(reference)
    best_fit = a[-1]*best_fit
    
    if plot:
        fig, f = plt.subplots()
        f.plot(xy_data[0],best_fit,label='Fit',color='tab:blue')
        f.plot(xy_data[0],xy_data[1],'.',label='Data',color='tab:red')
        f.plot(xy_data[0],best_fit,label='Fit amplitude: '+str(100*round(a[-1],2))+'%',color='white')
        if len(references_names) == 0:
            count = 1
            for a_n in a[:-1]:
                f.plot(xy_data[0],best_fit,label='Ref. '+str(count)+': '+str(100*round(a_n,2))+'%',color='white')
                count += 1
        elif len(references_names) < len(a[:-1]) or len(references_names) > len(a[:-1]):
            warnings.warn("Number of reference-names doesn't match number of references.")
            count = 1
            for a_n in a[:-1]:
                f.plot(xy_data[0],best_fit,label='Ref. '+str(count)+': '+str(100*round(a_n,2))+'%',color='white')
                count += 1
        elif len(references_names) == len(a[:-1]):
            for a_n,name in zip(a[:-1],references_names):
                f.plot(xy_data[0],best_fit,label=name+': '+str(100*round(a_n,2))+'%',color='white')
        f.plot(xy_data[0],best_fit,color='tab:blue')
        f.plot(xy_data[0],xy_data[1],'.',color='tab:red')
        f.legend(frameon=0)        
        if max(xy_data[1]) > 5 or max(xy_data[1]) < 0.8:
            f.set_ylabel('Intensity a.u.')
        else:
            f.set_ylabel('Normalized Intensity')
        if np.mean(np.diff(xy_data[0])) < 0.01:
            f.set_xlabel('Energy [keV]')
        elif np.mean(np.diff(xy_data[0])) < 10:
            f.set_xlabel('Energy [eV]')
        else:
            f.set_xlabel('Energy')
        plt.draw()
        plt.show()
    
    return results, [xy_data[0], best_fit]