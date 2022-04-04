#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget
from PyQt5 import uic
from PyQt5 import QtCore, QtGui
from cxwidgets import CXIntComboBox

import sys
import os
import re
import json
import pycx4.qcda as cda
from c_orbit.config.bpm_config_parser import load_bpm_cnames
from c_orbit.config.orbit_config_parser import load_config_orbit


class BPMConfig(QWidget):
    def __init__(self):
        super().__init__()
        path = os.getcwd()
        conf = re.sub('bpm_plot', 'config', path)
        direc = re.sub('bpm_plot', 'uis', path)

        self.bpms = {}
        self.cur_bpm = ''
        NUM_PER_ROW = 4
        ROW_RESERVED = 5

        self.setWindowTitle('BPM Configuration')
        self.setFixedSize(750, 780)
        grid = QGridLayout()
        i = 0
        for bpm in ['bpm01','bpm02','bpm03','bpm04','bpm05','bpm07','bpm08','bpm09','bpm10','bpm11','bpm12','bpm13',
                    'bpm14','bpm15','bpm16','bpm17']:
            chans_conf = load_bpm_cnames(conf + '/bpm_conf.txt', bpm)
            bpm_wid = uic.loadUi(direc + "/bpm_conf.ui")
            bpm_wid.bpm_name.setText(bpm.upper())
            bpm_wid.bpm_is_on.set_cname(chans_conf['is_on'])
            bpm_wid.bpm_numpts.set_cname(chans_conf['numpts'])
            bpm_wid.bpm_ptsofs.set_cname(chans_conf['ptsofs'])
            bpm_wid.bpm_delay.set_cname(chans_conf['delay'])
            colors = {0: '#0073ff', 1:'#00ff0d'}
            bpm_wid.bpm_istart = CXIntComboBox(cname=chans_conf['istart'], values={0: 'Injection', 1: 'FreeRun'},
                                                                   colors=colors)
            bpm_wid.cbox_grid.addWidget(bpm_wid.bpm_istart)

            grid.addWidget(bpm_wid, ROW_RESERVED * (i // NUM_PER_ROW), i % NUM_PER_ROW, ROW_RESERVED, 1)
            self.bpms[bpm] = bpm_wid
            i += 1
        self.ctrl_panel = uic.loadUi(direc + "/ctrl_btns.ui")
        grid.addWidget(self.ctrl_panel , ROW_RESERVED * (i // NUM_PER_ROW), i % NUM_PER_ROW, 1, NUM_PER_ROW)
        self.setLayout(grid)

        self.ctrl_panel.turns_bpm.currentTextChanged.connect(self.turn_bpm_changed)
        self.ctrl_panel.btn_inj.clicked.connect(self.inj_all)
        self.ctrl_panel.btn_free.clicked.connect(self.free_all)

        path = os.getcwd()
        soft_conf = load_config_orbit(conf + '/orbitd_conf.txt', path)
        chans_conf = soft_conf['chans_conf']
        conf = re.sub('bpm_plot', 'config', path)
        self.chan_cmd = cda.StrChan(**chans_conf['cmd'])
        self.chan_cmd.valueMeasured.connect(self.cmd)

        self.set_colors(colors)

    def turn_bpm_changed(self):
        if self.cur_bpm != self.ctrl_panel.turns_bpm.currentText():
            self.cur_bpm = self.ctrl_panel.turns_bpm.currentText()
            self.chan_cmd.setValue(json.dumps({'cmd': 'turn_bpm', 'client': 'turns', 'turn_bpm': self.cur_bpm}))

    def inj_all(self):
        for bpm, bpm_wid in self.bpms.items():
            bpm_wid.bpm_istart.setCurrentIndex(0)

    def free_all(self):
        for bpm, bpm_wid in self.bpms.items():
            bpm_wid.bpm_istart.setCurrentIndex(1)

    def set_colors(self, colors):
        for bpm, bpm_wid in self.bpms.items():
            bpm_wid.bpm_istart.setStyleSheet(
                'QComboBox {background: ' + colors[bpm_wid.bpm_istart.currentIndex()] + ";}")

    def cmd(self, chan):
        if chan.val:
            cmd_dict = json.loads(chan.val)
            cmd = cmd_dict.get('cmd', 'no_srv')
            if cmd == 'turn_bpm':
                if cmd_dict['turn_bpm'] != self.cur_bpm:
                    self.ctrl_panel.turns_bpm.setCurrentText(cmd_dict['turn_bpm'])

if __name__ == "__main__":
    app = QApplication(['bpm_cnfg'])
    w = BPMConfig()
    w.show()
    sys.exit(app.exec_())
