from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
import pycx4.qcda as cda
import sys

class TestChan:
    def __init__(self):
        super(TestChan, self).__init__()
        # self.win = uic.loadUi('/home/vbalakin/PycharmProjects/c_orbit/uis/test_chans.ui')
        # self.win.show()
        self.i = 0
        self.dict_chans = {}
        self.chans = {0: 'canhw:12.rst3.c1d1_q', 1: 'canhw:12.rst3.c1d1_q', 2: 'canhw:12.rst3.c1d2_q'}
        # self.win.pushButton.clicked.connect(self.create_chan)

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_cmd.valueMeasured.connect(self.create_chan)

    def create_chan(self, chan):
        print(chan.val)
        channel = cda.DChan(self.chans[self.i] + '.Iset', private=1)
        self.dict_chans[self.i] = channel
        self.dict_chans[self.i].valueMeasured.connect(self.connection_check)
        self.i += 1
        print('connection added')
        print(self.dict_chans)

    def connection_check(self, chan):
        print(chan.val)

if __name__ == "__main__":
    app = QApplication(['xc'])
    w = TestChan()
    sys.exit(app.exec_())
