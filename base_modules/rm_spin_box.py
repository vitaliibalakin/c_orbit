#!/usr/bin/env python3
from PyQt5.QtWidgets import QSpinBox


class RMSpinBox(QSpinBox):
    def __init__(self, init_val, iter_r):
        super(RMSpinBox, self).__init__()
        self.setMaximum(10000)
        self.setValue(init_val)
        self.setSingleStep(iter_r)
        self.setMinimum(-10000)
