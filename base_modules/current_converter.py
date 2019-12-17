#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
from magnetline_settings import MagnetType
import pycx4.qcda as cda


class CurrentConverter:
    def __init__(self):
        super(CurrentConverter, self).__init__()

        self.i_k = 0
        self.magnet_type = MagnetType
        self.current_to_field_correspondence = {'ringmag_d': self.i_2_field_rm_dip,
                                                'ringmag_q': self.i_2_field_rm_quad,
                                                'dcorr60': self.i_2_field_du60_cor_dip,
                                                'quad80q': self.i_2_field_du80_cor_dip}
        self.field_to_current_correspondence = {'ringmag_d': self.field_2_i_rm_dip,
                                                'dcorr60': self.field_2_i_du60_cor_dip,
                                                'quad80q': self.field_2_i_du80_cor_quad}

    def current_to_field(self, name, *currents):
        return self.current_to_field_correspondence[self.magnet_type[name][0]](currents)

    def field_to_current(self, name, field):
        return self.field_to_current_correspondence[self.magnet_type[name][0]](field)

    # CURRENT ---> FIELD
    @staticmethod
    def i_2_field_rm_dip(*currents):
        try:
            i_main = currents[0]
            i_cor = currents[1]
            i = i_cor / 1000 * 6.67 + i_main
            return -1138.9178 + 28.600754 * i + 0.04490153 * i**2 + 7.80301344e-5 * i**3 - 6.16697411e-8 * i**4 + \
                   1.69725511e-11 * i**5
        except Exception as exc:
            print(exc)

    @staticmethod
    def i_2_field_rm_quad(*currents):
        try:
            i_main = currents[0]
            i_cor = currents[1]
            i = i_cor / 1000 * 6.67 + i_main
            return 100.981701 - 1.47689856 * i + 0.0039728 * i**2 - 7.0629494e-6 * i**3 + 5.79274578e-9 * i**4 - \
                   1.71765978e-12 * i**5
        except Exception as exc:
            print(exc)

    @staticmethod
    def i_2_field_du60(*currents):
        try:
            i_main = currents[0]
            i_cor = currents[1]
            i = i_cor / 1000 * 1.5 + i_main
            return 16.83524125 + 2.832126125 * i - 0.0015659738 * i**2 + 2.84666125e-6 * i**3 - 1.83259875e-9 * i**4 + \
                   1.19244899875e-13 * i**5
        except Exception as exc:
            print(exc)

    @staticmethod
    def i_2_field_du80(*currents):
        try:
            i_main = currents[0]
            i_cor = currents[1]
            i = i_cor / 1000 * 1.36 + i_main
            return 13.38814 + 1.5170534 * i + 1.1680249e-3 * i**2 - 2.84518241e-6 * i**3 + 3.0909805e-9 * i**4 - \
                   1.2364183e-12 * i**5
        except Exception as exc:
            print(exc)

    @staticmethod
    def i_2_field_du60_cor_dip(*currents):
        i = currents[0] / 1000
        return 1.678 + 23.2841 * i - 0.0204779 * i ** 2

    @staticmethod
    def i_2_field_du80_cor_dip(*currents):
        i = currents[0] / 1000
        return 28.26716075 * i

    # FIELD ---> CURRENT
    @staticmethod
    def field_2_i_rm_dip(h):
        return 3.5967 + 6.430321e-2 * h - 2.122935e-06 * h**2 + 4.017689e-10 * h**3 - 3.317581e-14 * h**4 + \
               1.007860e-18 * h**5

    @staticmethod
    def field_2_i_du60(k):
        g = k
        return -28.57485 + 5.968237e-1 * g - 4.765216e-04 * g**2 + 5.002541e-7 * g**3 - 2.359256e-10 * g**4 + \
               4.106625e-14 * g**5

    @staticmethod
    def field_2_i_du60_cor_dip(h):
        return 0.12249 + 0.04503 * h - 3.826e-6 * h**2

    @staticmethod
    def field_2_i_du80(k):
        g = k
        return -12.33317 + 6.954716e-1 * g - 3.771475e-4 * g**2 + 5.303944e-7 * g**3 - 3.323782e-10 * g**4 + \
               7.646799e-14 * g**5

    @staticmethod
    def field_2_i_du80_cor_quad(h):
        return 0.03537674 * h


if __name__ == "__main__":
    app = QApplication(['CurConv'])
    w = CurrentConverter()
    sys.exit(app.exec_())
