from PyQt5.QtWidgets import QApplication
import sys
from PyQt5.QtCore import QTimer

import pycx4.qcda as cda
import numpy as np


class Test:
    def __init__(self):
        super(Test, self).__init__()
        self.data = np.linspace(1, 100, 100)
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)
        self.chan_fft.valueMeasured.connect(self.chan_callback)
        QTimer.singleShot(3000, self.chan_write)

    def chan_write(self):
        print('write')
        self.chan_fft.setValue(self.data)
        QTimer.singleShot(3000, self.chan_write)

    def chan_callback(self, chan):
        print(chan.val)


if __name__ == "__main__":
    app = QApplication(['c_orbit'])
    w = Test()
    sys.exit(app.exec_())
