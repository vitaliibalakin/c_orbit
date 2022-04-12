#!/usr/bin/env python3
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5 import uic
import sys
import os
import re
import pycx4.qcda as cda
import json
import pyqtgraph as pg
import datetime
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
        self.is_single_shot = False
        self.make_turns_shot = False
        self.make_fft_shot = False
        self.make_coor_shot = False

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
        p0 = QVBoxLayout()
        self.fft_plot_p.setLayout(p0)
        p0.addWidget(self.coor_p)
        p0.addWidget(self.fft_p)

        self.fft_e = FFTPlot(self)
        self.coor_e = CoorPlot(self)
        p1 = QVBoxLayout()
        self.fft_plot_e.setLayout(p1)
        p1.addWidget(self.coor_e)
        p1.addWidget(self.fft_e)

        self.cur_p = CurPlot(self)
        p2 = QVBoxLayout()
        self.turns_mes_plot_p.setLayout(p2)
        p2.addWidget(self.cur_p)

        self.cur_e = CurPlot(self)
        p3 = QVBoxLayout()
        self.turns_mes_plot_e.setLayout(p3)
        p3.addWidget(self.cur_e)

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
        # self.chan_res = cda.StrChan(**chans_conf['res'])
        # self.chan_res.valueMeasured.connect(self.cmd_res)

        # boxes changes
        self.btn_shot.clicked.connect(self.shot)
        self.chb_single_shot.stateChanged.connect(self.shot_mode)
        self.btn_save.clicked.connect(self.save)

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
                    self.cur_bpm = cmd_dict['turn_bpm']

    #########################################################
    #                    data proc part                     #
    #########################################################

    def cur_proc(self, chan):
        if chan.val.any():
            if (not self.is_single_shot) or self.make_turns_shot:
                self.cur_data = chan.val
                if self.ic_mode == 'p':
                    self.cur_p.turns_plot(chan.val / self.cur_cal[self.cur_bpm])
                elif self.ic_mode == 'e':
                    self.cur_e.turns_plot(chan.val / self.cur_cal[self.cur_bpm])
                else:
                    self.status_bar.showMessage('WTF cur_proc')
                self.make_turns_shot = False

    def fft_proc(self, chan):
        if chan.val.any():
            if (not self.is_single_shot) or self.make_fft_shot:
                self.fft_data = chan.val
                if self.ic_mode == 'p':
                    self.fft_p.fft_plot(chan.val)
                elif self.ic_mode == 'e':
                    self.fft_e.fft_plot(chan.val)
                else:
                    self.status_bar.showMessage('WTF fft_proc')
                self.make_fft_shot = False

    def coor_proc(self, chan):
        if chan.val.any():
            if (not self.is_single_shot) or self.make_coor_shot:
                self.coor_data = chan.val
                if self.ic_mode == 'p':
                    self.coor_p.coor_plot(chan.val)
                elif self.ic_mode == 'e':
                    self.coor_e.coor_plot(chan.val)
                else:
                    self.status_bar.showMessage('WTF coor_proc')
                self.make_coor_shot = False

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

    def shot(self):
        self.make_turns_shot = True
        self.make_fft_shot = True
        self.make_coor_shot = True

    def shot_mode(self, state):
        if state == 2:
            self.is_single_shot = True
        else:
            self.is_single_shot = False

    def save(self):
        if self.is_single_shot:
            time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('saved_turns/' + time_stamp, 'a') as the_file:
                the_file.write(json.dumps({'current': np.ndarray.tolist(self.cur_data),
                                           'fft': np.ndarray.tolist(self.fft_data),
                                           'coordinate': np.ndarray.tolist(self.coor_data)}))


if __name__ == "__main__":
    app = QApplication(['turns'])
    w = TurnsControl()
    sys.exit(app.exec_())
