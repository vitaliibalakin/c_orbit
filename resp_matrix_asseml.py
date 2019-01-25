#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda


class ResponseMatrixAssembling:
    def __init__(self):
        super(ResponseMatrixAssembling, self).__init__()
        """
        response matrix assembling
        """
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except Exception as err:
            print("No access to DB", err)

        self.cur = self.conn.cursor()
        self.cur.execute(
            "select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
            "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
            "devtype.name in ('UM4') group by grouping sets((devtype.name, full_name))")
        for elem in self.cur.fetchall():
            self.devnames_list.append(elem[1])
        print('devname_list', self.devnames_list)
        self.corr_names = ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z', 'c3d2_z',
                           'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1', 'crm2', 'crm3',
                           'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z', 'c3d3_z', 'c1d1_q',
                           'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q', 'c2d1_q', 'c2f1_q',
                           'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q', 'c3d1_q', 'c3f1_q', 'c3d2_q',
                           'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q',
                           'c4f3_q']
        self.chan_list = ['Iset', 'Imes']


if __name__ == "__main__":
    app = QApplication(['MainCorrectionControl'])
    w = ResponseMatrixAssembling()
    sys.exit(app.exec_())
