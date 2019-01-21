#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic, QtCore

import sys
import os
import numpy as np
# import pyqtgraph as pg
import pycx4.qcda as cda


class BPM(QMainWindow):
    def __init__(self):
        super(BPM, self).__init__()
        uic.loadUi("bpm's.ui", self)
        self.show()
        self.DIR = os.getcwd() + "/saved_modes"
        self.mode_auto = 0

        self.BPM_dict = {}
        self.lbl_w_dict = {'e2v4': self.lbl_e2v4_w, 'p2v4': self.lbl_p2v4_w, 'e2v2': self.lbl_e2v2_w,
                           'p2v2': self.lbl_p2v2_w,
                           'btn_sel_e2v4': self.lbl_e2v4_w, 'btn_sel_p2v4': self.lbl_p2v4_w,
                           'btn_sel_e2v2': self.lbl_e2v2_w, 'btn_sel_p2v2': self.lbl_p2v2_w}
        self.lbl_dict = {'e2v4': self.lbl_e2v4, 'p2v4': self.lbl_p2v4, 'e2v2': self.lbl_e2v2, 'p2v2': self.lbl_p2v2}

        self.setWindowTitle("Plot")

        # # x_plot area
        # self.plot_window_x = pg.GraphicsLayoutWidget(parent=self)
        # self.plot_x = self.plot_window_x.addPlot(title='X coordinates', enableMenu=False)
        # self.plot_x.showGrid(x=True, y=True)
        # self.plot_x.setLabel('left', "X coordinate", units='mm')
        # self.plot_x.setLabel('bottom', "Position", units='Abs')
        # self.plot_x.setRange(yRange=[-15, 15])
        #
        # # z_plot area
        # self.plot_window_z = pg.GraphicsLayoutWidget(parent=self)
        # self.plot_z = self.plot_window_z.addPlot(title='Z coordinates', enableMenu=False)
        # self.plot_z.showGrid(x=True, y=True)
        # self.plot_z.setLabel('left', "Z coordinate", units='mm')
        # self.plot_z.setLabel('bottom', "Position", units='Abs')
        # self.plot_z.setRange(yRange=[-15, 15])
        # p = QVBoxLayout()
        # self.plot_coor.setLayout(p)
        # p.addWidget(self.plot_window_x)
        # p.addWidget(self.plot_window_z)

        self.chan_list = [cda.DChan(key) for key in self.BPM_dict]
        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4)

        for chan in self.chan_list:
            chan.valueMeasured.connect(self.plot)
        self.chan_ic_mode.valueMeasured.connect(self.switch_state)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_sel_e2v4.clicked.connect(self.load_file)
        self.btn_sel_p2v4.clicked.connect(self.load_file)
        self.btn_sel_e2v2.clicked.connect(self.load_file)
        self.btn_sel_p2v2.clicked.connect(self.load_file)
        self.btn_close.clicked.connect(self.close)
        self.btn_run_auto.clicked.connect(self.run_auto)
        self.btn_stop_auto.clicked.connect(self.stop_auto)
        self.btn_plot_from_file.clicked.connect(self.plot_from_file)

        self.BPM_x = np.ndarray((16,), dtype=np.float64)
        self.BPM_z = np.ndarray((16,), dtype=np.float64)

    def plot(self):
        """
        plot actual beam orbit, if self.mode_auto == 1, doing nothing if == 0
        :return: show actual beam orbit
        """

        pass

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

        for key in self.lbl_dict:
            self.lbl_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.lbl_dict[self.chan_ic_mode.val].setStyleSheet("background-color:rgb(0, 255, 0);")

    def run_auto(self):
        """
        run auto collecting data from BPM's
        :return: give self.mode_auto = 1. Using in self.plot() function
        """

        if self.mode_auto:
            self.statusbar.showMessage('AUTO have already run')
        else:
            self.mode_auto = 1
            self.statusbar.showMessage('AUTO runs')

    def stop_auto(self):
        """
        stop auto collecting data from BPM's
        :return: stop plotting actual beam orbit
        """

        if self.mode_auto:
            self.mode_auto = 0
            self.statusbar.showMessage('AUTO stops')
        else:
            self.statusbar.showMessage('AUTO has already stopped')

    def plot_from_file(self):
        """
        plot beam orbit from file
        :return: show beam orbit from file
        """

        self.statusbar.showMessage('Made data plot from file')
        if self.mode_auto:
            self.mode_auto = 0


if __name__ == "__main__":
        app = QApplication(['BPM'])
        w = BPM()
        sys.exit(app.exec_())
