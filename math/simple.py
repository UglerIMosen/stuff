# -*- coding: utf-8 -*-
"""
@author: Thomas Smitshuysen

#simple mathematic tools
"""

def isfloat(string):
    # tests if the string is "floatable"
    try:
        float(string)
        return True
    except ValueError:
        return False
