#!/usr/bin/env python3


class HandlesTable:
    def __init__(self, table):
        super(HandlesTable, self).__init__()
        self.table = table
        self.handles = {}
        self.handle_descr = {}

    def add_row(self, name, descr, info):
        self.handles_renum()
        self.handle_descr[0] = {'name': name, 'descr': descr, 'info': info}



        self.handles[0] = info

    def delete_row(self, row):
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


