#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic, QtCore

import sys
import os
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda


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
        self.bpms_dict = {}
        self.bpm_x = {}
        self.bpm_z = {}
        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        self.bpm_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                         'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']

        # channels init
        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4)
        for bpm in self.bpm_list:
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
            chan.valueMeasured.connect(self.data_proc)
            self.bpms_dict[bpm] = chan

        # callbacks init
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file)
        self.chan_ic_mode.valueMeasured.connect(self.switch_state)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_close.clicked.connect(self.close)
        self.btn_calibrate.clicked.connect(self.calibrate)

        # self.bpm_chan1.valueChanged.connect(self.plot_)

    def window_forming(self):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.setWindowTitle("Plot")

        # x_plot area
        self.plot_window_x = pg.GraphicsLayoutWidget(parent=self)
        self.plot_x = self.plot_window_x.addPlot(title='X coordinates', enableMenu=False)
        self.plot_x.showGrid(x=True, y=True)
        self.plot_x.setLabel('left', "X coordinate", units='mm')
        self.plot_x.setLabel('bottom', "Position", units='Abs')
        self.plot_x.setRange(yRange=[-30, 30])

        # z_plot area
        self.plot_window_z = pg.GraphicsLayoutWidget(parent=self)
        self.plot_z = self.plot_window_z.addPlot(title='Z coordinates', enableMenu=False)
        self.plot_z.showGrid(x=True, y=True)
        self.plot_z.setLabel('left', "Z coordinate", units='mm')
        self.plot_z.setLabel('bottom', "Position", units='Abs')
        self.plot_z.setRange(yRange=[-15, 15])
        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        p.addWidget(self.plot_window_x)
        p.addWidget(self.plot_window_z)

    def data_proc(self, chan):
        self.bpm_x[chan.name.split('.')[-2]] = np.mean(chan.val[1024:2047])
        self.bpm_z[chan.name.split('.')[-2]] = np.mean(chan.val[2048:3071])
        self.plot_()

    def calibrate(self):
        print('calibrate')

    def plot_(self):
        """
        plot actual beam orbit, if self.mode_auto == 1, doing nothing if == 0
        :return: show actual beam orbit
        """
        x = []
        z = []
        if len(self.bpm_x) == 16:
            for key in sorted(self.bpm_x):
                x.append(self.bpm_x[key])
                z.append(self.bpm_z[key])
            self.plot_x.clear()
            self.plot_z.clear()
            self.plot_x.plot(x, pen=pg.mkPen('r', width=2))
            self.plot_z.plot(z, pen=pg.mkPen('r', width=2))

        # if isinstance(chan.val, np.ndarray):
        #     print('here')
        #     self.plot_x.clear()
        #     self.plot_x.plot(chan.val[1024:3071])

    def save_file(self):
        """
        save beam orbit for corresponding DR (K500) mode
        :return: file with the saved orbit
        """

        save_dir = QFileDialog.getSaveFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')
        if save_dir:
            file_name = save_dir[0] + '.txt'
            save_file = open(file_name, 'w')
            save_file.write('1')
            self.lbl_w_dict[self.chan_ic_mode.val].setText(file_name.split('/')[-1])
            save_file.close()

    def load_file(self):
        """
        allows us to choose file with required beam orbit for current DR (K500) mode
        :return: show required beam orbit
        """

        load_file = QFileDialog.getOpenFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')
        file_name = load_file[0]
        self.lbl_w_dict[self.sender().objectName()].setText(file_name.split('/')[-1])

        # replot data from file

    def switch_state(self):
        """
        switch the beam_type/fire_direction
        :return: corresponding beam orbit
        """
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.chan_ic_mode.val].setStyleSheet("background-color:rgb(0, 255, 0);")


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BPM()
    sys.exit(app.exec_())

