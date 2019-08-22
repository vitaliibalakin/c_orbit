#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import pyqtgraph as pg

import sys
import pycx4.qcda as cda
import numpy as np
import time
from scipy import optimize
import json

from basic_module_2_1 import BasicFunc


class Magnetization(BasicFunc):
    def __init__(self, call_upon_completion, name, step=500, stop=6, odz=100):
        super(Magnetization, self).__init__()
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
        self.odz = odz
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
                    self.checking_equality(self.val, self.magnetiz_proc, self.error, self.odz)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.magnetiz_proc, self.error, self.odz)

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
            self.chans['Iset'].setValue(self.init_val + self.step * (-1)**self.counter)
            self.counter += 1
            self.time_flag = True
            self.time_stamp = time.time() + 3

    def error(self, reason):
        if reason == 'check_eq':
            self.err_flag = True
            self.time_stamp = time.time() + 3
        if reason == 'verif':
            self.status = 'fail'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)


class CorMeasure(BasicFunc):
    def __init__(self, call_upon_completion, name, step=100, n_iter=5, a_bpm=15):
        super(CorMeasure, self).__init__()
        self.chans = {'Iset': None, 'Imes': None}
        self.val = {'Iset': None, 'Imes': None, 'time': None}
        self.bpm_val = {'x_orbit': None, 'z_orbit': None}
        self.name = name
        self.init_val = None
        self.step = step
        self.n_iter = -1 * n_iter
        self.stop = n_iter + 1
        self.cor_data = np.zeros([2*a_bpm, ])
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


