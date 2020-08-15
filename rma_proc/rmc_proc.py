#!/usr/bin/env python3

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5 import uic
import numpy as np
import json
import os
import re
import pyqtgraph as pg


class RMC:
    def __init__(self):
        super(RMC, self).__init__()
        direc = os.getcwd()
        direc = re.sub('rma_proc', 'uis', direc)
        uic.loadUi(direc + "/rma_main_window.ui", self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # sing values plot def
        self.plt = pg.PlotWidget(parent=self)
        self.plt.showGrid(x=True, y=True)
        self.plt.setLogMode(False, False)
        self.plt.setRange(yRange=[0, 6])
        self.plt_vals = pg.PlotDataItem()
        self.sing_reg = pg.LinearRegionItem(values=[0.5, 1], orientation=pg.LinearRegionItem.Horizontal)
        self.plt.addItem(self.sing_reg)
        self.plt.addItem(self.plt_vals)
        p = QVBoxLayout()
        self.sv_plot.setLayout(p)
        p.addWidget(self.plt)
        self.show()

        self.sing_reg.sigRegionChangeFinished.connect(self.sing_reg_upd)

    def rm_svd(self):
        u, sing_vals, vh = np.linalg.svd(self.rm['rm'])
        self.plt_vals.setData(sing_vals, pen=None, symbol='o')
        self.log_msg.append('SV is plotted')

    def sing_reg_upd(self, region_item):
        self.sing_val_range = region_item.getRegion()

    def reverse_rm(self):
        u, sing_vals, vh = np.linalg.svd(self.rm['rm'])
        counter = 0
        # small to zero, needed to 1 /
        for i in range(len(sing_vals)):
            if self.sing_val_range[0] < sing_vals[i] < self.sing_val_range[1]:
                sing_vals[i] = 1 / sing_vals[i]
                counter += 1
            else:
                sing_vals[i] = 0
        s_r = np.zeros((vh.shape[0], u.shape[0]))
        s_r[:counter, :counter] = np.diag(sing_vals)
        self.rev_rm = np.dot(np.transpose(vh), np.dot(s_r, np.transpose(u)))
        self.save_rev_rm()
        self.log_msg.append('RM reversed')

    def save_rev_rm(self):
        f = open(self.rm_name.text() + '_reversed_rm.txt', 'w')
        f.write(json.dumps({'rm_rev': np.ndarray.tolist(self.rev_rm), 'cors': self.dict_cors}))
        f.close()
        self.log_msg.append('RM saved')