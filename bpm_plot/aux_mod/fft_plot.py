#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import sys
import numpy as np
import scipy.signal as sp
import pyqtgraph as pg
from scipy.fftpack import fft


class FFTPlot(pg.PlotWidget):
    def __init__(self, parent, stat_bar):
        super(FFTPlot, self).__init__(parent=parent)
        self.stat_bar = stat_bar
        self.showGrid(x=True, y=True)
        # self.setLogMode(False, True)
        self.setLabel('left', "Ampl")
        self.setLabel('bottom', "Freq")
        self.setRange(xRange=[0, 0.5])
        self.x_plot = pg.PlotCurveItem()
        self.z_plot = pg.PlotCurveItem()
        self.x_lin_reg = pg.LinearRegionItem([0.345, 0.365])
        self.x_lin_reg.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 255, 50)))
        self.z_lin_reg = pg.LinearRegionItem([0.295, 0.315])
        self.z_lin_reg.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 50)))
        self.addItem(self.x_lin_reg)
        self.addItem(self.z_lin_reg)
        self.addItem(self.x_plot)
        self.addItem(self.z_plot)

        self.x_bound = [0.345, 0.365]
        self.z_bound = [0.2, 0.4]

        self.x_lin_reg.sigRegionChangeFinished.connect(self.x_bound_update)
        self.z_lin_reg.sigRegionChangeFinished.connect(self.z_bound_update)

    def fft_proc(self, data):
        h_len = len(data) // 2
        window = sp.nuttall(h_len)
        x_fft = np.fft.rfft((data[:h_len] - np.mean(data[:h_len])) * window, len(data[:h_len]), norm='ortho')
        z_fft = np.fft.rfft((data[h_len: len(data)] - np.mean(data[h_len: len(data)])) * window, len(data[h_len: len(data)]), norm='ortho')
        freq = np.fft.rfftfreq(h_len, 1)
        self.x_plot.setData(freq, np.abs(x_fft), pen=pg.mkPen('b', width=1))
        self.z_plot.setData(freq, np.abs(z_fft), pen=pg.mkPen('r', width=1))

        # searching of working DR point
        x_arr = freq[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))]
        z_arr = freq[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))]
        x_index = np.argmax(np.abs(x_fft)[np.where((freq < self.x_bound[1]) & (freq > self.x_bound[0]))])
        z_index = np.argmax(np.abs(z_fft)[np.where((freq < self.z_bound[1]) & (freq > self.z_bound[0]))])
        self.stat_bar.showMessage("nu_x | nu_z =" + str(x_arr[x_index]) + "|" + str(z_arr[z_index]))
        # print("working point = ", [x_arr[x_index], z_arr[z_index]])
        # print(max(np.abs(x_fft)))

    def x_bound_update(self, region_item):
        self.x_bound = region_item.getRegion()

    def z_bound_update(self, region_item):
        self.z_bound = region_item.getRegion()


if __name__ == "__main__":
    app = QApplication(['fft_plot'])
    w = FFTPlot(None)
    sys.exit(app.exec_())
