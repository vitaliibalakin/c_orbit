#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import uic, Qt
import sys
import os
import re
import json

from handles.table import Table
from handles.handles_table_old import HandlesTable
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

        # table def
        self.handles_creating = Table(self.table)
        # table def
        self.handles = HandlesTable(self.handles_table)
        # tree widget
        self.tree = TreeTableCom(self.handles_creating, 0, self.tree_widget)
        # callbacks
        self.btn_up.clicked.connect(self.step_up)
        self.btn_cst_up.clicked.connect(self.cst_step_up)
        self.btn_down.clicked.connect(self.step_down)
        self.btn_cst_down.clicked.connect(self.cst_step_down)
        self.btn_load_handle.clicked.connect(self.load_handle)
        self.btn_add_handle.clicked.connect(self.add)
        self.btn_del_handle.clicked.connect(self.remove)

        self.handles_table.itemPressed.connect(self.index)

        self.load_handles()

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
                handle = self.handles.get_handle(self.marked_row)
                for key, val in handle.items():
                    self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val[1]))
        else:
            self.marked_row = pr_item.row()
            for i in range(self.handles_table.columnCount()):
                self.handles_table.item(self.marked_row, i).setBackground(Qt.QColor('green'))
            handle = self.handles.get_handle(self.marked_row)
            for key, val in handle.items():
                self.handle_info.append('Name: ' + key + ' | ' + 'Step: ' + str(val[1]))

    def add(self):
        name = self.handle_name.text()
        descr = self.handle_descr.text()
        if name:
            if self.handles_creating.cor_list:
                for elem in self.handles_creating.cor_list:
                    elem['step'] = elem['step'].value()
                self.handles.add_row(name, descr, self.handles_creating.cor_list)
                self.handle_name.setText('')
            else:
                self.status_bar.showMessage('Choose elements for handle creating')
                return
        else:
            self.status_bar.showMessage('Enter the handle name')
            return
        # save current handles
        f = open('saved_handles.txt', 'w')
        f.write(json.dumps(self.handles.handle_descr))
        f.close()

        # clear objects
        self.handles_creating.free()
        self.tree.free()

    def remove(self):
        if self.marked_row is not None:
            self.handles.remove_row(self.marked_row)

            # save current handles
            f = open('saved_handles.txt', 'w')
            f.write(json.dumps(self.handles.handle_descr))
            f.close()

            # clear objects
            self.marked_row = None
            self.handle_info.clear()
        else:
            self.status_bar.showMessage('Choose row to delete')

    def step_up(self):
        if self.marked_row is not None:
            handle = self.handles.get_handle(self.marked_row)
            for key, k_val in handle.items():
                new_curr = k_val[0].val + k_val[1]
                # print(k_val[0].val)
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_up(self):
        if self.marked_row is not None:
            handle = self.handles.get_handle(self.marked_row)
            factor = self.cst_step.value()
            for key, k_val in handle.items():
                new_curr = k_val[0].val + k_val[1]*factor
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def step_down(self):
        # print(self.marked_row)
        if self.marked_row is not None:
            handle = self.handles.get_handle(self.marked_row)
            for key, k_val in handle.items():
                new_curr = k_val[0].val - k_val[1]
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def cst_step_down(self):
        if self.marked_row is not None:
            handle = self.handles.get_handle(self.marked_row)
            factor = self.cst_step.value()
            for key, k_val in handle.items():
                new_curr = k_val[0].val - k_val[1]*factor
                k_val[0].setValue(new_curr)
        else:
            self.status_bar.showMessage('Choose row to step')

    def load_handles(self):
        try:
            f = open('saved_handles.txt', 'r')
            handles = json.loads(f.read())
            f.close()
            for row_num, handle in handles.items():
                self.handles.add_row(handle['name'], handle['descr'], handle['cor_list'])
        except ValueError:
            self.status_bar.showMessage('empty saved file')

    def load_handle(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd(),
                                                    filter='Text Files (*.txt)')[0]
            f = open(file_name, 'r')
            handle = json.loads(f.readline())
            f.close()
            self.handles.add_row(handle['name'], handle['descr'], handle['cor_list'])

            f = open('saved_handles.txt', 'w')
            f.write(json.dumps(self.handles.handle_descr))
            f.close()

            if self.marked_row is not None:
                self.marked_row += 1
        except Exception as exc:
            self.status_bar.showMessage(str(exc))


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
