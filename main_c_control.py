#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda

import magnetization


class MainCorrectionControl:
    """
    main correction control script
    """
    def __init__(self):
        super(MainCorrectionControl, self).__init__()
        # self.del_chan = cda.StrChan('del_chan')
        self.modules_run = {}

        # self.del_chan.valueMeasured.connect(self.modules_del)

    def modules_del(self, chan):
        """
        delete the executable module after it's finishing
        :return: updated modules_run dict
        """
        if chan.val in self.modules_run:
            self.modules_run.pop(chan.val)


if __name__ == "__main__":
    app = QApplication(['MAGNETIZATION'])
    w = MainCorrectionControl()
    sys.exit(app.exec_())
