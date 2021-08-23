#!/usr/bin/env python3
import numpy as np
import json
import time
import re
import pycx4.pycda as cda
import scipy.signal as sp
from c_orbit.config.bpm_config_parser import load_config_bpm

class BPM:
    def __init__(self, bpm, collect_orbit, collect_tunes, send_current, send_fft, send_coor, CONF):
        super(BPM, self).__init__()
        self.collect_orbit, self.collect_tunes, self.send_current, self.send_fft, self.send_coor = \
            collect_orbit, collect_tunes, send_current, send_fft, send_coor

        chans_conf = load_config_bpm(CONF + '/bpm_conf.txt', bpm)
        for chan in ['datatxzi', 'numpts', 'tunes_range']:
            if chan not in chans_conf:
                print(bpm + ' ' + chan + ' is absent in bpm_conf')


        self.last_data_upd: int = 0
        self.no_connection: bool = False
        self.name: str = bpm
        self.turns_mes: int = 0
        self.act_state: int = 1
        self.marker: int = 0
        self.turn_num: int = 1
        self.data_len: int = 1024
        self.turn_slice: tuple = (100.0, 100.0)
        self.starting: bool = True
        self.coor: tuple = (0, 0)
        self.sigma: tuple = (0, 0)
        self.turn_arrays: nparray = np.ndarray([])
        self.x_bound: list = [0.345, 0.365]
        self.z_bound: list = [0.2, 0.4]

        self.chan_datatxzi = cda.VChan(**chans_conf['datatxzi'])
        self.chan_datatxzi.valueMeasured.connect(self.data_proc)
        self.chan_numpts = cda.DChan(**chans_conf['numpts'])
        self.chan_tunes_range = cda.StrChan(**chans_conf['tunes_range'])
        self.chan_tunes_range.valueMeasured.connect(self.tunes_range)
        # self.chan_marker = cda.DChan('cxhw:37.ring.' + bpm + '.marker')
        # self.chan_marker.valueMeasured.connect(self.marker_proc)

    # def marker_proc(self, chan):
    #     self.marker = 1
    #     self.collect_orbit()


    def data_proc(self, chan):
        data_len = int(len(chan.val) / 4)
        self.data_len = data_len
        self.turn_arrays = chan.val[data_len:3 * data_len]
        self.turn_slice = (chan.val[data_len + self.turn_num - 1], chan.val[2 * data_len + self.turn_num - 1])
        self.coor = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
        self.sigma = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))
        self.marker = 1

        self.collect_orbit()
        if self.turns_mes:
            self.fft_proc(chan.val[data_len:3 * data_len])
            self.send_current(chan.val[3*data_len:4*data_len])

    def fft_proc(self, data):
        self.send_coor(data)
        h_len = self.data_len
        window = sp.nuttall(h_len)
        x_fft = np.fft.rfft((data[:h_len] - np.mean(data[:h_len])) * window, len(data[:h_len]), norm='ortho')
        z_fft = np.fft.rfft((data[h_len: len(data)] - np.mean(data[h_len: len(data)])) * window,
                            len(data[h_len: len(data)]), norm='ortho')
        freq = np.fft.rfftfreq(h_len, 1)
        self.send_fft(np.concatenate([freq, np.abs(x_fft), np.abs(z_fft)]))

        # searching of working DR point
        x_arr = freq[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))]
        z_arr = freq[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))]
        x_index = np.argmax(np.abs(x_fft)[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))])
        z_index = np.argmax(np.abs(z_fft)[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))])
        x_tune = round(x_arr[x_index], 4)
        z_tune = round((1 - z_arr[z_index]), 4)
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