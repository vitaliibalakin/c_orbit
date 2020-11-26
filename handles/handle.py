#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem
from PyQt5 import uic, Qt
import pycx4.qcda as cda
import sys
import os
import re
import json

from handles.handle_creating_table import Table
from bpm_base.aux_mod.tree_table import TreeTableCom


class Handles(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        direc = os.getcwd()
        direc = re.sub('handles', 'uis', direc)
        uic.loadUi(direc + "/handle_window.ui", self)
        self.setWindowTitle('Handles')
        self.show()

        self.marked_row = None
        self.handles_info = {}
        self.handles_names = {}
        self.handles_descr = {}
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
        text = self.handles_table.item(row, column).text()
        if column == 0:
            cell = self.handles_names
        else:
            cell = self.handles_descr
        if not (cell[row] == text):
            cell[row] = text
            text = self.handles_table.item(row, column).text()
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'edit_item', 'item': [row, column],
                                               'text': text}))

    def index(self, row, column):
        # paint row & set handle info
        if self.marked_row is not None:
            if self.marked_row == row:
                for i in range(self.table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = None
                self.handle_info.clear()
            else:
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = row
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor(21, 139, 195))
                self.handle_info.clear()
                handle_i = self.handles_info[self.marked_row]
                for key, val in handle_i.items():
                    self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))
        else:
            self.marked_row = row
            for i in range(self.handles_table.columnCount()):
                self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor(21, 139, 195))
            handle = self.handles_info[self.marked_row]
            for key, val in handle.items():
                self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))

    def add(self):
        name = self.handle_name.text()
        descr = self.handle_descr.text()
        if name:
            if self.handles_creating.cor_list:
                for elem in self.handles_creating.cor_list:
                    elem['step'] = elem['step'].value()
                info = {'name': name, 'descr': descr, 'cor_list': self.handles_creating.cor_list}
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
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'delete_handle', 'row': self.marked_row}))
            # clear objects
            self.marked_row = None
            self.handle_info.clear()
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
            self.marked_row = None
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
                self.handles_table.insertRow(0)
                self.handles_table.setItem(0, 0, QTableWidgetItem(handle['name']))
                self.handles_table.setItem(0, 1, QTableWidgetItem(handle['descr']))
                self.handles_info[int(row_num)] = info
                self.handles_names[int(row_num)] = handle['name']
                self.handles_descr[int(row_num)] = handle['descr']

        except ValueError:
            self.status_bar.showMessage('empty saved file')

    #########################################################
    #                     command part                      #
    #########################################################

    def res(self, chan):
        res = chan.val
        print(chan.val)
        if res:
            chan_val = json.loads(res)
            self.status_bar.showMessage(chan_val['res'])
            if chan_val['res'] == 'handle_added':
                for i in range(self.handles_table.rowCount()):
                    self.handles_table.removeRow(0)
                self.load_handles()
            elif chan_val['res'] == 'handle_deleted':
                for i in range(self.handles_table.rowCount()):
                    self.handles_table.removeRow(0)
                self.load_handles()


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
