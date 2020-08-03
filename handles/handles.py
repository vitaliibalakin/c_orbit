import pycx4.qcda as cda
import sys
import os
import re
import numpy as np
from PyQt5.QtWidgets import QTableWidgetItem, QApplication, QMainWindow, QTableWidget
from PyQt5 import QtCore, QtGui
from PyQt5 import uic


class Some(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        direc = os.getcwd()
        direc = re.sub('handles', 'uis', direc)
        uic.loadUi(direc + "/handle_window.ui", self)
        self.show()
        self.marked_row = None
        self.dict_handles = {}
        self.dict_handles_now = {}

        # self.dict_lens_beta = {'1F1': [19.90920-19.72920], '1D1': [20.20920-20.02920],
        #                        '1F2': [16.44520-16.26520], '1D2': [16.04348-15.84691],
        #                        '1F3': [14.50848 - 14.31191], '1D3': [14.87848 - 14.68191],
        #                        '1F4': [18.17720 - 17.99720],
        #                        '2F1': [21.40920 - 21.22920], '2D1': [21.10920 - 20.92920],
        #                        '2F2': [24.87320 - 24.69320], '2D2': [25.29148 - 25.09491],
        #                        '2F3': [26.82048 - 26.62391], '2D3': [26.45048 - 26.25391],
        #                        '2F4': [23.14120 - 22.96120],
        #                        '3F1': [-6.016400 + 6.196400], '3D1': [-6.316400 + 6.496400],
        #                        '3F2': [-2.552400 + 2.732400], '3D2': [-2.134115 + 2.330685],
        #                        '3F3': [-0.5991150 + 0.7956850], '3D3': [-0.9691150 + 1.165685],
        #                        '3F4': [-4.284400 + 4.464400],
        #                        '4F1': [-7.516400 + 7.696400],'4D1': [-7.216400 + 7.396400],
        #                        '4F2': [-10.98040 + 11.16040], '4D2': [-11.38211 + 11.57868],
        #                        '4F3': [13.11368 - 12.91711], '4D3': [12.95642899999997 - 12.74368499999996]
        #                        '4F4': [-9.248400 + 9.428400]}

        self.table = Table(self.table_elem)
        # callbacks
        self.btn_freq_up.clicked.connect(self.step_up)
        self.btn_freq_down.clicked.connect(self.step_down)
        self.Add_Hendles.clicked.connect(self.add)
        self.Delete_Hendles.clicked.connect(self.remove)
        self.table_elem.cellPressed.connect(self.index)

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
        self.row_num += 1
        # add to table
        list_params = ["D3 | F3", "100 | 500", "0.1 | 0"]
        self.table.add_row(list_params)

    def remove(self):
        self.table.remove_row(self.marked_row)
        for i in range(self.marked_row, self.row_num):
            self.dict_heandles[i] = self.heandles[i+1]
            self.dict_heandles.delete(self.row_num)
            self.row_num -= 1

    def set_color_row(self, table, marked_row, color):
        for i in range(table.columnCount()):
            table.item(marked_row, i).SetBackground(color(7183255))

    def find_dq(self, lens, lens_1):
        self.qq = np.array([self.spin_delta_qx.value(), self.spin_delta_qy.value()])
        self.iki = np.array([[lens.int_x, lens_1.int_x], [lens.int_y, lens_1.int_y]])
        self.delta_k = np.linalg.solve(self.iki, self.qq)
        print(self.delta_k)
        return self.delta_k


class Table:
    def __init__(self, table):
        super(Table, self).__init__()
        self.table = table
        self.cur_list = []
        self.add_row(["D3 | F3", "100 | 500", "0.1 | 0"])

    def add_row(self, list_params):
        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(list_params[0]))
        self.table.setItem(row_num, 1, QTableWidgetItem(list_params[1]))
        self.table.setItem(row_num, 2, QTableWidgetItem(list_params[2]))

        # cor_dict = {'name': name, 'Name_Lens': 'ffff', 'mag_iter': 'ffffffff'}
        # self.table.setCellWidget(row_num, 1, cor_dict['name_Lens'])
        # self.table.setCellWidget(row_num, 2, cor_dict['mag_iter'])
        # self.cur_list.append(cor_dict)

    def remove_row(self, i):
        self.table.removeRow(i)


app = QApplication(['some'])
a = Some()
sys.exit(app.exec_())