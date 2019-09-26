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
        uic.loadUi("uis/for_fft.ui", self)
        self.show()
        self.av_buffer = np.empty(0)
        self.bpm = {}
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

        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=32)
        self.chan_x_fft = cda.VChan('cxhw:4.bpm_preproc.x_fft', max_nelems=131072)
        self.chan_z_fft = cda.VChan('cxhw:4.bpm_preproc.z_fft', max_nelems=131072)
        self.chan_cmd = cda.VChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024)
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
        self.bpm[bpm_num] = (np.mean(chan.val[data_len:2 * data_len - 1]),
                             np.mean(chan.val[2 * data_len:3 * data_len - 1]))
        if bpm_num == 'bpm15':
            self.fft(x_array=chan.val[data_len:2*data_len-1], z_array=chan.val[2 * data_len:3 * data_len - 1])

    def bpm_marker(self, chan):
        # print('mark')
        self.bpm_val_ren_cur[chan.name.split('.')[-2]] = 1
        if all(sorted(self.bpm_val_ren_cur.values())):
            for key in self.bpm_val_renew:
                self.bpm_val_renew[key] = 0
            x_orbit = np.array([])
            z_orbit = np.array([])
            for key in self.bpms:
                if key in self.cur_bpm_list:
                    x_orbit = np.append(x_orbit, self.bpm[key][0])
                    z_orbit = np.append(z_orbit, self.bpm[key][1])
                else:
                    x_orbit = np.append(x_orbit, 0.0)
                    z_orbit = np.append(z_orbit, 0.0)
            orbit = np.append(x_orbit, z_orbit)
            self.chan_orbit.setValue(orbit)
            result = self.calc_av(orbit)
            if result:
                self.chan_cmd.setValue(json.dumps({'av': np.ndarray.tolist(result[0]),
                                                   'sigma': np.ndarray.tolist(result[1])}))
                # result 0 is average, 1 is sigma
                # send av and sigma
                pass

    def calc_av(self, orbit):
        if len(self.av_buffer) == 0:
            self.av_buffer = orbit
        elif len(self.av_buffer) == 10:
            av = np.mean(self.av_buffer, axis=0)
            sigma = np.sqrt(np.sum((self.av_buffer - av) ** 2, axis=0))
            self.av_buffer = np.empty(0)
            return av, sigma
        elif len(self.av_buffer) > 10:
            self.av_buffer = np.vstack((self.av_buffer, orbit))
        elif len(self.av_buffer) < 10:
            self.av_buffer = np.vstack((self.av_buffer, orbit))

    def fft(self, x_array, z_array):
        res = {}
        print(x_array, z_array)
        fft = {'x': np.fft.rfft(x_array, len(x_array)), 'z': np.fft.rfft(z_array, len(z_array))}
        res['freq'] = np.fft.rfftfreq(len(x_array), 1)
        for coor, val in fft.items():
            res[coor] = np.sqrt(val.real ** 2 + val.imag ** 2)
        x_freq = res['freq'][np.argmax(res['x'][20:])]
        z_freq = res['freq'][np.argmax(res['z'][20:])]
        # print(x_freq, z_freq)
        self.chan_x_fft.setValue(res['x'])
        self.chan_z_fft.setValue(res['z'])


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BpmPreproc()
    sys.exit(app.exec_())
