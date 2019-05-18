#!/usr/bin/env python3

import pycx4.qcda as cda
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic


class BpmPreproc(QMainWindow):
    def __init__(self):
        super(BpmPreproc, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("test.ui", self)
        self.show()

        self.cur_bpm = 'bpm01'
        self.chan_bpm_vals = {'bpm01': {}, 'bpm02': {}, 'bpm03': {}, 'bpm04': {}, 'bpm05': {}, 'bpm07': {}, 'bpm08': {},
                              'bpm09': {}, 'bpm10': {}, 'bpm11': {}, 'bpm12': {}, 'bpm13': {}, 'bpm14': {}, 'bpm15': {},
                              'bpm16': {}}
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0}  # , 'bpm17': 0}
        print('start')
        for bpm, bpm_coor in self.bpm_val_renew.items():
            for i in range(4):
                chan = cda.VChan('cxhw:37.ring.' + bpm + '.line' + str(i), max_nelems=4096)
                chan.valueMeasured.connect(self.data_proc)
                self.chan_bpm_vals[bpm].update({i: chan})
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setRange(yRange=[0, 400])
        p = QVBoxLayout()
        self.widget.setLayout(p)
        p.addWidget(self.plot)

        self.cur_lines = {'0': np.ones([16, ]), '1': np.ones([16, ]), '2': np.ones([16, ]), '3': np.ones([16, ])}

        self.comboBox.currentTextChanged.connect(self.bpm_changed)

    def bpm_changed(self):
        self.cur_bpm = self.comboBox.currentText()

    def data_proc(self, chan):
        if chan.name.split('.')[-2] == self.cur_bpm:
            self.cur_lines[chan.name.split('.')[-1][-1]] = chan.val
            self.plot.clear()
            self.plot.plot(self.cur_lines['0'], pen=pg.mkPen('r'))
            self.plot.plot(self.cur_lines['1'], pen=pg.mkPen('g'))
            self.plot.plot(self.cur_lines['2'], pen=pg.mkPen('b'))
            self.plot.plot(self.cur_lines['3'], pen=pg.mkPen('y'))
            self.coor_calc()

    def coor_calc(self):
        x_ = np.mean((self.cur_lines['0'] - self.cur_lines['2']) / 2 / (self.cur_lines['0'] + self.cur_lines['2']))
        z_ = np.mean((self.cur_lines['1'] - self.cur_lines['3']) / 2 / (self.cur_lines['1'] + self.cur_lines['3']))
        rho_ = np.sqrt(x_**2 + z_**2)
        rho = (1 - np.sqrt(1 - 4 * rho_**2)) / 2 / rho_
        x = x_ * (1 + rho**2) * 80
        z = z_ * (1 + rho**2) * 80
        output = str(x) + '|||||' + str(z)
        self.statusbar.showMessage(output)


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BpmPreproc()
    sys.exit(app.exec_())
