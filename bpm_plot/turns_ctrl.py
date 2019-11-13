#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import sys
import pycx4.qcda as cda
import numpy as np
import pyqtgraph as pg
from bpm_plot.aux_mod.turns_plot import TurnsPlot


class TurnsControl(QMainWindow):
    def __init__(self):
        super(TurnsControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/plot's.ui", self)
        self.show()

        # other ordinary channels
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024)

        # other ctrl callbacks
        self.chan_cmd.valueMeasured.connect(self.cmd)

    def data_receiver(self, orbit, std=np.zeros(32), which='cur'):
        pass

    def cmd(self, chan):
        pass


if __name__ == "__main__":
    app = QApplication(['turns_control'])
    w = TurnsControl()
    sys.exit(app.exec_())
