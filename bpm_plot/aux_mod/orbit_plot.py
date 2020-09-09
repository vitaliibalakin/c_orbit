#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QGraphicsTextItem
from PyQt5 import QtCore
import sys
import pandas as pd
import numpy as np
import pyqtgraph as pg
from bpm_plot.aux_mod.bpm_point import BPMMarker
from bpm_plot.aux_mod.aper_plot import AperPlot
from bpm_plot.aux_mod.wrapper_tunes import PyQtElemPlot, LinesPlot, TextLabel


class OrbitPlot(pg.PlotWidget):
    def __init__(self, o_type, file_name, bpms, bpm_coor, parent):
        super(OrbitPlot, self).__init__(parent=parent)
        self.bpms = bpms
        self.showGrid(x=True, y=True)
        self.setLabel('left', o_type.upper() + " coordinate", units='mm')
        self.setLabel('bottom', "Position", units='m')
        self.setRange(yRange=[-50, 40])

        self.pos = {'cur': [], 'eq': [], 'dis': []}
        self.anchor = {'x': -43, 'z': -50}
        aper = np.transpose(np.loadtxt(file_name))
        self.addItem(AperPlot(aper))

        structure = pd.read_csv('mag_pd.txt')
        self.add_structure(structure, o_type)

        for coor in bpm_coor:
            bpm_e = BPMMarker(x=coor, color=QtCore.Qt.blue)
            bpm_c = BPMMarker(x=coor, color=QtCore.Qt.green)
            bpm_d = BPMMarker(x=coor, color=QtCore.Qt.red)
            self.addItem(bpm_e)
            self.addItem(bpm_c)
            self.addItem(bpm_d)
            self.pos['eq'].append(bpm_e)
            self.pos['cur'].append(bpm_c)
            self.pos['dis'].append(bpm_d)
        for bpm in self.pos['dis']:
            bpm.update_pos(100.0)
        self.update_orbit = {'eq': self.update_orbit_eq, 'cur': self.update_orbit_cur}

    def update_orbit_eq(self, orbit, bpm_list, std=np.zeros(16)):
        for i in range(len(self.bpms)):
            self.pos['eq'][i].update_pos(orbit[i])

    def update_orbit_cur(self, orbit, bpm_list, std=np.zeros(16)):
        for i in range(len(self.bpms)):
            if self.bpms[i] in bpm_list:
                # print(orbit)
                self.pos['cur'][i].update_pos(orbit[i])
                self.pos['dis'][i].update_pos(100.0)
            else:
                self.pos['cur'][i].update_pos(100.0)
                self.pos['dis'][i].update_pos(0.0)
        # for i in range(len(self.pos[which_orbit])):
        #     self.pos[which_orbit][i].update_pos(orbit[i])

    def add_structure(self, structure, o_type):
        anchor = self.anchor[o_type]
        self.addItem(LinesPlot([[structure.head(1)['s'].values[0], anchor], [structure.tail(1)['s'].values[0], anchor]],
                               color=QtCore.Qt.blue, l_type='s'))
        e2draw = ['QUAD', 'KSBEND', 'RFCA']
        line_counter = 0
        e_beg = -1
        for e_type in structure['ElementType']:
            if e_beg == -1:
                if e_type in e2draw:
                    e_beg = structure['s'][line_counter]
            elif e_type not in e2draw:
                e_end = structure['s'][line_counter - 1]
                if structure['ElementType'][line_counter - 1] == 'QUAD':
                    if structure['ElementName'][line_counter - 1][2] == 'F':
                        c_type = 'QUAD_F'
                    else:
                        c_type = 'QUAD_D'
                    self.addItem(PyQtElemPlot(e_beg, e_end, c_type=c_type, anchor=anchor))
                elif structure['ElementType'][line_counter - 1] == 'KSBEND':
                    c_type = 'KSBEND'
                    self.addItem(TextLabel(text=structure['ElementName'][line_counter - 1], anchor=anchor - 3, pos=(e_end + e_beg) / 2))
                    self.addItem(PyQtElemPlot(e_beg, e_end, c_type=c_type, anchor=anchor))
                elif structure['ElementType'][line_counter - 1] == 'RFCA':
                    c_type = 'RFCA'
                    self.addItem(TextLabel(text='CAV', anchor=anchor-3, pos=(e_end + e_beg) / 2))
                    self.addItem(PyQtElemPlot(e_beg, e_end, c_type=c_type, anchor=anchor))
                e_beg = -1
            line_counter += 1
