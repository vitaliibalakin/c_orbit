#!/usr/bin/env python3

import numpy as np
import json


class FileDataExchange:
    def __init__(self, directory, data_receiver, save_dir='/saved_modes', mode_file='/mode_file.txt'):
        super(FileDataExchange, self).__init__()
        self.dir, self.data_receiver, self.save_dir, self.mode_file = directory, data_receiver, save_dir, mode_file
        print(save_dir, mode_file)

    def save_file(self, file_name, orbit, mode):
            np.savetxt(file_name, orbit)
            self.mode_data_file(file_name, mode)
            self.data_receiver(orbit, which='eq', mode=mode)

    def load_file(self, file_name, mode):
        self.mode_data_file(file_name, mode)
        self.data_receiver(np.loadtxt(file_name), which='eq', mode=mode)

    def change_data_from_file(self, mode):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        try:
            self.data_receiver(np.loadtxt(data_mode[mode]), which='eq', mode=mode)
        except Exception as exc:
            self.data_receiver('incorrect_data_file', which='eq', mode=mode)
            print('func: change_data_from_file:', exc)

    def mode_data_file(self, file_name, mode):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        data_mode[mode] = file_name
        f = open(self.dir + self.mode_file, 'w')
        f.write(json.dumps(data_mode))
        f.close()
