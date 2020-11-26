#!/usr/bin/env python3
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox


class RMSpinBox(QDoubleSpinBox):
    def __init__(self, init_val, iter_r, low_limit=-10000):
        super(RMSpinBox, self).__init__()
        self.setDecimals(3)
        self.setMaximum(10000)
        self.setValue(init_val)
        self.setSingleStep(iter_r)
        self.setMinimum(low_limit)
