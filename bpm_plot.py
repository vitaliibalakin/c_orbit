#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic, QtCore, QtGui

import sys
import os
import json
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda

from bot_orbit_cor import BotOrbitCor


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

        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpm_coor = [0, 1.908, 3.144, 5.073, 6.7938, 8.7388, 9.9648, 11.8928, 13.7078, 15.6298, 16.8568, 18.8018,
                         20.5216, 22.4566, 23.7111, 25.6156]

        for i in range(len(self.bpm_coor)):
            bpm_e = BPMPoint(x=self.bpm_coor[i], color=QtCore.Qt.blue)
            bpm_c = BPMPoint(x=self.bpm_coor[i], color=QtCore.Qt.darkCyan)
            self.addItem(bpm_e)
            self.addItem(bpm_c)
            self.pos['eq'].append(bpm_e)
            self.pos['cur'].append(bpm_c)
        print(len(self.pos['eq']))

    def update_orbit(self, orbit, bpm_list, which_orbit='cur'):
        for i in range(len(self.bpms)):
            if self.bpms[i] in bpm_list:
                self.pos[which_orbit][i].update_pos(orbit[i])
            else:
                self.pos[which_orbit][i].update_pos(50.0)
        # for i in range(len(self.pos[which_orbit])):
        #     self.pos[which_orbit][i].update_pos(orbit[i])


class Orbit(QMainWindow):
    def __init__(self):
        super(Orbit, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        uic.loadUi("uis/bpm's.ui", self)
        self.show()

        self.bpm_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bot_spv = False
        self.rev_rm = {}
        self.cur_iter = 0
        self.CALIBRATE = False
        self.DIR = os.getcwd() + "/saved_modes"
        self.chan_lines = {}
        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        self.ic_mode_orbit = {'e2v2': None, 'p2v2': None, 'e2v4': None, 'p2v4': None}
        # plot space for orbits
        self.orbits = {'x_orbit': OrbitPlot('x'), 'z_orbit': OrbitPlot('z')}
        self.eq_orbit = {'x_orbit': np.zeros([1, 16]), 'z_orbit': np.zeros([1, 16])}
        self.cur_orbit = {'x_orbit': np.zeros([1, 16]), 'z_orbit': np.zeros([1, 16])}
        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        for o_type, plot in self.orbits.items():
            p.addWidget(plot)
        # plot space for fft
        self.plt_fft = pg.PlotWidget(parent=self)
        self.plt_fft.showGrid(x=True, y=True)
        self.plt_fft.setLogMode(False, True)
        self.plt_fft.addLegend()
        d = QVBoxLayout()
        self.plot_fft.setLayout(d)
        d.addWidget(self.plt_fft)

        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_x_orbit = cda.VChan('cxhw:4.bpm_preproc.x_orbit', max_nelems=16)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        self.chan_x_fft = cda.VChan('cxhw:4.bpm_preproc.x_fft', max_nelems=131072)
        self.chan_z_fft = cda.VChan('cxhw:4.bpm_preproc.z_fft', max_nelems=131072)

        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file)
        self.chan_x_orbit.valueMeasured.connect(self.new_orbit_mes)
        self.chan_z_orbit.valueMeasured.connect(self.new_orbit_mes)
        self.chan_x_fft.valueMeasured.connect(self.fft_plot)
        self.chan_z_fft.valueMeasured.connect(self.fft_plot)
        self.chan_ic_mode.valueMeasured.connect(self.switch_state)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_close.clicked.connect(self.close)
        self.btn_bot_on.clicked.connect(self.bot_ctrl)
        self.btn_bot_off.clicked.connect(self.bot_ctrl)

    def bot_ctrl(self):
        if self.bot_spv:
            self.bot_spv = False
            print('bot supervision is on')
        else:
            # selection of reverse response matrix
            rev_rm_name = QFileDialog.getOpenFileName(parent=self, directory=self.DIR, filter='Text Files (*.txt)')[0]
            f = open(rev_rm_name, 'r')
            self.rev_rm = json.loads(f.readline())
            f.close()
            self.bot_spv = True
            print('bot supervision is off')

    def new_orbit_mes(self, chan):
        d_type = chan.name.split('.')[-1]
        self.orbits[d_type].update_orbit(chan.val, self.bpm_list)
        self.cur_orbit[d_type] = chan.val
        # auto correction
        if self.bot_spv:
            func = np.sum((self.cur_orbit[d_type] - self.eq_orbit[d_type]) ** 2)
            if func > 5:
                BotOrbitCor.make_orbit_cor(self.cur_orbit[d_type] - self.eq_orbit[d_type], self.rev_rm[d_type],
                                           self.rev_rm['cor_names'])

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
        self.orbits['x_orbit'].update_orbit(orbit[0], self.bpm_list, which_orbit='eq')
        self.orbits['z_orbit'].update_orbit(orbit[1], self.bpm_list, which_orbit='eq')
        self.eq_orbit['x_orbit'] = np.array(orbit[0])
        self.eq_orbit['z_orbit'] = np.array(orbit[1])

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

    def fft_plot(self, chan):
        self.plt_fft.clear()
        freq = np.fft.rfftfreq(2*len(chan.val)-1, 1)
        self.plt_fft.plot(freq, chan.val, pen=pg.mkPen('b', width=2))
        # self.plt_fft.plot(freq, chan.val, pen=pg.mkPen('r', width=2), name='x fft')


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = Orbit()
    sys.exit(app.exec_())
