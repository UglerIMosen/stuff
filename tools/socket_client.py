import socket
import json
import time
import numpy as np
from pprint import pprint
from matplotlib import pyplot as plt

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.1)

name = 'dynpi-cellfurnace'
send_port    = 8500
recieve_port = 9000

class remote(object):

    def __init__(self,__recieve_port__,__send_port__):
        self.data_address = (name,__recieve_port__)
        self.command_address = (name,__send_port__)
        self.receive_sock = sock

    def comm(self, data, address, echo=False):
        #used for sending commands to pushserver
        if echo:
            print(' ')
        command = 'json_wn#{}'.format(json.dumps(data))
        if echo:
            print('Sending command: {}'.format(command))
        self.receive_sock.sendto(command.encode('ascii'), address)

    def send(self,string):
        data = {'method': string}
        self.comm(data, self.command_address)
        return time.time(), time.ctime()

    def set(self,setting,value):
        data = {'method': 'update_settings', setting: value}
        self.comm(data, self.command_address)
        return time.time(), time.ctime()

    def read_data(self):
        command = 'json_wn'
        self.receive_sock.sendto(command.encode('ascii'), self.data_address)
        return json.loads(self.receive_sock.recv(4096))

pi = remote(recieve_port,send_port)
print(pi.read_data())