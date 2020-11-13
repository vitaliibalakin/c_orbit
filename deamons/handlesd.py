#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys

import numpy as np
import pycx4.qcda as cda
import json
import os
import re
import datetime
from aux.service_daemon import CXService


class HandlesProc:
    def __init__(self):
        super(HandlesProc, self).__init__()
        self.cmd_table = {
            'add_handle': self.add_handle_, 'load_handle': self.load_handle_, 'delete_handle': self.delete_handle_,
            'edit_item': self.edit_item_, 'start_inj_cur': self.start_inj_cur_,
            'step_up': self.step_up_, 'cst_step_up': self.cst_step_up_,
            'step_down': self.step_down_, 'cst_step_down': self.cst_step_down_
        }

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)

    #########################################################
    #                     command part                      #
    #########################################################

    def cmd(self, chan):
        cmd = chan.val
        if cmd:
            chan_val = json.loads(cmd)
            command = chan_val.get('cmd', 'no_cmd')
            self.cmd_table[command](**chan_val)

    def add_handle_(self, **kwargs):
        pass

    def load_handle_(self, **kwargs):
        pass

    def delete_handle_(self, **kwargs):
        pass

    def edit_item_(self):
        pass

    def start_inj_cur_(self, **kwargs):
        pass

    def step_up_(self, **kwargs):
        pass

    def step_down_(self, **kwargs):
        pass

    def cst_step_up_(self, **kwargs):
        pass

    def cst_step_down_(self, **kwargs):
        pass


# class KMService(CXService):
#     def main(self):
#         print('run main')
#         self.w = HandlesProc()
#
#     def clean(self):
#         self.log_str('exiting handles_proc')
#
#
# bp = KMService("handlesd")

if __name__ == "__main__":
    app = QApplication(['handles_proc'])
    w = HandlesProc()
    sys.exit(app.exec_())
