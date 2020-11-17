#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
from scipy import optimize
import pyqtgraph as pg


class CoorPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(CoorPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        # self.setLogMode(False, True)
        self.setLabel('left', "coor", units='mm')
        self.setLabel('bottom', "Turn")
        self.x_plot = pg.PlotCurveItem()
        self.addItem(self.x_plot)
        self.z_plot = pg.PlotCurveItem()
        self.addItem(self.z_plot)
        self.setRange(xRange=[0, 1000])
        self.time = np.arange(1024)

    def coor_plot(self, data):
        h_len = len(data) // 2
        x = data[:h_len]
        z = data[h_len: len(data)]
        try:
            params, pcov = optimize.curve_fit(self.osc_fit, self.time, z, p0=[4, 5, 3, 5e-6, 11])
            print(params)
        except RuntimeError:
            print('fit error')
        self.x_plot.setData(x, pen=pg.mkPen('b', width=1))
        self.z_plot.setData(z, pen=pg.mkPen('r', width=1))

    @staticmethod
    def osc_fit(t, amp, freq, phase, decr, zero):
        return amp*np.cos(2*np.pi*freq*t + phase)*np.exp(-decr*t) + zero


if __name__ == "__main__":
    app = QApplication(['coor_plot'])
    w = CoorPlot(None)
    sys.exit(app.exec_())
