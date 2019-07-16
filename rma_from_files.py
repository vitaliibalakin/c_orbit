#!/usr/bin/env python3\

import sys
import numpy as np
from scipy import optimize
from PyQt5.QtWidgets import QApplication


class RMAFromFile:
    def __init__(self):
        super(RMAFromFile, self).__init__()
        self.bpms = ['bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11', 'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16',
                     'bpm01', 'bpm02', 'bpm03', 'bpm04']
        # self.cor_names = ['rst2.c1d2_z', 'rst2.c1f2_x', 'rst2.c1f1_x', 'rst2.c1d1_z', 'rst2.c2d2_z', 'rst2.c2f2_x',
        #                   'rst2.c2f1_x', 'rst2.c2d1_z', 'rst2.c3d2_z', 'rst2.c3f2_x', 'rst2.c3f1_x', 'rst2.c3d1_z',
        #                   'rst2.c4d2_z', 'rst2.c4f2_x', 'rst2.c4f1_x', 'rst2.c4d1_z',
        #                   'rst2.crm1', 'rst2.crm2', 'rst2.crm3', 'rst2.crm4', 'rst2.crm5', 'rst2.crm6', 'rst2.crm7',
        #                   'rst2.crm8',
        #                   'rst3.c3d3_z', 'rst3.c3f3_x', 'rst3.c4d3_z', 'rst3.c4f3_x', 'rst4.c1f4_z', 'rst4.c1d3_z',
        #                   'rst4.c1f3_x', 'rst4.c2f4_z', 'rst4.c2d3_z', 'rst4.c2f3_x', 'rst4.c3f4_z', 'rst4.c4f4_z']
        self.cor_names = ['rst3.c1d1_q', 'rst3.c1f1_q', 'rst3.c1d2_q', 'rst3.c1f2_q', 'rst3.c1d3_q', 'rst3.c1f4_q',
                          'rst3.c1f3_q', 'rst3.c2f4_q', 'rst3.c2d1_q', 'rst3.c2f1_q', 'rst3.c2d2_q', 'rst3.c2f2_q',
                          'rst3.c2d3_q', 'rst3.c3f4_q', 'rst3.c2f3_q', 'rst3.c4f4_q', 'rst3.c3d1_q', 'rst3.c3f1_q',
                          'rst3.c3d2_q', 'rst3.c3f2_q', 'rst3.c3d3_q', 'rst3.c4d3_q', 'rst3.c3f3_q', 'rst3.c4d1_q',
                          'rst3.c4f1_q', 'rst3.c4d2_q', 'rst3.c4f2_q', 'rst3.c4f3_q']
        self.buffer_x = np.zeros([len(self.bpms), len(self.cor_names)])
        self.buffer_z = np.zeros([len(self.bpms), len(self.cor_names)])
        j = 0
        for name in self.cor_names:
            resp_data = np.loadtxt('rma/positron/' + name + '.txt', skiprows=1)
            cur = np.arange(-100 * 5, 100 * (5 + 1), 100)
            mid = int(len(resp_data[0]) / 2)
            for i in range(mid):
                const, pcov = optimize.curve_fit(self.lin_fit, cur, resp_data[:, i])
                self.buffer_x[i, j] = const[0]

            for i in range(mid, len(resp_data[0]), 1):
                const, pcov = optimize.curve_fit(self.lin_fit, cur, resp_data[:, i])
                self.buffer_z[i-mid, j] = const[0]
            j += 1
        np.savetxt('rm_x_q.txt', self.buffer_x)
        np.savetxt('rm_z_q.txt', self.buffer_z)
        sys.exit()

    @staticmethod
    def lin_fit(x, a, c):
        return a * x + c


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = RMAFromFile()
    sys.exit(app.exec_())
