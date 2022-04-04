#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic
import sys
import json
import re
import os
import pycx4.qcda as cda
import numpy as np
import pyqtgraph as pg
from bpm_base.aux_mod.orbit_plot import OrbitPlot
from c_orbit.config.orbit_config_parser import load_config_orbit


class PlotControl(QMainWindow):
    def __init__(self):
        super(PlotControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        path = os.getcwd()
        conf = re.sub('bpm_plot', 'config', path)
        direc = re.sub('bpm_plot', 'uis', path)
        uic.loadUi(direc + "/bpm's.ui", self)
        self.setWindowTitle('Orbit Plot')
        self.show()

        soft_conf = load_config_orbit(conf + '/orbitd_conf.txt', path)
        chans_conf = soft_conf['chans_conf']
        self.bpms = soft_conf['bpm_conf']
        self.bpm_coor = soft_conf['bpm_coor']

        for chan in ['act_bpm', 'cmd', 'res', 'orbit', 'control_orbit', 'modet']:
            if chan not in chans_conf:
                print(chan + ' is absent in orbitd_conf')
                sys.exit(app.exec_())

        self.orbit_plots: dict = {
            'x_orbit': OrbitPlot('x', conf + '/x_aper.txt', self.bpms, self.bpm_coor, parent=self),
            'z_orbit': OrbitPlot('z', conf + '/z_aper.txt', self.bpms, self.bpm_coor, parent=self)}

        # variables for under control objects init
        self.ic_mode: str
        self.cur_orbit: nparray = np.zeros(2 * len(self.bpms))
        self.cur_bpms: list = self.bpms.copy()

        # migrate to special bpm tuning window
        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        for o_type, plot in self.orbit_plots.items():
            p.addWidget(plot)

        self.btn_dict: dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                               'p2v2': self.btn_sel_p2v2}
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file_)

        self.colors: dict = {'e2v4': 'background-color:#55ffff;', 'p2v4': 'background-color:#ff86ff;',
                             'e2v2': 'background-color:#75ff91;', 'p2v2': 'background-color:#ff6b6b;'}
        self.inj_mode_matr: dict = {'p': False, 'e': False}

        # self.btn_bot_on.clicked.connect(self.bot_ctrl)
        # self.btn_bot_off.clicked.connect(self.bot_ctrl)

        # action btn ctrl
        self.btn_bckgr_discard.clicked.connect(self.bckrg_discard)
        self.btn_save.clicked.connect(self.save_file_)
        self.btn_bckgr.clicked.connect(self.bckgr)
        self.btn_step_up.clicked.connect(self.step_up)
        self.btn_step_dn.clicked.connect(self.step_down)
        self.btn_load_rrm.clicked.connect(self.load_resp_mat)
        self.btn_reknob.clicked.connect(self.knob_recalc)

        # other ordinary channels
        self.chan_mode = cda.StrChan(**chans_conf['modet'])
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        self.chan_cmd = cda.StrChan(**chans_conf['cmd'])
        self.chan_res = cda.StrChan(**chans_conf['res'])
        self.chan_res.valueMeasured.connect(self.cmd_res)

        # data chans
        self.chan_orbit = cda.VChan(**chans_conf['orbit'])
        self.chan_orbit.valueMeasured.connect(self.new_orbit)
        self.chan_ctrl_orbit = cda.VChan(**chans_conf['control_orbit'])
        self.chan_ctrl_orbit.valueMeasured.connect(self.new_ctrl_orbit)

    def knob_recalc(self):
        self.chan_cmd.setValue(json.dumps({'cmd': 'knob_recalc', 'client': 'orbit'}))

    def load_resp_mat(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_rrms',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue(json.dumps({'cmd': 'load_rresp_mat', 'client': 'orbit', 'file_name': file_name}))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def step_down(self):
        self.chan_cmd.setValue(json.dumps({'cmd': 'step_dn', 'client': 'orbit'}))

    def step_up(self):
        self.chan_cmd.setValue(json.dumps({'cmd': 'step_up', 'client': 'orbit'}))

    def bckgr(self):
        self.btn_bckgr.setEnabled(False)
        self.spb_bckgr.setEnabled(False)
        self.chan_cmd.setValue(json.dumps({'cmd': 'bckgr', 'client': 'orbit', 'count': self.spb_bckgr.value()}))

    def bckrg_discard(self):
        self.chan_cmd.setValue(json.dumps({'cmd': 'bckgr_discard', 'client': 'orbit'}))

    def data_receiver(self, orbit, std=np.zeros(64), which='cur'):
        if len(orbit):
            self.orbit_plots['x_orbit'].update_orbit[which](orbit[:16], self.cur_bpms, std=std[32:48])
            self.orbit_plots['z_orbit'].update_orbit[which](orbit[16:32], self.cur_bpms, std=std[48:])

    def mode_changed(self, chan):
        self.ic_mode = chan.val
        # self.ic_mode = 'p2v2'  # delete after tests
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.ic_mode].setStyleSheet(self.colors[self.ic_mode])


    def load_file_(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_modes',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue((json.dumps({'cmd': 'load_orbit', 'client': 'orbit', 'file_name': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def save_file_(self):
        try:
            sv_file = QFileDialog.getSaveFileName(parent=self, directory=os.getcwd() + '/saved_modes',
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = sv_file[0]
                file_name = re.sub('.txt', '', file_name)
                file_name = file_name + '.txt'
                self.chan_cmd.setValue((json.dumps({'cmd': 'save_orbit', 'client': 'orbit', 'file_name': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def new_orbit(self, chan):
        self.data_receiver(chan.val)

    def new_ctrl_orbit(self, chan):
        self.data_receiver(chan.val, which='eq')

    def cmd_res(self, chan):
        if chan.val:
            client = json.loads(chan.val).get('client')
            action = json.loads(chan.val).get('action')
            time_stamp = json.loads(chan.val).get('time_stamp')
            if client == 'orbit':
                self.status_bar.showMessage(str(time_stamp) + ' ' + str(action))
                if action == 'bckgr_done':
                    self.btn_bckgr.setEnabled(True)
                    self.spb_bckgr.setEnabled(True)
            elif client == 'inj':
                if action == 'load -> loaded':
                    self.btn_inj_m.setStyleSheet(self.colors[self.ic_mode])
                    self.inj_mode_matr[self.ic_mode[0]] = True
                elif action == 'load -> file error':
                    self.dict_btns[bpm_name].setStyleSheet("background-color:rgb(255, 255, 255);")
                    self.inj_mode_matr[self.ic_mode[0]] = False


if __name__ == "__main__":
    app = QApplication(['orbit'])
    w = PlotControl()
    sys.exit(app.exec_())
