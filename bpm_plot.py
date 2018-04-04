#!/usr/bin/python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic

import sys
import pyqtgraph as pg
import pycx4.qcda as cda

class BPM(QMainWindow):
    def __init__(self):
        super(BPM, self).__init__()
        uic.loadUi("bpm's.ui", self)
        self.show()

        self.setWindowTitle("Plot")
        self.plot_window_x = pg.GraphicsLayoutWidget(parent=self)
        self.plot_x = self.plot_window_x.addPlot(title='X coordinates', enableMenu=False)
        self.plot_x.showGrid(x=True, y=True)
        self.plot_x.setLabel('left', "X coordinate", units='mm')
        self.plot_x.setLabel('bottom', "Position", units='Abs')
        self.plot_x.setRange(yRange=[-15, 15])

        self.setWindowTitle("Plot")
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


if __name__ == "__main__":
        app = QApplication(['BPM'])
        w = BPM()
        sys.exit(app.exec_())