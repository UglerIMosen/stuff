# -*- coding: utf-8 -*-
"""
@author: Thomas Smitshuysen

#simple mathematic tools
"""
import numpy as np
import math

def isfloat(string):
    # tests if the string is "floatable"
    try:
        float(string)
        return True
    except ValueError:
        return False

def round_to_nearest(val,number=1):
    number = abs(number)
    factor = round(val/number)
    try:
        precision = math.floor(math.log(number-np.trunc(number),10))
    except ValueError:
        return round(factor*number)
    return round(factor*number,-precision)

"""
def sort_by_int_key(s):
    return int(re.findall('\d+',s)[0])

files.sort(key=sort_func) #will sort by value of first integer found in file-name
"""
