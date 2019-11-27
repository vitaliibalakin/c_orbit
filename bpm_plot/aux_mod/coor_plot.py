#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
import scipy.signal as sp
import pyqtgraph as pg


class CoorPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(CoorPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        # self.setLogMode(False, True)
        self.setLabel('left', "coor", units='mm')
        self.setLabel('bottom', "Turn")
        self.setRange(xRange=[0, 1000])

    def coor_proc(self, data):
        h_len = int(len(data) / 2)
        x = data[:h_len]
        z = data[h_len: len(data)]
        self.clear()
        self.plot(x, pen=pg.mkPen('b', width=1))
        self.plot(z, pen=pg.mkPen('r', width=1))


if __name__ == "__main__":
    app = QApplication(['coor_plot'])
    w = CoorPlot(None)
    sys.exit(app.exec_())
