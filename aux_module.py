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
        module with functions, which used more than one module. Module for sharing to others
        """

    def chans_connect(self, chans, values, names, devtype='UM4'):
        """
        function connects to needed channels and creates their callbacks
        :param chans: chans representation structure
        :param values: chans vals representation structure
        :param names: use these names to create channels connections
        :param devtype: devtype of chosen elems
        :return: dict of chans and their values
        """
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
        # print('devname_list', devnames_list)

        for key in chans:
            chan_list.append(key)
        print(chan_list)

        for dname in devnames_list:
            name = dname.split('.')[-1]
            if name in names:
                for chan_type in chan_list:
                    chan = cda.DChan(dname + '.' + chan_type)
                    chans[chan_type][name] = chan
                    values[chan_type][name] = 0
                    chan.valueMeasured.connect(functools.partial(self.chan_val_change, chan, values))
        print(chans)
        return values, chans

    @staticmethod
    def chan_val_change(chan, values):
        """
        function update chans value
        :param chan: called function chan
        :param values: dict of chans values
        :return: new values dict
        """
        values[chan.name.split('.')[-1]][chan.name.split('.')[-2]] = chan.val

    @staticmethod
    def checking_equality(values_dict, err):
        """
        check the equality of of values in values_dict
        :param values_dict: dict with *Iset* and *Imes* vals
        :param err: list with error's chans
        :return: error list
        """
        print('check')
        for key in values_dict['Iset']:
            if abs(values_dict['Iset'][key] - values_dict['Imes'][key]) < 100:
                if key in err:
                    err.remove(key)
            else:
                if not (key in err):
                    err.append(key)
        return err

    def err_verification(self, values_dict, err, call_func, chan, chan_val):
        """
        make emergency ps status check, if the first was 'fail'
        :param values_dict: dict with *Iset* and *Imes* vals
        :param err: list with error's chans
        :param call_func: it's function, which should be called, if no errors after verification
        :param chan: it's chan, where information sends if some errors exist. Actually stopped method, which called
        err_verification
        :param chan_val: value, which should be send into the chan
        """
        print('recheck')
        err = self.checking_equality(values_dict, err)
        if not err:
            getattr(call_func[0](), call_func[1])
        else:
            print('error', err)
            # chan.setValue(chan_val)


if __name__ == "__main__":
    app = QApplication(['Auxiliary'])
    w = Auxiliary()
    sys.exit(app.exec_())
