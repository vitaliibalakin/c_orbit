#!/usr/bin/env python3

from PyQt5.QtWidgets import QTableWidgetItem
from bpm_base.aux_mod.rm_spin_box import RMSpinBox


class Table:
    def __init__(self, table):
        super(Table, self).__init__()
        self.table = table
        self.cor_list = []

    def add_row(self, **params):
        name = params.get('name', 'noname')
        it_id = params.get('id')
        cor_dict = {'id': it_id, 'name': name, 'step': RMSpinBox(0, 100)}

        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(name.split('.')[-1]))
        self.table.setCellWidget(row_num, 1, cor_dict['step'])
        self.cor_list.append(cor_dict)

    def remove_row(self, it_id):
        i = 0
        for elem in self.cor_list:
            if elem['id'] == it_id:
                self.table.removeRow(i)
                del(self.cor_list[i])
                break
            i += 1

    def free(self):
        list_f = self.cor_list.copy()
        for elem in list_f:
            self.remove_row(elem['id'])

    def get_cor_name_list(self):
        names = []
        for el in self.cor_list:
            names.append(el['name'])
        return names
