# -*- coding: utf-8 -*-
""" Omega CN7800 Modbus driver. Might also work with other CN units. Settings
on the device should be RTU and datalength 8 bit.
Set remote communication to on. Set T-sensor input as desired.
"""

import serial
import minimalmodbus


class CN7800(object):
    """Driver for the omega CN7800"""

    def __init__(self, path, slave_id):
        self.comm = minimalmodbus.Instrument(path, slave_id)
        self.comm.serial.baudrate = 9600
        self.comm.serial.parity = serial.PARITY_EVEN
        self.comm.serial.timeout = 0.5
        #self.comm.close_port_after_each_call = True
        self.slave_id = slave_id

    def temperature(self):
        return self.comm.read_register(0x1000,1)
    
    def setpoint(self):
        return self.comm.read_register(0x1001,1)

    def set_setpoint(self, value):
        if value > self.upper_limit():
            raise ValueError('Value must be below upper limit specified by the controller')
        self.comm.write_register(0x1001,value,1)
        return 'Setpoint is '+str(self.setpoint())

    def upper_limit(self):
        return self.comm.read_register(0x1002,1)

    def set_upper_limit(self,value):
        self.comm.write_register(0x1002,value,1)
        return 'Upper limit is '+str(self.upper_limit())

    def status(self):
        if self.comm.read_bit(0x0814) == 1:
            return 'RUNNING'
        elif self.comm.read_bit(0x0814) == 0:
            return 'STOPPED'
        else:
            return 'err'

    def start(self):
        self.comm.write_bit(0x0814,1)
        return 'RUN'

    def stop(self):
        self.comm.write_bit(0x0814,0)
        return 'STOP'

if __name__ == "__main__":
    omega = CN7800("/dev/serial/by-id/usb-FTDI_USB-RS485_Cable_AU05SW8J-if00-port0",1)
    for i in range(100):
        print(omega.read_temperature())
    
