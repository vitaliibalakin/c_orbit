#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import sys
import pyqtgraph as pg
import os
import numpy as np
import pycx4.qcda as cda

from bpm_plot.aux_mod.file_data_exchange import FileDataExchange


class TunesControl(QMainWindow):
    def __init__(self):
        super(TunesControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/wp's.ui", self)
        self.setWindowTitle('Orbit Plot')
        self.show()

        self.mode = ''
        self.cur_tunes = np.zeros(2)
        self.dir = os.getcwd()

        self.file_exchange = FileDataExchange(self.dir, self.data_receiver, '/saved_tunes', '/mode_tunes_file.txt')

        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file_)

        self.colors = {'e2v4': 'background-color:#55ffff;', 'p2v4': 'background-color:#ff86ff;',
                       'e2v2': 'background-color:#75ff91;', 'p2v2': 'background-color:#ff6b6b;'}

        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_mode.valueMeasured.connect(self.mode_changed)

    def mode_changed(self, chan):
        self.mode = chan.val
        print(self.mode)
        self.file_exchange.change_data_from_file(self.mode)

        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.mode].setStyleSheet(self.colors[self.mode])

    def data_receiver(self, tunes, which='cur'):
        if isinstance(tunes, np.ndarray):
            pass
        elif isinstance(tunes, str):
            tunes = np.zeros(2)

        # here update code

        if which == 'cur':
            # print(tunes)
            self.cur_tunes = tunes

    def load_file_(self):
        self.file_exchange.load_file(self, self.mode)

    def save_file_(self):
        self.file_exchange.save_file(self, self.cur_tunes, self.mode)


if __name__ == "__main__":
    app = QApplication(['tunes_ctrl'])
    w = TunesControl()
    sys.exit(app.exec_())
