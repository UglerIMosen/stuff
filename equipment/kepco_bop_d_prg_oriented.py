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

class kepco_prg_oriented(object):
    #simplified towards running a device
    #
    # #capital letters define settings
    # #__setting__ define read settings
    # #small letters define locally saved setting

    def __init__(self,ip):
        self.ip = ip
        self.time_delay = 0.06
        self.accuracy = 0.0001
        self.LIST_length_max = 1002 #steps
        self.LIST_min_length = 0.0005 #s

        self.port = 5025
        self.comm = telnetlib.Telnet(self.ip,self.port)
        self.write('*IDN?',echo=True,written=True)

        self.__name__()
        self.__state__()
        self.__mode__()
        self.__program__()
        #self.__init__('CURR')
        self.get_limits()

        self.prg_mode  = None
        self.func      = None
        self.offset    = None
        self.amplitude = None
        self.frequency = None
        self.dutycycle = None

    def write(self,cmd,echo=False,written=False):
        if written:
            self.command = cmd
        cmd = cmd + '\r\n'
        self.comm.write(cmd.encode())
        time.sleep(self.time_delay)
        if '?' in cmd:
            self.response = self.comm.read_until(b'\n').decode().strip('\r\n')
        else:
            self.response = ''
        if echo:
            self.echo = cmd+' >>> '+self.response
            print(self.echo)
        return self.response

    def __name__(self):
        self.name = self.write('*IDN?')
        return self.name

    def __state__(self):
        value = self.write('OUTP?')
        if value == '1':
            self.state = 1
        elif value == '0':
            self.state = 0
        else:
            print('Recieved unexpected response in "get_channel_state": ',value)
            self.state = None
        return self.state

    def __mode__(self):
        value = self.write('FUNC:MODE?')
        if value == '1':
            self.mode = 'CURR'
        elif value == '0':
            self.mode = 'VOLT'
        else:
            print('Recieved unexpected response: ',value)
            self.mode = None
        return self.mode

    def __program__(self):
        value = self.write(self.mode+':MODE?')
        if value == 'FIXED':
            self.program = 'stopped'
        elif value == 'LIST':
            self.program = 'running'
        else:
            print('Recieved unexpected response: ',value)
            self.program = None
        return self.program

    def __limits__(self):
        from_name = self.name().split(' ')[2].split('-')
        self.limits = {'VOLT': float(from_name[0]),
                       'CURR': float(from_name[1])}
        return self.limits

    def __I__(self):
        i = float(self.write('MEAS:CURR?'))
        return self.i

    def __V__(self):
        self.v = float(self.write('MEAS:VOLT?'))
        return self.v

    def INIT(self,mode):
        if value not in ['CURR','VOLT']:
            raise ValueError('Value has to be "CURR" or "VOLT"')
        self.write('FUNC:MODE '+mode)
        self.write(mode+':MODE FIX')
        self.write(mode+' 0')
        return self.__mode__()

    def OFF(self):
        self.write('OUTP 0')
        return self.__state__()

    def ON(self):
        self.write('OUTP 1')
        return self.__state__()

    def build_LIST_POIN(self,arr,precision=self.accuracy):
        #utility function for the LIST commands
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

    def PROGRAM(self,mode,func,offset,amplitude,frequency,dutycycle):
        if mode not in ['CURR','VOLT']:
            raise ValueError("'mode' has to be 'CURR' or 'VOLT'")
        if func not in ['DC','AC:DC','IV CURVE']:
            raise NameError("'func' has to be 'DC','AC:DC','IV CURVE'")

        #values
        self.prg_mode = mode
        self.func = func
        self.offset = round_to_nearest(offset,number=self.accuracy)
        self.amplitude = round_to_nearest(amplitude,number=self.accuracy)
        self.frequency = frequency
        self.dutycycle = dutycycle

        #limit values
        sphigh = self.offset+self.amplitude
        if sphigh > self.limits[self.prg_mode]:
            sphigh = self.limits[self.prg_mode]
        splow = self.offset-self.amplitude
        if splow < -self.limits[self.prg_mode]:
            splow = -self.limits[self.prg_mode]

        #pre setting
        if self.__program__() == 'running':
            running_change = True
            self.STOP()
        else:
            running_change = False
        self.write('LIST:CLE')

        #program
        if func == 'DC':
            self.write('LIST:'+self.prg_mode+' '+self.offset)
            self.write('LIST:DWEL 10')

        elif func == 'AC:DC':
            duration = 1/self.frequency
            step1 = round_to_nearest(self.dutycycle*duration,number=self.accuracy)
            step2 = round_to_nearest((1-self.dutycycle)*duration,number=self.accuracy)
            warn = False
            if step1 < self.LIST_min_length:
                warnings.warn('Step1 is too short. Setting to '+str(self.LIST_min_length)+' s')
                step1 = self.LIST_min_length
                warn = True
            if step2 < self.LIST_min_length:
                warnings.warn('Step2 is too short. Setting to '+str(self.LIST_min_length)+' s')
                step2 = self.LIST_min_length
                warn = True
            if warn:
                self.frequency = round(1/(step1+step2))
                print('Frequency changes to '+str(self.frequency))
            #AC:DC steps
            self.write('LIST:'+self.prg_mode+' '+str(round_to_nearest(sphigh,number=self.accuracy))+','+str(round_to_nearest(splow,number=self.accuracy)))
            #AC:DC duration
            self.write('LIST:DWEL '+str(step1)+','+str(step2))

        elif func == 'IV CURVE':
            if self.prg_mode == 'VOLT':
                zero = self.meas_volt()
            elif self.prg_mode == 'CURR':
                zero = 0
            points = (2*self.amplitude)/self.accuracy
            if points > self.LIST_length_max:
                points = self.LIST_length_max

            #IV steps
            step_up = np.linspace(splow,sphigh,int(points/2))
            step_down = np.linspace(sphigh,splow,int(points/2))
            step_up_1 = step_up[step_up >= zero]
            step_up_2 = step_up[step_up < zero]
            full = [*step_up_1,*step_down,*step_up_2]
            collection_of_steps = self.build_LIST_POIN(full)
            for steps in collection_of_steps:
                self.write('LIST:'+self.prg_mode+' '+steps)

            #dwell time
            duration = 1/self.frequency
            dwell = round_to_nearest(duration/points,number=self.accuracy)
            if dwell < self.LIST_min_length:
                warnings.warn("Specified IV duration is too short. Using "+str(self.LIST_min_length)+' s.')
                dwell = self.LIST_min_length
            self.write('LIST:DWEL '+str(dwell))

        #end setting
        self.write('LIST:COUN 0')
        if running_change:
            return self.START()
        else:
            return (self.prg_mode,self.func,self.offset,self.amplitude,self.frequency,self.dutycycle)

    def START(self):
        if None in [self.prg_mode,self.func,self.offset,self.amplitude,self.frequency,self.dutycycle]:
            warning.warn('No program in memory')
        else:
            self.write('FUNC:MODE '+self.prg_mode)
            self.ON()
            self.write(self.prg_mode+':MODE LIST'):
        return self.__program__(), self.__mode__()

    def STOP(self):
        self.OFF()
        self.write(self.mode+':MODE FIXED'):
        return self.__program__(), self.__mode__()

if __name__ == '__main__':

    psu_ip = '169.254.68.140'
    kepco = kepco_prg_oriented(psu_ip)
