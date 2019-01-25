#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda


class Magnetization:
    """
    make DR correctors magnetization process
    q - quadrupole, d - dipole
    type - type of correction (*q* or *d*)
    """
    def __init__(self, corr_list=0):
        super(Magnetization, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except Exception as err:
            print("No access to DB", err)

        # self.del_chan = cda.StrChan('del_chan')
        self.corr_chans = {'Iset': {}, 'Imes': {}}
        self.corr_values = {'Iset': {}, 'Imes': {}}
        self.init_corr_vals = {}
        self.devnames_list = []
        self.corr_err = []

        self.mag_flag = False
        self.counter = 0
        self.stop_mag = 5

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
                           'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q', 'c4f3_q'] # = corr_list
        self.chan_list = ['Iset', 'Imes']

        for dname in self.devnames_list:
            name = dname.split('.')[-1]
            if name in self.corr_names:
                for chan_type in self.chan_list:
                    chan = cda.DChan(dname + '.' + chan_type)
                    self.corr_chans[chan_type][name] = chan
                    self.corr_values[chan_type][name] = 0
                    chan.valueMeasured.connect(self.ps_val_change)
        print(self.corr_values)
        QTimer.singleShot(3000, self.mag_proc)

    def mag_proc(self):
        """
        function make magnetization. Check each step, if ok, calls next step nor emergency_check
        """
        if not self.mag_flag:
            self.init_corr_vals = self.corr_values['Iset'].copy()
            self.mag_flag = True

        for set_key in self.corr_values['Iset']:
            if abs(self.corr_values['Iset'][set_key] - self.corr_values['Imes'][set_key]) < 100:
                if set_key in self.corr_err:
                    self.corr_err.remove(set_key)
            else:
                self.corr_err.append(set_key)
        if not len(self.corr_err):
            if self.counter != self.stop_mag:
                # make next step
                # for c_name in self.corr_chans:
                #     self.corr_chans['Iset'][c_name].setValue(self.corr_values[c_name] + 1000 * (-1)**step)
                self.counter += 1
                QTimer.singleShot(3000, self.mag_proc)
                print(self.counter)
            else:
                # stop magnetization process
                # for c_name in self.corr_chans:
                #     self.corr_chans['Iset'][c_name].setValue(self.init_corr_vals[c_name])
                print('Magnetization finished')
                self.mag_flag = False
                # self.del_chan.setValue("mag")
        else:
            QTimer.singleShot(3000, self.emergency_check)

    def emergency_check(self):
        """
        make emergency ps status check, if the first was 'fail'
        :return: ps status
        """
        for set_key in self.corr_values['Iset']:
            if abs(self.corr_values['Iset'][set_key] - self.corr_values['Imes'][set_key]) < 100:
                if set_key in self.corr_err:
                    self.corr_err.remove(set_key)
        if not len(self.corr_err):
            QTimer.singleShot(3000, self.mag_proc)
        else:
            print('error', self.corr_err)

    def ps_val_change(self, chan):
        """
        function update chans value
        :param chan: called function chan
        :return: new value dict
        """
        self.corr_values[chan.name.split('.')[-1]][chan.name.split('.')[-2]] = chan.val


if __name__ == "__main__":
    app = QApplication(['MAGNETIZATION'])
    w = Magnetization()
    sys.exit(app.exec_())
