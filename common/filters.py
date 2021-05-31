# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta

from stuff import fermi

def smooth(f,pts):
    extent = np.ones(pts)/pts
    smoothed_f = np.convolve(f, extent, mode='same')
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
    return new_data

def high_pass_filter(data1D,cut,soft,damp=1e-6):
    filter_mask = fermi(np.arange(0,len(data1D),1),cut,soft)+np.flip(fermi(np.arange(0,len(data1D),1),cut-1,soft,offset=damp))
    fft_filtered_data = filter_mask*np.fft.fft(data1D)
    filtered_data = abs(np.fft.ifft(fft_filtered_data))
    return filtered_data