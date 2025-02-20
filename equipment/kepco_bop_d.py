# -*- coding: utf-8 -*-
""" driver for kepco bop d powersupply """
import telnetlib
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
        self.time_delay = 0.06 #s
        self.LIST_length_max = 1002
        self.list_empty = True

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

        print(self.get_name())
        print(self.get_access())
        print(self.get_channel_state())
        print(self.get_list_repetitions())
        print(self.meas_volt(),self.meas_curr())

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
        if 'KEPCO' not in self.name:
            self.name = self.write('*IDN?')
        return self.name

    def reset(self):
        self.write('*RST')
        print(self.get_name())
        print(self.get_access())
        print(self.get_channel_state())
        print(self.get_list_repetitions())

        print(self.meas_volt(),self.meas_curr())

    def get_access(self):
        value = self.write('SYST:REM?')
        if value == '1':
            self.access = 'REMOTE'
        elif value == '0':
            self.access = 'MANUAL'
        else:
            print('Recieved unexpected response in "get_access": ',value)
        return self.access

    def set_access(self,value):
        if value in ['REMOTE','remote',1,'ON','on',True]:
            self.write('SYST:REM 1')
        elif value in ['MANUAL','manual','analog','ANALOG',0,'OFF','off',False]:
            self.write('SYST:REM 1')
        else:
            print('Recieved unexpected setting in "set_access": ',value)
        return self.get_access()

    def get_channel_state(self):
        value = self.write('OUTP?')
        if value == '1':
            self.channel_state = 'ON'
        elif value == '0':
            self.channel_state = 'OFF'
        else:
            print('Recieved unexpected response in "get_channel_state": ',value)
        return self.channel_state

    def set_channel_state(self,value):
        if value in [1,'ON','on',True]:
            self.write('OUTP 1')
        elif value in [0,'OFF','off',False]:
            self.write('OUTP 0')
        else:
            print('Recieved unexpected setting in "set_channel_state: ',value)
        return self.get_channel_state()

    def get_curr(self):
        value = float(self.write('CURR?'))
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

    def get_list_repetitions(self):
        val = int(self.write('LIST:COUN?'))
        self.list_repetitions = val
        return self.list_repetitions

    def build_LIST_POIN(self,arr,precision=0.01):
        strarrout = []
        strout = ''
        j = 0
        for val in arr:
            strout += str(round_to_nearest(val,number=precision))+','
            j += 1
            if j > 10:
                strout = strout[:-1]
                strarrout.append(strout)
                strout = ''
                j = 0
        if strout != '':
            strout = strout[:-1]
            strarrout.append(strout)
            strout = ''
        return strarrout

    def DC(self,value,mode=''):
        if mode == '':
            mode = self.get_mode()
        elif mode not in ['VOLT','CURR']:
            raise NameError('mode should be either "VOLT" or "CURR"')

        print('--> DC\n')

        #initialize kepco
        self.write('*RST')
        time.sleep(0.1)
        self.set_mode(mode)

        if mode == 'VOLT':
            self.set_volt(value)
        elif mode == 'CURR':
            self.set_curr(value)

        self.write('OUTP ON')

    def IV(self,Vmin,Vmax,duration,mode='VOLT',repetitions=0,points=''):
        if mode == '':
            mode = self.get_mode()
        elif mode not in ['VOLT','CURR']:
            raise NameError('mode should be either "VOLT" or "CURR"')

        if mode == 'VOLT':
            zero = self.meas_volt()
        elif mode == 'CURR':
            zero = 0

        if points == '':
            points = self.LIST_length_max
        elif points > 1002:
            warnings.warn('Cannot do more points than 1002')
            points = 1002

        dwell = round_to_nearest(duration/points,0.0001)
        if duration < 0.0005*points or dwell < 0.0005:
            warnings.warn("Specified IV duration is too short. Using "+str(0.0005*points)+' s.')
            dwell = 0.0005

        print('--> IV\n')

        #initialize kepco
        self.write('*RST')
        time.sleep(0.1)
        self.set_mode(mode)
        self.write('LIST:CLE')

        #individual steps
        step_up = np.linspace(Vmin,Vmax,int(points/2))
        step_down = np.linspace(Vmax,Vmin,int(points/2))
        step_up_1 = step_up[step_up >= zero]
        step_up_2 = step_up[step_up < zero]
        full = [*step_up_1,*step_down,*step_up_2]
        count = 0
        listpoin = self.build_LIST_POIN(full)
        for poin in listpoin:
            self.write('LIST:'+mode+' '+poin)
            count += 1
            print('Uploading points: '+str(count)+'/'+str(len(listpoin)),end='\r')
        print('\n')

        #dwell time
        self.write('LIST:DWEL '+str(dwell))

        self.write('LIST:COUN '+str(repetitions))

        self.write('OUTP ON')
        self.write(mode+':MODE LIST')

    def ACDC(self,V1,V2,dutycycl,freq,mode='',repetitions=0):
        if mode == '':
            mode = self.get_mode()
        elif mode not in ['VOLT','CURR']:
            raise NameError('mode should be either "VOLT" or "CURR"')
        if dutycycl > 1 or dutycycl < 0:
            raise ValueError('Dutycycle is not between 0 and 1')

        print('--> AC:DC\n')

        #initialize kepco
        self.write('*RST')
        time.sleep(0.1)
        self.set_mode(mode)
        self.write('LIST:CLE')

        duration = 1/freq
        step1 = round_to_nearest(dutycycl*duration,number=0.0001)
        step2 = round_to_nearest((1-dutycycl)*duration,number=0.0001)
        warn = False
        if step1 < 0.0005:
            warnings.warn('Step1 is too short. Setting to 0.0005 s')
            step1 = 0.0005
            warn = True
        if step2 < 0.0005:
            warnings.warn('Step2 is too short. Setting to 0.0005 s')
            step2 = 0.0005
            warn = True
        if warn:
            print('Frequency changes to '+str(round(1/(step1+step2))))

        #steps
        self.write('LIST:'+mode+' '+str(round_to_nearest(V1,number=0.0001))+','+str(round_to_nearest(V2,number=0.0001)))

        #duration
        self.write('LIST:DWEL '+str(step1)+','+str(step2))

        self.write('LIST:COUN '+str(repetitions))

        self.write('OUTP ON')
        self.write(mode+':MODE LIST')

if __name__ == '__main__':

    psu_ip = '169.254.68.140'
    kepco = kepco_psu(psu_ip)
