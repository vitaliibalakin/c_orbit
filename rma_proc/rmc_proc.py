#!/usr/bin/env python3

from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
import numpy as np
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
        self.ex_kick = np.array([0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        # self.ex_kick = np.ones(32)

        self.rm = np.array([])
        self.rm_info = {}
        # sing values plot def
        self.plt = pg.PlotWidget(parent=self)
        self.plt.showGrid(x=True, y=True)
        self.plt.setLogMode(False, False)
        self.plt.setRange(yRange=[0, 0.1])
        self.plt_vals = pg.PlotDataItem()
        self.sing_reg = pg.LinearRegionItem(values=[0, 0.01], orientation=pg.LinearRegionItem.Horizontal)
        self.plt.addItem(self.sing_reg)
        self.plt.addItem(self.plt_vals)
        p = QVBoxLayout()
        self.sv_plot.setLayout(p)
        p.addWidget(self.plt)
        self.show()

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
            u, sing_vals, vh = np.linalg.svd(self.rm)
            self.plt_vals.setData(sing_vals, pen=None, symbol='o')
            self.status_bar.showMessage('Matrix loaded')
        except Exception as exc:
            self.status_bar.showMessage(str(exc))

    def reverse_rm(self):
        if self.rm.any():
            u, sing_vals, vh = np.linalg.svd(np.transpose(self.rm))
            print(self.rm.shape)
            s_r = np.zeros((vh.shape[0], u.shape[0]))
            # small to zero, needed to 1 /
            for i in range(len(sing_vals)):
                if self.sing_val_range[0] < sing_vals[i] < self.sing_val_range[1]:
                    s_r[i, i] = 1 / sing_vals[i]
                else:
                    sing_vals[i] = 0
            self.rev_rm = np.dot(np.transpose(vh), np.dot(s_r, np.transpose(u)))
            # print(np.dot(np.transpose(self.rm), self.rev_rm))
            self.status_bar.showMessage('Reverse response matrix calculated')
        else:
            self.status_bar.showMessage('Choose response matrix')

    def save_rev_rm(self):
        if self.rev_rm.any():
            np.savetxt('saved_rms/' + self.rev_rm_name.text() + '.txt', np.array(self.rev_rm),
                       header=json.dumps(self.rm_info))
            self.status_bar.showMessage('Reverse response matrix saved')
        else:
            self.status_bar.showMessage('Reverse response matrix is empty')

    def save_handle(self):
        kick = np.dot(self.rev_rm, self.ex_kick)
        print(kick)
        cor_list = []
        i = 0
        for key, val in self.rm_info.items():
            cor_list.append({'name': key, 'step': round(kick[i], 0)})
            i += 1
        handle = {'name': self.handle_name.text(), 'descr': self.handle_descr.text(), 'cor_list': cor_list}
        f = open('saved_handles/' + self.handle_name.text() + '.txt', 'w')
        f.write(json.dumps(handle))
        f.close()


if __name__ == "__main__":
    app = QApplication(['RMC_PROC'])
    w = RMC()
    sys.exit(app.exec_())
