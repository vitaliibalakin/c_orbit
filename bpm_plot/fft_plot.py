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
        self.addLegend()

    def fft_plot(self, data, fft_type):
        self.clear()
        freq = np.fft.rfftfreq(2*len(data)-1, 1)
        self.plot(freq, data, pen=pg.mkPen('b', width=2))


if __name__ == "__main__":
    app = QApplication(['fft_plot'])
    w = FFTPlot(None)
    sys.exit(app.exec_())
