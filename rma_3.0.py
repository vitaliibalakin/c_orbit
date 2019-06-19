#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import pycx4.qcda as cda
import numpy as np
import time

from basic_module_2_0 import BasicFunc


class CorMagnetization(BasicFunc):
    def __init__(self, call_upon_completion, name, step=1000, stop=6):
        super(CorMagnetization, self).__init__()
        self.chans = {'Iset': None, 'Imes': None}
        self.val = {'Iset': None, 'Imes': None}
        self.name = name
        self.init_val = None
        self.step = step
        self.stop = stop
        self.counter = 0
        self.status = None
        self.flag = False
        self.time_flag = False
        self.err_flag = False
        self.time_stamp = 0
        self.callback = call_upon_completion

        for chan in ['Iset', 'Imes']:
            cor_chan = cda.DChan('canhw:12.rst2.' + name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.magnetiz_proc, self.cor_error)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.magnetiz_proc, self.cor_error)

    def magnetiz_proc(self):
        print(self.name, self.counter)
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.counter == self.stop:
            self.flag = False
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)
        else:
            self.chans['Iset'].setValue(self.init_val)# + self.step * (-1)**self.counter)
            self.counter += 1
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
        

class CorMeasure(BasicFunc):
    def __init__(self, call_upon_completion, name, step=60, n_iter=19):
        super(CorMeasure, self).__init__()
        self.chans = {'Iset': None, 'Imes': None}
        self.val = {'Iset': None, 'Imes': None, 'time': None}
        self.bpm_val = None
        self.name = name
        self.init_val = None
        self.step = step
        self.n_iter = -1 * n_iter
        self.stop = n_iter + 1
        self.cor_data = np.zeros([13, ])
        self.response = None
        self.status = None
        self.flag = False
        self.time_flag = False
        self.err_flag = False
        self.data_flag = False
        self.time_stamp = 0
        self.callback = call_upon_completion

        for chan in ['Iset', 'Imes']:
            cor_chan = cda.DChan('canhw:12.rst2.' + name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan
        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_x_orbit.valueMeasured.connect(self.bpm_proc)

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.data_is_ready, self.cor_error)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.data_is_ready, self.cor_error)

    def cor_proc(self):
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.n_iter == self.stop:
            self.flag = False
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.response = [self.cor_data[1:], self.init_val]
            self.callback(self.name)
        else:
            self.chans['Iset'].setValue(self.init_val)  # + self.n_iter * self.step)
            self.n_iter += 1
            print(self.name, self.n_iter)
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
        self.data_flag = True

    def bpm_proc(self, chan):
        self.bpm_val = chan.val

        if self.data_flag:
            self.data_flag = False
            self.cor_data = np.vstack((self.cor_data, self.bpm_val))
            self.cor_proc()


class RMA(BasicFunc):
    def __init__(self, corr_names=None):
        super(RMA, self).__init__()
        # self.corr_names = ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z', 'c3d2_z',
        #                    'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1', 'crm2', 'crm3',
        #                    'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z', 'c3d3_z', 'c1d1_q',
        #                    'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q', 'c2d1_q', 'c2f1_q',
        #                    'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q', 'c3d1_q', 'c3f1_q', 'c3d2_q',
        #                    'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q',
        #                    'c4f3_q']
        self.cor_names = ['c1d2_z', 'c1d1_z']#, 'c2d2_z', 'c2d1_z', 'c3d2_z', 'c3d1_z', 'c4d2_z', 'c4d1_z']
        self.cor_mag_fail = []
        self.stack_names = self.cor_names.copy()
        self.cor_2_resp = {cor: CorMeasure(self.mes_comp, cor) for cor in self.cor_names}
        self.cor_2_mag = {cor: CorMagnetization(self.magn_comp, cor) for cor in self.cor_names}
        self.resp_matr = {name: [] for name in self.cor_names}
        QTimer.singleShot(3000, self.cor_magnetization)

    def cor_magnetization(self):
        for cor_name, elem in self.cor_2_mag.items():
            elem.magnetiz_proc()

    def cor_orbit_response(self):
        if len(self.stack_names):
            self.cor_2_resp[self.stack_names[0]].cor_proc()
        else:
            print('my work is done here')
            self.save_rma()

    def mes_comp(self, name):
        self.stack_names.remove(name)
        if self.cor_2_resp[name].status == 'fail':
            print(name, 'cor fail')
            # should I or not continue?
            self.cor_orbit_response()
        elif self.cor_2_resp[name].status == 'completed':
            print(name, 'go to the next step')
            self.save_cor_resp(name, self.cor_2_resp[name].response)
            print('queue = ', len(self.stack_names))
            self.cor_orbit_response()
        elif not self.cor_2_resp[name].status:
            print(name, 'response error')
        else:
            print(name, 'wtf')

    def magn_comp(self, name):
        print(name, self.cor_2_mag[name].status)
        self.stack_names.remove(name)
        if self.cor_2_mag[name].status == 'fail':
            print(name, 'cor mag fail')
            self.cor_mag_fail.append(name)
        elif self.cor_2_mag[name].status == 'completed':
            if not len(self.stack_names):
                self.stack_names = self.cor_names.copy()
                print('mag finished')
                if not len(self.cor_mag_fail):
                    print('ERROR', self.cor_mag_fail)
                    for elem in self.cor_mag_fail:
                        self.stack_names.remove(elem)
                self.cor_orbit_response()
        elif not self.cor_2_mag[name].status:
            print(name, 'mag error')
        else:
            print(name, 'wtf')

    def save_cor_resp(self, name, data):
        print(len(data))
        if len(data) == 2:
            np.savetxt(name + '.txt', data[0], header=(str(data[1]) + '|' + '19'))
            self.resp_matr[name] = data[0]

    def save_rma(self):
        print('rma collecting finished')
        # self.del_chan.setValue('rma': 'file_name')  # +json.dumps


if __name__ == "__main__":
    app = QApplication(['RMA'])
    w = RMA()
    sys.exit(app.exec_())
