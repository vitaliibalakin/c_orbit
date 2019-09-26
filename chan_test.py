#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import pycx4.qcda as cda
import numpy as np
import pyqtgraph as pg
import sys


class Test:
    def __init__(self):
        super(Test, self).__init__()

        self.chan_data = cda.VChan('cxhw:4.bpm_preproc.x_fft', max_nelems=131072)
        self.chan_data.valueMeasured.connect(self.data_proc)

        self.data_plot = pg.PlotWindow()
        self.data_plot.showGrid(x=True, y=True)

    def data_proc(self, chan):
        print(chan.name)
        self.data_plot.clear()
        self.data_plot.plot(chan.val)


if __name__ == "__main__":
    app = QApplication(['test'])
    w = Test()
    sys.exit(app.exec_())