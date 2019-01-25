#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda


class Auxiliary:
    def __init__(self):
        super(Auxiliary, self).__init__()
        """
        response matrix assembling
        """
        self.values = {'Iset': {}, 'Imes': {}}
        self.chans = {'Iset': {}, 'Imes': {}}
        # self.values, self.chans = self.chans_connect()

    def chans_connect(self):
        try:
            conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except Exception as err:
            print("No access to DB", err)

        devnames_list = []

        cur = conn.cursor()
        cur.execute(
            "select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
            "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
            "devtype.name in ('UM4') group by grouping sets((devtype.name, full_name))")
        for elem in cur.fetchall():
            devnames_list.append(elem[1])
        print('devname_list', devnames_list)
        names = ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z', 'c3d2_z',
                           'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1', 'crm2', 'crm3',
                           'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z', 'c3d3_z', 'c1d1_q',
                           'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q', 'c2d1_q', 'c2f1_q',
                           'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q', 'c3d1_q', 'c3f1_q', 'c3d2_q',
                           'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q',
                           'c4f3_q']
        chan_list = ['Iset', 'Imes']

        for dname in devnames_list:
            name = dname.split('.')[-1]
            if name in names:
                for chan_type in chan_list:
                    chan = cda.DChan(dname + '.' + chan_type)
                    self.chans[chan_type][name] = chan
                    self.values[chan_type][name] = 0
                    chan.valueMeasured.connect(self.ps_val_change)
        print(self.values)
        return self.values, self.chans

    def ps_val_change(self, chan):
        """
        function update chans value
        :param chan: called function chan
        :return: new value dict
        """
        self.corr_values[chan.name.split('.')[-1]][chan.name.split('.')[-2]] = chan.val


if __name__ == "__main__":
    app = QApplication(['Auxiliary'])
    w = Auxiliary()
    sys.exit(app.exec_())
