# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 08:48:36 2023

@author: thomas smitshuysen

#driver snippet for MFG-2110 function generator
"""

import serial

ser = serial.Serial(port='COM25',
                    baudrate=115200,
                    parity=serial.PARITY_NONE,
                    bytesize=serial.EIGHTBITS,
                    stopbits=serial.STOPBITS_ONE)

cmd = '*IDN?\r\n'
ser.write(cmd.encode())

#if ser.inWaiting() > 0:
if True:
    print(ser.read(ser.inWaiting()))

ser.close()
