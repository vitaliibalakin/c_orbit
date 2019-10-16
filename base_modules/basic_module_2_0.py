#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda


class BasicFunc:
    def __init__(self):
        super(BasicFunc, self).__init__()

    def chans_connect(self, chans, values, names, devtype='UM4'):
        try:
            conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except Exception as err:
            print("No access to DB", err)

        devnames_list = []
        chan_list = []

        cur = conn.cursor()
        cur.execute(
            "select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
            "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
            "devtype.name in (%(DEVTYPE)s) group by grouping sets((devtype.name, full_name))", {'DEVTYPE': devtype})
        for elem in cur.fetchall():
            devnames_list.append(elem[1])
        print('devname_list', devnames_list)

        for key in chans:
            chan_list.append(key)

        for dname in devnames_list:
            name = dname.split('.')[-1]
            print(name, names)
            if name in names:
                for chan_type in chan_list:
                    print(dname + '.' + chan_type)
                    if devtype == 'UM4':
                        chan = cda.DChan(dname + '.' + chan_type)
                    elif devtype == 'ring_bpm_preproc':
                        chan = cda.VChan(dname + '.' + chan_type, max_nelems=16)
                    else:
                        print('unknown devtype: ', devtype)
                        break
                    chans[chan_type][name] = chan
                    values[chan_type][name] = None
                    chan.valueMeasured.connect(functools.partial(self.chan_val_change, chan, values))
        print(chans)
        return values, chans

    @staticmethod
    def chan_val_change(chan, values):
        print(chan.val)
        values[chan.name.split('.')[-1]][chan.name.split('.')[-2]] = chan.val

    def checking_equality(self, val_dict, call_ok, call_err):
        print('check')
        if abs(val_dict['Iset'] - val_dict['Imes']) < 100:
            call_ok()
        else:
            call_err('check_eq')

    @staticmethod
    def err_verification(val_dict, call_ok, call_err):
        print('recheck')
        if abs(val_dict['Iset'] - val_dict['Imes']) < 100:
            call_ok()
        else:
            call_err('verif')


if __name__ == "__main__":
    app = QApplication(['BasicFunc'])
    w = BasicFunc()
    sys.exit(app.exec_())
