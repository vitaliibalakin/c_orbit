#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication

import sys
import numpy as np
import pycx4.qcda as cda


class BotOrbitCor:
    def __init__(self):
        super(BotOrbitCor, self).__init__()

    def make_orbit_cor(self, d, rev_rm, cor_names):
        chans_list = []
        d_i = np.dot(rev_rm, d)

        for cor_name in cor_names:
            cor_chan = cda.DChan('canhw:12.' + cor_name + '.Iset')
            chans_list.append(cor_chan)

        for i in range(len(d_i) - 1):
            chans_list[i].setValue(d_i[i])


if __name__ == "__main__":
    app = QApplication(['BOC'])
    w = BotOrbitCor()
    sys.exit(app.exec_())
