#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, Qt
import sys
import os
import re

from handles.table import Table
from handles.handles_table import HandlesTable
from base_modules.tree_table import TreeTableCom


class Handles(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        direc = os.getcwd()
        direc = re.sub('handles', 'uis', direc)
        uic.loadUi(direc + "/handle_window.ui", self)
        self.show()

        self.marked_row = None

        # table def
        self.handles_creating = Table(self.table)
        # table def
        self.handles = HandlesTable(self.handles_table, self.handle_info, self.status_bar)
        # tree widget
        self.tree = TreeTableCom(self.handles_creating, 40, self.tree_widget)
        # callbacks
        # self.btn_up.clicked.connect(self.step_up)
        # self.btn_down.clicked.connect(self.step_down)
        self.add_handle.clicked.connect(self.add)
        self.del_handle.clicked.connect(self.remove)

        self.handles_table.itemPressed.connect(self.index)

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

    def step_up(self):
        for name, val in self.dict_handles[self.marked_row].items():
            # self.currents.chans[name].setValue(self.currents.vals[name] + val)
            print(self.currents.vals[name] - val)

    def step_down(self):
        for name, val in self.dict_handles[self.marked_row].items():
            # self.currents.chans[name].setValue(self.currents.vals[name] - val)
            print(self.currents.vals[name] - val)

    def add(self):
        name = self.handle_name.text()
        if name == '':
            self.status_bar.showMessage('Enter the handle name')
        else:
            self.handles.add_row(name, self.handles_creating.cor_list)
            self.handles_creating.free()
            self.tree.free()
            self.handle_name.setText('')

    def remove(self):
        self.handles.remove_row(self.marked_row)

    def set_color_row(self, table, marked_row, color):
        for i in range(table.columnCount()):
            table.item(marked_row, i).SetBackground(color(7183255))


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
