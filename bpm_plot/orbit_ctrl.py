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
from bpm_plot.aux_mod.orbit_plot import OrbitPlot


class PlotControl(QMainWindow):
    def __init__(self):
        super(PlotControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        direc = os.getcwd()
        direc = re.sub('bpm_plot', 'uis', direc)
        uic.loadUi(direc + "/bpm's.ui", self)
        self.setWindowTitle('Orbit Plot')
        self.show()

        # variables for under control objects init
        self.ic_mode = ''
        self.cur_orbit = np.zeros(32)
        self.bpms = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12',
                     'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.cur_bpms = self.bpms.copy()
        self.bpm_coor = [21.4842, 23.39292, 24.6282, 26.5572, 0.8524, 2.7974, 4.0234, 5.9514, 7.7664, 9.6884,
                         10.9154, 12.8604, 14.5802, 16.5152, 17.7697, 19.6742]
        self.bpm_btns = [self.btn_bpm01, self.btn_bpm02, self.btn_bpm03, self.btn_bpm04, self.btn_bpm05, self.btn_bpm07,
                         self.btn_bpm08, self.btn_bpm09, self.btn_bpm10, self.btn_bpm11, self.btn_bpm12, self.btn_bpm13,
                         self.btn_bpm14, self.btn_bpm15, self.btn_bpm16, self.btn_bpm17]
        self.bpm_lbls = [self.lbl_bpm01, self.lbl_bpm02, self.lbl_bpm03, self.lbl_bpm04, self.lbl_bpm05, self.lbl_bpm07,
                         self.lbl_bpm08, self.lbl_bpm09, self.lbl_bpm10, self.lbl_bpm11, self.lbl_bpm12, self.lbl_bpm13,
                         self.lbl_bpm14, self.lbl_bpm15, self.lbl_bpm16, self.lbl_bpm17]
        self.worked_bpms = {bpm: 1 for bpm in self.bpms}
        self.dict_btns = {self.bpms[i]: self.bpm_btns[i] for i in range(len(self.bpms))}
        self.dict_lbls = {self.bpms[i]: self.bpm_lbls[i] for i in range(len(self.bpms))}
        for btn in self.bpm_btns:
            btn.clicked.connect(self.bpm_btn_clicked)

        # under control objects init
        self.orbit_plots = {'x_orbit': OrbitPlot('x', 'aper_files/x_aper.txt', self.bpms, self.bpm_coor, parent=self),
                            'z_orbit': OrbitPlot('z', 'aper_files/z_aper.txt', self.bpms, self.bpm_coor, parent=self)}

        p = QVBoxLayout()
        self.plot_coor.setLayout(p)
        for o_type, plot in self.orbit_plots.items():
            p.addWidget(plot)

        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file_)

        self.colors = {'e2v4': 'background-color:#55ffff;', 'p2v4': 'background-color:#ff86ff;',
                       'e2v2': 'background-color:#75ff91;', 'p2v2': 'background-color:#ff6b6b;'}

        # self.btn_bot_on.clicked.connect(self.bot_ctrl)
        # self.btn_bot_off.clicked.connect(self.bot_ctrl)

        # action btn ctrl
        self.btn_close.clicked.connect(self.close)
        self.btn_save.clicked.connect(self.save_file_)

        # other ordinary channels
        self.chan_act_bpm = cda.StrChan('cxhw:4.bpm_preproc.act_bpm', max_nelems=1024)
        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_act_bpm.valueMeasured.connect(self.act_bpm)
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        self.chan_res.valueMeasured.connect(self.cmd_res)

        # data chans
        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)
        self.chan_ctrl_orbit = cda.VChan('cxhw:4.bpm_preproc.control_orbit', max_nelems=64)
        self.chan_orbit.valueMeasured.connect(self.new_orbit)
        self.chan_ctrl_orbit.valueMeasured.connect(self.new_ctrl_orbit)

    def bpm_btn_clicked(self):
        bpm = self.sender().text()
        self.active_bpm(bpm)
        self.chan_act_bpm.setValue(json.dumps({'cur_bpms': self.cur_bpms}))
        self.chan_cmd.setValue(json.dumps({'cmd': 'cur_bpms', 'service': 'orbit', 'act_bpm': self.cur_bpms}))

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
        self.ic_mode = 'p2v2'  # delete after tests
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        try:
            self.btn_dict[self.ic_mode].setStyleSheet(self.colors[self.ic_mode])
        except Exception as exc:
            print(exc)

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
            print(exc)

    def load_file_(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_modes',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue((json.dumps({'cmd': 'load_orbit', 'service': 'orbit', 'file_name': file_name})))
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
                print(file_name)
                self.chan_cmd.setValue((json.dumps({'cmd': 'save_orbit', 'service': 'orbit', 'file_name': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def new_orbit(self, chan):
        self.data_receiver(chan.val)

    def new_ctrl_orbit(self, chan):
        self.data_receiver(chan.val, which='eq')

    def cmd_res(self, chan):
        try:
            rec = json.loads(chan.val).get('rec', 'no_rec')
            if rec == 'orbit':
                res = json.loads(chan.val).get('res', 'no_res')
                self.status_bar.showMessage(res)
        except Exception as exc:
            print(exc)


if __name__ == "__main__":
    app = QApplication(['orbit_ctrl'])
    w = PlotControl()
    sys.exit(app.exec_())
