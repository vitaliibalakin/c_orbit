#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
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
        self.table = Table(self.table)
        # table def
        self.handles_table = HandlesTable(self.handles_table)
        # tree widget
        self.tree = TreeTableCom(self.table, 40, self.tree_widget)
        # callbacks
        # self.btn_freq_up.clicked.connect(self.step_up)
        # self.btn_freq_down.clicked.connect(self.step_down)
        self.add_handle.clicked.connect(self.add)
        self.del_handle.clicked.connect(self.remove)
        # self.table.cellPressed.connect(self.index)

    def index(self):
        self.marked_row = self.table_elem.currentItem().row()

    def step_up(self):
        for name, val in self.dict_handles[self.marked_row].items():
            # self.currents.chans[name].setValue(self.currents.vals[name] + val)
            print(self.currents.vals[name] - val)

    def step_down(self):
        for name, val in self.dict_handles[self.marked_row].items():
            # self.currents.chans[name].setValue(self.currents.vals[name] - val)
            print(self.currents.vals[name] - val)

    def add(self):
        self.handles_table.add_row('1st', self.table.cor_list)
        self.table.free()

    def remove(self):
        self.table.remove_row(self.marked_row)
        for i in range(self.marked_row, self.row_num):
            self.dict_heandles[i] = self.heandles[i+1]
            self.dict_heandles.delete(self.row_num)
            self.row_num -= 1

    def set_color_row(self, table, marked_row, color):
        for i in range(table.columnCount()):
            table.item(marked_row, i).SetBackground(color(7183255))


if __name__ == "__main__":
    app = QApplication(['Handles'])
    w = Handles()
    sys.exit(app.exec_())
