#!/usr/bin/env python3
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
from scipy import optimize
import json
import sys
import numpy as np
import os
import re
import pyqtgraph as pg

from bpm_base.aux_mod.wrapper import Converter


class BetaProc(QMainWindow):
    def __init__(self):
        super(BetaProc, self).__init__()
        direc = os.getcwd()
        direc = re.sub('rma_proc', 'uis', direc)
        uic.loadUi(direc + "/beta_window.ui", self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.l_coor = {'1f1': 19.8192, '1f2': 16.3552, '1f4': 18.0872, '2f1': 21.3192, '2f2': 24.7832, '2f4': 23.0512,
                       '3f1': 6.1064, '3f2': 2.6424, '3f4': 4.3744, '4f1': 7.6064, '4f2': 11.0704, '4f4': 9.3384,
                       '1d1': 20.1192, '2d1': 21.0192, '3d1': 6.4064, '4d1': 7.3064, '1f3': 14.410195, '2f3': 26.7222,
                       '3f3': 0.6974, '4f3': 13.015395, '1d2': 15.945205, '2d2': 25.193195, '3d2': 2.2324,
                       '4d2': 11.480395,'1d3': 14.78019, '2d3': 26.352195, '3d3': 1.0674, '4d3': 12.645395}

        self.lens_type = {'1f1': 'du60', '1f2': 'du60', '1f4': 'du60', '2f1': 'du60', '2f2': 'du60', '2f4': 'du60',
                          '3f1': 'du60', '3f2':'du60', '3f4': 'du60', '4f1': 'du60', '4f2': 'du60', '4f4': 'du60',
                          '1d1': 'du60', '2d1': 'du60', '3d1': 'du60', '4d1': 'du60', '1f3': 'du80', '2f3': 'du80',
                          '3f3': 'du80', '4f3': 'du80', '1d2': 'du80', '2d2': 'du80', '3d2': 'du80', '4d2': 'du80',
                          '1d3': 'du80', '2d3': 'du80', '3d3': 'du80', '4d3': 'du80'}

        self.c_main = {'1f1': 'qf1n2', '1f2': 'qf1n2', '1f4': 'qf4',
                       '2f1': 'qf1n2', '2f2': 'qf1n2', '2f4': 'qf4',
                       '3f1': 'qf1n2', '3f2':'qf1n2', '3f4': 'qf4',
                       '4f1': 'qf1n2', '4f2': 'qf1n2', '4f4': 'qf4',
                       '1d1': 'qd1', '2d1': 'qd1', '3d1': 'qd1', '4d1': 'qd1',
                       '1f3': 'qf3', '2f3': 'qf3', '3f3': 'qf3', '4f3': 'qf3',
                       '1d2': 'qd2', '2d2': 'qd2', '3d2': 'qd2', '4d2': 'qd2',
                       '1d3': 'qd3', '2d3': 'qd3', '3d3': 'qd3', '4d3': 'qd3'}

        self.beta_x = np.array([])
        self.beta_y = np.array([])

        self.rm_info = {}

        self.plt_x = pg.PlotWidget(parent=self)
        self.plt_y = pg.PlotWidget(parent=self)
        self.error_x = pg.ErrorBarItem()
        self.plt_x.addItem(self.error_x)
        self.error_y = pg.ErrorBarItem()
        self.plt_y.addItem(self.error_y)
        self.plt_x.setLabel('left', 'beta_x', units='m')
        self.plt_y.setLabel('left', 'beta_y', units='m')
        self.plt_x.setLabel('bottom', 'S', units='m')
        self.plt_y.setLabel('bottom', 'S', units='m')
        self.plt_x.showGrid(x=True, y=True)
        self.plt_y.showGrid(x=True, y=True)
        self.plt_x.setLogMode(False, False)
        self.plt_y.setLogMode(False, False)
        self.plt_x.setRange(yRange=[0, 10])
        self.plt_y.setRange(yRange=[0, 8])
        p = QVBoxLayout()
        self.beta_plot.setLayout(p)
        p.addWidget(self.plt_x)
        p.addWidget(self.plt_y)
        self.show()

        model = Converter().sdds_to_pandas('ElementName', 's', 'betax', 'betay', file='dr_twiss_pos.twi')
        self.plt_x.plot(model.s, model.betax, pen=pg.mkPen('r', width=2))
        self.plt_y.plot(model.s, model.betay, pen=pg.mkPen('b', width=2))

        self.btn_plt_beta.clicked.connect(self.plot_beta)
        self.btn_save_betas.clicked.connect(self.save_betas)

    @staticmethod
    def cur2grad(e_type, cur, main_cur):
        energy = 430e6
        if e_type == 'du60':
            i = - cur / 1000 * 1.5 + main_cur
            grad = 16.83524125 + 2.832126125 * i - 0.0015659738 * i ** 2 + 2.84666125e-6 * i ** 3 - \
                   1.83259875e-9 * i ** 4 + 1.19244899875e-13 * i ** 5
            # to geom factor (eG/pc) and from SGS to SI
            return grad * 300 * 1e4 / energy
        elif e_type == 'du80':
            i = - cur / 1000 * 1.36 + main_cur
            grad = 13.38814 + 1.5170534 * i + 1.1680249e-3 * i ** 2 - 2.84518241e-6 * i ** 3 + 3.0909805e-9 * i ** 4 - \
                   1.2364183e-12 * i ** 5
            # to geom factor (eG/pc) and from SGS to SI
            return grad * 300 * 1e4 / energy

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    def plot_beta(self):
        cors_list = []
        beta_x, beta_y = [], []
        beta_x_err, beta_y_err = [], []
        i = 0
        # try:
        file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_rms',
                                                filter='Text Files (*.txt)')[0]
        f = open(file_name, 'r')
        rm_info = json.loads(f.readline().split('#')[-1])
        keys = list(rm_info.keys())
        f.close()
        rm = np.loadtxt(file_name, skiprows=1)
        stop = rm.shape[0]
        while i != stop:
            cors_list.append(keys[i].split('.')[-1][1:4])
            cur = np.arange(-1 * rm_info[keys[i]]['step'] * rm_info[keys[i]]['n_iter'],
                            rm_info[keys[i]]['step'] * (rm_info[keys[i]]['n_iter'] + 1),
                            rm_info[keys[i]]['step']) + rm_info[keys[i]]['init']
            x = rm[i][:2 * int(rm_info[keys[i]]['n_iter']) + 1]
            y = rm[i][2 * int(rm_info[keys[i]]['n_iter']) + 1:]
            grad = self.cur2grad(self.lens_type[keys[i].split('.')[-1][1:4]], cur,
                                 rm_info['main']['canhw:12.' + self.c_main[keys[i].split('.')[-1][1:4]]])
            const_x, pcov_x = optimize.curve_fit(self.lin_fit, grad, x * 4 * np.pi / 0.18)
            const_y, pcov_y = optimize.curve_fit(self.lin_fit, grad, y * 4 * np.pi / 0.18)
            beta_x.append(const_x[0])
            beta_x_err.append(np.sqrt(np.diag(pcov_x))[0])
            beta_y.append(-const_y[0])
            beta_y_err.append(np.sqrt(np.diag(pcov_y))[0])
            i += 1
        s = [self.l_coor[key] for key in cors_list]
        self.error_x.setData(x=np.array(s), y=np.array(beta_x), top=np.array(beta_x_err), bottom=np.array(beta_x_err), beam=0.3)
        self.plt_x.plot(s, beta_x, pen=None, symbol='x')
        print(s)
        print(beta_x_err)
        self.error_y.setData(x=np.array(s), y=np.array(beta_y), top=np.array(beta_y_err), bottom=np.array(beta_y_err), beam=0.3)
        self.plt_y.plot(s, beta_y, pen=None, symbol='x')
        print(beta_y_err)
        self.beta_x, self.beta_y, self.cors_list = beta_x, beta_y, cors_list
        self.rm_info = rm_info
        self.status_bar.showMessage('Betas plotted')
        # except KeyError as exc:
        #     self.status_bar.showMessage(str(exc))

    def save_betas(self):
        if self.beta_x and self.beta_y:
            np.savetxt('saved_rms/' + self.beta_text.text() + '.txt', np.array([self.beta_x, self.beta_y]),
                       header=json.dumps(self.cors_list))
            self.status_bar.showMessage('Betas saved')
        else:
            self.status_bar.showMessage('Betas is empty')


if __name__ == "__main__":
    app = QApplication(['BetaProc'])
    w = BetaProc()
    sys.exit(app.exec_())
