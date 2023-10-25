# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta

from scipy.special import erf
    
def fancy():
    print("Uh, that's pretty!")

def gauss(x_values,theta,intensity,sigma):
    x_values = np.array(x_values)
    sigma=(intensity/1000)**(0.125)*sigma
    return intensity*(1/(np.sqrt(2*np.pi)*sigma))*np.exp(-((x_values-theta)/(np.sqrt(2)*sigma))**2)

def fermi( x, cut, soft, offset=1e-6):
    return ((0.5*erf(-(x-cut)/soft)+0.5)/(0.5*erf(-(0-cut)/soft)+0.5))+offset

def format_of_file(file_name):
    comma_index = file_name[::-1].find('.')
    if comma_index == -1:
        return None
    else:
        return file_name[-comma_index:]
        
def name_of_file(file_name):
    comma_index = file_name[::-1].find('.')
    if comma_index == -1:
        return file_name
    else:
        return file_name[:-(comma_index+1)]
    
def time_stamp_str():
    return datetime.now().strftime("%Y%d%m_%H%M%S")
    
def progress_bar(ratio,length=18,start_str='[',end_str=']',progress_str='=',empty_str=' ',percentages=True):
    if length < 5:
        length=5
    if ratio < 0:
        ratio = 0 
    elif ratio > 1:
        ratio = 1
    if ratio == 0.5:
        ratio = 0.501
    prt_str = start_str+round(ratio*length)*progress_str
    prt_str = prt_str+(1+length-len(prt_str))*empty_str+end_str
    if percentages:
        perc_str = str(round(ratio*100))+'%'
        prt_str = prt_str[0:int(length/2)-1]+perc_str+prt_str[int(length/2)+len(perc_str)-1:]
    return(prt_str)