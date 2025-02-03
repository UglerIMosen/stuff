# -*- coding: utf-8 -*-
""" driver for Banner S15S humidity and temperature sensor """

import serial
import minimalmodbus

class S15S(object):
	
	def __init__(self,path,slaveid):
		self.comm = minimalmodbus.Instrument(path,slaveid)
		self.comm.serialbaudrate = 19200
		self.comm.serial.parity  = serial.PARITY_NONE
		self.comm.serial.timeout = 3
		self.slave_id = slaveid
		self.set_celsius()

	def set_fahrenheit(self):
		self.unit = 'F'
		return self.unit

	def set_celsius(self):
		self.unit = 'C'
		return self.unit

	def temperature(self):
		if self.unit == 'C':
			value = self.comm.read_register(0x0001)/20
		elif self.unit == 'F':
			value = self.comm.read_register(0x0002)/20
		return value

	def humidity(self):
		value = self.comm.read_register(0x0000)/100
		return value

	def dew_point(self):
		if self.unit == 'C':
			value = self.comm.read_register(0x0003)/100
		elif self.unit == 'F':
			value = self.comm.read_register(0x0004)/100
		return value
	
if __name__ == "__main__":
	import time
	sensor = S15S('/dev/serial/by-id/usb-FTDI_USB-RS485_Cable_AV0LE5WQ-if00-port0',1)
	for i in range(10):
		#for j in range(10):
		#	print(sensor.comm.read_register(0x0000+j)/20)
		print('T: ',sensor.temperature())
		print('H: ',sensor.humidity())
		print('DP: ',sensor.dew_point())
		time.sleep(3)
