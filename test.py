#!/usr/bin/env python3

import pycx4.qcda as cda
import sys
from PyQt5.QtWidgets import QApplication


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.chan_bpm_vals = []
        self.bpm_val_renew = {'bpm01': 0, 'bpm02': 0, 'bpm03': 0, 'bpm04': 0, 'bpm05': 0, 'bpm07': 0, 'bpm08': 0,
                              'bpm09': 0, 'bpm10': 0, 'bpm11': 0, 'bpm12': 0, 'bpm13': 0, 'bpm14': 0, 'bpm15': 0,
                              'bpm16': 0}  # , 'bpm17': 0}
        print('start')
        for bpm, bpm_coor in self.bpm_val_renew.items():
            # bpm channels init
            chan = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
            chan.valueMeasured.connect(self.data_proc)
            self.chan_bpm_vals.append(chan)
        print(self.chan_bpm_vals)
        self.chan_z_orbit = cda.VChan('cxhw:4.bpm_preproc.z_orbit', max_nelems=16)
        self.chan_z_orbit.valueMeasured.connect(self.data_proc)

    def data_proc(self, chan):
        print(chan.val)


if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = BpmPreproc()
    sys.exit(app.exec_())
