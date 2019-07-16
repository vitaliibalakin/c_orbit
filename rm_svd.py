#!/usr/bin/env python3

import sys
import numpy as np
import pyqtgraph as pg
from scipy import optimize
from PyQt5.QtWidgets import QApplication


class SVD:
    def __init__(self):
        super(SVD, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        data = np.loadtxt('cooked_rm/rm_x.txt')
        u, s, vh = np.linalg.svd(data)
        plt = pg.plot()
        # plt.setRange(yRange=[0, 1000])
        plt.showGrid(x=True, y=True)
        plt.addLegend(offset=(0, 100))

        plt.plot(s, pen=None, symbol='o', name='singular values')
        # sys.exit()


if __name__ == "__main__":
    app = QApplication(['FFT'])
    w = SVD()
    sys.exit(app.exec_())
