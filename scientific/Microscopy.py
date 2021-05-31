import numpy as np
import re
from matplotlib import pyplot as plt

class spectroscopy(object):

    def __init__(self):
        pass
        
    def load_edx(file):
        file_object = open(file, 'r')
        file_lines = file_object.readlines()
    
        energy = []
        count = []
    
        for line in file_lines:
            if not re.findall('\#',line):
                energy.append(float(re.findall('[-+]?\d+\.\d+',line)[0]))
                count.append(float(re.findall('[-+]?\d+\.\d+',line)[1]))
        return energy, count

    def load_eels(file):
        file_object = open(file, 'r')
        file_lines = file_object.readlines()
    
        energy = []
        count = []
        for line in file_lines:
            if not re.findall('\#',line):
                energy.append(float(re.findall('[-+]?\d*\.\d+|\d+',line)[0]))
                count.append(float(re.findall('[-+]?\d*\.\d+|\d+',line)[1]))
        return energy, count

class TIA(object):

    def __init__(self):
        pass

    def plot_edx_linescan(name):
        #virtuel haadf from edx-counts
        file = hs.load(name)

        data = file.data

        haadf = []
        for line in data:
            haadf.append([])
            for spectrum in line:
                haadf[-1].append(spectrum.sum())
        
        mask = []
        for line in haadf:
            mask.append(all(v == 0 for v in line) == False)
        
        fig, f = plt.subplots()
        f.matshow(np.array(haadf)[mask])
        f.set_title(name)
        plt.tight_layout()
        plt.draw()