import numpy as np
import re
from matplotlib import pyplot as plt
import hyperspy.api as hs
import os
import time
import inspect
import math

from stuff.common.import_tools import load_delimited_data as ldd
from stuff.common.import_tools import find_directory as fd
from stuff.common.stuff import format_of_file, name_of_file
from stuff.math.simple import round_to_nearest

class spectroscopy(object):

    def __init__(self):
        self.init_edx_library()
        self.init_amu_colormap()

    def init_amu_colormap(self):
        map = []
        for cmap in ['Set2','Dark2','tab20b','tab20c']:
            map_cache = plt.get_cmap(cmap,20)
            map = [*map,*map_cache(range(20))]
        self.amu_colormap = map
        self.amu_colormap[6] = [0,0,0,1] #C
        self.amu_colormap[7] = [1-0,1-0,1-1,1] #N
        self.amu_colormap[8] = [1-1,1-0,1-0,1] #O
        self.amu_colormap[14] = [1-0,1-0,1-153/255,1]
        self.amu_colormap[16] = [1-204/255,1-204/205,1] #S
        self.amu_colormap[26] = [1-255/255, 1-128/255, 1] #Fe
        self.amu_colormap[28] = [1-0, 1-204/255, 1] #Ni

        return self.amu_colormap

    def init_edx_library(self):
        raw = ldd(inspect.getfile(self.__class__)[:-13]+'edx_lines',delimiter=' ')
        keys = list(raw.keys())

        library = {'Energy' : {}, 'Element' : {}, 'Z' : {}}
        for eV, number, element, line, intensity in zip(raw[keys[0]],raw[keys[1]],raw[keys[2]],raw[keys[3]],raw[keys[4]]):
            if type(eV) == str:
                eV = float(eV.replace(',',''))
            if eV in library['Energy'].keys():
                library['Energy'][eV] = [*library['Energy'][eV],(element,number,line,intensity)]
            else:
                library['Energy'][eV] = [(element,number,line,intensity)]
            if element in library['Element'].keys():
                library['Element'][element] = [*library['Element'][element],(number,line,eV,intensity)]
            else:
                library['Element'][element] = [(number,line,eV,intensity)]
            if number in library['Z'].keys():
                library['Z'][number] = [*library['Z'][number],(element,line,eV,intensity)]
            else:
                library['Z'][number] = [(element,line,eV,intensity)]
        self.edxlib = library
        return library

    def get_color_by_element(self,element):
        return self.amu_colormap[self.edxlib['Element'][element][0][0]]

    def get_color_by_Z(self,Z):
        return self.amu_colormap[Z]

    def load_edx(self,file):
        file_object = open(file, 'r')
        file_lines = file_object.readlines()

        energy = []
        count = []

        for line in file_lines:
            if not re.findall('\#',line):
                energy.append(float(re.findall('[-+]?\d+\.\d+',line)[0]))
                count.append(float(re.findall('[-+]?\d+\.\d+',line)[1]))
        return [energy, count]

    def load_eels(self,file):
        file_object = open(file, 'r')
        file_lines = file_object.readlines()

        energy = []
        count = []
        for line in file_lines:
            if not re.findall('\#',line):
                energy.append(float(re.findall('[-+]?\d*\.\d+|\d+',line)[0]))
                count.append(float(re.findall('[-+]?\d*\.\d+|\d+',line)[1]))
        return [energy, count]

    def OXINST_findlabels(self,path):
        file = open(path)
        lines = file.readlines()
        filtlines = [line for line in lines if 'LABEL' in line]
        elements = []
        for line in filtlines:
            element = line.split(' ')[-1][:-1]
            if element not in elements:
                elements.append(element)
        return elements

    def edx_spectrum_plot(self,data,title='',eV_limit = 20, labelpath=False, label_Icutoff=0.04,skip=[]):
        fig, f = plt.subplots()
        fig.set_figwidth(12)
        fig.set_figheight(5)

        norm = (sum(data[1])*np.mean(np.diff(data[0])))
        data[1] = list(np.array(data[1])/norm)
        f.plot(data[0],data[1],color='firebrick')

        resolution_magnitude = math.floor(math.log(np.mean(np.diff(data[0])),10))

        if labelpath is not False:
            path = labelpath
            def plot_element_lines(element,data,keV=True):
                resolution = np.mean(np.diff(data[0]))
                if keV:
                    factor = 1000
                else:
                    factor = 1

                label = True
                family = {}
                for line in self.edxlib['Element'][element]:
                    if line[-1] >= 100:
                        eV = round_to_nearest(line[2]/factor,resolution)
                        if eV <= eV_limit:
                            intensity = data[1][data[0].index(eV)]/line[-1]
                            family[line[1][0]]=intensity

                for line in self.edxlib['Element'][element]:
                    eV = round_to_nearest(line[2]/factor,resolution)

                    if eV <= eV_limit:
                        #if data[1][data[0].index(eV)] > 0.02*max(data[1]):
                        #    intensity = data[1][data[0].index(eV)]/line[-1]
                        if line[-1] >= 100 and data[1][data[0].index(eV)] > label_Icutoff*max(data[1]):
                            f.text(eV,line[-1]*family[line[1][0]],element,rotation=45)
                        if label:
                            f.vlines(eV,0,line[-1]*family[line[1][0]],color=self.get_color_by_element(element),label=element)
                            label = False
                        else:
                            f.vlines(eV,0,line[-1]*family[line[1][0]],color=self.get_color_by_element(element))


            for element in self.OXINST_findlabels(path):
                if element not in skip:
                    plot_element_lines(element,data)

        f.set_xlabel('Energy (eV)')
        f.set_ylabel('Intensity (norm.)')
        f.set_xlim([-0.4,eV_limit+1])
        f.legend(frameon=0)
        f.set_title(title)
        plt.tight_layout()
        plt.draw()

    def edx_lineplot(self,data,skip=[],title=''):
        keys = list(data.keys())
        total_count = np.zeros(len(data[keys[1]]))
        intensity_order = []
        y_keys = []

        for key in keys[1:]:
            if not any(exp in key for exp in skip):
                total_count = total_count+np.array(data[key])
                intensity_order.append(sum(data[key]))
                y_keys.append(key)

        descending = [x for y, x in sorted(zip(intensity_order,y_keys))]

        full = total_count/total_count
        fig, f = plt.subplots()
        for key in descending:
            #f.plot(data[keys[0]],100*data[key]/total_count)
            if '(counts)' in key:
                f.fill_between(data[keys[0]],100*full,label=key[:-8],color=self.get_color_by_element(key.split(' ')[0]))
            else:
                f.fill_between(data[keys[0]],100*full,label=key,color=self.get_color_by_element(key.split(' ')[0]))
            full = full-np.array(data[key])/total_count
        f.set_xlabel('Distance (µm)')
        f.set_ylabel('EDX norm. count (%)')
        f.legend(bbox_to_anchor=(1.05, 1))
        f.set_title(title)
        f.set_ylim([0,100])
        f.set_xlim([data[keys[0]][0],data[keys[0]][-1]])
        plt.tight_layout()
        plt.draw()

class TIA(object):

    def __init__(self):
        pass

    def plot_edx_linescan(self,name):
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
