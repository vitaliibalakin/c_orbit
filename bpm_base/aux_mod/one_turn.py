#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
from scipy import optimize
import pyqtgraph as pg


class OneTurnPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(OneTurnPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        # self.setLogMode(False, True)
        self.setLabel('left', "coor", units='mm')
        self.setLabel('bottom', "Turn")
        self.x_fit_plot = pg.PlotCurveItem()
        self.addItem(self.x_fit_plot)
        self.z_fit_plot = pg.PlotCurveItem()
        self.addItem(self.z_fit_plot)
        self.x_plot = pg.PlotCurveItem()
        self.addItem(self.x_plot)
        self.z_plot = pg.PlotCurveItem()
        self.addItem(self.z_plot)
        self.setRange(xRange=[0, 1])
        self.time = np.array([0.8524, 2.7974, 4.0234, 5.9514, 7.7664, 9.6884, 10.9154, 12.8604, 14.5802, 16.5152,
                              17.7697, 19.6742, 21.4842, 23.39292, 24.6282, 26.5572]) / 27.4011

    def one_turn_plot(self, data):
        time = self.time
        h_len = len(data) // 2
        x = data[:h_len]
        z = data[h_len: len(data)]
        for_del = []
        for i in range(len(x)):
            if x[i] == 100.0:
                for_del.append(i)
        for i in reversed(for_del):
            del (x[i])
            del (z[i])
            del (time[i])
        try:
            params, pcov = optimize.curve_fit(self.osc_fit, time, x, p0=[4, 5, 3, 5e-6, 11])
            self.x_fit_plot.setData(x=np.linspace(0, 1, 100),
                                    y=self.osc_fit(np.linspace(0, 1, 100), params[0], params[1], params[2], params[3], params[4]),
                                    pen=pg.mkPen('b', width=1))
            # self.z_fit_plot.setData(x=self.time, y=x, pen=pg.mkPen('r', width=1))
            print('one_turn_plot', params)
        except RuntimeError:
            print('fit error')
        self.x_plot.setData(x=time, y=x, pen=None, symbol='o')
        # self.z_plot.setData(x=time, y=z, pen=None, symbol='x')

    @staticmethod
    def osc_fit(t, amp, freq, phase, decr, zero):
        return amp*np.cos(2*np.pi*freq*t + phase)*np.exp(-decr*t) + zero


if __name__ == "__main__":
    app = QApplication(['one_turn_proc'])
    w = OneTurnPlot(None)
    sys.exit(app.exec_())
