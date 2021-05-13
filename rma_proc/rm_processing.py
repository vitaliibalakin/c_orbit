#!/usr/bin/env python3

from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
import numpy as np
import pycx4.qcda as cda
import json
import os
import sys
import re
import pyqtgraph as pg


class RMC(QMainWindow):
    def __init__(self):
        super(RMC, self).__init__()
        direc = os.getcwd()
        direc = re.sub('rma_proc', 'uis', direc)

        uic.loadUi(direc + "/sv_window.ui", self)
        self.setWindowTitle('RM calc')
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.sb_kick: list = [
            self.sb_x_1, self.sb_x_2, self.sb_x_3, self.sb_x_4, self.sb_x_5, self.sb_x_6, self.sb_x_7,
            self.sb_x_8, self.sb_x_9, self.sb_x_10, self.sb_x_11, self.sb_x_12, self.sb_x_13,
            self.sb_x_14, self.sb_x_15, self.sb_x_16,
            self.sb_y_1, self.sb_y_2, self.sb_y_3, self.sb_y_4, self.sb_y_5, self.sb_y_6, self.sb_y_7,
            self.sb_y_8, self.sb_y_9, self.sb_y_10, self.sb_y_11, self.sb_y_12, self.sb_y_13,
            self.sb_y_14, self.sb_y_15, self.sb_y_16]
        #                     1, 2, 3, 4, 5, 7, 8, 9, 10,11,12,13,14,15,16,17
        self.kick = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        self.rm = np.array([])
        self.rev_rm = np.array([])
        self.rm_info: dict = {}
        # sing values plot def
        self.plt = pg.PlotWidget(parent=self)
        self.plt.showGrid(x=True, y=True)
        self.plt.setLogMode(False, False)
        self.plt.setRange(yRange=[0, 0.01])
        self.plt_vals = pg.PlotDataItem()
        self.sing_reg = pg.LinearRegionItem(values=[0, 0.01], orientation=pg.LinearRegionItem.Horizontal)
        self.sing_val_range: tuple = (0, 10)
        self.plt.addItem(self.sing_reg)
        self.plt.addItem(self.plt_vals)
        p = QVBoxLayout()
        self.sv_plot.setLayout(p)
        p.addWidget(self.plt)
        self.show()

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)

        self.sing_reg.sigRegionChangeFinished.connect(self.sing_reg_upd)
        self.btn_calc_reverse.clicked.connect(self.reverse_rm)
        self.btn_load_matrix.clicked.connect(self.load_rm)
        self.btn_save_reverse.clicked.connect(self.save_rev_rm)
        self.btn_save_handle.clicked.connect(self.save_handle)

    def sing_reg_upd(self, region_item):
        self.sing_val_range = region_item.getRegion()

    def load_rm(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_rms',
                                                    filter='Text Files (*.txt)')[0]
            f = open(file_name, 'r')
            self.rm_info = json.loads(f.readline().split('#')[-1])
            self.rm_info.pop('main')
            f.close()
            self.rm = np.loadtxt(file_name, skiprows=1)
            u, sing_vals, vh = np.linalg.svd(np.transpose(self.rm))
            self.plt_vals.setData(sing_vals, pen=None, symbol='o')
            self.status_bar.showMessage('Matrix loaded')
        except Exception as exc:
            self.status_bar.showMessage(str(exc))

    def reverse_rm(self):
        if self.rm.any():
            u, sing_vals, vh = np.linalg.svd(np.transpose(self.rm))
            s_r = np.zeros((vh.shape[0], u.shape[0]))
            # small to zero, needed to 1 /
            for i in range(len(sing_vals)):
                print(sing_vals[i])
                if self.sing_val_range[0] < sing_vals[i] < self.sing_val_range[1]:
                    s_r[i, i] = 1 / sing_vals[i]
            self.rev_rm = np.dot(np.transpose(vh), np.dot(s_r, np.transpose(u)))
            print(np.dot(np.transpose(self.rm), self.rev_rm))
            self.status_bar.showMessage('Reverse response matrix calculated')
        else:
            self.status_bar.showMessage('Choose response matrix')

    def save_rev_rm(self):
        if self.rev_rm.any():
            np.savetxt('saved_rms/' + self.rev_rm_name.text() + '.txt', np.array(self.rev_rm),
                       header=json.dumps(self.rm_info))
            self.status_bar.showMessage('Reverse response matrix saved')
        else:
            self.status_bar.showMessage('Calculate reverse matrix first')

    def save_handle(self):
        if self.rev_rm.any():
            curr = np.dot(self.rev_rm, self.assemble_kick())
            print(np.dot(np.transpose(self.rm), curr))
            print('currents', curr)
            cor_list = []
            i = 0
            for key, param in self.rm_info.items():
                cor_list.append({'name': key, 'id': param['id'], 'step': round(curr[i], 0)})
                i += 1
            self.knob_transfer(self, self.handle_name.text(), self.handle_descr.text(), cor_list)
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'add_handle', 'info': info}))
            self.handle_name.setText('def_h_name')
            self.handle_descr.setText('def_h_descr')
            self.status_bar.showMessage('Handle saved')
        else:
            self.status_bar.showMessage('Calculate reverse matrix first')

    def knob_transfer(self, name, descr, cor_list):
        self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'add_handle', 'name': name, 'descr': descr}))
        for cor in cor_list:
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'add_cor', 'cor': cor}))
        self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'handle_complete'}))

    def assemble_kick(self):
        for i in range(len(self.sb_kick)):
            self.kick[i] = self.sb_kick[i].value()
        if self.kick.any():
            return self.kick
        else:
            self.status_bar.showMessage('Enter kick first')


if __name__ == "__main__":
    app = QApplication(['RMC_PROC'])
    w = RMC()
    sys.exit(app.exec_())
