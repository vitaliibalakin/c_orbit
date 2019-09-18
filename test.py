#!/usr/bin/env python3

import pycx4.qcda as cda
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout
from PyQt5 import uic


class Test(QMainWindow):
    def __init__(self):
        super(Test, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/test.ui", self)
        self.show()

        self.cur_bpm = 'bpm01'
        self.chan_bpm_vals = {'bpm01': {}, 'bpm02': {}, 'bpm03': {}, 'bpm04': {}, 'bpm05': {}, 'bpm07': {}, 'bpm08': {},
                              'bpm09': {}, 'bpm10': {}, 'bpm11': {}, 'bpm12': {}, 'bpm13': {}, 'bpm14': {}, 'bpm15': {},
                              'bpm16': {}, 'bpm17': {}}
        self.chan_bpm_vals_env = {'bpm01': {}, 'bpm02': {}, 'bpm03': {}, 'bpm04': {}, 'bpm05': {}, 'bpm07': {}, 'bpm08': {},
                                  'bpm09': {}, 'bpm10': {}, 'bpm11': {}, 'bpm12': {}, 'bpm13': {}, 'bpm14': {}, 'bpm15': {},
                                  'bpm16': {}, 'bpm17': {}}
        print('start')
        for bpm, bpm_coor in self.chan_bpm_vals.items():
            for i in range(4):
                chan = cda.VChan('cxhw:37.ring.' + bpm + '.line' + str(i), max_nelems=4096)
                chan.valueMeasured.connect(self.data_proc)
                self.chan_bpm_vals[bpm].update({i: chan})
            chan_env = cda.VChan('cxhw:37.ring.' + bpm + '.dataenvl', max_nelems=512)
            chan_env.valueMeasured.connect(self.data_proc_env)
            self.chan_bpm_vals_env[bpm].update({0: chan_env})

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setRange(yRange=[0, 400])
        self.plot_env = pg.PlotWidget()
        self.plot_env.showGrid(x=True, y=True)
        p = QHBoxLayout()
        self.widget.setLayout(p)
        p.addWidget(self.plot)
        p.addWidget(self.plot_env)

        self.cur_lines = {'0': np.ones([100, ]), '1': np.ones([100, ]), '2': np.ones([100, ]), '3': np.ones([100, ])}

        self.comboBox.currentTextChanged.connect(self.bpm_changed)

    def bpm_changed(self):
        self.cur_bpm = self.comboBox.currentText()

    def data_proc_env(self, chan):
        if chan.name.split('.')[-2] == self.cur_bpm:
            self.plot_env.clear()
            self.plot_env.plot(chan.val[:11], pen=pg.mkPen('r'))
            self.plot_env.plot(chan.val[128:139], pen=pg.mkPen('g'))
            self.plot_env.plot(chan.val[256:267], pen=pg.mkPen('b'))
            self.plot_env.plot(chan.val[384:395], pen=pg.mkPen('y'))

    def data_proc(self, chan):
        if chan.name.split('.')[-2] == self.cur_bpm:
            self.cur_lines[chan.name.split('.')[-1][-1]] = chan.val
            self.plot.clear()
            self.plot.plot(self.cur_lines['0'], pen=pg.mkPen('r'))
            self.plot.plot(self.cur_lines['1'], pen=pg.mkPen('g'))
            self.plot.plot(self.cur_lines['2'], pen=pg.mkPen('b'))
            self.plot.plot(self.cur_lines['3'], pen=pg.mkPen('y'))
            # self.coor_calc()

    def coor_calc(self):
        if self.cur_bpm in ['bpm04', 'bpm05', 'bpm13', 'bpm14']:
            x_ = np.mean((self.cur_lines['0'] - self.cur_lines['2']) / 2 / (self.cur_lines['0'] + self.cur_lines['2']))
            z_ = np.mean((self.cur_lines['1'] - self.cur_lines['3']) / 2 / (self.cur_lines['1'] + self.cur_lines['3']))
        else:
            x_ = np.mean((self.cur_lines['1'] + self.cur_lines['2'] - self.cur_lines['0'] - self.cur_lines['3']) /
                         (self.cur_lines['1'] + self.cur_lines['2'] + self.cur_lines['0'] + self.cur_lines['3']) / 2)
            z_ = np.mean((self.cur_lines['0'] + self.cur_lines['1'] - self.cur_lines['2'] - self.cur_lines['3']) /
                         (self.cur_lines['1'] + self.cur_lines['2'] + self.cur_lines['0'] + self.cur_lines['3']) / 2)
        rho_ = np.sqrt(x_**2 + z_**2)
        rho = (1 - np.sqrt(1 - 4 * rho_**2)) / 2 / rho_
        if self.cur_bpm in ['bpm04', 'bpm05', 'bpm13', 'bpm14']:
            x = x_ * (1 + rho**2) * 40
            z = z_ * (1 + rho**2) * 40
        else:
            x = x_ * (1 + rho ** 2) * 30
            z = z_ * (1 + rho ** 2) * 30
        output = str(x) + '|||||' + str(z)
        self.statusbar.showMessage(output)


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = Test()
    sys.exit(app.exec_())
