#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic, QtCore, QtGui

import sys
import os
import json
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda


class BPMPoint(pg.GraphicsObject):
    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.color = kwargs.get('color', QtCore.Qt.darkCyan)
        self.point_obj()

    def point_obj(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        p.setBrush(self.color)
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(self.x, self.y), 0.3, 3)
        p.end()

    def update_pos(self, y_pos):
        self.setPos(0, y_pos)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class AperView(pg.GraphicsObject):
    def __init__(self, aper):
        pg.GraphicsObject.__init__(self)
        self.picture = pg.QtGui.QPicture()
        self.aper_widget(aper)

    def aper_widget(self, aper):
        p = pg.QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('b'))
        for i in range(0, len(aper[0])-1):
            p.drawLine(pg.QtCore.QPointF(aper[0][i], aper[1][i]*1000),
                       pg.QtCore.QPointF(aper[0][i + 1], aper[1][i + 1]*1000))
        for i in range(0, len(aper[0])-1):
            p.drawLine(pg.QtCore.QPointF(aper[0][i], aper[1][i]*(-1000)),
                       pg.QtCore.QPointF(aper[0][i + 1], aper[1][i + 1]*(-1000)))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class OrbitPlot(pg.PlotWidget):
    def __init__(self, o_type):
        super(OrbitPlot, self).__init__()
        self.showGrid(x=True, y=True)
        self.setLabel('left', o_type.upper() + " coordinate", units='mm')
        self.setLabel('bottom', "Position", units='m')
        self.setRange(yRange=[-48, 48])

        self.pos = {'cur': [], 'eq': []}
        aper = np.transpose(np.loadtxt(o_type + '_aper.txt'))
        self.addItem(AperView(aper))

        self.bpms = {'bpm01': 21.4842, 'bpm02': 23.3922, 'bpm03': 24.6282, 'bpm04': 26.5572, 'bpm05': 0.8524,
                     'bpm07': 2.7974, 'bpm08': 4.0234, 'bpm09': 5.9514, 'bpm10': 7.7664, 'bpm11': 9.6884,
                     'bpm12': 10.9154, 'bpm13': 12.8604, 'bpm14': 14.5802, 'bpm15': 16.5152, 'bpm16': 17.7697} #,
                     #'bpm17': 19.6742}
        self.bpm_coor = sorted(self.bpms.values())

        for i in range(len(self.bpm_coor)):
            bpm_e = BPMPoint(x=self.bpm_coor[i], color=QtCore.Qt.blue)
            bpm_c = BPMPoint(x=self.bpm_coor[i], color=QtCore.Qt.darkCyan)
            self.addItem(bpm_e)
            self.addItem(bpm_c)
            self.pos['eq'].append(bpm_e)
            self.pos['cur'].append(bpm_c)

    def update_orbit(self, orbit, which_orbit='cur'):
        for i in range(len(self.pos[which_orbit])):
            self.pos[which_orbit][i].update_pos(orbit[i])


class Orbit(QMainWindow):
    def __init__(self):
        super(Orbit, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("bpm's.ui", self)
        self.show()

        self.cur_iter = 0
        self.CALIBRATE = False
        self.DIR = os.getcwd() + "/saved_modes"
        self.chan_lines = {}
        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        self.ic_mode_orbit = {'e2v2': None, 'p2v2': None, 'e2v4': None, 'p2v4': None}
        self.orbits = {'x_orbit': OrbitPlot('x'), 'z_orbit': OrbitPlot('z')}
        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        for o_type, plot in self.orbits.items():
            p.addWidget(plot)

        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file)
        self.chan_x_orbit.valueMeasured.connect(self.new_orbit_mes)
        self.chan_z_orbit.valueMeasured.connect(self.new_orbit_mes)
        self.chan_ic_mode.valueMeasured.connect(self.switch_state)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_close.clicked.connect(self.close)

    def new_orbit_mes(self, chan):
        self.orbits[chan.name.split('.')[-1]].update_orbit(chan.val)

    def save_file(self):
        sv_file = QFileDialog.getSaveFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')
        if sv_file:
            file_name = sv_file[0] + '.txt'
            np.savetxt(file_name, np.vstack((self.chan_x_orbit.val, self.chan_z_orbit.val)))
            self.renew_ic_mode_orbit_file(file_name, self.chan_ic_mode.val)

    def load_file(self):
        file_name = QFileDialog.getOpenFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')[0]
        self.renew_ic_mode_orbit_file(file_name, self.chan_ic_mode.val)

    def switch_state(self, chan):
        f = open('icmode_file.txt', 'r')
        self.ic_mode_orbit = json.loads(f.read())
        f.close()
        print(self.ic_mode_orbit)
        if self.ic_mode_orbit[chan.val]:
            orbit = np.loadtxt(self.ic_mode_orbit[chan.val])
        else:
            orbit = np.zeros([2, 16])
        print(orbit)
        self.orbits['x_orbit'].update_orbit(orbit[0], which_orbit='eq')
        self.orbits['z_orbit'].update_orbit(orbit[1], which_orbit='eq')

        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[chan.val].setStyleSheet("background-color:rgb(0, 255, 0);")

    def renew_ic_mode_orbit_file(self, file_name, mode):
        f = open('icmode_file.txt', 'r')
        self.ic_mode_orbit = json.loads(f.read())
        f.close()
        self.ic_mode_orbit[mode] = file_name
        f = open('icmode_file.txt', 'w')
        f.write(json.dumps(self.ic_mode_orbit))
        f.close()
        self.switch_state(self.chan_ic_mode)


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = Orbit()
    sys.exit(app.exec_())
