#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import pycx4.qcda as cda
import numpy as np
import time

from basic_module_2_1 import BasicFunc


class MainMagnetization(BasicFunc):
    def __init__(self, call_upon_completion, name, step=0.5, stop=6):
        super(MainMagnetization, self).__init__()
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
            cor_chan = cda.DChan('canhw:12.' + name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.magnetiz_proc, self.cor_error, 1.2)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.magnetiz_proc, self.cor_error, 1.2)

    def magnetiz_proc(self):
        print(self.name, self.counter)
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.counter == self.stop:
            self.flag = False
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name, 'main')
        else:
            self.chans['Iset'].setValue(self.init_val + self.step * (-1)**self.counter)
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
            self.callback(self.name, 'main')


class CorMagnetization(BasicFunc):
    def __init__(self, call_upon_completion, name, step=500, stop=6):
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
            cor_chan = cda.DChan('canhw:12.' + name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.magnetiz_proc, self.cor_error, 100)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.magnetiz_proc, self.cor_error, 100)

    def magnetiz_proc(self):
        print(self.name, self.counter)
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.counter == self.stop:
            self.flag = False
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name, 'cor')
        else:
            self.chans['Iset'].setValue(self.init_val + self.step * (-1)**self.counter)
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
            self.callback(self.name, 'cor')
        

class CorMeasure(BasicFunc):
    def __init__(self, call_upon_completion, name, step=100, n_iter=5):
        super(CorMeasure, self).__init__()
        self.chans = {'Iset': None, 'Imes': None}
        self.val = {'Iset': None, 'Imes': None, 'time': None}
        self.bpm_val = {'x_orbit': None, 'z_orbit': None}
        self.name = name
        self.init_val = None
        self.step = step
        self.n_iter = -1 * n_iter
        self.stop = n_iter + 1
        self.cor_data = np.zeros([30, ])
        self.response = None
        self.status = None
        self.flag = False
        self.time_flag = False
        self.err_flag = False
        self.data_flag = {'x_orbit': 1, 'z_orbit': 1}
        self.time_stamp = 0
        self.callback = call_upon_completion

        for chan in ['Iset', 'Imes']:
            cor_chan = cda.DChan('canhw:12.' + name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan
        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_x_orbit.valueMeasured.connect(self.bpm_proc)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        self.chan_z_orbit.valueMeasured.connect(self.bpm_proc)

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
            self.chans['Iset'].setValue(self.init_val + self.n_iter * self.step)
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
        self.data_flag['x_orbit'] = 0
        self.data_flag['z_orbit'] = 0

    def bpm_proc(self, chan):
        otype = chan.name.split('.')[-1]
        self.bpm_val[otype] = chan.val
        if not self.data_flag[otype]:
            self.data_flag[otype] = 1
            if all(self.data_flag.values()):
                self.cor_data = np.vstack((self.cor_data, np.append(self.bpm_val['x_orbit'],
                                                                    self.bpm_val['z_orbit'])))
                self.cor_proc()


class RMA(BasicFunc):
    def __init__(self, corr_names=None):
        super(RMA, self).__init__()
        # self.cor_names = ['rst2.c1d2_z', 'rst2.c1f2_x', 'rst2.c1f1_x', 'rst2.c1d1_z', 'rst2.c2d2_z', 'rst2.c2f2_x',
        #                    'rst2.c2f1_x', 'rst2.c2d1_z', 'rst2.c3d2_z', 'rst2.c3f2_x', 'rst2.c3f1_x', 'rst2.c3d1_z',
        #                    'rst2.c4d2_z', 'rst2.c4f2_x', 'rst2.c4f1_x', 'rst2.c4d1_z',
        #                    'rst2.crm1', 'rst2.crm2', 'rst2.crm3', 'rst2.crm4', 'rst2.crm5', 'rst2.crm6', 'rst2.crm7',
        #                    'rst2.crm8',
        #                    'rst3.c3d3_z', 'rst3.c3f3_x', 'rst3.c4d3_z', 'rst3.c4f3_x',
        #                    'rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
        #                    'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
        #                    'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
        #                    'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
        #                    'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q', 'rst3.Sx2_1F4', 'rst3.Sy2_1F4',
        #                    'rst3.Sx1_1F4', 'rst3.Sy1_1F4', 'rst3.Sx2_2F4', 'rst3.Sy2_2F4', 'rst3.Sy1_2F4',
        #                    'rst3.Sx1_2F4', 'rst3.Sx2_3F4', 'rst3.Sy2_3F4', 'rst3.Sy1_3F4', 'rst3.Sx1_3F4',
        #                    'rst3.Sx2_4F4', 'rst3.Sy2_4F4', 'rst3.Sy1_4F4', 'rst3.Sx1_4F4', 'rst4.cSM1', 'rst4.cSM2',
        #                    'rst4.c1f4_z', 'rst4.c1d3_z', 'rst4.c1f3_x', 'rst4.c2f4_z', 'rst4.c2d3_z', 'rst4.c2f3_x',
        #                    'rst4.c3f4_z', 'rst4.c4f4_z']

        self.main_names = ['drm', 'dsm', 'qd1', 'qf1n2', 'qf4', 'qd2', 'qd3', 'qf3']
        self.cor_names = ['rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
                           'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
                           'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
                           'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
                           'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q']
        self.cor_mag_fail = []
        self.stack_names = self.cor_names.copy() #+ self.main_names.copy()
        self.main_2_mag = {main: MainMagnetization(self.magn_comp, main) for main in self.main_names}
        self.cor_2_mag = {cor: CorMagnetization(self.magn_comp, cor) for cor in self.cor_names}
        self.mag_types = {'cor': self.cor_2_mag, 'main': self.main_2_mag}

        self.cor_2_resp = {cor: CorMeasure(self.mes_comp, cor) for cor in self.cor_names}
        self.resp_matr = {name: [] for name in self.cor_names}
        QTimer.singleShot(9000, self.cor_orbit_response)

    def cor_magnetization(self):
        for mtype, coresp_dict in self.mag_types.items():
            for elem_name, elem in coresp_dict.items():
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

    def magn_comp(self, name, mtype):
        print(name, self.mag_types[mtype][name].status)
        self.stack_names.remove(name)
        if self.mag_types[mtype][name].status == 'fail':
            print(name, 'mag fail')
            self.cor_mag_fail.append(name)
        elif self.mag_types[mtype][name].status == 'completed':
            if not len(self.stack_names):
                self.stack_names = self.cor_names.copy()
                print('mag finished')
                if not len(self.cor_mag_fail):
                    print('Fail List EMPTY')
                else:
                    print(self.cor_mag_fail)
                    for elem in self.cor_mag_fail:
                        self.stack_names.remove(elem)
                # self.cor_orbit_response()
        elif not self.mag_types[mtype][name].status:
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
