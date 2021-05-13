from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
import pycx4.qcda as cda
import sys

class TestChan:
    def __init__(self):
        super(TestChan, self).__init__()
        self.win = uic.loadUi('/home/vbalakin/PycharmProjects/c_orbit/uis/test_chans.ui')
        self.win.show()
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)

        self.win.pushButton.clicked.connect(self.send_info)

    def send_info(self):
        self.chan_cmd.setValue('DO')

if __name__ == "__main__":
    app = QApplication(['xd'])
    w = TestChan()
    sys.exit(app.exec_())
