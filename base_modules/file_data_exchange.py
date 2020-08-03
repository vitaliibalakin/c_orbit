#!/usr/bin/env python3

import numpy as np
import json


class FileDataExchange:
    def __init__(self, directory, data_receiver, save_dir='/saved_modes', mode_file='/mode_file.txt'):
        super(FileDataExchange, self).__init__()
        self.dir, self.data_receiver, self.save_dir, self.mode_file = directory, data_receiver, save_dir, mode_file
        print(save_dir, mode_file)

    def save_file(self, file_name, data, mode, service):
        np.savetxt(file_name, data)
        self.mode_data_file(file_name, mode)
        self.data_receiver(data, mode=mode, service=service)

    def load_file(self, file_name, mode, service):
        self.mode_data_file(file_name, mode)
        self.data_receiver(np.loadtxt(file_name), mode=mode, service=service)

    def change_data_from_file(self, mode, service):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        try:
            self.data_receiver(np.loadtxt(data_mode[mode]), mode=mode)
        except Exception as exc:
            if service == 'orbit':
                data = np.zeros(64)
                self.data_receiver(data, mode=mode, msg='file_mistake | check ' + service)
            elif service == 'tunes':
                data = np.zeros(2)
                self.data_receiver(data, mode=mode, msg='file_mistake | check ' + service)
            print('func: change_data_from_file:', exc)

    def mode_data_file(self, file_name, mode):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        data_mode[mode] = file_name
        f = open(self.dir + self.mode_file, 'w')
        f.write(json.dumps(data_mode))
        f.close()
