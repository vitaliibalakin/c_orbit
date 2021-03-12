#!/usr/bin/env python3
from bpm_base.device_proc import DeviceFunc
import pycx4.qcda as cda
import time
import numpy as np


class CorMeasure(DeviceFunc):
    def __init__(self, call_upon_completion, name, it_id, step, n_mesh, prg, resp_type='coords'):
        super(CorMeasure, self).__init__()
        self.chans = {'Iset': None, 'Imes': None}
        self.val = {'Iset': None, 'Imes': None, 'time': None}
        self.name = name
        self.id = it_id
        self.init_val = None
        self.step = step
        self.n_mesh = -1 * n_mesh
        self.prg = prg
        self.stop = n_mesh + 1
        self.response = None
        self.std_err = None
        self.status = None
        self.flag = False
        self.time_flag = False
        self.err_flag = False
        self.data_flag = True
        self.time_stamp = 0
        self.resp_type = resp_type
        self.callback = call_upon_completion
        self.chan_resps = {'coords': cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64),
                           'tunes': cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=1)}
        self.cor_data_resps = {'coords': np.zeros([32, ]), 'tunes': np.zeros([2, ])}
        self.cor_std = np.zeros([32, ])
        for chan in ['Iset', 'Imes']:
            cor_chan = cda.DChan(name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan
        self.cor_data = self.cor_data_resps[resp_type]
        self.chan_data = self.chan_resps[resp_type]
        self.chan_data.valueMeasured.connect(self.data_proc)

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.data_is_ready, self.cor_error, 100)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.data_is_ready, self.cor_error, 100)

    def proc(self):
        self.prg.setValue((self.n_mesh / 2 / (self.stop-1) + 1 / 2) * 100)
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.n_mesh == self.stop:
            self.flag = False
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.response = [self.cor_data[1:], self.init_val]
            self.std_err = self.cor_std[1:]
            self.callback(self.name)
        else:
            self.chans['Iset'].setValue(self.init_val + self.n_mesh * self.step)
            # print(self.name, self.n_mesh)
            self.n_mesh += 1
            self.time_flag = True
            self.time_stamp = time.time() + 3

    def cor_error(self, reason):
        if reason == 'check_eq':
            self.err_flag = True
            self.time_stamp = time.time() + 3
        if reason == 'verif':
            self.status = 'fail'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)

    def data_is_ready(self):
        self.data_flag = False

    def data_proc(self, chan):
        if not self.data_flag:
            self.data_flag = True
            if self.resp_type == 'coords':
                self.cor_data = np.vstack((self.cor_data, chan.val[0:32]))
                self.cor_std = np.vstack((self.cor_std, chan.val[32:]))
            elif self.resp_type == 'tunes':
                self.cor_data = np.vstack((self.cor_data, chan.val))
            self.proc()
