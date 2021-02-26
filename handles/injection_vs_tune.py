#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import pycx4.qcda as cda
import json
import sys


class InjTune(QMainWindow):
    def __init__(self):
        super(InjTune, self).__init__()

        self.chan_ring_current = cda.DChan('cxhw:0.dcct.beamcurrent', on_update=True)
        self.chan_ring_current.valueMeasured.connect(self.ring_current_changed)
        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=True)
        self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_f3 = cda.DChan('canhw:12.qf3.Iset')
        self.chan_f3.valueMeasured.connect(self.i_f3_changed)
        self.chan_d3 = cda.DChan('canhw:12.qd3.Iset')
        self.chan_d3.valueMeasured.connect(self.i_d3_changed)
        self.chan_injected = cda.IChan('cxhw:0.ddm.injected', on_update=True)
        self.chan_injected.valueMeasured.connect(self.injection_event)

        self.cur_tunes = [0.0, 0.0]
        self.tunes_flag = False
        self.cur_flag = True
        self.permission = False
        self.counter = 0
        self.i_f3 = 0
        self.i_d3 = 0
        #############################
        self.shift_x = [0.4459, 0.1422]
        self.shift_y = [0.1394, 0.4004]
        self.n_iter = 10
        self.cur_x_it = 0
        self.cur_y_it = 0
        #############################
        self.init_f3_flag = True
        self.init_d3_flag = True
        self.init_f3 = 0
        self.init_d3 = 0

        # QTimer.singleShot(6000, self.start)

    def start(self):
        # n*x tune shift
        self.i_f3 += self.n_iter * self.shift_x[0]
        self.i_d3 += self.n_iter * self.shift_x[1]
        # n*y tune shift
        self.i_f3 += self.n_iter * self.shift_y[0]
        self.i_d3 += self.n_iter * self.shift_y[1]

        self.chan_f3.setValue(self.i_f3)
        self.chan_d3.setValue(self.i_d3)
        self.cur_x_it = -1 * self.n_iter
        self.cur_y_it = -1 * self.n_iter
        QTimer.singleShot(6000, self.set_tune_flag_true)

    def injection_event(self, chan):
        self.permission = True

    def i_f3_changed(self, chan):
        if self.init_f3_flag:
            self.init_f3 = chan.val
            self.init_f3_flag = False
        self.i_f3 = chan.val

    def i_d3_changed(self, chan):
        if self.init_d3_flag:
            self.init_d3 = chan.val
            self.init_d3_flag = False
        self.i_d3 = chan.val

    def ring_current_changed(self, chan):
        if self.counter >= 22:
            self.counter = 0
            self.cur_flag = False
            self.tune_shift()
        else:
            if self.cur_flag & self.permission:
                self.permission = False
                self.counter += 1
                self.ring_cur_data[json.dumps(self.cur_tunes)].append(chan.val)

    def tunes_changed(self, chan):
        if self.tunes_flag:
            self.cur_tunes[0] = chan.val[0]
            self.cur_tunes[1] = chan.val[1]
            self.ring_cur_data[json.dumps(self.cur_tunes)] = []
            self.cur_flag = True
            self.tunes_flag = False

    def tune_shift(self):
        self.make_shift()
        QTimer.singleShot(4000, self.set_tune_flag_true)

    def make_shift(self):
        print(self.cur_x_it, self.cur_y_it)
        print('--------------------------')
        if self.cur_x_it == self.n_iter:
            if self.cur_y_it == self.n_iter:
                # end & save
                print('FINISH')
                f = open('save_inj_tune_resp.txt', 'w')
                f.write(json.dumps(self.ring_cur_data))
                f.close()
                self.chan_f3.setValue(self.init_f3)
                self.chan_d3.setValue(self.init_d3)
                sys.exit(app.exec_())
                # start params
                self.cur_tunes = [0.0, 0.0]
                self.tunes_flag = False
                self.cur_flag = False
                self.n_iter = 1
                self.cur_x_it = 0
                self.cur_y_it = 0
                self.init_f3_flag = True
                self.init_d3_flag = True
                self.init_f3 = 0
                self.init_d3 = 0
            else:
                # y tune shift
                self.i_f3 -= self.shift_y[0]
                self.i_d3 -= self.shift_y[1]
                self.cur_y_it += 1
                # 2*n*x tune shift
                self.i_f3 += 2 * self.n_iter * self.shift_x[0]
                self.i_d3 += 2 * self.n_iter * self.shift_x[1]

                self.chan_f3.setValue(self.i_f3)
                self.chan_d3.setValue(self.i_d3)
                self.cur_x_it = -1 * self.n_iter
        else:
            # x tune shift
            self.chan_f3.setValue(self.i_f3 - self.shift_x[0])
            self.chan_d3.setValue(self.i_d3 - self.shift_x[1])
            self.cur_x_it += 1

    def set_tune_flag_true(self):
        self.tunes_flag = True


if __name__ == "__main__":
    app = QApplication(['inj_tune'])
    w = InjTune()
    sys.exit(app.exec_())
