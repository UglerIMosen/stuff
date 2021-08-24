import numpy as np
import re
from matplotlib import pyplot as plt
import hyperspy.api as hs
import os
import time

from stuff.common.import_tools import find_directory as fd
from stuff.common.stuff import format_of_file, name_of_file


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
        
def convert_image_to_file(input_format,output_format):
    allowed_input_formats = ['dm4','dm3','emi','ser','hspy','jpg','jpeg','JPG','JPEG','png','tif','tiff','TIFF','MRC','MRCZ','EMSA','emsa','MSA','msa','netCDF','NetCDF','bcf','BCF','spx','SPX','EMD','emd','NCEM','ncem','EMD','emd','velox','Velox','VELOX','spc','spd','h5','elid','sur','pro','nxs','xml']
    allowed_output_formats = ['','hpsy','jpg','jpeg','JPG','JPEG','png','tif','tiff','TIFF','MRCZ','EMSA','emsa','MSA','msa','EMD','emd','NCEM','h5','nxs']
    if input_format[0] == '.':
        input_format == input_format[1:]
    if input_format not in allowed_input_formats:
        raise TypeError(input_format+' is not a supported format for reading.')    
    if output_format[0] == '.':
        output_format == output_format[1:]
    if output_format not in allowed_output_formats:
        raise TypeError(input_format+' is not a supported format for saving.')    

    folder = fd()
    save_folder = folder+'/converted from '+input_format+' to '+output_format+' on '+time.ctime()

    file_list = [file for file in os.listdir(folder) if format_of_file(file) == input_format]

    image_list = []
    for file in file_list:
        image_list.append(hs.load(folder+'/'+file))

    os.mkdir(save_folder)

    for image,file in zip(image_list,file_list):
        try:
            image.save(save_folder+'/'+name_of_file(file)+'.'+output_format)
            print('File saved as "'+save_folder+'/'+name_of_file(file)+'.'+output_format+'"')
        except:
            print('\n    Error saving into '+save_folder+'/'+name_of_file(file)+'.'+output_format)
            print('        Could not save file: '+file,end='\n')
    
    print('End of program')