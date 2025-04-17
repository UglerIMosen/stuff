# -*- coding: utf-8 -*-
"""
Based of PyExpLabSys: https://github.com/CINF/PyExpLabSys
Thx for the good work!
"""

from PyExpLabSys.common.sockets import DateDataPullSocket, DataPushSocket
import time

class data_socket(object):

    def __init__(self,name='generic pull socket', entries=['I','V'],port = 9000):
        self.name = name
        self.data_entries = entries
        self.port = port
        self.socket = DateDataPullSocket(self.name, self.data_entries, port=self.port)
        self.socket.start()

    def stop(self):
        self.socket.stop()

    def set_point_now(self, entry, data_point):
        if entry not in self.data_entries:
            raise KeyError('Key not found in data_entries')
            return
        self.socket.set_point(entry, data_point)

class cmd_socket(object):
    
    def __init__(self, name = 'generic push socket', settings = {'sp': 0, 'rate': 1}, port=8500):
        self.name = name
        self.settings = settings
        self.port = port
        self.socket = DataPushSocket(self.name,
                                     action='callback_direct',
                                     callback=self.callback,
                                     return_format='json',
                                     port=self.port)
        self.socket.start()

    def callback(self, data):
        method_name = data.pop('method')
        method = self.__getattribute__(method_name)
        return method(**data)

    def update_settings(self, **kwargs):
        for key in kwargs.keys():
            if key not in self.settings.keys():
                raise ValueError(key+' was not recognized as a possible setting')
        self.settings.update(kwargs)
        print('Update settings with: {}'.format(kwargs))
        return 'Updated settings with: {}'.format(kwargs)

    def stop_sock(self):
        self.socket.stop()
