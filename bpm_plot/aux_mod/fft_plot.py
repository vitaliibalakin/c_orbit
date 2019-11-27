#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
import scipy.signal as sp
import pyqtgraph as pg
from scipy.fftpack import fft


class FFTPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(FFTPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        # self.setLogMode(False, True)
        self.setLabel('left', "Ampl")
        self.setLabel('bottom', "Freq")
        self.setRange(xRange=[0, 0.5])

    def fft_proc(self, data):
        h_len = len(data) // 2
        # window = sp.nuttall(h_len)
        x_fft = np.fft.rfft(data[:h_len] - np.mean(data[:h_len]), len(data[:h_len]), norm='ortho')
        z_fft = np.fft.rfft(data[h_len: len(data)] - np.mean(data[h_len: len(data)]), len(data[h_len: len(data)]), norm='ortho')
        self.clear()
        freq = np.fft.rfftfreq(h_len, 1)
        self.plot(freq, np.abs(x_fft), pen=pg.mkPen('b', width=1))
        self.plot(freq, np.abs(z_fft), pen=pg.mkPen('r', width=1))
        # print(max(np.abs(x_fft)))


if __name__ == "__main__":
    app = QApplication(['fft_plot'])
    w = FFTPlot(None)
    sys.exit(app.exec_())
