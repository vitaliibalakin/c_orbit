#!/usr/bin/env python3

from PyQt5.QtWidgets import QTableWidgetItem
import pycx4.qcda as cda


class HandlesTable:
    def __init__(self, table):
        super(HandlesTable, self).__init__()
        self.table = table
        self.handle_list = []

    def add_row(self, name, cors_list):
        handle_params = {}
        for cor in cors_list:
            handle_params['chan'] = cda.DChan(cor['name'] + '.Iset')
            handle_params['step'] = cor['step'].value()
            print(handle_params['chan'], handle_params['step'])
        handle_dict = {'name': name, 'descr': '', 'param': handle_params}

        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(name))
        self.table.setItem(row_num, 1, QTableWidgetItem(handle_dict['descr']))
        self.handle_list.append(handle_dict)

    def remove_row(self, name):
        i = 0
        for elem in self.handle_list:
            if elem['name'] == name:
                self.table.removeRow(i)
                del(self.handle_list[i])
                break
            i += 1

    def free(self):
        list_f = self.handle_list.copy()
        for elem in list_f:
            self.remove_row(elem['name'])

    def get_cor_name_list(self):
        names = []
        for el in self.cor_list:
            names.append(el['name'])
        return names
