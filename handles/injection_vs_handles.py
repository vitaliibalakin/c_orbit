#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtCore import QTimer
from PyQt5 import uic, Qt
from PyQt5 import QtCore
import pycx4.qcda as cda
from functools import partial
import os
import re
import json
import sys


class BtnHandle:
    def __init__(self, btn, name, mate_name):
        super(BtnHandle, self).__init__()
        self.widget = btn
        self.name = name
        self.mate_name = mate_name
        self.text = None
        self.row = None
        self.flag = False

class InjTune(QMainWindow):
    def __init__(self):
        super(InjTune, self).__init__()
        direc = os.getcwd()
        direc = re.sub('handles', 'uis', direc)
        self.p_win = uic.loadUi(direc + "/inj_vs_tune.ui")
        self.setWindowTitle('InjResp')
        self.p_win.show()

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=True)
        # self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_extracted = cda.DChan('cxhw:0.dcct.extractioncurrent', on_update=True)
        # self.chan_extracted.valueMeasured.connect(self.extracted_event)

        self.p_win.handles_table.cellPressed.connect(self.index)
        self.handle_1 = BtnHandle(self.p_win.btn_handle_1, 'Handle #1', 'Handle #2')
        self.p_win.btn_handle_1.clicked.connect(partial(self.hand_choosed, self.handle_1))
        self.handle_2 = BtnHandle(self.p_win.btn_handle_2, 'Handle #2', 'Handle #1')
        self.p_win.btn_handle_2.clicked.connect(partial(self.hand_choosed, self.handle_2))
        self.p_win.btn_start.clicked.connect(self.start)

        ##########################
        self.marked_row = None
        self.cross_booked = {'Handle #1': None, 'Handle #2': None}
        ##########################
        self.cur_tunes = [0.0, 0.0]
        ##########################
        self.n_iter = 10
        self.cur_1_it = 0
        self.cur_2_it = 0
        #########################
        self.shift = None       #  tune shift func

        self.load_handles()

    def start(self):
        if self.cross_booked['Handle #1'] is not None and self.cross_booked['Handle #2'] is not None:
            self.shift = make_shift_2h
            # n*type_1 tune shift
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_1.row, 'factor': self.n_iter}))
            # n*type_2 tune shift
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_2.row, 'factor': self.n_iter}))

            self.cur_1_it = -1 * self.n_iter
            self.cur_2_it = -1 * self.n_iter
            # QTimer.singleShot(6000, self.set_tune_flag_true)
        elif self.cross_booked['Handle #1'] is not None:
            self.shift = make_shift_1h
        elif self.cross_booked['Handle #2'] is not None:
            self.shift = make_shift_1h
        else:
            self.p_win.status_bar.showMessage('Choose handles')

    def hand_choosed(self, btn):
        if self.marked_row is not None:
            if self.marked_row != self.cross_booked[btn.mate_name]:
                if self.marked_row != btn.row:
                    btn.flag = True
                    self.cross_booked[btn.name] = btn.row = self.marked_row
                    btn.widget.text = self.p_win.handles_table.item(self.marked_row, 0).text()
                    btn.widget.setStyleSheet("background-color:rgb(0, 255, 0);")
                    btn.widget.setText(btn.widget.text)
                else:
                    btn.flag = False
                    self.cross_booked[btn.name] = btn.row = None
                    btn.widget.text = None
                    btn.widget.setStyleSheet("background-color:rgb(255, 255, 255);")
                    btn.widget.setText(btn.name)
            else:
                self.p_win.status_bar.showMessage('Choose another handle')
        else:
            if self.cross_booked['Handle #1'] is not None or self.cross_booked['Handle #2'] is not None:
                self.p_win.status_bar.showMessage('Choose second handle or press Start')
            else:
                self.p_win.status_bar.showMessage('Choose handle first')

    def make_shift_2h(self):
        print(self.cur_1_it, self.cur_2_it)
        print('--------------------------')
        if self.cur_1_it == self.n_iter:
            if self.cur_2_it == self.n_iter:
                # end & save
                print('FINISH')
                f = open('save_inj_tune_resp.txt', 'w')
                f.write(json.dumps(self.ring_cur_data))
                f.close()

                # to init state
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                                   'row': self.handle_1.row, 'factor': self.n_iter}))
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                                   'row': self.handle_2.row, 'factor': self.n_iter}))
                # to defaults
                self.marked_row = None
                self.cross_booked = {'Handle #1': None, 'Handle #2': None}
                self.cur_tunes = [0.0, 0.0]
                self.n_iter = 10
                self.cur_1_it = 0
                self.cur_2_it = 0
                self.shift = None
                # handle #1
                self.handle_1.flag = False
                self.handle_1.row = None
                self.handle_1.widget.text = None
                self.handle_1.widget.setStyleSheet("background-color:rgb(255, 255, 255);")
                self.handle_1.widget.setText(self.handle_1.name)
                # handle #2
                self.handle_2.flag = False
                self.handle_2.row = None
                self.handle_2.widget.text = None
                self.handle_2.widget.setStyleSheet("background-color:rgb(255, 255, 255);")
                self.handle_2.widget.setText(self.handle_2.name)

            else:
                # 2 handle step
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up',
                                                   'row': self.handle_2.row}))
                self.cur_2_it += 1
                # 2*n* 1 handle step
                self.cur_1_it = -1 * self.n_iter
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'cst_step_up', 'row': self.handle_1.row,
                                                   'factor': 2 * self.n_iter}))
        else:
            # 1 handle step
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up', 'row': self.handle_1.row}))
            self.cur_1_it += 1

    def make_shift_1h(self):
        pass

    def tunes_changed(self, chan):
        if self.tunes_flag:
            self.cur_tunes[0] = chan.val[0]
            self.cur_tunes[1] = chan.val[1]
            self.ring_cur_data[json.dumps(self.cur_tunes)] = []
            self.cur_flag = True
            self.tunes_flag = False

    def extracted_event(self, chan):
        if self.counter >= 22:
            self.counter = 0
            self.cur_flag = False
            self.shift()
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
