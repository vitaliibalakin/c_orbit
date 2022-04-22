#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import uic, Qt
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import os
import re
import sys
import numpy as np
from scipy import optimize
import json

# instruments for main procedure
from bpm_base.device_proc import DeviceFunc
from bpm_base.aux_mod.tree_table import TreeTableCom
from bpm_base.aux_mod.magnetization import MagnetizationProc
from rma_proc.cor_proc import CorMeasure
from rma_proc.rmc_table import Table


class RMA(QMainWindow, DeviceFunc):
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
        self.resp_creating = Table(self.cor_set_table)
        # tree def
        self.tree = TreeTableCom(self.resp_creating, 40, self.tree_widget)

        self.cor_set_table.itemPressed.connect(self.index)

        self.magn = None
        self.set_default()

        self.btn_start_coll.clicked.connect(self.start_rma)
        self.btn_start_magn.clicked.connect(self.start_magn)
        self.btn_stop_proc.clicked.connect(self.stop_rma)
        self.btn_save_table.clicked.connect(self.save_table)
        self.btn_load_table.clicked.connect(self.load_table)
        self.chb_all.stateChanged.connect(self.all_sel)
        self.btn_right.clicked.connect(self.move_right)
        self.btn_left.clicked.connect(self.move_left)

    def set_default(self):
        self.resp_type.setEnabled(True)
        self.move_all = False
        self.prg_bar.setValue(0)
        self.elem_prg_bar.setValue(0)
        self.counter = 0
        self.stop_proc = 0
        self.stack_names = []
        self.cor_fail = []
        self.sing_val_range = []
        self.selected_rows = []
        self.stack_elems = {}
        self.dict_cors = {}
        self.main_cur = {}
        self.resp_matr_dict = {}

    def all_sel(self, chb_state):
        if chb_state == 2:
            self.move_all = True
        elif chb_state == 0:
            self.move_all = False
        else:
            print('chb_state = ', chb_state)

    def index(self, pr_item):
        marked_entry = pr_item.row()
        if marked_entry in self.selected_rows:
            self.selected_rows.remove(marked_entry)
            for i in range(self.cor_set_table.columnCount()):
                self.cor_set_table.item(marked_entry, 0).setBackground(Qt.QColor('white'))
        else:
            self.selected_rows.append(pr_item.row())
            for i in range(self.cor_set_table.columnCount()):
                self.cor_set_table.item(marked_entry, 0).setBackground(Qt.QColor('green'))

    def move_right(self):
        self.resp_creating.common_step(self.selected_rows, self.rm_step_box.value(),
                                       self.st_step_box.value(), self.move_all)

    def move_left(self):
        self.resp_creating.common_step(self.selected_rows, (-1) * self.rm_step_box.value(),
                                       (-1) * self.st_step_box.value(), self.move_all)

    ###########################################
    #               MAGNETIZATION!            #
    ###########################################

    def start_magn(self):
        if self.magn is None:
            self.magn = MagnetizationProc(prg=self.proc_progress, elem_prg=self.elem_progress)
        self.btn_start_coll.setEnabled(False)
        self.btn_start_magn.setEnabled(False)
        self.btn_stop_proc.setEnabled(False)
        self.lbl_elem.setText('MAGN')
        self.log_msg.append('start magnetization')
        self.prg_bar.setValue(0)
        self.magn.start()

    def elem_progress(self, val):
        self.elem_prg_bar.setValue(val)

    def proc_progress(self, val):
        self.prg_bar.setValue(val)
        if val == 146:
            self.cor_fail = self.magn.cor_fail
            self.main_cur = self.magn.main_cur
            self.btn_start_coll.setEnabled(True)
            self.btn_start_magn.setEnabled(True)
            self.btn_stop_proc.setEnabled(True)
            self.prg_bar.setValue(100)
            self.log_msg.append('stop magnetization')

    ###########################################
    #                COLLECTING               #
    ###########################################

    def start_rma(self):
        self.resp_type.setEnabled(False)
        self.btn_start_magn.setEnabled(False)
        self.btn_start_coll.setEnabled(False)
        self.log_msg.append('start_rma')
        self.prg_bar.setValue(0)
        # deleting from stack FAIL elems
        for num, cor in self.resp_creating.cor_dict.items():
            if not (cor['name'] in self.cor_fail):
                self.stack_names.append(cor['name'])
                self.stack_elems[cor['name']] = CorMeasure(self.action_loop, cor['name'], cor['id'],
                                                           step=cor['rm_step'].value(), n_mesh=cor['rm_iter'].value(),
                                                           prg=self.elem_prg_bar, resp_type=self.resp_type.currentText())
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
            self.stack_names.remove(name)
            self.prg_bar.setValue(int((1 - len(self.stack_names) / self.counter) * 100))
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
                self.btn_start_coll.setEnabled(True)
                self.save_rma()
                self.set_default()
        else:
            # switch variables to default
            self.log_msg.append('External interruption')
            self.btn_start_magn.setEnabled(True)
            self.resp_type.setEnabled(True)
            self.btn_start_coll.setEnabled(True)
            self.set_default()

    def rma_string_calc(self, name, data, std_err):
        info = self.stack_elems[name]
        resp_arr = data[0]
        # print(len(resp_arr))
        init_val = data[1]
        buffer = []
        err_buffer = []
        cur = np.arange(-1 * info.step * (info.n_mesh - 1), info.step * info.n_mesh, info.step) + init_val
        if self.resp_type.currentText() == 'coords':
            for i in range(len(resp_arr[0])):
                const, pcov = optimize.curve_fit(self.lin_fit, cur, resp_arr[:, i],
                                                 sigma=std_err[:, i], absolute_sigma=True)
                print('#########################')
                print(name, i)
                print('const', const)
                print('err', std_err[:, i])
                print('resp', resp_arr[:, i])
                print('cur', cur)
                if abs(const[0]) < 1E-7:
                    buffer.append(0.0)
                    err_buffer.append(0.0)
                else:
                    # print(const[0], np.sqrt(np.diag(pcov))[0])
                    buffer.append(const[0])
                    err_buffer.append(np.sqrt(np.diag(pcov))[0])
        elif self.resp_type.currentText() == 'tunes':
            # collect tunes x|z to convert cur -> grad in another application and then plot betas
            buffer = np.ndarray.tolist(np.append(resp_arr[:, 0], resp_arr[:, 1]))
        self.resp_matr_dict[name] = {'data': buffer, 'si_err': err_buffer, 'id': info.id,
                                     'step': info.step, 'n_iter': info.n_mesh - 1, 'init': init_val}

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c

    ###########################################
    #              FILE WORKING               #
    ###########################################

    def save_table(self):
        table = self.resp_creating.cor_dict.copy()
        for num, table_line in table.items():
            for key in table_line:
                if not (key == 'name' or key == 'id'):
                    table_line[key] = table_line[key].value()
        try:
            sv_file = QFileDialog.getSaveFileName(parent=self, directory=os.getcwd() + '/saved_tables',
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
            self.tree.free_dev_set()
            for num, line in table.items():
                self.tree.set_item_selected(line['id'])
                self.resp_creating.add_row(**line)
            self.log_msg.append('TABLE loaded')
        except Exception as exc:
            self.log_msg.append(str(exc))

    def save_rma(self):
        dict_cors = {}
        rm = []
        si_err = []
        responses = {"name": "ic dr response", "responce data": {}}
        for name, resp in self.resp_matr_dict.items():
            dict_cors[name] = {'id': resp['id'], 'step': resp['step'], 'n_iter': resp['n_iter'], 'init': resp['init']}
            rm.append(resp['data'])
            si_err.append(resp['si_err'])

        dict_cors['main'] = self.main_cur
        np.savetxt('saved_rms/' + self.rm_name.text() + '.txt', np.array(rm), header=json.dumps(dict_cors))
        # if self.resp_type.currentText() == 'coords':
        np.savetxt('saved_rms/' + self.rm_name.text() + '_std_err' + '.txt', np.array(si_err))

        bpm_list = ['bpm01_x', 'bpm02_x', 'bpm03_x', 'bpm04_x', 'bpm05_x', 'bpm07_x', 'bpm08_x', 'bpm09_x',
                    'bpm10_x', 'bpm11_x', 'bpm12_x', 'bpm13_x', 'bpm14_x', 'bpm15_x', 'bpm16_x', 'bpm17_x',
                    'bpm01_z', 'bpm02_z', 'bpm03_z', 'bpm04_z', 'bpm05_z', 'bpm07_z', 'bpm08_z', 'bpm09_z',
                    'bpm10_z', 'bpm11_z', 'bpm12_z', 'bpm13_z', 'bpm14_z', 'bpm15_z', 'bpm16_z', 'bpm17_z',]
        for cname, resp in self.resp_matr_dict.items():
            name = cname.split('.')[-1]
            for i in range(len(bpm_list)):
                responses["responce data"][f"{bpm_list[i]} / {name}"] = {"units": "mm/mA",
                                                                         "slope": resp['data'][i],
                                                                         "slope error": resp['si_err'][i]}
        f = open('saved_rms/' + self.rm_name.text() + '.json', "w")
        json.dump(responses, f, indent='\t')
        f.close()
        self.log_msg.append('RM saved')
        self.log_msg.append('RM collecting process has finished')
        self.set_default()


if __name__ == "__main__":
    app = QApplication(['RMC'])
    w = RMA()
    sys.exit(app.exec_())
