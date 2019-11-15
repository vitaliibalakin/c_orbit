#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import sys
import pycx4.qcda as cda
import numpy as np
import json
import pyqtgraph as pg
from bpm_plot.aux_mod.turns_plot import TurnsPlot
from bpm_plot.aux_mod.fft_plot import FFTPlot


class TurnsControl(QMainWindow):
    def __init__(self):
        super(TurnsControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/plot's.ui", self)
        self.setWindowTitle('Orbit Plot')
        self.show()

        # fft and turns
        self.fft = FFTPlot(self)
        self.turns = TurnsPlot(self)

        p0 = QVBoxLayout()
        self.turns_mes_plot.setLayout(p0)
        p0.addWidget(self.turns)

        p1 = QVBoxLayout()
        self.fft_plot.setLayout(p1)
        p1.addWidget(self.fft)

        # other ordinary channels
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024)
        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)

        # other ctrl callbacks
        self.chan_turns.valueMeasured.connect(self.turn_proc)
        self.chan_fft.valueMeasured.connect(self.fft_proc)

        # boxes changes
        self.turns_mes_box.currentTextChanged.connect(self.bpm_num_changed)
        self.fft_box.currentTextChanged.connect(self.bpm_num_changed)

    def bpm_num_changed(self):
        self.chan_cmd.setValue(json.dumps({'turn_bpm': self.turns_mes_box.currentText(),
                                           'fft_bpm': self.fft_box.currentText()}))

    def turn_proc(self, chan):
        self.turns.turns_plot(chan.val)

    def fft_proc(self, chan):
        self.fft.fft_proc(chan.val)


if __name__ == "__main__":
    app = QApplication(['turns_ctrl'])
    w = TurnsControl()
    sys.exit(app.exec_())
