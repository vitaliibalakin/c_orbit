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
        self.cur_bpm_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']

        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0, 'bpm17': 0}
        self.bpm_numpts_renew = self.bpm_val_renew.copy()
        self.bpm_val_ren_cur = {bpm: 0 for bpm in self.cur_bpm_list}

        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        self.chan_x_fft = cda.VChan('cxhw:4.bpm_preproc.x_fft', max_nelems=131072)
        self.chan_z_fft = cda.VChan('cxhw:4.bpm_preproc.z_fft', max_nelems=131072)
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

    def bpm_numpts(self, chan):
        self.bpm_numpts_renew[chan.name.split('.')[-2]] = chan.val

    def data_proc(self, chan):
        bpm_num = chan.name.split('.')[-2]
        data_len = int(self.bpm_numpts_renew[bpm_num][0])
        self.bpm_x[bpm_num] = np.mean(chan.val[data_len:2*data_len-1])
        self.bpm_z[bpm_num] = np.mean(chan.val[2*data_len:3*data_len-1])

        if bpm_num == 'bpm15':
            print(data_len)
            self.fft(x_array=chan.val[data_len:2*data_len-1], z_array=chan.val[2 * data_len:3 * data_len - 1])

    def bpm_marker(self, chan):
        # print('mark')
        self.bpm_val_ren_cur[chan.name.split('.')[-2]] = 1
        if all(sorted(self.bpm_val_ren_cur.values())):
            for key in self.bpm_val_renew:
                self.bpm_val_renew[key] = 0
            x = np.array([])
            z = np.array([])
            for key in self.bpms:
                if key in self.cur_bpm_list:
                    x = np.append(x, self.bpm_x[key])
                    z = np.append(z, self.bpm_z[key])
                else:
                    x = np.append(x, 0.0)
                    z = np.append(z, 0.0)
            self.chan_x_orbit.setValue(x)
            self.chan_z_orbit.setValue(z)

    def fft(self, x_array, z_array):
        res = {}
        print(x_array, z_array)
        fft = {'x': np.fft.rfft(x_array, len(x_array)), 'z': np.fft.rfft(z_array, len(z_array))}
        res['freq'] = np.fft.rfftfreq(len(x_array), 1)
        for coor, val in fft.items():
            res[coor] = np.sqrt(val.real ** 2 + val.imag ** 2)
        x_freq = res['freq'][np.argmax(res['x'][20:])]
        z_freq = res['freq'][np.argmax(res['z'][20:])]
        print(x_freq, z_freq)
        self.chan_x_fft.setValue(res['x'])
        self.chan_z_fft.setValue(res['z'])


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BpmPreproc()
    sys.exit(app.exec_())
