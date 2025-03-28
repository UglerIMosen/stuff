# -*- coding: utf-8 -*-
"""
@author: thoe
"""
import numpy as np


def gauss(x_values,theta,intensity,sigma):
    x_values = np.array(x_values)
    sigma=(intensity/1000)**(0.125)*sigma
    return intensity*(1/(np.sqrt(2*np.pi)*sigma))*np.exp(-((x_values-theta)/(np.sqrt(2)*sigma))**2)

def fermi( x, cut, soft, offset=1e-6):
    return ((0.5*erf(-(x-cut)/soft)+0.5)/(0.5*erf(-(0-cut)/soft)+0.5))+offset
