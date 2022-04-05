#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget
from PyQt5 import uic
from PyQt5 import QtCore, QtGui
import pyqtgraph as pg
import sys
import os
import re
import json
import pycx4.qcda as cda
from bpm_base.aux_mod.single_bpm_view import BPMPlot
from c_orbit.config.bpm_config_parser import load_bpm_cnames
from c_orbit.config.orbit_config_parser import load_config_orbit


class BPMsView(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', '#f7d592')
        pg.setConfigOption('foreground', 'k')
        path = os.getcwd()
        conf = re.sub('bpm_plot', 'config', path)
        direc = re.sub('bpm_plot', 'uis', path)

        soft_conf = load_config_orbit(conf + '/orbitd_conf.txt')
        bpms_list = soft_conf['bpm_conf']
        bpms_aper = soft_conf['bpm_aper']
        self.bpms = {}
        self.cur_bpm = ''
        NUM_PER_ROW = 8

        self.setWindowTitle('BPM View')
        self.setFixedSize(1800, 600)
        grid = QGridLayout()
        i = 0
        for bpm in bpms_list:
            chans_conf = load_bpm_cnames(conf + '/bpm_conf.txt', bpm)
            bpm_wid = uic.loadUi(direc + "/bpm_display.ui")
            bpm_wid.bpm_name.setText(bpm.upper())
            bpm_wid.bpm_is_on.set_cname(chans_conf['is_on'])
            bpm_wid.bpm_x.set_cname(chans_conf['x'])
            bpm_wid.bpm_z.set_cname(chans_conf['z'])
            bpm_wid.bpm_xstd.set_cname(chans_conf['xstd'])
            bpm_wid.bpm_zstd.set_cname(chans_conf['zstd'])
            bpm_wid.bpm_plot = BPMPlot(self, chans_conf['xstd'], chans_conf['zstd'], bpms_aper[bpm][0],
                                                                                     bpms_aper[bpm][1])
            bpm_wid.view_grid.addWidget(bpm_wid.bpm_plot)
            grid.addWidget(bpm_wid, (i // NUM_PER_ROW), i % NUM_PER_ROW, 1, 1)
            self.bpms[bpm] = bpm_wid
            i += 1
        self.setLayout(grid)

if __name__ == "__main__":
    app = QApplication(['bpm_display'])
    w = BPMsView()
    w.show()
    sys.exit(app.exec_())
