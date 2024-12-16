""" Simple driver for Keithley Model 2700 """

import serial
import time
import re

class keithley2700(object):
    
    def __init__(self, port='COM3',baud=9600):
        self.ser = serial.Serial(port,baud)
        self.timeout = 1
        self.unit_mode_dic = {
                            'VOLT:DC' : 'VDC',
                            'VOLT:AC' : 'VAC',
                            'CURR:DC' : 'ADC',
                            'CURR:AC' : 'AAC',
                            'RES'     : 'OHM',
                            'FRES'    : 'Hz',
                            'TEMP'    : '',
                            }

        self.device_name()
        self.device_mode()
        self.device_unit()
        self.device_TC_type()
        self.device_TC_unit()

    def comm(self,user_cmd,echo=False):
        cmd = user_cmd+'\r'
        self.ser.write(cmd.encode('ascii'))
        if '?' in cmd:
            time.sleep(0.2)
            tic = time.time()
            while time.time()-tic < self.timeout:
                if self.ser.inWaiting() != 0:
                    break
                if time.time()-tic < self.timeout:
                    raise TimeoutError("Timeout")
                time.sleep(0.2)
            reply = self.ser.read(self.ser.inWaiting()).decode()
            reply = reply.strip('\x13')
            reply = reply.strip('\r')
            reply = reply.strip('\x11')
        else:
            time.sleep(2)
            reply = self.comm(user_cmd.split(' ')[0]+'?')
        if echo:
            print(reply)
        return reply

    def device_name(self):
        self.name = self.comm('*IDN?')
        return self.name
    
    def device_mode(self):
        self.mode = self.comm('SENS:FUNC?').strip('"')
        return self.mode 
 
    def set_mode(self,value):
        if value not in self.unit_mode_dic:
            raise ValueError('Use one of the following modes: ',self.unit_mode_dic.keys())
        self.comm('SENS:FUNC "'+value+'"')
        self.device_mode()
        self.device_unit()
        return self.mode
 
    def device_unit(self):
        if self.mode == 'TEMP':
            self.unit = self.comm('UNIT:TEMP?')
        else:
            self.unit = self.unit_mode_dic[self.mode]
        return self.unit

    def device_TC_type(self):
        self.TC_type = self.comm('TEMP:TYPE?')
        return self.TC_type

    def set_TC_type(self,value):
        if value not in ['J', 'K', 'T', 'E', 'R', 'S', 'B', 'N']:
            raise ValueError('Use one of the following types: ',['J', 'K', 'T', 'E', 'R', 'S', 'B', 'N'])
        self.comm('TEMP:TYPE '+value)
        self.device_TC_type()
        return self.TC_type

    def device_TC_unit(self):
        self.TC_unit = self.comm('UNIT:TEMP?')
        return self.TC_unit
        
    def integration_time(self):
        return self.comm('SENS:VOLT:APER?')
    
    def set_integration_time(self,value):
        if type(value) != int and type(value) != float:
            raise TypeError('Value is not integer nor float.')
        return self.comm('SENS:VOLT:APER '+value)
        
    def dataframe(self):
        self.ser.flushInput()
        return self.comm('DATA?')

    def data(self):
        dataframe = self.dataframe()
        try:
            value = float(dataframe.split(',')[0].strip(self.unit))
        except ValueError:
            value = float(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",dataframe)[0])
        except IndexError:
            value = None
        return value
        
    def read(self):
        self.ser.flushInput()
        dataframe = self.comm('READ?')
        try:
            value = float(dataframe.split(',')[0].strip(self.unit))
        except ValueError:
            value = float(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",dataframe)[0])
        except IndexError:
            value = None
        return value

if __name__ == '__main__':
    keith = keithley2700()
    print(keith.name)
    print(keith.mode)
    if keith.mode == 'TEMP':
        print(keith.TC_type)
        print(keith.TC_unit)
    else:
        print(keith.unit)
    while True:
        print(keith.data())
        time.sleep(1)