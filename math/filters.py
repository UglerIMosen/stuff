# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta
import warnings
from scipy.signal import correlate

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

def phase_shift(x,y):
    #copy-pasted from https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
    A = np.array(list(x))
    B = np.array(list(y))

    nsamples = A.size
    # regularize datasets by subtracting mean and dividing by s.d.
    A -= A.mean(); A /= A.std()
    B -= B.mean(); B /= B.std()
    # Find cross-correlation
    xcorr = correlate(A, B)
    # delta time array to match xcorr
    dt = np.arange(1-nsamples, nsamples)
    return dt[xcorr.argmax()]

def eliminate_phaseshift(x,y,reduce_data=True):
    if len(y) != len(x):
        raise ValueError('x and y must have same length')
    #only set "reduce data" to False, if the data contains an integer number of complete wavelengths (the data start and end at same point in the inharmonic wave)
    initial_shift = phase_shift(x,y)
    if initial_shift == 0:
        print('No phase-shift detected. Returning raw data.')
        return x,y
    if initial_shift < 0:
        xy_exchange = True
        x_cache = x
        x = y
        y = x_cache
    else:
        xy_exchange = False
    initial_shift = abs(initial_shift)
    shifts = []
    for i in range(initial_shift,len(x)):
        shift = phase_shift(x[i:],y[:-i])
        if i == initial_shift and shift != 0:
            shift_is_zero = False
        elif shift == 0:
            shift_is_zero = True
        if shift_is_zero:
            if shift == 0:
                shifts.append(i)
            else:
                break
    shift = round(np.mean(shifts))
    x = x[shift:]
    y = y[:-shift]
    if xy_exchange:
        x_cache = x
        x = y
        y = x_cache
    return x,y
