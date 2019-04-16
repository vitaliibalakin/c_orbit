#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic, QtCore
from aQt.QtCore import QTimer

import sys
import os
import json
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda
import functools as ftl


class BPM(QMainWindow):
    """
    show DR orbit
    """
    def __init__(self):
        super(BPM, self).__init__()
        uic.loadUi("bpm's.ui", self)
        self.show()
        self.window_forming()

        self.DIR = os.getcwd() + "/saved_modes"
        self.cur_orbit = np.array([])
        self.saved_orbit = np.array([])
        self.chan_bpm_vals = {}
        self.chan_bpm_marker = {}
        self.chan_bpm_numpts = {}
        self.bpm_x = {}
        self.bpm_z = {}
        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        self.icmode_orbit = {'e2v2': None, 'p2v2': None, 'e2v4': None, 'p2v4': None}
        self.bpms = {'bpm01': 21.4842, 'bpm02': 23.3922, 'bpm03': 24.6282, 'bpm04': 26.5572, 'bpm05': 0.8524,
                     'bpm07': 2.7974, 'bpm08': 4.0234, 'bpm09': 5.9514, 'bpm10': 7.7664, 'bpm11': 9.6884,
                     'bpm12': 10.9154, 'bpm13': 12.8604, 'bpm14': 14.5802, 'bpm15': 16.5152, 'bpm16': 17.7697,
                     'bpm17': 19.6742}
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0, 'bpm17': 0}
        self.bpm_numpts_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                                 'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                                 'bpm16': 0, 'bpm17': 0}
        self.bpm_cor = sorted(self.bpms.values())

        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        # bpms numpts
        for bpm, bpm_cor in self.bpms.items():
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.numpts')
            chan.valueMeasured.connect(self.bpm_numpts)
            self.chan_bpm_numpts[bpm] = chan

        # channels init
        for bpm, bpm_cor in self.bpms.items():
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
            chan.valueMeasured.connect(self.data_proc)
            self.chan_bpm_vals[bpm] = chan

        # bpms marker init
        for bpm, bpm_cor in self.bpms.items():
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.marker')
            chan.valueMeasured.connect(self.bpm_marker)
            self.chan_bpm_marker[bpm] = chan

        # callbacks init
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(ftl.partial(self.load_file, key))
        self.chan_ic_mode.valueMeasured.connect(self.switch_state)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_close.clicked.connect(self.close)
        self.btn_calibrate.clicked.connect(self.calibrate)

    def window_forming(self):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.setWindowTitle("IC DR orbit")

        # x_plot area
        self.plot_window_x = pg.GraphicsLayoutWidget(parent=self)
        self.plot_x = self.plot_window_x.addPlot(title='X coordinates', enableMenu=False)
        self.plot_x.showGrid(x=True, y=True)
        self.plot_x.setLabel('left', "X coordinate", units='mm')
        self.plot_x.setLabel('bottom', "Position", units='m')
        self.plot_x.setRange(yRange=[-20, 20])

        # z_plot area
        self.plot_window_z = pg.GraphicsLayoutWidget(parent=self)
        self.plot_z = self.plot_window_z.addPlot(title='Z coordinates', enableMenu=False)
        self.plot_z.showGrid(x=True, y=True)
        self.plot_z.setLabel('left', "Z coordinate", units='mm')
        self.plot_z.setLabel('bottom', "Position", units='m')
        self.plot_z.setRange(yRange=[-24, 24])
        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        p.addWidget(self.plot_window_x)
        p.addWidget(self.plot_window_z)

        self.x_aper = np.transpose(np.loadtxt('x_aper.txt'))
        self.z_aper = np.transpose(np.loadtxt('y_aper.txt'))

    def data_proc(self, chan):
        bpm_num = chan.name.split('.')[-2]
        data_len = int(self.bpm_numpts_renew[bpm_num][0])
        self.bpm_x[bpm_num] = np.mean(chan.val[data_len:2*data_len-1])
        self.bpm_z[bpm_num] = np.mean(chan.val[2*data_len:3*data_len-1])
        if len(self.bpm_x) == 16:
            x = np.array([])
            z = np.array([])
            for key in sorted(self.bpms, key=self.bpms.__getitem__):
                x = np.append(x, self.bpm_x[key])
                z = np.append(z, self.bpm_z[key])
            self.cur_orbit = np.array([x, z])

    def calibrate(self):
        print('calibrate')

    def bpm_numpts(self, chan):
        self.bpm_numpts_renew[chan.name.split('.')[-2]] = chan.val

    def bpm_marker(self, chan):
        self.bpm_val_renew[chan.name.split('.')[-2]] = 1
        # print(self.bpm_val_renew)
        if all(sorted(self.bpm_val_renew.values())):
            for key in self.bpm_val_renew:
                self.bpm_val_renew[key] = 0
            self.plot_()

    def plot_(self):
        """
        :return: show actual beam orbit
        """

        if len(self.bpm_x) == 16:
            self.plot_x.clear()
            self.plot_x.plot(self.bpm_cor, self.saved_orbit[0], pen=None, symbol='o', symbolBrush=(0, 234, 0),
                             symbolPen='g', symbolSize=10)
            self.plot_x.plot(self.bpm_cor, self.cur_orbit[0], pen=None, symbol='star', symbolSize=25)
            self.plot_x.plot(self.x_aper[0], self.x_aper[1]*1000 / 2, pen=pg.mkPen('b', width=2))
            self.plot_x.plot(self.x_aper[0], self.x_aper[1]*(-1000) / 2, pen=pg.mkPen('b', width=2))

            self.plot_z.clear()
            self.plot_z.plot(self.bpm_cor, self.saved_orbit[1], pen=None, symbol='o', symbolBrush=(0, 234, 0),
                             symbolPen='g', symbolSize=10)
            self.plot_z.plot(self.bpm_cor, self.cur_orbit[1], pen=None, symbol='star', symbolSize=25)
            self.plot_z.plot(self.z_aper[0], self.z_aper[1]*1000 / 2, pen=pg.mkPen('b', width=2))
            self.plot_z.plot(self.z_aper[0], self.z_aper[1]*(-1000) / 2, pen=pg.mkPen('b', width=2))

    def save_file(self):
        """
        save beam orbit for corresponding DR (K500) mode
        :return: file with the saved orbit
        """

        sv_file = QFileDialog.getSaveFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')
        if sv_file:
            file_name = sv_file[0] + '.txt'
            np.savetxt(file_name, self.cur_orbit)
            self.renew_icmode_orbit_file(file_name, self.chan_ic_mode.val)

    def load_file(self, mode):
        """
        allows us to choose file with required beam orbit for current DR (K500) mode
        :return: show required beam orbit
        """

        file_name = QFileDialog.getOpenFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')[0]
        self.renew_icmode_orbit_file(file_name, mode)

    def switch_state(self, chan):
        """
        switch the beam_type/fire_direction
        :return: corresponding beam orbit
        """
        f = open('icmode_file.txt', 'r')
        self.icmode_orbit = json.loads(f.read())
        f.close()
        print(self.icmode_orbit)
        if self.icmode_orbit[chan.val]:
            self.saved_orbit = np.loadtxt(self.icmode_orbit[chan.val])
        else:
            self.saved_orbit = np.zeros([16, 16])
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[chan.val].setStyleSheet("background-color:rgb(0, 255, 0);")

    def renew_icmode_orbit_file(self, file_name, mode):
        self.saved_orbit = np.loadtxt(file_name)
        f = open('icmode_file.txt', 'r')
        self.icmode_orbit = json.loads(f.read())
        f.close()
        self.icmode_orbit[mode] = file_name
        f = open('icmode_file.txt', 'w')
        f.write(json.dumps(self.icmode_orbit))
        f.close()


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BPM()
    sys.exit(app.exec_())

