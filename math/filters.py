# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta
import warnings

from stuff.common.stuff import fermi

def smooth(f,pts,boundary='same'):
    extent = np.ones(pts)/pts
    if boundary == 'same':
        fs = f[0]*np.ones(pts)
        fe = f[-1]*np.ones(pts)
        f = np.array([*fs,*f,*fe])
    smoothed_f = np.convolve(f, extent, mode='same')
    if boundary == 'same':
        smoothed_f = smoothed_f[pts:-pts]
    return smoothed_f

def median_filter(data,cycles = 1):
    new_data = data
    for n in range(cycles):
        data_0 = new_data[:-2]
        data_1 = new_data[1:-1]
        data_2 = new_data[2:]
        new_data = [new_data[0]]
        for p0,p1,p2 in zip(data_0,data_1,data_2):
            new_data.append(np.median([p0,p1,p2]))
        new_data.append(p2)
    return np.array(new_data)

def rolling_median_filter(data,cycles = 1,forwards=True,backwards=False):
    index_list = list(range(1,len(data)-1))
    for i in range(cycles):
        if forwards:
            for index in index_list:
                data[index]=np.median([data[index-1],data[index],data[index+1]])
        if backwards:
            index_list.reverse()
            for index in index_list:
                data[index]=np.median([data[index-1],data[index],data[index+1]])
    return data

def low_pass_filter(data1D,cut,soft,damp=1e-6):
    filter_mask = fermi(np.arange(0,len(data1D),1),cut,soft)+np.flip(fermi(np.arange(0,len(data1D),1),cut-1,soft,offset=damp))
    fft_filtered_data = filter_mask*np.fft.fft(data1D)
    filtered_data = abs(np.fft.ifft(fft_filtered_data))
    return filtered_data

def bin_data(xy_data, xrange = False, resolution=1):
    xy_data = [np.array(xy_data[0]),np.array(xy_data[1])]
    if not xrange:
        xrange = [xy_data[0][0],xy_data[0][-1]]
    if resolution < np.mean(np.diff(xy_data[0])):
        warnings.warn('The x-data seems inadequate for the chosen resolution. This might cause problems')
    bins = np.arange(xrange[0]-resolution/2,xrange[1]+resolution/2,resolution)
    binned_x_data = np.arange(xrange[0],xrange[1],resolution)

    mask = np.logical_and(xy_data[0]>xrange[0],xy_data[0]<xrange[1])
    binned_y_data = (np.histogram(xy_data[0][mask],bins,weights=xy_data[1][mask])[0] / np.histogram(xy_data[0][mask],bins)[0])
    return np.array([binned_x_data,binned_y_data])

def derivative(xy_data,order=1,epsilon = 1e-7):
    if order == 0:
        return xy_data
    else:
        x  = np.array(xy_data[0])
        dx = xy_data[0]
        dy = xy_data[1]
        for i in range(0,order):
            dx_w_zeros = np.diff(dx)
            dy = np.diff(dy)
            dx = []
            for value in dx_w_zeros:
                if value < epsilon:
                    dx.append(epsilon)
                else:
                    dx.append(value)
            dydx = dy/dx
            x = 0.5*(x[:-1]+x[1:])
        return [x,dydx]

def integrate(xy_data):
    if len(xy_data) == 2:
        integrated_sum = [xy_data[1][0]*(xy_data[0][1]-xy_data[0][0])]
        for value,difference in zip(xy_data[1][1:],np.diff(xy_data[0])):
            integrated_sum.append(integrated_sum[-1]+value*(difference))
        return [xy_data[0],integrated_sum]
    else:
        integrated_sum = [xy_data[0]]
        for value in xy_data[1:]:
            integrated_sum.append(integrated_sum[-1]+value)
        return integrated_sum
