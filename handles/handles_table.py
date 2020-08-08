#!/usr/bin/env python3

from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget

import pycx4.qcda as cda


class HandlesTable:
    def __init__(self, table, handle_info, status_bar):
        super(HandlesTable, self).__init__()
        self.table, self.status_bar = table, status_bar
        self.handle_list = []

    def add_row(self, name, cors_list):
        handle_params = {}
        row_num = self.table.rowCount()
        if cors_list:
            for cor in cors_list:
                handle_params[cor['name'].split('.')[-1]] = [cda.DChan(cor['name'] + '.Iset'), cor['step'].value()]
            handle_sett = {'name': name, 'descr': '', 'param': handle_params}
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(name))
            self.table.setItem(row_num, 1, QTableWidgetItem(handle_sett['descr']))
            self.handle_list.append(handle_sett)
        else:
            self.status_bar.showMessage('Choose element for handle creating')

    def remove_row(self, row):
        self.table.removeRow(row)
        for i in range(0, len(self.handle_list)):
            if i == row:
                del(self.handle_list[i])
                break

    def get_handle(self, row):
        for i in range(0, len(self.handle_list)):
            if i == row:
                return self.handle_list[i]['param']

    def get_handle_list(self):
        names = []
        for el in self.handle_list:
            names.append(el['name'])
        return names
