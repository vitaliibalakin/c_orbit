#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

import sys
import functools
import pycx4.qcda as cda

from magnetization import Magnetization
from resp_matrix_asseml import ResponseMatrixAssembling
from test import Test


class MainCorrectionControl(QMainWindow):
    """
    main correction control script
    """
    def __init__(self):
        super(MainCorrectionControl, self).__init__()
        uic.loadUi("c_orbit_main.ui", self)
        # self.del_chan = cda.StrChan('del_chan')

        self.rma_file_name = None

        self.modules_run = {}
        self.modules_dict = {'mag': Magnetization, 'rma': ResponseMatrixAssembling, 'test': Test}
        self.modules_call = {'mag': 'mag_proc', 'rma': 'resp_matr_ass_proc', 'test': 'test'}
        self.module_del = {'mag': self.delete_mag, 'rma': self.delete_rma}
        # self.module_run('mag')

        # self.del_chan.valueMeasured.connect(self.module_finish)

    # factory pattern
    def module_finish(self, chan):
        """
        delete the executable module after it's finishing
        :return: nothing
        """
        k, sys_info = chan.val.items()  # +json.loads
        if k in self.modules_run:
            self.module_del[k](sys_info)

    def module_run(self, module):
        """
        run chosen module
        :return:
        """
        print('imhere')
        self.modules_run[module] = getattr(self.modules_dict[module](), self.modules_call[module])
        self.modules_run[module]()

    def delete_mag(self, sys_info):
        """
        delete *mag* module from *self.modules_run dict*
        :param sys_info: None
        """
        self.modules_run.pop('mag')

    def delete_rma(self, file_name):
        """
        give name of the file with the last response matrix for further operational and delete *rma* module from
        *self.modules_run* dict
        :param file_name: name of the file contains the last response matrix
        """
        self.rma_file_name = file_name
        self.modules_run.pop('rma')


if __name__ == "__main__":
    app = QApplication(['MainCorrectionControl'])
    w = MainCorrectionControl()
    w.show()
    sys.exit(app.exec_())
