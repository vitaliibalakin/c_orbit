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
        print(mode)
        sv_file = QFileDialog.getSaveFileName(parent=parent, directory=self.dir, filter='Text Files (*.txt)')
        if sv_file:
            file_name = sv_file[0] + '.txt'
            np.savetxt(file_name, orbit)
            self.mode_orbit_file(file_name, mode)
            self.data_receiver(orbit, which='eq')

    def load_file(self, parent, mode):
        print("mode=", mode)
        file_name = QFileDialog.getOpenFileName(parent=parent, directory=self.dir, filter='Text Files (*.txt)')[0]
        self.mode_orbit_file(file_name, mode)
        self.data_receiver(np.loadtxt(file_name), which='eq')

    def change_orbit_from_file(self, mode):
        f = open('mode_file.txt', 'r')
        mode_orbit = json.loads(f.read())
        f.close()
        self.data_receiver(np.loadtxt(mode_orbit[mode]), which='eq')

    @staticmethod
    def mode_orbit_file(file_name, mode):
        f = open('mode_file.txt', 'r')
        mode_orbit = json.loads(f.read())
        f.close()
        mode_orbit[mode] = file_name
        f = open('mode_file.txt', 'w')
        f.write(json.dumps(mode_orbit))
        f.close()
