#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda


class MAGNETIZATION:
    """
    make DR correctors magnetization process
    q - quadrupole, d - dipole
    type - type of correction (*q* or *d*)
    """
    def __init__(self):
        super(MAGNETIZATION, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except:
            print("No access to DB")

        # self.command_chan = cda.StrChan('command_chan')
        self.corr_chans = {'q': {}, 'd': {}}
        self.corr_values = {'q': {}, 'd': {}}
        self.devnames_list = []

        self.type = ''
        self.mag_flag = False

        self.cur = self.conn.cursor()
        self.cur.execute(
            "select devtype.name, namesys.name || '.' || dev.name as full_name from dev,dev_devtype,devtype, namesys "
            "where dev.id=dev_devtype.dev_id and devtype.id=dev_devtype.devtype_id and namesys.id=dev.namesys_id and "
            "devtype.name in ('UM4') group by grouping sets((devtype.name, full_name))")
        for elem in self.cur.fetchall():
            self.devnames_list.append(elem[1])
        print('devname_dict', self.devnames_list)

        self.corr_names = {'d': ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z',
                                 'c3d2_z', 'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1',
                                 'crm2', 'crm3', 'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z',
                                 'c3d3_z'],
                           'q': ['c1d1_q', 'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q',
                                 'c2d1_q', 'c2f1_q', 'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q',
                                 'c3d1_q', 'c3f1_q', 'c3d2_q', 'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q',
                                 'c4f1_q', 'c4d2_q', 'c4f2_q', 'c4f3_q']}

        for dname in self.devnames_list:
            name = dname.split('.')[-1]
            if name in self.corr_names['d']:
                chan = cda.DChan(dname + '.Iset')
                self.corr_chans['d'][chan.name] = chan
                self.corr_values['d'][chan.name] = 0
            elif name in self.corr_names['q']:
                chan = cda.DChan(dname + '.Iset')
                self.corr_chans['q'][chan.name] = chan
                self.corr_values['q'][chan.name] = 0
        print(self.corr_values)

        #self.command_chan.valueChanged.connect(self.mag_proc)
        self.mag_proc()

    def mag_proc(self, chan=0):
        """
        function make magnetization
        :param chan: command chan
        """
        # self.type = chan.name
        self.mag_flag = True
        self.mag_step(10)

    def mag_step(self, stop_val, step=0):
        """
        function make one single step
        :param step: number of step
        :param stop_val: stop value
        :return: single magnetization step
        """
        if step != stop_val:
            for c_name in self.corr_chans[self.type]:
                self.corr_chans[self.type][c_name].setValue(self.corr_values[self.type][c_name] + 100 * (-1)**step)
            QTimer.singleShot(1000, functools.partial(self.mag_step, stop_val=stop_val, step=step+1))
            print(step)
        else:
            for c_name in self.corr_chans[self.type]:
                self.corr_chans[self.type][c_name].setValue(self.corr_values[self.type][c_name])
            print('Magnetization finished')
            self.mag_flag = False

    def ps_val_change(self, chan):
        """
        function update chans value
        :param chan: called function chan
        :return: new value dict
        """
        if not self.mag_flag:
            try:
                self.corr_values['d'][chan.name] = chan.val
            except KeyError:
                self.corr_values['q'][chan.name] = chan.val


if __name__ == "__main__":
    app = QApplication(['MAGNETIZATION'])
    w = MAGNETIZATION()
    sys.exit(app.exec_())
