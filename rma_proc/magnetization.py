#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from bpm_base.device_proc import DeviceFunc
import pycx4.qcda as cda
import sys
import time


class Magnetization(DeviceFunc):
    def __init__(self, call_upon_completion, name, step, stop, odz, prg):
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
        self.prg = prg
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
            self.status = 'completed'
            self.chans['Iset'].setValue(self.init_val)
            self.callback(self.name)
        else:
            # self.prg.setValue(100 * self.counter / (self.stop - 1))
            self.prg(100 * self.counter / (self.stop - 1))
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


class MagnetizationProc(DeviceFunc):
    def __init__(self, **prg):
        super(MagnetizationProc, self).__init__()
        self.prg = prg.get('prg', self.proc_progress)
        self.control_sum = 0
        self.cor_fail = []
        self.mag_names = ['canhw:12.drm', 'canhw:12.dsm', 'canhw:12.qd1', 'canhw:12.qf1n2', 'canhw:12.qf4',
                          'canhw:12.qd2', 'canhw:12.qd3', 'canhw:12.qf3']
        self.elems_2_mag = {name: Magnetization(self.action_loop, name, step=0.5, stop=5, odz=1.2, prg=self.prg)
                            for name in self.mag_names}
        self.progress = {name: 0 for name, elem in self.elems_2_mag.items()}
        self.main_cur = self.progress.copy()
        QTimer.singleShot(3000, self.start)

    def start(self):
        for name, elem in self.elems_2_mag.items():
            elem.proc()

    def action_loop(self, name):
        if self.elems_2_mag[name].status == 'fail':
            self.control_sum += 1
            self.progress[name] = -1
            self.cor_fail.append(name)
        elif self.elems_2_mag[name].status == 'completed':
            self.control_sum += 1
            self.progress[name] = 1

        # remember init vals
        if not (name in self.main_cur):
            self.main_cur[name] = self.elems_2_mag[name].init_val

        if self.control_sum == len(self.progress):
            self.control_sum = 0
            self.prg(146.0)
        else:
            self.prg(round(self.control_sum/len(self.progress) * 100, 0))

    def proc_progress(self, val):
        print(val)


if __name__ == "__main__":
    app = QApplication(['MagnetizationProc'])
    w = MagnetizationProc()
    sys.exit(app.exec_())
