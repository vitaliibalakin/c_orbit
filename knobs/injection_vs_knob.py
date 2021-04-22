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
        direc = re.sub('knobs', 'uis', direc)
        self.p_win = uic.loadUi(direc + "/inj_vs_tune.ui")
        self.setWindowTitle('InjResp')
        self.p_win.show()

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=True)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=True)
        self.chan_res.valueMeasured.connect(self.res)
        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=True)
        self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_extracted = cda.DChan('cxhw:0.dcct.extractioncurrent', on_update=True)
        self.chan_extracted.valueMeasured.connect(self.extracted_current)
        self.chan_eshots = cda.DChan('cxhw:0.ddm.eshots')
        self.chan_eshots.valueMeasured.connect(self.shots_num)
        self.chan_eshots = cda.DChan('cxhw:0.ddm.pshots')
        self.chan_eshots.valueMeasured.connect(self.shots_num)
        self.chan_modet = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=True)
        self.chan_modet.valueMeasured.connect(self.modet)
        self.chan_modet = cda.DChan("cxhw:0.ddm.extracted", on_update=True)
        self.chan_modet.valueMeasured.connect(self.extraction)

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
        self.extraction_flag:bool = False
        self.cur_flag:bool = False
        self.tunes_flag:bool = False
        self.shots_skip:dict = {'p': 10, 'e': 2}
        ##########################
        self.marked_row:int = None
        self.cross_booked:dict = {'Handle #1': None, 'Handle #2': None}
        ##########################
        self.mode:str = 'e'
        self.cur_tunes:list = [0.0, 0.0]
        self.ring_cur_arr:list = []
        self.ring_cur_data:dict = {}
        ##########################
        self.skip_counter:int = 0
        self.counter:int = 0
        self.n_amount:int = 36
        self.shots_counter:int = 1
        self.n_mesh:int = 1
        self.n_shots:int = 3
        self.cur_1_it:int = 0
        self.cur_2_it:int = 0
        ##########################
        self.load_handles()

    def start(self) -> None:
        self.n_shots = self.p_win.n_shots.value()
        self.n_mesh = self.p_win.n_mesh.value()
        self.p_win.btn_handle_1.setEnabled(False)
        self.p_win.btn_handle_2.setEnabled(False)
        self.p_win.n_shots.setEnabled(False)
        self.p_win.n_mesh.setEnabled(False)
        self.p_win.btn_start.setEnabled(False)
        self.p_win.progress_bar.setValue(0)
        if self.cross_booked['Handle #1'] is not None and self.cross_booked['Handle #2'] is not None:
            self.p_win.status_bar.showMessage('Start 2 knobs procedure')
            self.shift = self.make_shift_2h
            self.n_amount = (self.n_mesh * 2 + 1) ** 2
            # n*type_1 tune shift
            # self.status_bar.showMessage(self.handle_1.row, self.handle_2.row)
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_1.row, 'factor': self.n_mesh}))
            # n*type_2 tune shift
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle_2.row, 'factor': self.n_mesh}))

            self.cur_1_it = -1 * self.n_mesh
            self.cur_2_it = -1 * self.n_mesh
            QTimer.singleShot(6000, self.next_step)
        else:
            self.p_win.status_bar.showMessage('Start 1 knob procedure')
            if self.cross_booked['Handle #1'] is not None:
                self.handle = self.handle_1
            elif self.cross_booked['Handle #2'] is not None:
                self.handle = self.handle_2
            else:
                self.p_win.status_bar.showMessage('Choose knobs')
                self.p_win.btn_handle_1.setEnabled(True)
                self.p_win.btn_handle_2.setEnabled(True)
                self.p_win.n_shots.setEnabled(True)
                self.p_win.n_mesh.setEnabled(True)
                self.p_win.btn_start.setEnabled(True)
                return
            self.shift = self.make_shift_1h
            self.n_amount = (self.n_mesh * 2 + 1)
            self.cur_1_it = -1 * self.n_mesh
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle.row, 'factor': self.n_mesh}))
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
        if self.cur_1_it == self.n_mesh:
            if self.cur_2_it == self.n_mesh:
                # end & save
                self.p_win.status_bar.showMessage('FINISH')
                self.p_win.progress_bar.setValue(100)
                f = open('save_inj_tune_resp.txt', 'w')
                f.write(json.dumps(self.ring_cur_data))
                f.close()

                # to init state
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                                   'row': self.handle_1.row, 'factor': self.n_mesh}))
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                                   'row': self.handle_2.row, 'factor': self.n_mesh}))
                # to defaults
                self.index(self.marked_row)
                self.cross_booked = {'Handle #1': None, 'Handle #2': None}
                self.cur_tunes = [0.0, 0.0]
                self.n_mesh = 3
                self.counter = 0
                self.n_amount = 36
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

                self.p_win.btn_handle_1.setEnabled(True)
                self.p_win.btn_handle_2.setEnabled(True)
                self.p_win.n_shots.setEnabled(True)
                self.p_win.n_mesh.setEnabled(True)
                self.p_win.btn_start.setEnabled(True)
                return
            else:
                self.counter += 1
                self.p_win.progress_bar.setValue(int(self.counter / self.n_amount * 100))
                # 2 handle step
                self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up',
                                                   'row': self.handle_2.row}))
                self.cur_2_it += 1
                # 2*n* 1 handle step
                self.cur_1_it = -1 * self.n_mesh
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'cst_step_down', 'row': self.handle_1.row,
                                                   'factor': 2 * self.n_mesh}))
        else:
            self.counter += 1
            self.p_win.progress_bar.setValue(int(self.counter / self.n_amount * 100))
            # 1 handle step
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up', 'row': self.handle_1.row}))
            self.cur_1_it += 1
        QTimer.singleShot(6000, self.next_step)

    def make_shift_1h(self) -> None:
        if self.cur_1_it == self.n_mesh:
            self.p_win.status_bar.showMessage('FINISH')
            self.p_win.progress_bar.setValue(100)
            f = open('save_inj_tune_resp.txt', 'w')
            f.write(json.dumps(self.ring_cur_data))
            f.close()

            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'cst_step_down',
                                               'row': self.handle.row, 'factor': self.n_mesh}))

            # to defaults
            self.handle = None
            self.index(self.marked_row)
            self.cross_booked = {'Handle #1': None, 'Handle #2': None}
            self.cur_tunes = [0.0, 0.0]
            self.n_mesh = 3
            self.n_amount = 36
            self.counter = 0
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

            self.p_win.btn_handle_1.setEnabled(True)
            self.p_win.btn_handle_2.setEnabled(True)
            self.p_win.n_shots.setEnabled(True)
            self.p_win.n_mesh.setEnabled(True)
            self.p_win.btn_start.setEnabled(True)
            return
        else:
            self.counter += 1
            self.p_win.progress_bar.setValue(int(self.counter / self.n_amount * 100))
            self.chan_cmd.setValue(json.dumps({'client': 'inj_vs_handles', 'cmd': 'step_up', 'row': self.handle.row}))
            self.cur_1_it += 1
        QTimer.singleShot(6000, self.next_step)

    def shots_num(self, chan) -> None:
        self.shots_skip[chan.name[-6]] = chan.val // 2 + 1

    def modet(self, chan)-> None:
        self.mode = chan.val[0]

    def extraction(self, chan):
        self.extraction_flag = True

    def tunes_changed(self, chan) -> None:
        if self.extraction_flag and self.tunes_flag:
            if self.skip_counter < self.shots_skip[self.mode]:
                self.skip_counter += 1
            else:
                self.skip_counter = 0
                self.cur_tunes[0] = round(chan.val[0], 5)
                self.cur_tunes[1] = round(chan.val[1], 5)
                self.cur_flag = True
                self.tunes_flag = False
                self.extraction_flag = False

    def extracted_current(self, chan) -> None:
        if self.shots_counter >= self.n_shots:
            self.shots_counter = 0
            self.ring_cur_data[self.counter] = {json.dumps(self.cur_tunes): round(np.mean(self.ring_cur_arr), 1)}
            self.ring_cur_arr = []
            self.cur_flag = False
            self.shift()
        else:
            if self.cur_flag:
                self.shots_counter += 1
                self.ring_cur_arr.append(chan.val)

    def next_step(self) -> None:
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

    def res(self, chan) -> None:
        if chan.val:
            cmd_res = json.loads(chan.val)
            client = cmd_res.get('client')
            res = cmd_res.get('res')
            if client == 'handle':
                self.update_table()

                m_row = self.marked_row
                self.marked_row = None
                if res == 'handle_added':
                    if m_row is not None:
                        self.index(m_row + 1)
                elif res == 'handle_deleted':
                    row = cmd_res['row']
                    if m_row is not None:
                        if m_row < row:
                            self.index(m_row)
                        elif m_row > row:
                            self.index(m_row - 1)

    def update_table(self) -> None:
        for i in range(self.p_win.handles_table.rowCount()):
            self.p_win.handles_table.removeRow(0)
        self.load_handles()


if __name__ == "__main__":
    app = QApplication(['inj_vs'])
    w = InjTune()
    sys.exit(app.exec_())
