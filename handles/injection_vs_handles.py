#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtCore import QTimer
from PyQt5 import uic, Qt
from PyQt5 import QtCore
import pycx4.qcda as cda
from functools import partial
import numpy as np
import os
import re
import json
import sys


class BtnHandle:
    def __init__(self, btn, name, mate_name):
        super(BtnHandle, self).__init__()
        self.widget:object = btn
        self.name:str = name
        self.mate_name:str = mate_name
        self.text:str = None
        self.row:int = None
        self.flag:bool = False

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
        self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_extracted = cda.DChan('cxhw:0.dcct.extractioncurrent', on_update=True)
        self.chan_extracted.valueMeasured.connect(self.extracted_event)

        self.p_win.handles_table.cellPressed.connect(self.index)
        self.handle_1:object = BtnHandle(self.p_win.btn_handle_1, 'Handle #1', 'Handle #2')
        self.p_win.btn_handle_1.clicked.connect(partial(self.hand_choosed, self.handle_1))
        self.handle_2:object = BtnHandle(self.p_win.btn_handle_2, 'Handle #2', 'Handle #1')
        self.p_win.btn_handle_2.clicked.connect(partial(self.hand_choosed, self.handle_2))
        self.p_win.btn_start.clicked.connect(self.start)

        #########################
        self.shift:function = None  # tune shift func
        self.handle:object = None
        ##########################
        self.cur_flag:bool = False
        self.tunes_flag:bool = False
        ##########################
        self.marked_row:int = None
        self.cross_booked:dict = {'Handle #1': None, 'Handle #2': None}
        ##########################
        self.cur_tunes:list = [0.0, 0.0]
        self.ring_cur_arr:list = []
        self.ring_cur_data:dict = {}
        ##########################
        self.n_iter:int = 1
        self.counter:int = 0
        self.cur_1_it:int = 0
        self.cur_2_it:int = 0

        self.load_handles()

    def start(self) -> None:
        if self.cross_booked['Handle #1'] is not None and self.cross_booked['Handle #2'] is not None:
            print('start_2')
            self.shift = self.make_shift_2h
            # n*type_1 tune shift
            print(self.handle_1.row, self.handle_2.row)
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_1.row, 'factor': self.n_iter}))
            # n*type_2 tune shift
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_2.row, 'factor': self.n_iter}))

            self.cur_1_it = -1 * self.n_iter
            self.cur_2_it = -1 * self.n_iter
            QTimer.singleShot(6000, self.next_step)
        else:
            print('start_1')
            if self.cross_booked['Handle #1'] is not None:
                self.handle = self.handle_1
            elif self.cross_booked['Handle #2'] is not None:
                self.handle = self.handle_2
            else:
                self.p_win.status_bar.showMessage('Choose handles')
                return
            self.shift = self.make_shift_1h
            self.cur_1_it = -1 * self.n_iter
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle.row, 'factor': self.n_iter}))
            QTimer.singleShot(6000, self.next_step)

    def hand_choosed(self, btn:object) -> None:
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

    def make_shift_2h(self) -> None:
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
                return
            else:
                # 2 handle step
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up',
                                                   'row': self.handle_2.row}))
                self.cur_2_it += 1
                # 2*n* 1 handle step
                self.cur_1_it = -1 * self.n_iter
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'cst_step_down', 'row': self.handle_1.row,
                                                   'factor': 2 * self.n_iter}))
        else:
            # 1 handle step
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up', 'row': self.handle_1.row}))
            self.cur_1_it += 1
        QTimer.singleShot(6000, self.next_step)

    def make_shift_1h(self) -> None:
        print(self.cur_1_it)
        print('--------------------------')
        if self.cur_1_it == self.n_iter:
            print('FINISH')
            f = open('save_inj_tune_resp.txt', 'w')
            f.write(json.dumps(self.ring_cur_data))
            f.close()

            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle.row, 'factor': self.n_iter}))

            # to defaults
            self.handle = None
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
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up', 'row': self.handle.row}))
            self.cur_1_it += 1
            QTimer.singleShot(6000, self.next_step)

    def tunes_changed(self, chan) -> None:
        if self.tunes_flag:
            self.cur_tunes[0] = chan.val[0]
            self.cur_tunes[1] = chan.val[1]
            self.cur_flag = True
            self.tunes_flag = False

    def extracted_event(self, chan) -> None:
        print('counter', self.counter)
        if self.counter >= 3:
            self.counter = 0
            self.ring_cur_data[json.dumps(self.cur_tunes)] = np.mean(self.ring_cur_arr)
            print(self.ring_cur_data)
            self.ring_cur_arr = []
            self.cur_flag = False
            self.shift()
        else:
            if self.cur_flag:
                self.counter += 1
                self.ring_cur_arr.append(chan.val)

    def next_step(self) -> None:
        print('next step')
        self.tunes_flag = True

    def index(self, row:int, column=0) -> None:
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

    def load_handles(self) -> None:
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
    app = QApplication(['inj_vs'])
    w = InjTune()
    sys.exit(app.exec_())
