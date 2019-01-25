#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
import psycopg2
import functools
import pycx4.qcda as cda

from magnetization import Magnetization
from resp_matrix_asseml import ResponseMatrixAssembling


class MainCorrectionControl:
    """
    main correction control script
    """
    def __init__(self):
        super(MainCorrectionControl, self).__init__()
        # self.del_chan = cda.StrChan('del_chan')
        self.modules_run = {}
        self.modules_dict = {'mag': Magnetization, 'rma': ResponseMatrixAssembling}
        self.modules_func = {'mag': 'mag_proc', 'rma': 'resp_matr_ass_proc'}
        self.run_module('mag')

        # self.del_chan.valueMeasured.connect(self.modules_del)

    def modules_del(self, chan):
        """
        delete the executable module after it's finishing
        :return: updated modules_run dict
        """
        if chan.val in self.modules_run:
            self.modules_run.pop(chan.val)

    def run_module(self, module):
        """
        run chosen module
        :return:
        """
        print('imhere')
        self.modules_run[module] = getattr(self.modules_dict[module](), self.modules_func[module])


if __name__ == "__main__":
    app = QApplication(['MainCorrectionControl'])
    w = MainCorrectionControl()
    sys.exit(app.exec_())
