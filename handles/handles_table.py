#!/usr/bin/env python3

from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget
import json

import pycx4.qcda as cda


class HandlesTable:
    def __init__(self, table):
        super(HandlesTable, self).__init__()
        self.table = table
        self.current_item = None
        self.handles = {}
        self.handle_descr = {}

        self.table.cellDoubleClicked.connect(self.selection)
        self.table.itemSelectionChanged.connect(self.edit_item)

    def selection(self, row, column):
        self.current_item = (row, column)

    def edit_item(self):
        if self.current_item:
            text = self.table.item(self.current_item[0], self.current_item[1]).text()
            if self.current_item[1] == 0:
                self.handle_descr[self.current_item[0]]['name'] = text
                f = open('saved_handles.txt', 'w')
                f.write(json.dumps(self.handle_descr))
                f.close()
            else:
                self.handle_descr[self.current_item[0]]['descr'] = text
                f = open('saved_handles.txt', 'w')
                f.write(json.dumps(self.handle_descr))
                f.close()
            self.current_item = None

    def add_row(self, name, descr, cors_list):
        handle_params = {}
        row_num = self.table.rowCount()
        self.handle_descr[row_num] = {'name': name, 'descr': descr, 'cor_list': []}
        for cor in cors_list:
            if cor['name'].split('.')[-1][0] == 'G':
                handle_params[cor['name'].split('.')[-1]] = [cda.DChan(cor['name'] + '.Uset'), cor['step']]
                # handle_params[cor['name'].split('.')[-1]][0].valueMeasured.connect(self.CLB)
            else:
                handle_params[cor['name'].split('.')[-1]] = [cda.DChan(cor['name'] + '.Iset'), cor['step']]
                # handle_params[cor['name'].split('.')[-1]][0].valueMeasured.connect(self.CLB)
            self.handle_descr[row_num]['cor_list'].append(cor)

        self.table.insertRow(row_num)
        self.table.setItem(row_num, 0, QTableWidgetItem(name))
        self.table.setItem(row_num, 1, QTableWidgetItem(descr))
        self.handles[row_num] = handle_params

    def CLB(self, chan):
        print(chan.name, chan.val)

    def remove_row(self, row):
        # deleting table row
        self.table.removeRow(row)
        # deleting info from dicts and renumering dicts
        for k in range(row, len(self.handles) - 1):
            self.handles[k] = self.handles[k + 1]
            self.handle_descr[k] = self.handle_descr[k + 1]
        del(self.handles[len(self.handles) - 1])
        del(self.handle_descr[len(self.handle_descr) - 1])

    def get_handle(self, row):
        return self.handles[row]

    # def get_handle_list(self):
    #     names = []
    #     for el in self.handles:
    #         names.append(el['name'])
    #     return names
