#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import os
import re
import sys
import numpy as np
from scipy import optimize
import json

# instruments for main procedure
from base_modules.basic_module import BasicFunc
from base_modules.tree_table import TreeTableCom
from rma_proc.magnetiz import Magnetization
from rma_proc.cor_proc import CorMeasure
from rma_proc.table import Table


class RMA(QMainWindow, BasicFunc):
    def __init__(self):
        super(RMA, self).__init__()
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

        # table def
        self.table = Table(self.cor_set_table)
        # tree def
        self.tree = TreeTableCom(self.table, 40, self.tree_widget)

        self.rma_ready = 0
        self.counter = 0
        self.stop_proc = 0
        self.rm = {}
        self.sing_val_range = []
        self.stack_names = []
        self.stack_elems = {}
        self.cor_fail = []
        self.dict_cors = {}
        self.resp_matr_dict = {}
        self.rev_rm = np.array([])

        self.btn_start_coll.clicked.connect(self.start_rma)
        self.btn_start_magn.clicked.connect(self.start_magn)
        self.btn_stop_proc.clicked.connect(self.stop_rma)
        self.btn_reverse_rm.clicked.connect(self.reverse_rm)
        self.sing_reg.sigRegionChangeFinished.connect(self.sing_reg_upd)
        self.btn_save_table.clicked.connect(self.save_table)
        self.btn_load_table.clicked.connect(self.load_table)
        self.btn_save_rev_rm.clicked.connect(self.save_rev_rm)

        self.rm_svd()

    ###########################################
    #               MAGNETIZATION!            #
    ###########################################

    def start_magn(self):
        self.log_msg.clear()
        self.log_msg.append('start_magn')
        # self.label_type.setText('MAGN')
        # main_names = ['drm', 'dsm', 'qd1', 'qf1n2', 'qf4', 'qd2', 'qd3', 'qf3']
        main_names = []
        main_2_mag = {main: Magnetization(self.action_loop, main, step=self.mag_range_main.value(),
                                          stop=self.mag_iter_main.value(), odz=1.2, prg=self.elem_prg_bar)
                      for main in main_names}
        self.stack_names = main_names.copy()
        cor_2_mag = {}
        for cor in self.table.cor_list:
            self.stack_names.append(cor['name'])
            cor_2_mag[cor['name']] = Magnetization(self.action_loop, cor['name'], step=cor['mag_range'].value(),
                                                   stop=cor['mag_iter'].value(), odz=100, prg=self.elem_prg_bar)
        self.counter = len(self.stack_names)
        self.stack_elems = {**main_2_mag.copy(), **cor_2_mag.copy()}
        print(self.stack_elems)
        # this command will start MAGN Procedure
        self.lbl_elem.setText(self.stack_names[0].split('.')[-1])
        QTimer.singleShot(9000, self.stack_elems[self.stack_names[0]].proc)

    ###########################################
    #                ASSEMBLING               #
    ###########################################

    def start_rma(self):
        self.rma_ready = 1
        self.log_msg.append('start_rma')
        # self.label_type.setText('RMA')
        self.prg_bar.setValue(0)
        # deleting from stack FAIL elems
        for cor in self.table.cor_list:
            if not (cor['name'] in self.cor_fail):
                self.stack_names.append(cor['name'])
                self.stack_elems[cor['name']] = CorMeasure(self.action_loop, cor['name'], step=cor['rm_step'].value(),
                                                           n_iter=cor['rm_iter'].value(), prg=self.elem_prg_bar,
                                                           resp_type=self.resp_type.currentText())
        if not len(self.cor_fail):
            self.log_msg.append('Fail List EMPTY')
        else:
            self.log_msg.append(self.cor_fail)
            self.cor_fail = []
        self.counter = len(self.stack_names)
        # this command will start RMA Procedure
        self.lbl_elem.setText(self.stack_names[0].split('.')[-1])
        QTimer.singleShot(9000, self.stack_elems[self.stack_names[0]].proc)

    def stop_rma(self):
        self.stop_proc = 1

    def action_loop(self, name):
        if not self.stop_proc:
            self.log_msg.append(name.split('.')[-1] + ": " + self.stack_elems[name].status)
            self.stack_names.remove(name)
            self.prg_bar.setValue((1 - len(self.stack_names) / self.counter) * 100)
            if self.stack_elems[name].status == 'fail':
                self.cor_fail.append(name)
            elif not self.stack_elems[name].status:
                self.log_msg.append(name.split('.')[-1], 'wtf')
                self.cor_fail.append(name)
            elif self.stack_elems[name].status == 'completed':
                if self.rma_ready:
                    # if RMA
                    self.rma_string_calc(name, self.stack_elems[name].response)
            # continue make response
            if len(self.stack_names):
                self.lbl_elem.setText(self.stack_names[0].split('.')[-1])
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
            self.prg_bar.setValue(0)
            self.elem_prg_bar.setValue(0)
            self.rma_ready = 0
            self.counter = 0
            self.stop_proc = 0
            self.rm = {}
            self.stack_names = []
            self.stack_elems = {}
            self.cor_fail = []
            self.dict_cors = {}
            self.resp_matr_dict = {}

    def rma_string_calc(self, name, data):
        info = self.stack_elems[name]
        print(info.step, info.n_iter)
        buffer = []
        cur = np.arange(-1 * info.step * (info.n_iter-1), info.step * info.n_iter, info.step)
        for i in range(len(data[0][0])):
            const, pcov = optimize.curve_fit(self.lin_fit, cur, data[0][:, i])
            buffer.append(const[0])
        self.resp_matr_dict[name] = {'data': buffer, 'step': info.step, 'n_iter': info.n_iter - 1}
        print(self.resp_matr_dict)

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    # def save_cor_resp(self, name, data):
    #     if len(data) == 2:
    #         np.savetxt(name + '.txt', data[0], header=(str(data[1]) + '|' + '19'))
    #         self.resp_matr_dict[name] = data[0]

    def save_rma(self):
        dict_cors = {}
        rm = []
        for name, resp in self.resp_matr_dict.items():
            dict_cors[name] = {'step': resp['step'], 'n_iter': resp['n_iter']}
            rm.append(resp['data'])
        np.savetxt('saved_rms/' + self.rm_name.text() + '.txt', np.array(rm), header=json.dumps(dict_cors))
        self.rm = {'rm': np.array(rm), 'cor_names': dict_cors}
        self.dict_cors = dict_cors
        self.log_msg.append('RM saved')
        self.log_msg.append('RMA process finished')
        self.rm_svd()

    ###########################################
    #                REVERSING                #
    ###########################################

    def rm_svd(self):
        # self.plt.clear()
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

    ###########################################
    #              FILE WORKING               #
    ###########################################

    # table
    def data_receiver_t(self):
        pass

    def save_table(self):
        table = self.table.cor_list.copy()
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
        f.write(json.dumps({'rm_rev': np.ndarray.tolist(self.rev_rm), 'cors': self.dict_cors}))
        f.close()
        self.log_msg.append('RM saved')


if __name__ == "__main__":
    app = QApplication(['RMA'])
    w = RMA()
    sys.exit(app.exec_())