class RMA(QMainWindow, BasicFunc):
    def __init__(self):
        super(RMA, self).__init__()
        uic.loadUi("uis/rma_main_window.ui", self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # x sing values plot
        self.plt_x = pg.PlotWidget(parent=self)
        self.plt_x.showGrid(x=True, y=True)
        self.plt_x.addLegend(offset=(0, 100))
        self.plt_x.setLogMode(False, True)
        # z sing values plot
        self.plt_z = pg.PlotWidget(parent=self)
        self.plt_z.showGrid(x=True, y=True)
        self.plt_z.addLegend(offset=(0, 100))
        self.plt_z.setLogMode(False, True)

        p = QVBoxLayout()
        self.sv_plot.setLayout(p)
        p.addWidget(self.plt_x)
        p.addWidget(self.plt_z)

        self.show()
        self.rma_ready = 0
        self.rm = {}
        self.stack_names = []
        self.cor_fail = []
        self.cor_names = []
        self.list_names = []
        self.resp_matr_x = {}
        self.resp_matr_z = {}

        self.btn_start_rma.clicked.connect(self.start_rma)
        self.btn_stop_rma.clicked.connect(self.stop_rma)
        self.btn_reverse_rm.clicked.connect(self.reverse_rm)

    def start_rma(self):
        print('start_rma')
        if self.rma_ready:
            self.label_type.setText('RMA')
            self.rma_ready = 0
            self.cor_names = ['rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
                              'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
                              'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
                              'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
                              'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q']
            self.stack_names = self.cor_names.copy()

            # deleting from stack FAIL elems
            if not len(self.cor_fail):
                print('Fail List EMPTY')
            else:
                print(self.cor_fail)
                for elem in self.cor_fail:
                    if elem in self.stack_names:
                        self.stack_names.remove(elem)
                self.cor_fail = []
            self.counter = len(self.stack_names)
            self.cor_2_resp = {
                cor: CorMeasure(self.mes_comp, cor, step=self.rma_step.value(), n_iter=self.rma_iter.value(), a_bpm=15)
                for cor in self.stack_names}
            self.cor_orbit_response()
        else:
            self.log_msg.clear()
            self.label_type.setText('Magnetization')
            cor_names = ['rst2.c1d2_z', 'rst2.c1f2_x', 'rst2.c1f1_x', 'rst2.c1d1_z', 'rst2.c2d2_z', 'rst2.c2f2_x',
                         'rst2.c2f1_x', 'rst2.c2d1_z', 'rst2.c3d2_z', 'rst2.c3f2_x', 'rst2.c3f1_x', 'rst2.c3d1_z',
                         'rst2.c4d2_z', 'rst2.c4f2_x', 'rst2.c4f1_x', 'rst2.c4d1_z',
                         'rst2.crm1', 'rst2.crm2', 'rst2.crm3', 'rst2.crm4', 'rst2.crm5', 'rst2.crm6', 'rst2.crm7',
                         'rst2.crm8',
                         'rst3.c3d3_z', 'rst3.c3f3_x', 'rst3.c4d3_z', 'rst3.c4f3_x',
                         'rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
                         'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
                         'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
                         'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
                         'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q', 'rst3.Sx2_1F4', 'rst3.Sy2_1F4',
                         'rst3.Sx1_1F4', 'rst3.Sy1_1F4', 'rst3.Sx2_2F4', 'rst3.Sy2_2F4', 'rst3.Sy1_2F4',
                         'rst3.Sx1_2F4', 'rst3.Sx2_3F4', 'rst3.Sy2_3F4', 'rst3.Sy1_3F4', 'rst3.Sx1_3F4',
                         'rst3.Sx2_4F4', 'rst3.Sy2_4F4', 'rst3.Sy1_4F4', 'rst3.Sx1_4F4', 'rst4.cSM1', 'rst4.cSM2',
                         'rst4.c1f4_z', 'rst4.c1d3_z', 'rst4.c1f3_x', 'rst4.c2f4_z', 'rst4.c2d3_z', 'rst4.c2f3_x',
                         'rst4.c3f4_z', 'rst4.c4f4_z']
            main_names = ['drm', 'dsm', 'qd1', 'qf1n2', 'qf4', 'qd2', 'qd3', 'qf3']
            self.stack_names = main_names.copy() + cor_names.copy()
            self.counter = len(self.stack_names)
            main_2_mag = {main: Magnetization(self.magn_comp, main, step=self.mag_range_main.value(),
                                              stop=self.mag_iter_main.value(), odz=1.2) for main in main_names}
            cor_2_mag = {cor: Magnetization(self.magn_comp, cor, step=self.mag_range_cor.value(),
                                            stop=self.mag_iter_cor.value(), odz=100) for cor in cor_names}
            self.mag_types = {**main_2_mag.copy(), **cor_2_mag.copy()}
            for elem_name, elem in self.mag_types.items():
                elem.magnetiz_proc()

    def stop_rma(self):
        print('stop_rma')

    def cor_orbit_response(self):
        if len(self.stack_names):
            self.cor_2_resp[self.stack_names[0]].cor_proc()
        else:
            self.log_msg.append('work is done here, saving RM')
            self.save_rma()

    def mes_comp(self, name):
        self.log_msg.append(name + ": " + self.cor_2_resp[name].status)
        self.stack_names.remove(name)
        self.prg_bar.setValue((len(self.stack_names) / self.counter) * 100)
        if self.cor_2_resp[name].status == 'fail':
            self.cor_fail.append(name)
            self.cor_orbit_response()
        elif self.cor_2_resp[name].status == 'completed':
            self.rma_string_calc(name, self.cor_2_resp[name].response)
            self.cor_orbit_response()
        elif not self.cor_2_resp[name].status:
            self.log_msg.append(name, 'response error')
        else:
            self.log_msg.append(name, 'wtf')

    def magn_comp(self, name):
        self.log_msg.append(name + ": " + self.mag_types[name].status)
        self.stack_names.remove(name)
        self.prg_bar.setValue((1 - len(self.stack_names) / self.counter) * 100)
        if self.mag_types[name].status == 'fail':
            self.cor_fail.append(name)
        elif not self.mag_types[name].status:
            self.cor_fail.append(name)
        else:
            self.log_msg.append(name, 'wtf')

        if not len(self.stack_names):
            self.log_msg.append('mag finished, rma started')
            self.rma_ready = 1
            self.start_rma()

    def rma_string_calc(self, name, data):
        mid = int(len(data[0]) / 2)
        buffer_x = []
        buffer_z = []
        cur = np.arange(-1 * self.rma_step.value() * self.rma_iter.value(),
                        self.rma_step.value() * (self.rma_iter.value() + 1), self.rma_step.value())
        for i in range(mid):
            const, pcov = optimize.curve_fit(self.lin_fit, cur, data[:, i])
            buffer_x.append(const[0])

        for i in range(mid, len(data[0]), 1):
            const, pcov = optimize.curve_fit(self.lin_fit, cur, data[:, i])
            buffer_z.append(const[0])
        self.resp_matr_x[name] = buffer_x
        self.resp_matr_z[name] = buffer_z

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    def save_cor_resp(self, name, data):
        if len(data) == 2:
            np.savetxt(name + '.txt', data[0], header=(str(data[1]) + '|' + '19'))
            self.resp_matr[name] = data[0]

    def save_rma(self):
        list_names = []
        rm_x = []
        for name, resp in self.resp_matr_x.values():
            list_names.append(name)
            rm_x.append(resp)
        np.savetxt(self.rm_name.text() + '_x.txt', np.array(rm_x), header=json.dumps(list_names))

        rm_z = []
        for name, resp in self.resp_matr_z.values():
            rm_z.append(resp)
        np.savetxt(self.rm_name.text() + '_z.txt', np.array(rm_z), header=json.dumps(list_names))
        self.rm = {'x': np.array(rm_x), 'z': np.array(rm_z), 'cor_names': list_names}
        self.list_names = list_names
        self.log_msg.append('RM saved')
        self.rm_svd()

    def rm_svd(self):
        self.plt_x.clear()
        self.plt_z.clear()
        u_x, s_x, vh_x = np.linalg.svd(self.rm['x'])
        u_z, s_z, vh_z = np.linalg.svd(self.rm['z'])
        self.plt_x.plot(s_x, pen=None, symbol='o')
        self.plt_z.plot(s_z, pen=None, symbol='o')

    def reverse_rm(self):
        x_sv_am = self.x_sv.value()
        z_sv_am = self.z_sv.value()
        u_x, s_x, vh_x = np.linalg.svd(self.rm['x'])
        u_z, s_z, vh_z = np.linalg.svd(self.rm['z'])
        for i in range(x_sv_am, len(s_x) - 1):
            s_x[i] = 0
        for i in range(z_sv_am, len(s_z) - 1):
            s_z[i] = 0
        s_x_r = np.zeros((vh_x.shape[0], u_x.shape[0]))
        s_x_r[:x_sv_am, :x_sv_am] = np.diag(1 / s_x)
        rm_x_rev = np.dot(np.transpose(vh_x), np.dot(s_x_r, np.transpose(u_x)))
        s_z_r = np.zeros((vh_z.shape[0], u_z.shape[0]))
        s_z_r[:z_sv_am, :z_sv_am] = np.diag(1 / s_z)
        rm_z_rev = np.dot(np.transpose(vh_z), np.dot(s_z_r, np.transpose(u_z)))

        f = open(self.rm_name.text(), 'w')
        f.write(json.dumps({'x_orbit': rm_x_rev, 'z_orbit': rm_z_rev, 'cor_names': self.list_names}))
        f.close()


if __name__ == "__main__":
    app = QApplication(['RMA'])
    w = RMA()
    sys.exit(app.exec_())
