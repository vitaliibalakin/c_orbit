#!/usr/bin/env python3
from PyQt5.QtWidgets import QTableWidgetItem


class Table:
    def __init__(self, table):
        super(Table, self).__init__()
        self.table = table
        self.cors_list = []
        for cor in ['rst2.crm1', 'rst2.crm2']:
            self.add_row(name=cor)

    def add_row(self, **params):
        # params
        name = params.get('name', 'noname')
        mag_range = params.get('mag_range', 500)
        mag_iter = params.get('mag_iter', 5)
        rm_step = params.get('rm_step', 100)
        rm_iter = params.get('rm_iter', 5)
        cor_dict = {'name': name, 'mag_range': RMSpinBox(mag_range, 100), 'mag_iter': RMSpinBox(mag_iter, 1),
                    'rm_step': RMSpinBox(rm_step, 100), 'rm_iter': RMSpinBox(rm_iter, 1)}
        # new line
        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(name))
        self.table.setCellWidget(row_num, 1, cor_dict['mag_range'])
        self.table.setCellWidget(row_num, 2, cor_dict['mag_iter'])
        self.table.setCellWidget(row_num, 3, cor_dict['rm_step'])
        self.table.setCellWidget(row_num, 4, cor_dict['rm_iter'])
        self.cors_list.append(cor_dict)

    def remove_row(self, name):
        i = 0
        for elem in self.cors_list:
            # print(elem['name'], name)
            if elem['name'] == name:
                self.table.removeRow(i)
                del(self.cors_list[i])
                break
            i += 1

    def free(self):
        list_f = self.cors_list.copy()
        for elem in list_f:
            self.remove_row(elem['name'])
