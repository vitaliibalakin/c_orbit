#!/usr/bin/env python3

from PyQt5.QtWidgets import QFileDialog
import numpy as np
import json


class FileDataExchange:
    def __init__(self, directory, data_receiver, save_dir='/saved_modes', mode_file='/mode_file.txt'):
        super(FileDataExchange, self).__init__()
        self.dir, self.data_receiver, self.save_dir, self.mode_file = directory, data_receiver, save_dir, mode_file
        print(save_dir, mode_file)

    def save_file(self, parent, orbit, mode):
        try:
            sv_file = QFileDialog.getSaveFileName(parent=parent, directory=self.dir + self.save_dir,
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = sv_file[0] + '.txt'
                np.savetxt(file_name, orbit)
                self.mode_data_file(file_name, mode)
                self.data_receiver(orbit, which='eq')
        except Exception as exc:
            print('func: save_file:', exc)

    def load_file(self, parent, mode):
        try:
            file_name = QFileDialog.getOpenFileName(parent=parent, directory=self.dir + self.save_dir,
                                                    filter='Text Files (*.txt)')[0]
            self.mode_data_file(file_name, mode)
            self.data_receiver(np.loadtxt(file_name), which='eq')
        except Exception as exc:
            print('func: load_file:', exc)

    def change_data_from_file(self, mode):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        try:
            self.data_receiver(np.loadtxt(data_mode[mode]), which='eq')
        except Exception as exc:
            self.data_receiver('incorrect_data_file', which='eq')
            print('func: change_data_from_file:', exc)

    def mode_data_file(self, file_name, mode):
        f = open(self.dir + self.mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        data_mode[mode] = file_name
        f = open(self.dir + self.mode_file, 'w')
        f.write(json.dumps(data_mode))
        f.close()
