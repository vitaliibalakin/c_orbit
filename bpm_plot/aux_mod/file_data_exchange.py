#!/usr/bin/env python3

from PyQt5.QtWidgets import QFileDialog
import numpy as np
import json


class FileDataExchange:
    def __init__(self, directory, data_receiver, bpm_count=16):
        super(FileDataExchange, self).__init__()
        self.dir = directory
        self.data_receiver = data_receiver
        self.bpm_count = bpm_count

    def save_file(self, parent, orbit, mode):
        try:
            sv_file = QFileDialog.getSaveFileName(parent=parent, directory=self.dir + "/saved_modes",
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = sv_file[0] + '.txt'
                np.savetxt(file_name, orbit)
                self.mode_orbit_file(file_name, mode)
                self.data_receiver(orbit, which='eq')
        except Exception as exc:
            print('func: save_file:', exc)

    def load_file(self, parent, mode):
        print("mode=", mode)
        try:
            file_name = QFileDialog.getOpenFileName(parent=parent, directory=self.dir + "/saved_modes",
                                                    filter='Text Files (*.txt)')[0]
            self.mode_orbit_file(file_name, mode)
            self.data_receiver(np.loadtxt(file_name), which='eq')
        except Exception as exc:
            print('func: load_file:', exc)

    def change_orbit_from_file(self, mode):
        f = open(self.dir + '/mode_file.txt', 'r')
        mode_orbit = json.loads(f.read())
        f.close()
        try:
            self.data_receiver(np.loadtxt(mode_orbit[mode]), which='eq')
        except Exception as exc:
            self.data_receiver(np.zeros(32), which='eq')
            print('func: change_orbit_from_file:', exc)

    def mode_orbit_file(self, file_name, mode):
        f = open(self.dir + '/mode_file.txt', 'r')
        mode_orbit = json.loads(f.read())
        f.close()
        mode_orbit[mode] = file_name
        f = open(self.dir + '/mode_file.txt', 'w')
        f.write(json.dumps(mode_orbit))
        f.close()
