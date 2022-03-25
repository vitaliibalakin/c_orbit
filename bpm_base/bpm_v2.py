#!/usr/bin/env python3
import numpy as np
import json
import time
import re
import pycx4.pycda as cda
import scipy.signal as sp
from c_orbit.config.bpm_config_parser import load_config_bpm

class BPM:
    def __init__(self, bpm, collect_orbit, chan_tunes, chan_turns, chan_fft, chan_coor, CONF):
        super(BPM, self).__init__()
        self.collect_orbit, self.chan_tunes, self.chan_turns, self.chan_fft, self.chan_coor = \
            collect_orbit, chan_tunes, chan_turns, chan_fft, chan_coor

        chans_conf = load_config_bpm(CONF + '/bpm_conf.txt', bpm)
        print(chans_conf)
        for chan in ['datatxzi', 'numpts', 'tunes_range', 'is_on', 'x', 'xstd', 'z', 'zstd']:
            if chan not in chans_conf:
                print(bpm + ' ' + chan + ' is absent in bpm_conf')
            else:
                self.chan_is_on = cda.DChan(**chans_conf['is_on'])
                self.chan_is_on.valueMeasured.connect(self.is_on)
                self.chan_x = cda.DChan(**chans_conf['x'])
                self.chan_xstd = cda.DChan(**chans_conf['xstd'])
                self.chan_z = cda.DChan(**chans_conf['z'])
                self.chan_zstd = cda.DChan(**chans_conf['zstd'])
                self.chan_datatxzi = cda.VChan(**chans_conf['datatxzi'])
                self.chan_datatxzi.valueMeasured.connect(self.data_proc)
                # self.chan_numpts = cda.DChan(**chans_conf['numpts'])
                self.chan_tunes_range = cda.StrChan(**chans_conf['tunes_range'])
                self.chan_tunes_range.valueMeasured.connect(self.tunes_range)

        self.name: str = bpm
        self.turns_mes: int = 0
        self.act_state: int = 1
        self.data_len: int = 1024
        self.coor: tuple = (0.0, 0.0)
        self.std: tuple = (0.0, 0.0)
        self.x_bound: list = [0.345, 0.365]
        self.z_bound: list = [0.2, 0.4]

    def is_on(self, chan):
        self.act_state = chan.val

    def data_proc(self, chan):
        data_len = int(len(chan.val) / 4)
        self.data_len = data_len
        self.coor = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
        self.std = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))
        self.chan_x.setValue(self.coor[0])
        self.chan_z.setValue(self.coor[1])
        self.chan_xstd.setValue(self.std[0])
        self.chan_zstd.setValue(self.std[1])
        self.marker = 1

        self.collect_orbit()
        if self.turns_mes:
            self.fft_proc(chan.val[data_len:3 * data_len])
            self.chan_turns.setValue(chan.val[3*data_len:4*data_len])

    def fft_proc(self, data):
        self.chan_coor.setValue(data)
        h_len = self.data_len
        window = sp.nuttall(h_len)
        x_fft = np.fft.rfft((data[:h_len] - np.mean(data[:h_len])) * window, len(data[:h_len]), norm='ortho')
        z_fft = np.fft.rfft((data[h_len: len(data)] - np.mean(data[h_len: len(data)])) * window,
                            len(data[h_len: len(data)]), norm='ortho')
        freq = np.fft.rfftfreq(h_len, 1)
        self.chan_fft(np.concatenate([freq, np.abs(x_fft), np.abs(z_fft)]))

        # searching of working DR point
        try:
            x_arr = freq[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))]
            z_arr = freq[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))]
            x_index = np.argmax(np.abs(x_fft)[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))])
            z_index = np.argmax(np.abs(z_fft)[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))])
            x_tune = round(x_arr[x_index], 6)
            z_tune = round((1 - z_arr[z_index]), 6)
            self.chan_tunes.setValue(np.array([x_tune, z_tune]))
        except ValueError:
            pass


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