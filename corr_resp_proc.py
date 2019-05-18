#!/usr/bin/env python3

import sys
import numpy as np
import pyqtgraph as pg
from scipy import optimize
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic


class RespProc(QMainWindow):
    def __init__(self):
        super(RespProc, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("resp_proc.ui", self)
        self.show()

        self.read_file('crm3')
        self.cur_bpm = 'bpm01'
        self.bpm_plot()

        self.bpm_vals = {'bpm01': [], 'bpm02': [], 'bpm03': [], 'bpm04': [], 'bpm05': [], 'bpm07': [], 'bpm08': [],
                         'bpm09': [], 'bpm10': [], 'bpm11': [], 'bpm12': [], 'bpm13': [], 'bpm14': [], 'bpm15': [],
                         'bpm16': []}
        self.bpm_const = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                          'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                          'bpm16': 0}
        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                     'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16']
        print('start')
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setRange(yRange=[-40, 40])
        p = QVBoxLayout()
        self.widget.setLayout(p)
        p.addWidget(self.plot)

        self.cur_lines = {'0': np.ones([16, ]), '1': np.ones([16, ]), '2': np.ones([16, ]), '3': np.ones([16, ])}

        self.comboBox.currentTextChanged.connect(self.bpm_changed)
        self.comboBox_2.currentTextChanged.connect(self.cor_changed)

    def cor_changed(self):
        self.read_file(self.comboBox_2.currentText())
        self.bpm_plot()

    def read_file(self, cor):
        f = open(cor + '.txt', 'r')
        cor_info = f.readline()
        f.close()
        init_cur = float(cor_info.split('|')[0])
        cur_step = float(cor_info.split('|')[1])
        resp_data = np.loadtxt(cor + '.txt', skiprows=1)
        for i in range(len(resp_data[0])):
            self.bpm_vals[self.bpms[i]] = np.vstack((np.arange(init_cur - 20 * cur_step,
                                                               init_cur + 20 * cur_step,
                                                               20), resp_data[:, i]))
            const, pcov = optimize.curve_fit(self.lin_fit, self.bpm_vals[self.bpms[i]][0],
                                             self.bpm_vals[self.bpms[i][1]])
            self.bpm_vals[self.bpms[i]] = \
                np.vstack((self.bpm_vals[self.bpms[i]],
                           self.lin_fit(self.bpm_vals[self.bpms[i]][0], const)))
            self.bpm_const[self.bpms[i]] = const

    def bpm_changed(self):
        self.cur_bpm = self.comboBox.currentText()
        self.bpm_plot()

    def bpm_plot(self):
        self.plot.clear()
        self.plot.plot(self.bpm_vals[self.cur_bpm][0], self.bpm_vals[self.cur_bpm][1], pen=None, symbol='o')
        self.plot.plot(self.bpm_vals[self.cur_bpm][0], self.bpm_vals[self.cur_bpm][2], pen=pg.mkPen('g'))

    @staticmethod
    def lin_fit(x, a):
        return a * x


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = RespProc()
    sys.exit(app.exec_())
