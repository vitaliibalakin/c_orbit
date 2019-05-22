#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import functools as ftl
import sys
import pycx4.qcda as cda

from basic_module import BasicFunc


class Magnetization(BasicFunc):
    def __init__(self, corr_names=0):
        super(Magnetization, self).__init__()
        self.init_corr_values = {}

        self.flag = False
        self.counter = 0
        self.stop_mag = 5
        # self.corr_names = ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z', 'c3d2_z',
        #                    'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1', 'crm2', 'crm3',
        #                    'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z', 'c3d3_z', 'c1d1_q',
        #                    'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q', 'c2d1_q', 'c2f1_q',
        #                    'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q', 'c3d1_q', 'c3f1_q', 'c3d2_q',
        #                    'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q',
        #                    'c4f3_q']
        self.corr_err = []
        self.corr_names = ['crm5', 'crm3']

        self.corr_values, self.corr_chans = self.chans_connect({'Iset': {}, 'Imes': {}}, {'Iset': {}, 'Imes': {}},
                                                               self.corr_names, 'UM4')

        # QTimer.singleShot(3000, self.mag_proc)

    def mag_proc(self):
        if not self.flag:
            self.init_corr_values = self.corr_values['Iset'].copy()
            self.flag = True
        print(self.corr_values)

        if not len(self.checking_equality(self.corr_values, self.corr_err)):
            if self.counter != self.stop_mag:
                # make next step
                # for c_name, c_val in self.init_corr_values.items():
                #     self.corr_chans['Iset'][c_name].setValue(c_val + 1000 * (-1)**self.counter)
                self.counter += 1
                QTimer.singleShot(3000, self.mag_proc)
                print(self.counter)
            else:
                # stop magnetization process
                for c_name, c_chan in self.corr_chans['Iset'].items():
                    c_chan.setValue(self.init_corr_values[c_name])
                print('Magnetization finished')
                # self.del_chan.setValue('mag': 0)  # +json.dumps
        else:
            # I don't know correctly err_verification will call back mag_proc or not. Checking is required
            QTimer.singleShot(3000, ftl.partial(self.err_verification, self.corr_err, [Magnetization, 'mag_proc'],
                              'f_stop_chan', 'mag'))


if __name__ == "__main__":
    app = QApplication(['MAGNETIZATION'])
    w = Magnetization()
    sys.exit(app.exec_())
