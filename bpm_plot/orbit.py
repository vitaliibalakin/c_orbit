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

        # variables for under control objects init
        self.ic_mode: str
        self.cur_orbit: nparray = np.zeros(len(self.bpms))
        self.cur_bpms: list = self.bpms.copy()

        # migrate to special bpm tuning window
        self.bpm_btns: list = [self.btn_bpm01, self.btn_bpm02, self.btn_bpm03, self.btn_bpm04, self.btn_bpm05, self.btn_bpm07,
                               self.btn_bpm08, self.btn_bpm09, self.btn_bpm10, self.btn_bpm11, self.btn_bpm12, self.btn_bpm13,
                               self.btn_bpm14, self.btn_bpm15, self.btn_bpm16, self.btn_bpm17]
        self.bpm_lbls:  list = [self.lbl_bpm01, self.lbl_bpm02, self.lbl_bpm03, self.lbl_bpm04, self.lbl_bpm05, self.lbl_bpm07,
                                self.lbl_bpm08, self.lbl_bpm09, self.lbl_bpm10, self.lbl_bpm11, self.lbl_bpm12, self.lbl_bpm13,
                                self.lbl_bpm14, self.lbl_bpm15, self.lbl_bpm16, self.lbl_bpm17]
        self.worked_bpms: dict = {bpm: 1 for bpm in self.bpms}
        self.dict_btns: dict = {self.bpms[i]: self.bpm_btns[i] for i in range(len(self.bpms))}
        self.dict_lbls: dict = {self.bpms[i]: self.bpm_lbls[i] for i in range(len(self.bpms))}
        for btn in self.bpm_btns:
            btn.clicked.connect(self.bpm_btn_clicked)

        # under control objects init
        self.orbit_plots: dict = {'x_orbit': OrbitPlot('x', conf + '/x_aper.txt', self.bpms, self.bpm_coor, parent=self),
                                  'z_orbit': OrbitPlot('z', conf + '/z_aper.txt', self.bpms, self.bpm_coor, parent=self)}

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
        self.btn_inj_m.clicked.connect(self.load_inj_matrix)

        # other ordinary channels
        self.chan_act_bpm = cda.StrChan(**chans_conf['act_bpm'])
        self.chan_act_bpm.valueMeasured.connect(self.act_bpm)
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

    def load_inj_matrix(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/injection_m',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue(json.dumps({'cmd': 'load_inj_matrix', 'client': 'inj', 'file_name': file_name}))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def bckgr(self):
        self.btn_bckgr.setEnabled(False)
        self.spb_bckgr.setEnabled(False)
        self.chan_cmd.setValue(json.dumps({'cmd': 'bckgr', 'client': 'orbit', 'count': self.spb_bckgr.value()}))

    def bckrg_discard(self):
        self.chan_cmd.setValue(json.dumps({'cmd': 'bckgr_discard', 'client': 'orbit'}))

    def bpm_btn_clicked(self):
        bpm = self.sender().text()
        self.active_bpm(bpm)
        self.chan_act_bpm.setValue(json.dumps({'cur_bpms': self.cur_bpms}))
        self.chan_cmd.setValue(json.dumps({'cmd': 'cur_bpms', 'client': 'orbit', 'act_bpm': self.cur_bpms}))

    def active_bpm(self, bpm):
        if self.worked_bpms[bpm]:
            self.worked_bpms[bpm] = 0
            self.dict_btns[bpm].setStyleSheet("background-color:rgb(255, 0, 0);")
            self.dict_lbls[bpm].setStyleSheet("background-color:rgb(255, 0, 0);")
            if bpm in self.cur_bpms:
                self.cur_bpms.remove(bpm)
        else:
            self.worked_bpms[bpm] = 1
            self.dict_btns[bpm].setStyleSheet("background-color:rgb(0, 255, 0);")
            self.dict_lbls[bpm].setStyleSheet("background-color:rgb(0, 255, 0);")
            if bpm not in self.cur_bpms:
                self.cur_bpms.append(bpm)
        self.orbit_plots['x_orbit'].update_orbit['cur'](self.cur_orbit[:16], self.cur_bpms)  #  , std=std[32:48])
        self.orbit_plots['z_orbit'].update_orbit['cur'](self.cur_orbit[16:32], self.cur_bpms)  #  , std=std[48:])

    def data_receiver(self, orbit, std=np.zeros(64), which='cur'):
        if len(orbit):
            self.orbit_plots['x_orbit'].update_orbit[which](orbit[:16], self.cur_bpms, std=std[32:48])
            self.orbit_plots['z_orbit'].update_orbit[which](orbit[16:32], self.cur_bpms, std=std[48:])
            self.orbit_to_lbl(orbit)

    def orbit_to_lbl(self, orbit):
        for i in range(0, 16):
            bpm = self.bpms[i]
            if self.worked_bpms[bpm]:
                self.dict_lbls[bpm].setText(str(round(orbit[i], 2)) + " | " + str(round(orbit[i + 16], 2)))
            else:
                self.dict_lbls[bpm].setText('None')

    def mode_changed(self, chan):
        self.ic_mode = chan.val
        # self.ic_mode = 'p2v2'  # delete after tests
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.ic_mode].setStyleSheet(self.colors[self.ic_mode])
        if self.inj_mode_matr[self.ic_mode[0]]:
            self.btn_inj_m.setStyleSheet(self.colors[self.ic_mode])
        else:
            self.btn_inj_m.setStyleSheet("background-color:rgb(255, 255, 255);")

    def act_bpm(self, chan):
        try:
            act_bpm = json.loads(chan.val)
            new_cur_bpms = act_bpm['cur_bpms']
            cur_bpms = self.cur_bpms
            for bpm in self.bpms:
                if bpm in new_cur_bpms and bpm in cur_bpms:
                    pass
                elif bpm not in new_cur_bpms and bpm not in cur_bpms:
                    pass
                elif bpm in new_cur_bpms and bpm not in cur_bpms:
                    self.active_bpm(bpm)
                elif bpm not in new_cur_bpms and bpm in cur_bpms:
                    self.active_bpm(bpm)
            self.orbit_to_lbl(self.cur_orbit[:32])
        except Exception as exc:
            self.status_bar.showMessage('act_bpm', exc)

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
