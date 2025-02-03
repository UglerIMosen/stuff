# -*- coding: utf-8 -*-
""" driver for kepco bop d powersupply """
import telnetlib
from pprint import pprint
from tools.misc import round_to_nearest
import numpy as np
import warnings
import time
### LIST COMMANDS ###
"""
LIST:cmd - List command
LIST:CLE - clear list
LIST:COUN - how many repetitions. 0-255, 0 means indefinitely
LIST:DWEL - minimum 0.0005, upto 10 s
LIST:CURR - adds current value points. up to 1002 data points
LIST:VOLT - adds voltage value points. up to 1002 data points
LIST:CURR:POIN? -number of points
LIST:DWEL:POIN? -nubmer of dwell times

VOLT:MODE LIST - execute VOLT list
CURR:MODE LIST - execute CURR list


"""

class kepco_psu(object):

    def __init__(self,ip,echo=False):
        self.ip = ip
        self.echo = echo
        self.time_delay = 0.05 #s
        self.LIST_length_max = 1002

        if self.echo:
            self.port = 5024
            self.comm = telnetlib.Telnet(self.ip,self.port)
        elif not self.echo:
            self.port = 5025
            self.comm = telnetlib.Telnet(self.ip,self.port)
        else:
            print('No applicable "echo" setting. Disabling echo')
            self.port = 5025
            self.comm = telnetlib.Telnet(self.ip,self.port)
        
        self.get_name()
        self.get_access()
        self.get_channel_state()
        self.get_list_repetitions()
        
    def set_echo(self,echo):
        if type(echo) != bool:
            raise TypeError('Input is not boolean.')
        self.echo = echo
        if self.echo:
            self.port = 5024
            self.comm = telnetlib.Telnet(self.ip,self.port)
        elif not self.echo:
            self.port = 5025
            self.comm = telnetlib.Telnet(self.ip,self.port)            
        
    def write(self,cmd,echo=False):
        cmd = cmd + '\r\n'
        self.comm.write(cmd.encode())
        time.sleep(self.time_delay)
        if self.echo:
            echo_resp = self.comm.read_until(b'\n').decode().strip('\r\n')
        else:
            echo_resp = ''
        if '?' in cmd:
            resp = self.comm.read_until(b'\n').decode().strip('\r\n')
        else:
            resp = ''
        if echo:
            print(echo_resp,'\n',resp)
        return resp

    def get_name(self):
        self.name = self.write('*IDN?')
        return self.name

    def reset(self):
        self.write('*RST')
        self.get_access()
        self.get_channel_state()

    def get_access(self):
        value = self.write('SYST:REM?')
        if value == '1':
            self.access = 'REMOTE'
        elif value == '0':
            self.access = 'MANUAL'
        else:
            print('Recieved unexpected response: ',value)
        return self.access
    
    def set_access(self,value):
        if value in ['REMOTE','remote',1,'ON','on',True]:
            self.write('SYST:REM 1')
        elif value in ['MANUAL','manual','analog','ANALOG',0,'OFF','off',False]:
            self.write('SYST:REM 1')
        else:
            print('Recieved unexpected setting: ',value)
        return self.get_access()
        
    def get_channel_state(self):
        value = self.write('OUTP?')
        if value == '1':
            self.channel_state = 'ON'
        elif value == '0':
            self.channel_state = 'OFF'
        else:
            print('Recieved unexpected response: ',value)
        return self.channel_state

    def set_channel_state(self,value):
        if value in [1,'ON','on',True]:
            self.write('OUTP 1')
        elif value in [0,'OFF','off',False]:
            self.write('OUTP 0')
        else:
            print('Recieved unexpected setting: ',value)
        return self.get_channel_state()        

    def get_curr(self):
        value = float(self.write('CURR?'))
        return value

    def meas_curr(self):
        value = float(self.write('MEAS:CURR?'))
        return value

    def meas_curr(self):
        value = float(self.write('MEAS:CURR?'))
        return value

    def set_curr(self,value):
        #will disregard any mode setting
        if type(value) not in [int,float]:
            raise ValueError('Given value is not int nor float')
        self.write('CURR '+str(value))
        return self.get_curr()

    def get_volt(self):
        value = float(self.write('VOLT?'))
        return value

    def meas_volt(self):
        value = float(self.write('MEAS:VOLT?'))
        return value

    def set_volt(self,value):
        #will disregard any mode setting
        if type(value) not in [int,float]:
            raise ValueError('Given value is not int nor float')
        self.write('VOLT '+str(value))
        return self.get_volt()

    def get_mode(self):
        value = self.write('FUNC:MODE?')
        if value == '1':
            self.channel_state = 'CURR'
        elif value == '0':
            self.channel_state = 'VOLT'
        else:
            print('Recieved unexpected response: ',value)
        return self.channel_state

    def set_mode(self,value):
        if value in [1,'CURR','curr']:
            self.write('FUNC:MODE CURR')
        elif value in [0,'VOLT','volt']:
            self.write('FUNC:MODE VOLT')
        else:
            print('Recieved unexpected setting: ',value)
        return self.get_mode()
    
    def reset_list_program(self,value):
        self.write('LIST:CLE')
        self.list_program = ''
        
    def get_list_repetitions(self):
        val = int(self.write('LIST:COUN?'))
        self.list_repetitions = val
        return self.list_repetitions
    
    def build_LIST_POIN(self,arr,precision=0.0001):
        strout = ''
        for val in arr:
            strout += str(round_to_nearest(val,number=precision))+','
        strout = strout[:-1]
        return strout
        
    def IV(self,Vmin,Vmax,duration,mode='VOLT',repetitions=0):
        if mode == 'VOLT':
            self.write('*RST')
            zero = self.meas_volt()
        elif mode == 'CURR':
            self.write('*RST')
            zero = 0
        else:
            raise NameError('mode should be either "VOLT" or "CURR"')
        if duration < 0.0005*self.LIST_length_max:
            warnings.warn("Specified IV duration is too short. Using "+str(0.0005*self.LIST_length_max)+' s.')
            duration = 0.0005*self.LIST_length_max
        
        print('--> IV\n')
        
        #initialize kepco
        self.write('*RST')
        self.write('LIST:CLE')

        #individual steps
        step_up = np.linspace(Vmin,Vmax,int(self.LIST_length_max/2))
        step_down = np.linspace(Vmax,Vmin,int(self.LIST_length_max/2))
        step_up_1 = step_up[step_up >= zero]
        step_up_2 = step_up[step_up < zero]
        full = [*step_up_1,*step_down,*step_up_2]
        count = 0
        for setp in full:
            count+=1
            print('Uploading points: '+str(count)+'/'+str(self.LIST_length_max),end='\r')
            self.write('LIST:'+mode+' '+str(round_to_nearest(setp,number=0.0001)))
        print('\n')
        #listpoin = self.build_LIST_POIN(full)
        #self.write('LIST:'+mode+' '+listpoin)
        
        #dwell time
        dwell = round_to_nearest(duration/self.LIST_length_max,0.0001)
        self.write('LIST:DWEL '+str(dwell))

        self.write('LIST:COUN '+str(repetitions))
        
        self.write('OUTP ON')
        self.write(mode+':MODE LIST')
    
    def ACDC(self,V1,V2,dutycycl,freq,mode='VOLT',repetitions=0):
        if mode == 'VOLT':
            self.write('*RST')
            zero = self.meas_volt()
        elif mode == 'CURR':
            self.write('*RST')
            zero = 0
        else:
            raise NameError('mode should be either "VOLT" or "CURR"')
        if dutycycl > 1 or dutycycl < 0:
            raise ValueError('Dutycycle is not between 0 and 1')

        print('--> AC:DC\n')

        #initialize kepco
        self.write('*RST')
        self.write('LIST:CLE')

        duration = 1/freq
        step1 = dutycycl*duration
        warn = False
        if step1 < 0.0005:
            warnings.warn('Step1 is too short. Setting to 0.0005 s')
            step1 = 0.0005
            warn = True
        step2 = (1-dutycycl)
        if step2 < 0.0005:
            warnings.warn('Step2 is too short. Setting to 0.0005 s')
            step2 = 0.0005
            warn = True
        if warn:
            print('Frequency changes to '+str(round(1/(step1+step2))))

        #step1
        self.write('LIST:'+mode+' '+str(round_to_nearest(V1,number=0.0001)))
        self.write('LIST:DWEL '+str(step1))

        #step2
        self.write('LIST:'+mode+' '+str(round_to_nearest(V2,number=0.0001)))
        self.write('LIST:DWEL '+str(step2))

        self.write('LIST:COUN '+str(repetitions))
        
        self.write('OUTP ON')
        self.write(mode+':MODE LIST')

if __name__ == '__main__':

    psu_ip = '169.254.68.140'
    kepco = kepco_psu(psu_ip)