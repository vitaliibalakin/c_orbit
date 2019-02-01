#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import functools
import sys
import pycx4.qcda as cda


class Test:
    """
    make DR correctors magnetization process
    q - quadrupole, d - dipole
    type - type of correction (*q* or *d*)
    """
    def __init__(self, corr_names=0):
        super(Test, self).__init__()
        print('test created')

    def test(self):
        print('test completed')


if __name__ == "__main__":
    app = QApplication(['test'])
    w = Test()
    sys.exit(app.exec_())
