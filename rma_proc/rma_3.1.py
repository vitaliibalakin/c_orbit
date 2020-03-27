#!/usr/bin/env python3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
import re
from PyQt5 import uic
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import os
import sys
import numpy as np
from scipy import optimize
import json

from c_orbit.base_modules.basic_module_2_1 import BasicFunc
from base_modules.file_data_exchange_v2 import FileDataExchange
from rma_proc.magnetiz import Magnetization
from rma_proc.cor_proc import CorMeasure
from rma_proc.table import Table


class RMA(QMainWindow, BasicFunc):
    def __init__(self):
        super(RMA, self).__init__()
        uic.loadUi("uis/rma_main_window.ui", self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # sing values plot
        self.plt = pg.PlotWidget(parent=self)
        self.plt.showGrid(x=True, y=True)
        self.plt.setLogMode(False, False)
        self.plt.setRange(yRange=[0, 6])
        self.sing_reg = pg.LinearRegionItem(values=[0.5, 1], orientation=pg.LinearRegionItem.Horizontal)
        self.plt.addItem(self.sing_reg)
        p = QVBoxLayout()
        self.sv_plot.setLayout(p)
        p.addWidget(self.plt)
        self.show()

        self.rma_ready = 0
        self.counter = 0
        self.stop_proc = 0
        self.rm = {}
        self.sing_val_range = []
        self.stack_names = []
        self.stack_elems = {}
        self.cor_fail = []
        self.list_names = []
        self.resp_matr_dict = {}
        self.rev_rm = np.array([])

        self.btn_start_proc.clicked.connect(self.start_rma)
        self.btn_stop_proc.clicked.connect(self.stop_rma)
        self.btn_reverse_rm.clicked.connect(self.reverse_rm)
        self.sing_reg.sigRegionChangeFinished.connect(self.sing_reg_upd)
        self.btn_save_table.clicked.connect(self.save_table)
        self.btn_load_table.clicked.connect(self.load_table)
        self.btn_save_rev_rm.clicked.connect(self.save_rev_rm)

        self.table = Table(self.cor_set_table)
        self.file_table = FileDataExchange(os.getcwd() + '/saved_table', self.data_receiver_t)
        self.file_rev_rm = FileDataExchange(os.getcwd() + '/saved_rev_rm', self.data_receiver_rev_rm)

    ###########################################
    #               MAGNETIZATION             #
    ###########################################

    def start_magn(self):
        self.log_msg.clear()
        self.log_msg.append('start_magn')
        self.label_type.setText('MAGN')
        # cor_names = ['rst2.c1d2_z', 'rst2.c1f2_x', 'rst2.c1f1_x', 'rst2.c1d1_z', 'rst2.c2d2_z', 'rst2.c2f2_x',
        #              'rst2.c2f1_x', 'rst2.c2d1_z', 'rst2.c3d2_z', 'rst2.c3f2_x', 'rst2.c3f1_x', 'rst2.c3d1_z',
        #              'rst2.c4d2_z', 'rst2.c4f2_x', 'rst2.c4f1_x', 'rst2.c4d1_z',
        #              'rst2.crm1', 'rst2.crm2', 'rst2.crm3', 'rst2.crm4', 'rst2.crm5', 'rst2.crm6', 'rst2.crm7',
        #              'rst2.crm8',
        #              'rst3.c3d3_z', 'rst3.c3f3_x', 'rst3.c4d3_z', 'rst3.c4f3_x',
        #              'rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
        #              'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
        #              'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
        #              'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
        #              'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q', 'rst3.Sx2_1F4', 'rst3.Sy2_1F4',
        #              'rst3.Sx1_1F4', 'rst3.Sy1_1F4', 'rst3.Sx2_2F4', 'rst3.Sy2_2F4', 'rst3.Sy1_2F4',
        #              'rst3.Sx1_2F4', 'rst3.Sx2_3F4', 'rst3.Sy2_3F4', 'rst3.Sy1_3F4', 'rst3.Sx1_3F4',
        #              'rst3.Sx2_4F4', 'rst3.Sy2_4F4', 'rst3.Sy1_4F4', 'rst3.Sx1_4F4', 'rst4.cSM1', 'rst4.cSM2',
        #              'rst4.c1f4_z', 'rst4.c1d3_z', 'rst4.c1f3_x', 'rst4.c2f4_z', 'rst4.c2d3_z', 'rst4.c2f3_x',
        #              'rst4.c3f4_z', 'rst4.c4f4_z']
        main_names = ['drm', 'dsm', 'qd1', 'qf1n2', 'qf4', 'qd2', 'qd3', 'qf3']
        main_2_mag = {main: Magnetization(self.action_loop, main, step=self.mag_range_main.value(),
                                          stop=self.mag_iter_main.value(), odz=1.2, prg=self.elem_prg_bar)
                      for main in main_names}
        self.stack_names = main_names.copy()
        cor_2_mag = {}
        for cor in self.table.cors_list:
            self.stack_names.append(cor['name'])
            cor_2_mag[cor['name']] = Magnetization(self.action_loop, cor['name'], step=cor['mag_range'].value(),
                                                   stop=cor['mag_iter'].value(), odz=100, prg=self.elem_prg_bar)
        self.counter = len(self.stack_names)
        self.stack_elems = {**main_2_mag.copy(), **cor_2_mag.copy()}
        print(self.stack_elems)
        # this command will start MAGN Procedure
        self.lbl_elem.setText(self.stack_names[0])
        QTimer.singleShot(9000, self.stack_elems[self.stack_names[0]].proc)

    ###########################################
    #                ASSEMBLING               #
    ###########################################

    def start_rma(self):
        self.rma_ready = 1
        self.log_msg.append('start_rma')
        self.label_type.setText('RMA')
        self.prg_bar.setValue(0)
        # self.cor_names = ['rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
        #                   'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
        #                   'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
        #                   'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
        #                   'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q']

        # deleting from stack FAIL elems
        for cor in self.table.cors_list:
            if not (cor['name'] in self.cor_fail):
                self.stack_names.append(cor['name'])
                self.stack_elems[cor['name']] = CorMeasure(self.action_loop, cor['name'], step=cor['rm_step'].value(),
                                                           n_iter=cor['rm_iter'].value(), prg=self.elem_prg_bar,
                                                           resp_type=self.resp_type.currentText)
        if not len(self.cor_fail):
            self.log_msg.append('Fail List EMPTY')
        else:
            self.log_msg.append(self.cor_fail)
            self.cor_fail = []
        self.counter = len(self.stack_names)
        # this command will start RMA Procedure
        self.lbl_elem.setText(self.stack_names[0])
        QTimer.singleShot(9000, self.stack_elems[self.stack_names[0]].proc)

    def stop_rma(self):
        self.stop_proc = 1

    def action_loop(self, name):
        if not self.stop_proc:
            self.log_msg.append(name + ": " + self.stack_elems[name].status)
            self.stack_names.remove(name)
            self.prg_bar.setValue((1 - len(self.stack_names) / self.counter) * 100)
            if self.stack_elems[name].status == 'fail':
                self.cor_fail.append(name)
            elif not self.stack_elems[name].status:
                self.log_msg.append(name, 'wtf')
                self.cor_fail.append(name)
            elif self.stack_elems[name].status == 'completed':
                if self.rma_ready:
                    # if RMA
                    self.rma_string_calc(name, self.stack_elems[name].response)
            # continue make response
            if len(self.stack_names):
                self.lbl_elem.setText(self.stack_names[0])
                self.stack_elems[self.stack_names[0]].proc()
            else:
                self.stack_elems = {}
                if self.rma_ready:
                    self.rma_ready = 0
                    self.log_msg.append('RMA stage completed, saving RM')
                    self.save_rma()
                else:
                    self.rma_ready = 1
                    self.log_msg.append('MAGN stage completed, go to RMA')
                    self.start_rma()
        else:
            # switch variables to default
            self.log_msg.append('External interruption')
            self.rma_ready = 0
            self.counter = 0
            self.stop_proc = 0
            self.rm = {}
            self.stack_names = []
            self.stack_elems = {}
            self.cor_fail = []
            self.list_names = []
            self.resp_matr_dict = {}

    def rma_string_calc(self, name, data):
        info = self.stack_elems[name]
        buffer = []
        cur = np.arange(-1 * info.step * (info.n_iter-1), info.step * info.n_iter, info.step)
        print(len(data[0][:, 0]), len(cur))
        for i in range(len(data[0][0])):
            const, pcov = optimize.curve_fit(self.lin_fit, cur, data[0][:, i])
            buffer.append(const[0])
        self.resp_matr_dict[name] = buffer

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    def save_cor_resp(self, name, data):
        if len(data) == 2:
            np.savetxt(name + '.txt', data[0], header=(str(data[1]) + '|' + '19'))
            self.resp_matr_dict[name] = data[0]

    def save_rma(self):
        list_names = []
        rm = []
        for name, resp in self.resp_matr_dict.items():
            list_names.append(name)
            rm.append(resp)
        np.savetxt(self.rm_name.text() + '.txt', np.array(rm), header=json.dumps(list_names))
        self.rm = {'rm': np.array(rm), 'cor_names': list_names}
        self.list_names = list_names
        self.log_msg.append('RM saved')
        self.log_msg.append('RMA process finished')
        self.rm_svd()

    ###########################################
    #                REVERSING                #
    ###########################################

    def rm_svd(self):
        self.plt.clear()
        u, sing_vals, vh = np.linalg.svd(self.rm['rm'])
        self.plt.plot(sing_vals, pen=None, symbol='o')
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

    ###########################################
    #              FILE WORKING               #
    ###########################################

    # table
    def data_receiver_t(self):
        pass

    def save_table(self):
        table = self.table.cors_list.copy()
        for table_line in table:
            for key in table_line:
                if not (key == 'name'):
                    table_line[key] = table_line[key].value()
        try:
            sv_file = QFileDialog.getSaveFileName(parent=self, directory=os.getcwd() + '/saved_table',
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = re.sub('.txt', '', sv_file[0]) + '.txt'
                f = open(file_name, 'w')
                f.write(json.dumps(table))
                f.close()
                self.log_msg.append('TABLE saved')
        except Exception as exc:
            self.log_msg.append(str(exc))

    def load_table(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_table',
                                                    filter='Text Files (*.txt)')[0]
            f = open(file_name, 'r')
            table = json.loads(f.readline())
            f.close()
            self.table.free()
            for line in table:
                self.table.add_row(**line)
            self.log_msg.append('TABLE loaded')
        except Exception as exc:
            self.log_msg.append(str(exc))

    # reverse response matrix
    def data_receiver_rev_rm(self):
        pass

    def save_rev_rm(self):
        f = open(self.rm_name.text() + '_reversed_rm.txt', 'w')
        f.write(json.dumps({'rm_rev': np.ndarray.tolist(self.rev_rm), 'cor_names': self.list_names}))
        f.close()
        self.log_msg.append('RM saved')


if __name__ == "__main__":
    app = QApplication(['RMA'])
    w = RMA()
    sys.exit(app.exec_())
