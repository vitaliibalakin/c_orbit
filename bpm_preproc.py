#!/usr/bin/env python3

import numpy as np
import pycx4.qcda as cda
import sys
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic


class BpmPreproc(QMainWindow):
    def __init__(self):
        super(BpmPreproc, self).__init__()
        uic.loadUi("uis/for_fft.ui", self)
        self.show()
        self.bpm_x = {}
        self.bpm_z = {}
        self.chan_bpm_marker = []
        self.chan_bpm_numpts = []
        self.chan_bpm_vals = []
        self.for_fft_x = []
        self.for_fft_z = []
        self.cur_bpm_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09']

        self.bpms = {'bpm01': 0, 'bpm02': 1.908, 'bpm03': 3.144, 'bpm04': 5.073, 'bpm05': 6.7938,
                     'bpm07': 8.7388, 'bpm08': 9.9648, 'bpm09': 11.8928, 'bpm10': 13.7078, 'bpm11': 15.6298,
                     'bpm12': 16.8568, 'bpm13': 18.8018, 'bpm14': 20.5216, 'bpm15': 22.4566, 'bpm16': 23.7111,
                     'bpm17': 25.6156}
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0, 'bpm17': 0}
        self.bpm_numpts_renew = self.bpm_val_renew.copy()
        self.bpm_val_ren_cur = {bpm: 0 for bpm in self.cur_bpm_list}

        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        self.btn_fft.clicked.connect(self.save_fft)
        print('start')

        for bpm, bpm_coor in self.bpm_val_renew.items():
            # bpm numpts init
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.numpts')
            chan.valueMeasured.connect(self.bpm_numpts)
            self.chan_bpm_numpts.append(chan)

            # bpm channels init
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
            chan.valueMeasured.connect(self.data_proc)
            self.chan_bpm_vals.append(chan)

            # bpms marker init
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.marker')
            chan.valueMeasured.connect(self.bpm_marker)
            self.chan_bpm_marker.append(chan)

    def save_fft(self):
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        np.savetxt("p_for_fft" + " " + time, np.vstack((self.for_fft_x, self.for_fft_z)))

    def bpm_numpts(self, chan):
        self.bpm_numpts_renew[chan.name.split('.')[-2]] = chan.val

    def data_proc(self, chan):
        bpm_num = chan.name.split('.')[-2]
        data_len = int(self.bpm_numpts_renew[bpm_num][0])
        self.bpm_x[bpm_num] = np.mean(chan.val[data_len:2*data_len-1])
        self.bpm_z[bpm_num] = np.mean(chan.val[2*data_len:3*data_len-1])

        if bpm_num == 'bpm15':
            self.for_fft_x = chan.val[data_len:2*data_len-1]
            self.for_fft_z = chan.val[2*data_len:3*data_len-1]

    def bpm_marker(self, chan):
        self.bpm_val_ren_cur[chan.name.split('.')[-2]] = 1
        if all(sorted(self.bpm_val_ren_cur.values())):
            for key in self.bpm_val_renew:
                self.bpm_val_renew[key] = 0
            x = np.array([])
            z = np.array([])
            for key in sorted(self.bpms, key=self.bpms.__getitem__):
                if key in self.cur_bpm_list:
                    x = np.append(x, self.bpm_x[key])
                    z = np.append(z, self.bpm_z[key])
                else:
                    x = np.append(x, 500)
                    z = np.append(z, 500)
            self.chan_x_orbit.setValue(x)
            self.chan_z_orbit.setValue(z)
            # print(x, z)


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BpmPreproc()
    sys.exit(app.exec_())
