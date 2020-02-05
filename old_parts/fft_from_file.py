#!/usr/bin/env python3

import sys
import numpy as np
import pyqtgraph as pg
from scipy import optimize
from PyQt5.QtWidgets import QApplication


class FFTFromFile:
    def __init__(self):
        super(FFTFromFile, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        data = np.loadtxt('fft/e_for_fft 2019-06-26 04:53:41')
        res = {}
        fft = {'x': np.fft.rfft(data[0], len(data[0])), 'z': np.fft.rfft(data[1], len(data[1]))}
        # freq = np.fft.rfftfreq(len(data[0]), 91.5e-9)
        freq = np.fft.rfftfreq(len(data[0]), 1)
        for coor, val in fft.items():
            res[coor] = np.sqrt(val.real ** 2 + val.imag ** 2)

        plt = pg.plot()
        plt.setRange(yRange=[0, 1000])
        plt.showGrid(x=True, y=True)
        plt.addLegend()
        label_style = {'font-size': '20pt'}
        # plt.setLabel('bottom', units='V', **label_style)
        plt.plot(freq, res['z'], pen=pg.mkPen('b', width=2), name='z fft')
        plt.plot(freq, res['x'], pen=pg.mkPen('r', width=2), name='x fft')

        # sys.exit()


if __name__ == "__main__":
    app = QApplication(['FFT'])
    w = FFTFromFile()
    sys.exit(app.exec_())
