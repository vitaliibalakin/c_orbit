#!/usr/bin/env python3
import numpy as np
import pycx4.pycda as cda


class BPM:
    def __init__(self, bpm, receiver):
        super(BPM, self).__init__()
        self.receiver = receiver
        self.name = bpm
        self.turns_mes = 0
        self.act_state = 1
        self.marker = 0
        self.coor = (0, 0)
        self.sigma = (0, 0)

        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)
        self.chan_datatxzi = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
        self.chan_numpts = cda.DChan('cxhw:37.ring.' + bpm + '.numpts')
        self.chan_marker = cda.DChan('cxhw:37.ring.' + bpm + '.marker')
        self.chan_datatxzi.valueMeasured.connect(self.data_proc)
        self.chan_marker.valueMeasured.connect(self.marker_proc)

    def marker_proc(self, chan):
        # print(chan.val)
        self.marker = 1
        self.receiver()

    def data_proc(self, chan):
        data_len = int(len(chan.val) / 4)
        self.coor = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
        self.sigma = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))
        # print(chan.name, data_len)
        if self.turns_mes:
            self.chan_fft.setValue(chan.val[data_len:3 * data_len])
            self.chan_turns.setValue(chan.val[3*data_len:4*data_len])
