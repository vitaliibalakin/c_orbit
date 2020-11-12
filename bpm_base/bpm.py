#!/usr/bin/env python3
import numpy as np
import json
import pycx4.qcda as cda
import scipy.signal as sp


class BPM:
    def __init__(self, bpm, collect_orbit, collect_tunes, send_current, send_fft, send_coor):
        super(BPM, self).__init__()
        self.collect_orbit, self.collect_tunes, self.send_current, self.send_fft, self.send_coor = \
            collect_orbit, collect_tunes, send_current, send_fft, send_coor
        self.name = bpm
        self.turns_mes = 0
        self.act_state = 1
        self.marker = 0
        self.coor = (0, 0)
        self.sigma = (0, 0)
        self.x_bound = [0.345, 0.365]
        self.z_bound = [0.2, 0.4]

        self.chan_datatxzi = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=524288)
        self.chan_numpts = cda.DChan('cxhw:37.ring.' + bpm + '.numpts')
        self.chan_marker = cda.DChan('cxhw:37.ring.' + bpm + '.marker')
        self.chan_tunes_range = cda.StrChan('cxhw:4.bpm_preproc.tunes_range', max_nelems=4096)
        self.chan_tunes_range.valueMeasured.connect(self.tunes_range)
        self.chan_datatxzi.valueMeasured.connect(self.data_proc)
        self.chan_marker.valueMeasured.connect(self.marker_proc)

    def marker_proc(self, chan):
        # print(chan.val)
        self.marker = 1
        self.collect_orbit()

    def data_proc(self, chan):
        data_len = int(len(chan.val) / 4)
        self.coor = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
        self.sigma = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))
        if self.turns_mes:
            self.fft_proc(chan.val[data_len:3 * data_len])
            self.send_current(chan.val[3*data_len:4*data_len])

    def fft_proc(self, data):
        self.send_coor(data)
        h_len = len(data) // 2
        window = sp.nuttall(h_len)
        x_fft = np.fft.rfft((data[:h_len] - np.mean(data[:h_len])) * window, len(data[:h_len]), norm='ortho')
        z_fft = np.fft.rfft((data[h_len: len(data)] - np.mean(data[h_len: len(data)])) * window,
                            len(data[h_len: len(data)]), norm='ortho')
        freq = np.fft.rfftfreq(h_len, 1)
        self.send_fft(np.array([freq, np.abs(x_fft), np.abs(z_fft)]))

        # searching of working DR point
        x_arr = freq[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))]
        z_arr = freq[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))]
        x_index = np.argmax(np.abs(x_fft)[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))])
        z_index = np.argmax(np.abs(z_fft)[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))])
        x_tune = round(x_arr[x_index], 3)
        z_tune = round((1 - z_arr[z_index]), 3)
        self.collect_tunes(np.array([x_tune, z_tune]))

    def tunes_range(self, chan):
        if chan.val:
            bounds = json.loads(chan.val)
            self.x_bound = bounds[0:2]
            self.z_bound = bounds[2:4]
        else:
            print('bpm.py', 'empty tunes range data', self.name)
            self.x_bound = [0.345, 0.365]
            self.z_bound = [0.2, 0.4]
            # self.chan_tunes_range.setValue(json.dumps(self.x_bound + self.z_bound))
