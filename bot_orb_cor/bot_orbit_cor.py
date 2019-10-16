#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication

import sys
import numpy as np
import pycx4.qcda as cda
import json


class BotOrbitCor:
    def __init__(self):
        super(BotOrbitCor, self).__init__()

    @staticmethod
    def make_orbit_cor(d, rev_rm, cor_names):
        chans_list = []
        log = {}
        d_i = np.dot(rev_rm, d)

        for cor_name in cor_names:
            cor_chan = cda.DChan('canhw:12.' + cor_name + '.Iset')
            chans_list.append(cor_chan)

        for i in range(len(d_i) - 1):
            chans_list[i].setValue(d_i[i] / 100)
            log[chans_list[i].name] = d_i[i] / 100

        f = open('last_log', 'w')
        f.write(json.dumps(log))
        f.close()


if __name__ == "__main__":
    app = QApplication(['BOC'])
    w = BotOrbitCor()
    sys.exit(app.exec_())
