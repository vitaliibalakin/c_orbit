#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem
from PyQt5 import uic, Qt
from PyQt5 import QtCore
import pycx4.qcda as cda
import sys
import os
import re
import json

from knobs.knob_creating_table import Table
from bpm_base.aux_mod.tree_table import TreeTableCom


class Handles(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        direc = os.getcwd()
        direc = re.sub('knobs', 'uis', direc)
        uic.loadUi(direc + "/handle_window.ui", self)
        self.setWindowTitle('Handles')
        self.show()

        self.marked_row = None
        self.edit_block = False
        self.self_sender = False
        self.handles_info = {}
        self.cell_col = {0: 'name', 1: 'descr'}

        # table def
        self.handles_creating = Table(self.table)
        # tree widget
        self.tree = TreeTableCom(self.handles_creating, 0, self.tree_widget)
        # callbacks
        self.btn_up.clicked.connect(self.step_up)
        self.btn_cst_up.clicked.connect(self.cst_step_up)
        self.btn_down.clicked.connect(self.step_down)
        self.btn_cst_down.clicked.connect(self.cst_step_down)
        self.btn_add_handle.clicked.connect(self.add)
        self.btn_del_handle.clicked.connect(self.delete)

        # control channels
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_res.valueMeasured.connect(self.res)

        self.load_handles()
        self.handles_table.cellPressed.connect(self.index)
        self.handles_table.cellChanged.connect(self.edit_item)

    def edit_item(self, row, column):
        if self.edit_block:
            return
        text = self.handles_table.item(row, column).text()
        self.self_sender = True
        self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'edit_item', 'item': [row, column],
                                           'text': text}))

    def index(self, row, column=0):
        # paint row & set handle info
        self.edit_block = True
        if self.marked_row is not None:
            if self.marked_row == row:
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = None
                self.handle_info.clear()
            else:
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = row
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(row, i).setBackground(Qt.QColor(21, 139, 195))
                self.handle_info.clear()
                handle_i = self.handles_info[row]
                for key, val in handle_i.items():
                    self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))
        else:
            self.marked_row = row
            for i in range(self.handles_table.columnCount()):
                self.handles_table.item(row, i).setBackground(Qt.QColor(21, 139, 195))
            handle = self.handles_info[row]
            for key, val in handle.items():
                self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))
        self.edit_block = False

    def add(self):
        name = self.handle_name.text()
        descr = self.handle_descr.text()
        if name:
            if self.handles_creating.cor_list:
                for elem in self.handles_creating.cor_list:
                    elem['step'] = elem['step'].value()
                info = {'name': name, 'descr': descr, 'cor_list': self.handles_creating.cor_list}
                self.self_sender = True
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'add_handle', 'info': info}))
                self.handle_name.setText('')
                self.handles_creating.free()
                self.tree.free()
            else:
                self.status_bar.showMessage('Choose elements for handle creating')
        else:
            self.status_bar.showMessage('Enter the handle name')

    def delete(self):
        if self.marked_row is not None:
            self.self_sender = True
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'delete_handle', 'row': self.marked_row}))
        else:
            self.status_bar.showMessage('Choose row to delete')

    def step_up(self):
        if self.marked_row is not None:
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'step_up', 'row': self.marked_row}))
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_up(self):
        if self.marked_row is not None:
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'cst_step_up', 'row': self.marked_row,
                                               'factor': self.cst_step.value()}))
        else:
            self.status_bar.showMessage('Choose row to step')

    def step_down(self):
        if self.marked_row is not None:
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'step_down', 'row': self.marked_row}))
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_down(self):
        if self.marked_row is not None:
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'cst_step_down', 'row': self.marked_row,
                                               'factor': self.cst_step.value()}))
        else:
            self.status_bar.showMessage('Choose row to step')

    def load_handles(self):
        try:
            self.edit_block = True
            self.handles_info = {}
            self.handles_names = {}
            self.handles_descr = {}
            f = open('saved_handles.txt', 'r')
            handles = json.loads(f.read())
            f.close()
            for row_num, handle in handles.items():
                info = {}
                for cor in handle['cor_list']:
                    info[cor['name'].split('.')[-1]] = cor['step']
                self.handles_info[int(row_num)] = info
                self.handles_table.insertRow(0)
                name = QTableWidgetItem(handle['name'])
                name.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                descr = QTableWidgetItem(handle['descr'])
                descr.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                self.handles_table.setItem(0, 0, name)
                self.handles_table.setItem(0, 1, descr)
            self.edit_block = False
        except ValueError:
            self.status_bar.showMessage('empty saved file')

    #########################################################
    #                     command part                      #
    #########################################################

    def res(self, chan):
        if chan.val:
            cmd_res = json.loads(chan.val)
            client = cmd_res.get('client')
            res = cmd_res.get('res')
            if client == 'handle':
                self.update_table()
                self.status_bar.showMessage(res)

                m_row = self.marked_row
                self.marked_row = None
                self.handle_info.clear()
                if res == 'handle_added':
                    if m_row is not None:
                        self.index(m_row + 1)
                elif res == 'handle_deleted':
                    if self.self_sender:
                        pass
                    else:
                        row = cmd_res['row']
                        if m_row is not None:
                            if m_row < row:
                                self.index(m_row)
                            elif m_row > row:
                                self.index(m_row - 1)
                elif res == 'handle_edited':
                    if m_row is not None:
                        self.index(m_row)
                self.self_sender = False

    def update_table(self):
        print('update')
        for i in range(self.handles_table.rowCount()):
            self.handles_table.removeRow(0)
        self.load_handles()


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
