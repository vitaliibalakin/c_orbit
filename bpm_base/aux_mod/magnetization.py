#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from bpm_base.device_proc import DeviceFunc
import pycx4.qcda as cda
import sys
import time


class Magnetization(DeviceFunc):
    def __init__(self, call_upon_completion, name, step, stop, odz, elem_prg):
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
        self.elem_prg = elem_prg
        self.callback = call_upon_completion

        for chan in ['Iset', 'Imes']:
            cor_chan = cda.DChan(name + '.' + chan)
            cor_chan.valueMeasured.connect(self.val_change)
            self.chans[chan] = cor_chan

    def val_change(self, chan):
        self.val[chan.name.split('.')[-1]] = chan.val

        if self.time_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.time_flag = False
                    self.checking_equality(self.val, self.proc, self.error, self.odz)

        if self.err_flag:
            if time.time() > self.time_stamp:
                if chan.name.split('.')[-1] == 'Imes':
                    self.err_flag = False
                    self.err_verification(self.val, self.proc, self.error, self.odz)

    def proc(self):
        if not self.flag:
            self.flag = True
            self.init_val = self.val['Iset']
        if self.counter == self.stop:
            self.flag = False
            self.counter = 0
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)
        else:
            # self.elem_prg.setValue(100 * self.counter / (self.stop - 1))
            self.elem_prg(int(100 * self.counter / (self.stop - 1)))
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
            self.counter = 0
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)


class MagnetizationProc(DeviceFunc):
    def __init__(self, **prg):
        super(MagnetizationProc, self).__init__()
        self.prg = prg.get('prg', self.proc_progress)
        self.elem_prg = prg.get('elem_prg', self.elem_progress)
        self.control_sum = 0
        self.cor_fail = []
        self.mag_names = ['canhw:12.drm', 'canhw:12.dsm', 'canhw:12.qd1', 'canhw:12.qf1n2', 'canhw:12.qf4',
                          'canhw:12.qd2', 'canhw:12.qd3', 'canhw:12.qf3']
        self.sext_names = ['canhw:12.rst3.sy2_4f4', 'canhw:12.rst3.sy1_3f4', 'canhw:12.rst3.sy2_2f4',
                           'canhw:12.rst3.sy1_1f4', 'canhw:12.rst3.sy2_1f4', 'canhw:12.rst3.sy1_2f4',
                           'canhw:12.rst3.sy2_3f4', 'canhw:12.rst3.sy1_4f4', 'canhw:12.rst3.sx2_4f4',
                           'canhw:12.rst3.sx1_3f4', 'canhw:12.rst3.sx2_2f4', 'canhw:12.rst3.sx1_1f4',
                           'canhw:12.rst3.sx2_1f4', 'canhw:12.rst3.sx1_2f4', 'canhw:12.rst3.sx2_3f4',
                           'canhw:12.rst3.sx1_4f4']
        self.main_2_mag = {name: Magnetization(self.action_loop, name, step=0.5, stop=5, odz=2, elem_prg=self.elem_prg)
                           for name in self.mag_names}
        self.sext_2_mag = {name: Magnetization(self.action_loop, name, step=400, stop=5, odz=100, elem_prg=self.elem_prg)
                           for name in self.sext_names}

        self.elems_2_mag = {**self.main_2_mag, **self.sext_2_mag}
        self.progress = {**{name: 0 for name, elem in self.main_2_mag.items()},
                         **{name: 0 for name, elem in self.sext_2_mag.items()}}
        self.main_cur = self.progress.copy()

    def start(self):
        QTimer.singleShot(3000, self.begin_proc)

    def begin_proc(self):
        self.main_cur = self.progress.copy()
        for name, elem in self.elems_2_mag.items():
            elem.proc()

    def action_loop(self, name):
        # remember init vals
        if name in self.main_cur:
            self.main_cur[name] = self.elems_2_mag[name].init_val

        if self.elems_2_mag[name].status == 'fail':
            self.control_sum += 1
            self.progress[name] = -1
            self.cor_fail.append(name)
        elif self.elems_2_mag[name].status == 'completed':
            self.control_sum += 1
            self.progress[name] = 1

        if self.control_sum == len(self.progress):
            self.control_sum = 0
            self.prg(int(146))
            for key, val in self.progress.items():
                self.progress[key] = 0
        else:
            self.prg(int(self.control_sum/len(self.progress) * 100))

    def proc_progress(self, val):
        print(val)
        if val == 146:
            print('magnetization has finished')
            sys.exit()

    def elem_progress(self, val):
        print('elem_progress', val)


if __name__ == "__main__":
    app = QApplication(['MagnetizationProc'])
    w = MagnetizationProc()
    sys.exit(app.exec_())
