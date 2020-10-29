from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import pycx4.qcda as cda
import json
import sys


class InjTune(QMainWindow):
    def __init__(self):
        super(InjTune, self).__init__()

        self.chan_ring_current = cda.DChan('cxhw:0.dcct.beamcurrent')
        self.chan_ring_current.valueMeasured.connect(self.ring_current_changed)
        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=1)
        self.chan_tunes.valueMeasured.connect(self.tunes_changed)
        self.chan_f3 = cda.DChan('cxhw:12.qf3.Tset')
        self.chan_f3.valueMeasured.connect(self.i_f3_changed)
        self.chan_d3 = cda.DChan('cxhw:12.qd3.Tset')
        self.chan_d3.valueMeasured.connect(self.i_d3_changed)
        self.ring_cur_data = {}
        self.cur_tunes = [0.0, 0.0]
        self.tunes_flag = False
        self.cur_flag = False
        self.counter = 0
        self.i_f3 = 0
        self.i_d3 = 0
        #############################
        self.shift_x = [4.459, 1.422]
        self.shift_y = [0.647, 2.002]
        self.n_iter = 3
        self.cur_x_it = 0
        self.cur_y_it = 0

        QTimer.singleShot(6000, self.start)

    def start(self):
        # n*x tune shift
        self.chan_f3.setValue(self.i_f3 - self.n_iter * self.shift_x[0])
        self.chan_d3.setValue(self.i_d3 - self.n_iter * self.shift_x[1])
        # n*y tune shift
        self.chan_f3.setValue(self.i_f3 + self.n_iter * self.shift_y[0])
        self.chan_d3.setValue(self.i_d3 + self.n_iter * self.shift_y[1])
        self.cur_x_it = -3
        self.cur_y_it = -3
        QTimer.singleShot(4000, self.set_tune_flag_true)

    def i_f3_changed(self, chan):
        self.i_f3 = chan.val

    def i_d3_changed(self, chan):
        self.i_d3 = chan.val

    def ring_current_changed(self, chan):
        if self.counter >= 22:
            self.counter = 0
            self.cur_flag = False
            self.tune_shift()
        else:
            if self.cur_flag:
                self.counter += 1
                self.ring_cur_data[json.dumps(self.cur_tunes)].append(chan.val)
                print(self.counter, self.ring_cur_data)

    def tunes_changed(self, chan):
        if self.tunes_flag:
            self.cur_tunes[0] = chan.val[0]
            self.cur_tunes[1] = chan.val[1]
            self.ring_cur_data[json.dumps(self.cur_tunes)] = []
            self.cur_flag = True
            self.tunes_flag = False

    def tune_shift(self):
        self.make_shift()
        QTimer.singleShot(4000, self.set_tune_flag_true)

    def make_shift(self):
        if self.cur_x_it == 3:
            if self.cur_y_it == 3:
                # end
                pass
            else:
                # y tune shift
                self.chan_f3.setValue(self.i_f3 - self.shift_y[0])
                self.chan_d3.setValue(self.i_d3 - self.shift_y[1])
                self.cur_y_it += 1
                # 2*n*x tune shift
                self.chan_f3.setValue(self.i_f3 - 2 * self.n_iter * self.shift_x[0])
                self.chan_d3.setValue(self.i_d3 - 2 * self.n_iter * self.shift_x[1])
                self.cur_x_it = -3
        else:
            # x tune shift
            self.chan_f3.setValue(self.i_f3 + self.shift_x[0])
            self.chan_d3.setValue(self.i_d3 + self.shift_x[1])
            self.cur_x_it += 1

    def set_tune_flag_true(self):
        print('true')
        self.tunes_flag = True


if __name__ == "__main__":
    app = QApplication(['inj_tune'])
    w = InjTune()
    sys.exit(app.exec_())
