#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import functools
import numpy as np

from basic_module import BasicFunc


class ResponseMatrixAssembling(BasicFunc):
    def __init__(self, corr_names=None, bpm_names=None):
        super(ResponseMatrixAssembling, self).__init__()
        # self.corr_names = ['c1d2_z', 'c1f2_x', 'c1f1_x', 'c1d1_z', 'c2d2_z', 'c2f2_x', 'c2f1_x', 'c2d1_z', 'c3d2_z',
        #                    'c3f2_x', 'c3f1_x', 'c3d1_z', 'c4d2_z', 'c4f2_x', 'c4f1_x', 'c4d1_z', 'crm1', 'crm2', 'crm3',
        #                    'crm4', 'crm5', 'crm6', 'crm7', 'crm8', 'c4f3_x', 'c3f3_x', 'c4d3_z', 'c3d3_z', 'c1d1_q',
        #                    'c1f1_q', 'c1d2_q', 'c1f2_q', 'c1d3_q', 'c1f4_q', 'c1f3_q', 'c2f4_q', 'c2d1_q', 'c2f1_q',
        #                    'c2d2_q', 'c2f2_q', 'c2d3_q', 'c3f4_q', 'c2f3_q', 'c4f4_q', 'c3d1_q', 'c3f1_q', 'c3d2_q',
        #                    'c3f2_q', 'c3d3_q', 'c4d3_q', 'c3f3_q', 'c4d1_q', 'c4f1_q', 'c4d2_q', 'c4f2_q',
        #                    'c4f3_q']
        self.corr_names = ['crm3', 'crm5']
        self.bpm_names = ['bpm_preproc']
        self.corr_err = []
        self.flag = False
        self.init_corr_values = {}
        self.orbit_resp_data = np.zeros([15, ])
        self.orbit_changes_data = np.zeros([15, ])

        self.counter = {'c_val': -19, 'c_name': 0}  # -4 to make symmetrical interval -4..4
        self.stop = {'c_val': 20, 'c_name': len(self.corr_names)}
        self.step = 20
        self.c_name = self.corr_names[self.counter['c_name']]

        self.corr_values, self.corr_chans = self.chans_connect({'Iset': {}, 'Imes': {}}, {'Iset': {}, 'Imes': {}},
                                                               self.corr_names, 'UM4')
        self.bpm_values, self.bpm_chans = self.chans_connect({'x_orbit': {}}, {'x_orbit': {}}, self.bpm_names,
                                                             'ring_bpm_preproc')
        print(self.bpm_values, self.bpm_chans)

    def bpm_data_proc(self):
        # go to next step
        self.orbit_resp_data = np.vstack(self.orbit_resp_data, self.bpm_values)
        self.resp_matr_ass_proc()

    def resp_matr_ass_proc(self):
        if not self.flag:
            self.init_corr_values = self.corr_values['Iset'].copy()
            self.flag = True
        print(self.corr_values)

        if not len(self.checking_equality(self.corr_values, self.corr_err)):
            if self.counter['c_val'] != self.stop['c_val']:
                print(self.c_name, self.counter['c_val'])
                self.corr_chans['Iset'][self.c_name].setValue(self.init_corr_values[self.c_name]
                                                              + self.counter['c_val'] * self.step)
                self.counter['c_val'] += 1
                QTimer.singleShot(3000, self.bpm_data_proc)

            else:
                self.corr_chans['Iset'][self.c_name].setValue(self.init_corr_values[self.c_name])
                self.counter['c_name'] += 1
                self.save_corr_resp()
                if self.counter['c_name'] != self.stop['c_name']:
                    self.c_name = self.corr_names[self.counter['c_name']]
                    self.counter['c_val'] = -19
                    self.resp_matr_ass_proc()
                else:
                    self.save_rma()
        else:
            QTimer.singleShot(3000, functools.partial(self.err_verification, self.corr_values, self.corr_err,
                                                      [ResponseMatrixAssembling, 'bpm_data_proc'],
                                                      'f_stop_chan', 'rma'))

    def save_corr_resp(self):
        for i in range(self.orbit_resp_data[:, 0] - 2):
            self.orbit_changes_data = np.vstack(self.orbit_changes_data, self.orbit_resp_data[i + 1] -
                                                self.orbit_resp_data[i + 2])
            
        np.savetxt(self.c_name + '.txt', self.orbit_changes_data,
                   header=(self.c_name + '|' + str(self.init_corr_values['Imes'][self.c_name]) + '19'))

        self.orbit_resp_data = np.zeros([15, ])
        self.orbit_changes_data = np.zeros([15, ])

    def save_rma(self):
        print('rma collecting finished')
        # self.del_chan.setValue('rma': 'file_name')  # +json.dumps


if __name__ == "__main__":
    app = QApplication(['ResponseMatrixAssembling'])
    w = ResponseMatrixAssembling()
    sys.exit(app.exec_())
