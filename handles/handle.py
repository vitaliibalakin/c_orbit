#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem
from PyQt5 import uic, Qt
import pycx4.qcda as cda
import sys
import os
import re
import json

from handles.table import Table
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
        self.current_item = None
        self.handles_info = {}

        # table def
        self.handles_creating = Table(self.table)
        # tree widget
        self.tree = TreeTableCom(self.handles_creating, 0, self.tree_widget)
        # callbacks
        self.btn_up.clicked.connect(self.step_up)
        self.btn_cst_up.clicked.connect(self.cst_step_up)
        self.btn_down.clicked.connect(self.step_down)
        self.btn_cst_down.clicked.connect(self.cst_step_down)
        self.btn_load_handle.clicked.connect(self.load_handle)
        self.btn_add_handle.clicked.connect(self.add)
        self.btn_del_handle.clicked.connect(self.delete)

        # control channels
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_res.valueMeasured.connect(self.res)

        self.handles_table.itemPressed.connect(self.index)
        self.handles_table.cellDoubleClicked.connect(self.selection)
        self.handles_table.itemSelectionChanged.connect(self.edit_item)

        self.load_handles()

    # done
    def get_handle(self, row):
        return self.handles_info[row]

    # done
    def selection(self, row, column):
        self.current_item = (row, column)

    # done
    def edit_item(self):
        if self.current_item:
            text = self.handles_table.item(self.current_item[0], self.current_item[1]).text()
            if self.current_item[1] == 0:
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'edit_item', 'name': text}))
            else:
                self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'edit_item', 'descr': text}))
            self.current_item = None

    def index(self, pr_item):
        # paint row & set handle info
        if self.marked_row is not None:
            if self.marked_row == pr_item.row():
                for i in range(self.table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = None
                self.handle_info.clear()
            else:
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('white'))
                self.marked_row = pr_item.row()
                for i in range(self.handles_table.columnCount()):
                    self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('green'))
                self.handle_info.clear()
                handle_i = self.get_handle(self.marked_row)
                for key, val in handle_i.items():
                    self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))
        else:
            self.marked_row = pr_item.row()
            for i in range(self.handles_table.columnCount()):
                self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('green'))
            handle = self.get_handle(self.marked_row)
            for key, val in handle.items():
                self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val))

    def add(self):
        name = self.handle_name.text()
        descr = self.handle_descr.text()
        short_info = {}
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

    # done
    def delete(self):
        if self.marked_row is not None:
            self.handles.delete_row(self.marked_row)
            for k in range(self.marked_row, len(self.handles_info) - 1):
                self.handles_info[k] = self.handles_info[k + 1]
            del (self.handles_info[len(self.handles_info) - 1])
            # send msg
            self.chan_cmd.setValue(json.dumps({'client': 'handle', 'cmd': 'delete', 'row': self.marked_row}))
            # clear objects
            self.marked_row = None
            self.handle_info.clear()
        else:
            self.status_bar.showMessage('Choose row to delete')

    def step_up(self):
        if self.marked_row is not None:
            handle = self.get_handle(self.marked_row)
            for key, k_val in handle.items():
                new_curr = k_val[0].val + k_val[1]
                # print(k_val[0].val)
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_up(self):
        if self.marked_row is not None:
            handle = self.get_handle(self.marked_row)
            factor = self.cst_step.value()
            for key, k_val in handle.items():
                new_curr = k_val[0].val + k_val[1]*factor
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def step_down(self):
        # print(self.marked_row)
        if self.marked_row is not None:
            handle = self.get_handle(self.marked_row)
            for key, k_val in handle.items():
                new_curr = k_val[0].val - k_val[1]
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_down(self):
        if self.marked_row is not None:
            handle = self.get_handle(self.marked_row)
            factor = self.cst_step.value()
            for key, k_val in handle.items():
                new_curr = k_val[0].val - k_val[1]*factor
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    # done
    def load_handles(self):
        try:
            f = open('saved_handles.txt', 'r')
            handles = json.loads(f.read())
            f.close()
            info = {}
            for row_num, handle in handles.items():
                for cor in handle['cor_list']:
                    info[cor['name'].split('.')[-1]] = cor['step']
                self.handles_table.insertRow(0)
                self.handles_table.setItem(0, 0, QTableWidgetItem(handle['name']))
                self.handles_table.setItem(0, 1, QTableWidgetItem(handle['descr']))
                self.handles_info[int(row_num)] = info

        except ValueError:
            self.status_bar.showMessage('empty saved file')

    # done
    def handles_renum(self):
        for i in reversed(range(len(self.handles))):
            self.handles_info[i+1] = self.handles_info.pop(i)

    #########################################################
    #                     command part                      #
    #########################################################

    def res(self, chan):
        pass


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
