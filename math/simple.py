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

"""
def sort_by_int_key(s):
    return int(re.findall('\d+',s)[0])

files.sort(key=sort_func) #will sort by value of first integer found in file-name
"""