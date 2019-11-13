#!/usr/bin/env python3

import numpy as np
import pycx4.qcda as cda
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic


class BpmPreproc(QMainWindow):
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.bpm_fft = 'bpm15'
        self.bpm_turns = 'bpm15'
        self.bpm = {}
        self.bpm_sigma = {}
        self.chan_bpm_marker = []
        self.chan_bpm_numpts = []
        self.chan_bpm_vals = []
        self.cur_bpm_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                             'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']

        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0, 'bpm17': 0}
        self.bpm_numpts_renew = self.bpm_val_renew.copy()
        self.bpm_val_ren_cur = {bpm: 0 for bpm in self.cur_bpm_list}

        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)
        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024)
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
        self.bpm[bpm_num] = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
        self.bpm_sigma[bpm_num] = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))
        if bpm_num == self.bpm_fft:
            self.chan_fft.setValue(chan.val[data_len:3 * data_len])

        if bpm_num == self.bpm_turns:
            self.chan_turns.setValue(chan.val[3*data_len:4*data_len])

        # if bpm_num == 'bpm07':
        #     self.btn_fft.setText(str(round(chan.val[data_len], 5)))
        #     print(chan.val[data_len + +111: data_len+114])

    def bpm_marker(self, chan):
        # print('mark')
        self.bpm_val_ren_cur[chan.name.split('.')[-2]] = 1
        if all(sorted(self.bpm_val_ren_cur.values())):
            for key in self.bpm_val_renew:
                self.bpm_val_renew[key] = 0
            x_orbit = np.array([])
            x_orbit_sigma = np.array([])
            z_orbit = np.array([])
            z_orbit_sigma = np.array([])
            for key in self.bpms:
                if key in self.cur_bpm_list:
                    x_orbit = np.append(x_orbit, self.bpm[key][0])
                    x_orbit_sigma = np.append(x_orbit_sigma, self.bpm_sigma[key][0])
                    z_orbit = np.append(z_orbit, self.bpm[key][1])
                    z_orbit_sigma = np.append(z_orbit_sigma, self.bpm_sigma[key][1])
                else:
                    x_orbit = np.append(x_orbit, 0.0)
                    x_orbit_sigma = np.append(x_orbit_sigma, 0.0)
                    z_orbit = np.append(z_orbit, 0.0)
                    z_orbit_sigma = np.append(z_orbit_sigma, 0.0)
            orbit = np.array([x_orbit, z_orbit, x_orbit_sigma, z_orbit_sigma])
            self.chan_orbit.setValue(orbit)


if __name__ == "__main__":
    app = QApplication(['bpm_preproc'])
    w = BpmPreproc()
    sys.exit(app.exec_())
