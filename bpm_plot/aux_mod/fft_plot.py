#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import sys
import numpy as np
import json
import pyqtgraph as pg
import pycx4.qcda as cda


class FFTPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(FFTPlot, self).__init__(parent=parent)
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

        self.chan_tunes_range = cda.StrChan('cxhw:4.bpm_preproc.tunes_range')

        self.x_lin_reg.sigRegionChangeFinished.connect(self.x_bound_update)
        self.z_lin_reg.sigRegionChangeFinished.connect(self.z_bound_update)

    def fft_plot(self, data):
        f_len = len(data) // 3
        freq = data[:f_len]
        x_fft = data[f_len:2 * f_len]
        z_fft = data[2 * f_len:3 * f_len]
        self.x_plot.setData(freq, x_fft, pen=pg.mkPen('b', width=1))
        self.z_plot.setData(freq, z_fft, pen=pg.mkPen('r', width=1))

    def x_bound_update(self, region_item):
        self.x_bound = list(region_item.getRegion())
        self.chan_tunes_range.setValue(json.dumps(self.x_bound + self.z_bound))

    def z_bound_update(self, region_item):
        self.z_bound = list(region_item.getRegion())
        self.chan_tunes_range.setValue(json.dumps(self.x_bound + self.z_bound))


if __name__ == "__main__":
    app = QApplication(['fft_plot'])
    w = FFTPlot(None)
    sys.exit(app.exec_())
