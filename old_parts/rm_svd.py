#!/usr/bin/env python3

import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication


class SVD:
    def __init__(self):
        super(SVD, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        data = np.loadtxt('cooked_rm/rm_z_q.txt')
        u, s, vh = np.linalg.svd(data)
        plt = pg.plot()
        # plt.setRange(yRange=[0, 1000])
        plt.showGrid(x=True, y=True)
        plt.addLegend(offset=(0, 100))
        plt.setLogMode(False, True)
        plt.plot(s, pen=None, symbol='o', name='singular values')
        # sys.exit()
        print('u', u.shape)
        print('s', s.shape)
        print('vh', vh.shape)
        s_r = np.zeros((vh.shape[0], u.shape[0]))
        s_r[:min(vh.shape[0], u.shape[0]), :min(vh.shape[0], u.shape[0])] = np.diag(1/s)
        m = np.dot(np.transpose(vh), np.dot(s_r, np.transpose(u)))
        print(m)


if __name__ == "__main__":
    app = QApplication(['FFT'])
    w = SVD()
    sys.exit(app.exec_())
