import pycx4.qcda as cda
import sys
from PyQt5.QtWidgets import QApplication


class SofaTest:
    def __init__(self):
        super(SofaTest, self).__init__()
        self.value = 0
        self.chan = cda.VChan("canhw:12.drm.Imes")
        self.chan2 = cda.VChan("canhw:12.dsm.Imes")
        self.chan2.valueMeasured.connect(self.callback)
        self.chan.valueMeasured.connect(self.callback)

    def callback(self, chan):
        print(self.value)
        print(chan.val, chan.name)


app = QApplication(['sofa_test'])
w = SofaTest()
sys.exit(app.exec_())
