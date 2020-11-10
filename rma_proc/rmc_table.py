#!/usr/bin/env python3

from PyQt5.QtWidgets import QTableWidgetItem
from bpm_base.aux_mod.rm_spin_box import RMSpinBox


class Table:
    def __init__(self, table):
        super(Table, self).__init__()
        self.table = table
        self.cor_dict = {}

    def add_row(self, **params):
        # params
        name = params.get('name', 'noname')
        it_id = params.get('id')
        cor_dict = {'id': it_id, 'name': name, 'rm_step': RMSpinBox(100, 100), 'rm_iter': RMSpinBox(5, 1)}
        # new line
        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(name.split('.')[-1]))
        self.table.setCellWidget(row_num, 1, cor_dict['rm_step'])
        self.table.setCellWidget(row_num, 2, cor_dict['rm_iter'])
        self.cor_dict[row_num] = cor_dict

    def remove_row(self, row):
        # deleting table row
        self.table.removeRow(row)
        # deleting info from dicts and renumering dicts
        for k in range(row, len(self.cor_dict) - 1):
            self.cor_dict[k] = self.cor_dict[k + 1]
        del(self.cor_dict[len(self.cor_dict) - 1])

    def common_step(self, selected_rows, rm_step, st_step, sel_all=False):
        if sel_all:
            selected_rows = []
            for i in range(self.table.rowCount()):
                selected_rows.append(i)
        for row in selected_rows:
            self.cor_dict[row]['rm_step'].setValue(self.cor_dict[row]['rm_step'].value() + rm_step)
            self.cor_dict[row]['rm_iter'].setValue(self.cor_dict[row]['rm_iter'].value() + st_step)

    def free(self):
        for row, elem in self.cor_dict:
            # deleting table row
            self.table.removeRow(row)
            # deleting info from dicts
            del(self.cor_dict[row])

    def get_cor_name_list(self):
        names = []
        for el in self.cor_dict:
            names.append(el['name'])
        return names
