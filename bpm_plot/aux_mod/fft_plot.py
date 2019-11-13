#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
import pyqtgraph as pg


class FFTPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(FFTPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        self.setLogMode(False, True)
        self.setLabel('left', "Ampl", units='mm')
        self.setLabel('bottom', "Freq")
        self.setRange(xRange=[0, 0.5])

    def fft_proc(self, data):
        h_len = int(len(data) / 2)
        x_fft = np.sqrt(data[0:h_len].real ** 2 + data[0:h_len].imag ** 2)
        z_fft = np.sqrt(data[h_len: len(data)].real ** 2 + data[h_len: len(data)].imag ** 2)
        self.clear()
        freq = np.fft.rfftfreq(len(data)-1, 1)
        self.plot(freq, x_fft, pen=pg.mkPen('b', width=1))
        self.plot(freq, z_fft, pen=pg.mkPen('r', width=1))


if __name__ == "__main__":
    app = QApplication(['fft_plot'])
    w = FFTPlot(None)
    sys.exit(app.exec_())
