# -*- coding: utf-8 -*-
"""
@author: Thomas Smitshuysen

#driver snippet for LeadFluid (or golander?) BT101L peristaltic pump
#assuming dcba byteorder
"""

import serial
import minimalmodbus
import time

class LeadFluid(object):

    def __init__(self):
        self.comm = minimalmodbus.Instrument('COM7',1)
        self.comm.serial.baudrate = 9600
        self.comm.serial.parity = serial.PARITY_EVEN
        self.comm.bytesize = 8

        self.int_to_flowunit = {1 : 'muL/min', 2: 'mL/min', 3: 'L/min'}
        self.flowunit_to_int = {}
        for key in self.int_to_flowunit.keys():
            self.flowunit_to_int[self.int_to_flowunit[key]] = key

        self.read_unit()
        self.read_status()
        self.read_direction()

    def read(self,register):
        return self.comm.read_register(register)

    def write(self,register,integer):
        return self.comm.write_register(register,integer)

    def read_status(self):
        value = self.read(4126)
        if value == 1:
            self.status = 'RUNNING'
        elif value == 0:
            self.status = 'STOPPED'
        else:
            raise ValueError('Status recieved from pump could not be interpreted (1 for running, 0 for stopped).\n Integer recieved: '+str(value))
        return self.status

    def start(self):
        self.write(4126,1)
        time.sleep(1)
        return self.read_status()

    def stop(self):
        try:
            self.write(4126,0)
        except minimalmodbus.NoResponseError:
            pass
        time.sleep(3)
        return self.read_status()

    def read_direction(self):
        value = self.read(4023)
        if value == 0:
            self.direction = 'clockwise'
        elif value == 1:
            self.direction = 'counter clockwise'
        else:
            raise ValueError('Status recieved from pump could not be interpreted (0 for clockwise, 1 for counter).\n Integer recieved: '+str(value))
        return self.direction

    def read_unit(self):
        self.unit = self.int_to_flowunit[self.read(4022)]
        return self.unit

    def set_unit(self,unit):
        if unit in self.int_to_flowunit:
            self.write(4022,unit)
        elif unit in self.flowunit_to_int:
            self.write(4022,self.flowunit_to_int[unit])
        else:
            raise ValueError('Unit not recognized. Use one of the following:',*self.int_to_flowunit,*self.flowunit_to_int)
        return self.read_unit()

    def flow(self,echo=True):
        value = self.comm.read_float(4015,byteorder=3)
        if echo:
            print(str(value)+' '+self.unit)
        return value

    def set_flow(self,flow,echo=True):
        self.comm.write_float(4015,flow,byteorder=3)
        return self.flow(echo=echo)

if __name__ == "__main__":
    pump = LeadFluid()
