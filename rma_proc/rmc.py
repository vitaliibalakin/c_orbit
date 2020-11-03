#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
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
from rma_proc.magnetiz import MagnetizationProc
from rma_proc.cor_proc import CorMeasure
from rma_proc.table import Table


class RMA(QMainWindow, BasicFunc):
    def __init__(self):
        super(RMA, self).__init__()
        direc = os.getcwd()
        direc = re.sub('rma_proc', 'uis', direc)
        uic.loadUi(direc + "/rmc_main_window.ui", self)
        self.setWindowTitle('Response Collecting')
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.show()

        # table def
        self.table = Table(self.cor_set_table)
        # tree def
        self.tree = TreeTableCom(self.table, 40, self.tree_widget)

        self.set_default()

        self.btn_start_coll.clicked.connect(self.start_rma)
        self.btn_start_magn.clicked.connect(self.start_magn)
        self.btn_stop_proc.clicked.connect(self.stop_rma)
        self.btn_save_table.clicked.connect(self.save_table)
        self.btn_load_table.clicked.connect(self.load_table)

    def set_default(self):
        self.resp_type.setEnabled(True)
        self.prg_bar.setValue(0)
        self.elem_prg_bar.setValue(0)
        self.counter = 0
        self.stop_proc = 0
        self.stack_names = []
        self.cor_fail = []
        self.sing_val_range = []
        self.stack_elems = {}
        self.dict_cors = {}
        self.main_cur = {}
        self.rm = {}
        self.resp_matr_dict = {}
        self.rev_rm = np.array([])

    ###########################################
    #               MAGNETIZATION!            #
    ###########################################

    def start_magn(self):
        self.magn = MagnetizationProc(prg=self.proc_progress)
        self.btn_start_coll.setEnabled(False)

    def proc_progress(self, val):
        self.elem_prg_bar.setValue(val)
        if val == 100:
            self.cor_fail = self.magn.cor_fail
            self.main_cur = self.magn.main_cur
            self.btn_start_coll.setEnabled(True)

    ###########################################
    #                COLLECTING               #
    ###########################################

    def start_rma(self):
        self.resp_type.setEnabled(False)
        self.btn_start_magn.setEnabled(False)
        self.log_msg.append('start_rma')
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
            self.log_msg.append("fail_list: " + str(self.cor_fail))
            self.cor_fail = []
        self.counter = len(self.stack_names)
        # this command will start RMA Procedure
        self.lbl_elem.setText(self.stack_names[0].split('.')[-1])
        QTimer.singleShot(3000, self.stack_elems[self.stack_names[0]].proc)

    def stop_rma(self):
        self.stop_proc = 1

    def action_loop(self, name):
        if not self.stop_proc:
            self.log_msg.append(name.split('.')[-1] + ": " + self.stack_elems[name].status)
            self.prg_bar.setValue((1 - len(self.stack_names) / self.counter) * 100)
            self.stack_names.remove(name)
            if self.stack_elems[name].status == 'fail':
                self.cor_fail.append(name)
            elif not self.stack_elems[name].status:
                self.log_msg.append(name.split('.')[-1], 'wtf')
                self.cor_fail.append(name)
            elif self.stack_elems[name].status == 'completed':
                self.rma_string_calc(name, self.stack_elems[name].response, self.stack_elems[name].std_err)

            # continue make response
            if len(self.stack_names):
                self.lbl_elem.setText(self.stack_names[0].split('.')[-1])
                self.stack_elems[self.stack_names[0]].proc()
            else:
                self.log_msg.append('RMA stage completed, saving RM')
                self.btn_start_magn.setEnabled(True)
                self.resp_type.setEnabled(True)
                self.save_rma()
                self.set_default()
        else:
            # switch variables to default
            self.log_msg.append('External interruption')
            self.btn_start_magn.setEnabled(True)
            self.resp_type.setEnabled(True)
            self.set_default()

    def rma_string_calc(self, name, data, std_err):
        info = self.stack_elems[name]
        resp_arr = data[0]
        # print(len(resp_arr))
        init_val = data[1]
        buffer = []
        err_buffer = []
        cur = np.arange(-1 * info.step * (info.n_iter-1), info.step * info.n_iter, info.step) + init_val
        if self.resp_type.currentText() == 'coords':
            for i in range(len(resp_arr[0])):
                const, pcov = optimize.curve_fit(self.lin_fit, cur, resp_arr[:, i], sigma=std_err[:, i])
                if const[0] < 1E-7:
                    buffer.append(0)
                    err_buffer.append(0)
                else:
                    print(const[0], np.sqrt(np.diag(pcov))[0])
                    buffer.append(const[0])
                    err_buffer.append(np.sqrt(np.diag(pcov))[0])
        elif self.resp_type.currentText() == 'tunes':
            # collect tunes x|z to convert cur -> grad in another application and then plot betas
            buffer = np.ndarray.tolist(np.append(resp_arr[:, 0], resp_arr[:, 1]))
        self.resp_matr_dict[name] = {'data': buffer, 'si_err': err_buffer,
                                     'step': info.step, 'n_iter': info.n_iter - 1, 'init': init_val}

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    ###########################################
    #              FILE WORKING               #
    ###########################################

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

    def save_rma(self):
        dict_cors = {}
        rm = []
        si_err = []
        for name, resp in self.resp_matr_dict.items():
            dict_cors[name] = {'step': resp['step'], 'n_iter': resp['n_iter'], 'init': resp['init']}
            rm.append(resp['data'])
            si_err.append(resp['si_err'])
        dict_cors['main'] = self.main_cur
        np.savetxt('saved_rms/' + self.rm_name.text() + '.txt', np.array(rm), header=json.dumps(dict_cors))
        if self.resp_type.currentText() == 'coords':
            np.savetxt('saved_rms/' + self.rm_name.text() + '_std_err' + '.txt', np.array(si_err))
        self.rm = {'rm': np.array(rm), 'cor_names': dict_cors}
        self.dict_cors = dict_cors
        self.log_msg.append('RM saved')
        self.log_msg.append('RMA process finished')
        self.set_default()


if __name__ == "__main__":
    app = QApplication(['RMC'])
    w = RMA()
    sys.exit(app.exec_())
