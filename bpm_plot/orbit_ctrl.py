#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import sys
import os
import json
import pycx4.qcda as cda
import numpy as np
import pyqtgraph as pg
from bpm_plot.aux_mod.orbit_plot import OrbitPlot
from bpm_plot.aux_mod.file_data_exchange import FileDataExchange
from bpm_plot.aux_mod.cx_data_exchange import CXDataExchange


class PlotControl(QMainWindow):
    def __init__(self):
        super(PlotControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/bpm's.ui", self)
        self.setWindowTitle('Orbit Plot')
        self.show()

        # variables for under control objects init
        self.mode = ''
        self.cur_orbit = np.zeros(32)
        self.dir = os.getcwd()
        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpm_coor = [0, 1.908, 3.144, 5.073, 6.7938, 8.7388, 9.9648, 11.8928, 13.7078, 15.6298, 16.8568, 18.8018,
                         20.5216, 22.4566, 23.7111, 25.6156]
        self.cur_bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                         'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpm_btns = [self.btn_bpm01, self.btn_bpm02, self.btn_bpm03, self.btn_bpm04, self.btn_bpm05, self.btn_bpm07,
                         self.btn_bpm08, self.btn_bpm09, self.btn_bpm10, self.btn_bpm11, self.btn_bpm12, self.btn_bpm13,
                         self.btn_bpm14, self.btn_bpm15, self.btn_bpm16, self.btn_bpm17]
        self.bpm_lbls = [self.lbl_bpm01, self.lbl_bpm02, self.lbl_bpm03, self.lbl_bpm04, self.lbl_bpm05, self.lbl_bpm07,
                         self.lbl_bpm08, self.lbl_bpm09, self.lbl_bpm10, self.lbl_bpm11, self.lbl_bpm12, self.lbl_bpm13,
                         self.lbl_bpm14, self.lbl_bpm15, self.lbl_bpm16, self.lbl_bpm17]
        self.worked_bpms = {bpm: 1 for bpm in self.bpms}
        self.dict_lbls = {self.bpms[i]: self.bpm_lbls[i] for i in range(len(self.bpms))}
        # under control objects init
        self.orbit_plots = {'x_orbit': OrbitPlot('x', 'aper_files/x_aper.txt', self.bpms, self.bpm_coor, parent=self),
                            'z_orbit': OrbitPlot('z', 'aper_files/z_aper.txt', self.bpms, self.bpm_coor, parent=self)}
        self.file_exchange = FileDataExchange(self.dir, self.data_receiver)
        self.cx_exchange = CXDataExchange(self.data_receiver)

        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        for o_type, plot in self.orbit_plots.items():
            p.addWidget(plot)

        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}

        # self.btn_bot_on.clicked.connect(self.bot_ctrl)
        # self.btn_bot_off.clicked.connect(self.bot_ctrl)

        # action btn ctrl
        self.btn_close.clicked.connect(self.close)
        self.btn_save.clicked.connect(self.save_file_)
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file_)
        for btn in self.bpm_btns:
            btn.clicked.connect(self.active_bpm)

        # other ordinary channels
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024)
        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)

        # other ctrl callbacks
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        # self.chan_cmd.valueMeasured.connect(self.cmd)

    def active_bpm(self):
        bpm = self.sender().text()
        if self.worked_bpms[bpm]:
            self.worked_bpms[bpm] = 0
            self.sender().setStyleSheet("background-color:rgb(255, 0, 0);")
            self.dict_lbls[bpm].setStyleSheet("background-color:rgb(255, 0, 0);")
            if bpm in self.cur_bpms:
                self.cur_bpms.remove(bpm)
        else:
            self.worked_bpms[bpm] = 1
            self.sender().setStyleSheet("background-color:rgb(0, 255, 0);")
            self.dict_lbls[bpm].setStyleSheet("background-color:rgb(0, 255, 0);")
            if bpm not in self.cur_bpms:
                self.cur_bpms.append(bpm)
        self.chan_cmd.setValue(json.dumps({'cur_bpms': self.cur_bpms}))
        self.orbit_plots['x_orbit'].update_orbit['cur'](self.cur_orbit[:16], self.cur_bpms)  #  , std=std[32:48])
        self.orbit_plots['z_orbit'].update_orbit['cur'](self.cur_orbit[16:32], self.cur_bpms)  #  , std=std[48:])

    def data_receiver(self, orbit, std=np.zeros(32), which='cur'):
        self.orbit_plots['x_orbit'].update_orbit[which](orbit[:16], self.cur_bpms, std=std[32:48])
        self.orbit_plots['z_orbit'].update_orbit[which](orbit[16:32], self.cur_bpms, std=std[48:])
        if which == 'cur':
            self.cur_orbit = orbit
            self.orbit_to_lbl(orbit[:32])

    def orbit_to_lbl(self, orbit):
        for i in range(0, 16):
            bpm = self.bpms[i]
            if self.worked_bpms[bpm]:
                self.dict_lbls[bpm].setText(str(round(orbit[i], 2)) + " | " + str(round(orbit[i + 16], 2)))
            else:
                self.dict_lbls[bpm].setText('None')

    def mode_changed(self, chan):
        self.mode = chan.val

        self.file_exchange.change_orbit_from_file(self.mode)

        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.mode].setStyleSheet("background-color:rgb(0, 255, 0);")

    def cmd(self, chan):
        pass

    def load_file_(self):
        self.file_exchange.load_file(self, self.mode)

    def save_file_(self):
        self.file_exchange.save_file(self, self.cur_orbit, self.mode)


if __name__ == "__main__":
    app = QApplication(['orbit_ctrl'])
    w = PlotControl()
    sys.exit(app.exec_())
