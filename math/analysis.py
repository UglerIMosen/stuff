# -*- coding: utf-8 -*-
"""
@author: thoe
"""

import numpy as np
import re
from datetime import datetime, timedelta

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
