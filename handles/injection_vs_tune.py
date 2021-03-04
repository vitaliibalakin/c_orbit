#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtCore import QTimer
from PyQt5 import uic, Qt
from PyQt5 import QtCore
import pycx4.qcda as cda
import os
import re
import json
import sys


class InjTune(QMainWindow):
    def __init__(self):
        super(InjTune, self).__init__()
        direc = os.getcwd()
        direc = re.sub('handles', 'uis', direc)
        self.p_win = uic.loadUi(direc + "/inj_vs_tune.ui")
        self.setWindowTitle('InjResp')
        self.p_win.show()

        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=True)
        # self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_extracted = cda.DChan('cxhw:0.dcct.extractioncurrent', on_update=True)
        # self.chan_extracted.valueMeasured.connect(self.extracted_event)

        self.p_win.btn_start.clicked.connect(self.start)

        ##########################
        self.marked_row = None
        ##########################
        self.cur_tunes = [0.0, 0.0]
        self.handle_first = False
        self.handle_second = False
        ##########################
        self.n_iter = 10
        self.cur_x_it = 0
        self.cur_y_it = 0
        #########################
        self.shift = None       #  tune shift func

        self.load_handles()
        self.p_win.handles_table.cellPressed.connect(self.index)

    def start(self):
        if self.handle_second and self.handle_first:
            self.shift = make_shift_2h
            # n*x tune shift
            self.i_f3 += self.n_iter * self.shift_x[0]
            self.i_d3 += self.n_iter * self.shift_x[1]
            # n*y tune shift
            self.i_f3 += self.n_iter * self.shift_y[0]
            self.i_d3 += self.n_iter * self.shift_y[1]

            self.chan_f3.setValue(self.i_f3)
            self.chan_d3.setValue(self.i_d3)
            self.cur_x_it = -1 * self.n_iter
            self.cur_y_it = -1 * self.n_iter
            # QTimer.singleShot(6000, self.set_tune_flag_true)
        elif self.handle_second or self.handle_first:
            self.shift = make_shift_1h
            if self.handle_first:
                pass
            else:
                pass
        else:
            self.p_win.status_bar.showMessage('Choose handles')

    def tunes_changed(self, chan):
        if self.tunes_flag:
            self.cur_tunes[0] = chan.val[0]
            self.cur_tunes[1] = chan.val[1]
            self.ring_cur_data[json.dumps(self.cur_tunes)] = []
            self.cur_flag = True
            self.tunes_flag = False

    def make_shift_2h(self):
        print(self.cur_x_it, self.cur_y_it)
        print('--------------------------')
        if self.cur_x_it == self.n_iter:
            if self.cur_y_it == self.n_iter:
                # end & save
                print('FINISH')
                f = open('save_inj_tune_resp.txt', 'w')
                f.write(json.dumps(self.ring_cur_data))
                f.close()
                self.chan_f3.setValue(self.init_f3)
                self.chan_d3.setValue(self.init_d3)
                sys.exit(app.exec_())
                # start params
                self.cur_tunes = [0.0, 0.0]
                self.tunes_flag = False
                self.cur_flag = False
                self.n_iter = 1
                self.cur_x_it = 0
                self.cur_y_it = 0
                self.init_f3_flag = True
                self.init_d3_flag = True
                self.init_f3 = 0
                self.init_d3 = 0
            else:
                # y tune shift
                self.i_f3 -= self.shift_y[0]
                self.i_d3 -= self.shift_y[1]
                self.cur_y_it += 1
                # 2*n*x tune shift
                self.i_f3 += 2 * self.n_iter * self.shift_x[0]
                self.i_d3 += 2 * self.n_iter * self.shift_x[1]

                self.chan_f3.setValue(self.i_f3)
                self.chan_d3.setValue(self.i_d3)
                self.cur_x_it = -1 * self.n_iter
        else:
            # x tune shift
            self.chan_f3.setValue(self.i_f3 - self.shift_x[0])
            self.chan_d3.setValue(self.i_d3 - self.shift_x[1])
            self.cur_x_it += 1

    def make_shift_1h(self):
        pass

    def extracted_event(self, chan):
        if self.counter >= 22:
            self.counter = 0
            self.cur_flag = False
            self.make_shift()
        else:
            if self.cur_flag & self.permission:
                self.permission = False
                self.counter += 1
                self.ring_cur_data[json.dumps(self.cur_tunes)].append(chan.val)

    def index(self, row, column=0):
        # paint row & set handle info
        if self.marked_row is not None:
            if self.marked_row == row:
                for i in range(self.p_win.handles_table.columnCount()):
                    self.p_win.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = None
            else:
                for i in range(self.p_win.handles_table.columnCount()):
                    self.p_win.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = row
                for i in range(self.p_win.handles_table.columnCount()):
                    self.p_win.handles_table.item(row, i).setBackground(Qt.QColor(21, 139, 195))
        else:
            self.marked_row = row
            for i in range(self.p_win.handles_table.columnCount()):
                self.p_win.handles_table.item(row, i).setBackground(Qt.QColor(21, 139, 195))

    def load_handles(self):
        try:
            f = open('saved_handles.txt', 'r')
            handles = json.loads(f.read())
            f.close()
            for row_num, handle in handles.items():
                self.p_win.handles_table.insertRow(0)
                name = QTableWidgetItem(handle['name'])
                name.setFlags(QtCore.Qt.ItemIsEnabled)
                descr = QTableWidgetItem(handle['descr'])
                descr.setFlags(QtCore.Qt.ItemIsEnabled)
                self.p_win.handles_table.setItem(0, 0, name)
                self.p_win.handles_table.setItem(0, 1, descr)
        except ValueError:
            self.status_bar.showMessage('empty saved file')


if __name__ == "__main__":
    app = QApplication(['inj_tune'])
    w = InjTune()
    sys.exit(app.exec_())
