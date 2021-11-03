#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import sys
import os
import re
import pycx4.qcda as cda
import json
import pyqtgraph as pg
from bpm_base.aux_mod.cur_plot import CurPlot
from bpm_base.aux_mod.fft_plot import FFTPlot
from bpm_base.aux_mod.coor_plot import CoorPlot
from bpm_base.aux_mod.one_turn import OneTurnPlot
from c_orbit.config.orbit_config_parser import load_config_orbit


class TurnsControl(QMainWindow):
    def __init__(self):
        super(TurnsControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        path = os.getcwd()
        conf = re.sub('bpm_plot', 'config', path)
        direc = re.sub('bpm_plot', 'uis', path)
        uic.loadUi(direc + "/plot's.ui", self)
        self.setWindowTitle('Turns Plot')
        self.show()

        self.ic_mode = 'e'
        self.cur_bpm = 'bpm01'
        self.cur_num_pts = 1024
        self.cur_turn_num = 1

        soft_conf = load_config_orbit(conf + '/orbitd_conf.txt', path)
        chans_conf = soft_conf['chans_conf']
        self.cur_cal = soft_conf['cur_calib']

        for chan in ['turns', 'cmd', 'coor', 'fft', 'modet']:
            if chan not in chans_conf:
                print(chan + ' is absent in orbitd_conf')
                sys.exit(app.exec_())

        # fft and turns
        self.fft_p = FFTPlot(self)
        self.coor_p = CoorPlot(self)
        # self.one_turn_p = OneTurnPlot(self)
        p0 = QVBoxLayout()
        self.fft_plot_p.setLayout(p0)
        p0.addWidget(self.coor_p)
        # p0.addWidget(self.one_turn_p)
        p0.addWidget(self.fft_p)

        self.fft_e = FFTPlot(self)
        self.coor_e = CoorPlot(self)
        # self.one_turn_e = OneTurnPlot(self)
        p1 = QVBoxLayout()
        self.fft_plot_e.setLayout(p1)
        p1.addWidget(self.coor_e)
        # p1.addWidget(self.one_turn_e)
        p1.addWidget(self.fft_e)

        self.turns_p = CurPlot(self)
        p2 = QVBoxLayout()
        self.turns_mes_plot_p.setLayout(p2)
        p2.addWidget(self.turns_p)

        self.turns_e = CurPlot(self)
        p3 = QVBoxLayout()
        self.turns_mes_plot_e.setLayout(p3)
        p3.addWidget(self.turns_e)

        # other ordinary channels & callbacks
        # self.chan_one_turn = cda.VChan('cxhw:4.bpm_preproc.one_turn', max_nelems=32)
        # self.chan_one_turn.valueMeasured.connect(self.one_turn_proc)
        self.chan_turns = cda.VChan(**chans_conf['turns'])
        self.chan_turns.valueMeasured.connect(self.cur_proc)
        self.chan_fft = cda.VChan(**chans_conf['fft'])
        self.chan_fft.valueMeasured.connect(self.fft_proc)
        self.chan_coor = cda.VChan(**chans_conf['coor'])
        self.chan_coor.valueMeasured.connect(self.coor_proc)
        self.chan_mode = cda.StrChan(**chans_conf['modet'])
        self.chan_mode.valueMeasured.connect(self.mode_proc)
        self.chan_cmd = cda.StrChan(**chans_conf['cmd'])
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan(**chans_conf['res'])
        self.chan_res.valueMeasured.connect(self.cmd_res)

        # boxes changes
        self.turns_bpm.currentTextChanged.connect(self.bpm_changed)
        self.bpm_num_pts.valueChanged.connect(self.num_pts_changed)
        self.turn_number.valueChanged.connect(self.turn_number_changed)

        self.chan_cmd.setValue(json.dumps({'client': 'turns', 'cmd': 'status'}))

    #########################################################
    #                     command part                      #
    #########################################################

    def cmd(self, chan):
        if chan.val:
            cmd_dict = json.loads(chan.val)
            cmd = cmd_dict.get('cmd', 'no_srv')
            if cmd == 'turn_bpm':
                if cmd_dict['turn_bpm'] != self.cur_bpm:
                    self.turns_bpm.setCurrentText(cmd_dict['turn_bpm'])
            elif cmd == 'num_pts':
                if cmd_dict['num_pts'] != self.cur_num_pts:
                    self.cur_num_pts = cmd_dict['num_pts']
                    self.bpm_num_pts.setValue(cmd_dict['num_pts'])

    def cmd_res(self, chan):
        if chan.val:
            client = json.loads(chan.val).get('client', 'no_client')
            if client == 'turns':
                self.cur_bpm = json.loads(chan.val).get('turn_bpm')
                self.turns_bpm.setCurrentText(self.cur_bpm)
                self.cur_num_pts = json.loads(chan.val).get('num_pts')
                print(self.cur_num_pts)
                self.bpm_num_pts.setValue(self.cur_num_pts)

    def turn_number_changed(self, turn_num):
        if self.cur_turn_num != turn_num:
            self.cur_turn_num = turn_num
            self.chan_cmd.setValue(json.dumps({'cmd': 'turn_num', 'client': 'turns', 'turn_num': turn_num}))

    def bpm_changed(self):
        if self.cur_bpm != self.turns_bpm.currentText():
            self.cur_bpm = self.turns_bpm.currentText()
            self.chan_cmd.setValue(json.dumps({'cmd': 'turn_bpm', 'client': 'turns', 'turn_bpm': self.cur_bpm}))
            self.chan_cmd.setValue(json.dumps({'cmd': 'num_pts', 'client': 'turns', 'num_pts': self.cur_num_pts}))

    def num_pts_changed(self, bpm_num_pts):
        if self.cur_num_pts != bpm_num_pts:
            self.cur_num_pts = bpm_num_pts
            self.chan_cmd.setValue(json.dumps({'cmd': 'num_pts', 'client': 'turns', 'num_pts': bpm_num_pts}))

    #########################################################
    #                    data proc part                     #
    #########################################################

    def one_turn_proc(self, chan):
        if chan.val.any():
            if self.ic_mode == 'p':
                self.one_turn_p.one_turn_plot(chan.val)
            elif self.ic_mode == 'e':
                self.one_turn_e.one_turn_plot(chan.val)
            else:
                self.status_bar.showMessage('WTF one_turn_proc')

    def cur_proc(self, chan):
        if chan.val.any():
            if self.ic_mode == 'p':
                self.turns_p.turns_plot(chan.val / self.cur_cal[self.turns_bpm.currentText()])
            elif self.ic_mode == 'e':
                self.turns_e.turns_plot(chan.val / self.cur_cal[self.turns_bpm.currentText()])
            else:
                self.status_bar.showMessage('WTF cur_proc')

    def fft_proc(self, chan):
        if chan.val.any():
            if self.ic_mode == 'p':
                self.fft_p.fft_plot(chan.val)
            elif self.ic_mode == 'e':
                self.fft_e.fft_plot(chan.val)
            else:
                self.status_bar.showMessage('WTF fft_proc')

    def coor_proc(self, chan):
        if chan.val.any():
            if self.ic_mode == 'p':
                self.coor_p.coor_plot(chan.val)
            elif self.ic_mode == 'e':
                self.coor_e.coor_plot(chan.val)
            else:
                self.status_bar.showMessage('WTF coor_proc')

    def mode_proc(self, chan):
        if chan.val:
            self.ic_mode = chan.val[0]
            if self.ic_mode == 'p':
                self.tab_fourier.setCurrentIndex(1)
                self.tab_turns.setCurrentIndex(1)
            elif self.ic_mode == 'e':
                self.tab_fourier.setCurrentIndex(0)
                self.tab_turns.setCurrentIndex(0)
            else:
                self.status_bar.showMessage('WTF mode_proc')


if __name__ == "__main__":
    app = QApplication(['turns'])

    w = TurnsControl()
    sys.exit(app.exec_())
