#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
import pycx4.qcda as cda

MagnetLines = {
    'Pinjection' : ['K1','K2','1L0','c1L0x','1L1','c1L1z','1M4','1L2','1M2',
'1L3','c1L3z','1L4','c1L4z','1L5','1M3','1L6','1M4','1L7','c1L7z','1L8','c1L8x',
'1L9','1L10','1M5','1M6','1L11','c1L11x','1M7','SM1'],
    'Einjection' : ['K1','K3','2L1','c2L1z','2L2','c2L2x','2L3','c2L3z','2L4','c2L4x',
'2M1','2M3','2L5','c2L5x','2M3','2Cx','SM2'],
    'Ring' : ['Q3F3','c3F3','Q3D3','c3D3','Q3D2','c3D2','Q3F2','c3F2',
'RM5','SY1_3F4','SX1_3F4','Q3F4','c3F4z','SX2_3F4','SY2_3F4','RM6',
'Q3F1','c3F1','Q3D1','c3D1','Q4D1','c4D1','Q4F1','c4F1','RM7','SY1_4F4','SX1_4F4',
'Q4F4','c4F4z','SX2_4F4','SY2_4F4','RM8','Q4F2','c4F2','Q4D2','c4D2','Q4D3','c4D3','Q4F3','c4F3',
'Q1F3','c1F3','Q1D3','c1D3','Q1D2','c1D2','Q1F2','c1F2','RM1','SY1_1F4','SX1_1F4',
'Q1F4','c1F4z','SX2_1F4','SY2_1F4','RM2',
'Q1F1','c1F1','Q1D1','c1D1','Q2D1','c2D1','Q2F1','c2F1','RM3','SY1_2F4','SX1_2F4','Q2F4','c2F4z',
'SX2_2F4','SY2_2F4','RM4','Q2F2','c2F2','Q2D2','c2D2','Q2D3','c2D3','Q2F3','c2F3'],
    'Pextraction' : ['SM1','c4C1x','4M1','4L1','4L2','4M2','4M3','4L3','4L4','c4L4z',
'4M4','4L5','4M5','4L6','4L7','c4L7x',
'3L6p','3L7p','c3L7zp'],
    'Eextraction' : ['SM2','3M1','3L1','3L2','3M2','c3C2x','3M3','3L3','3L4','c3L4x',
'3M4','3L5','3M5','3L6e','3L7e','c3L7ze']
}
# dict [0,1,2,3]: name: type, power sources, polarity, direction
MagnetType = {
  'K1': ['korr',['11.Cor1'],'plus'],
  'K2' : ['korr',['11.Cor2n3'],'plus'],
  'K3' : ['korr',['11.Cor2n3'],'plus'],
  '1L0' : ['quad60',['12.q1l0'],'plus'],
  '1L1' : ['quad60',['12.q1l1'],'minus'],
  '1M1' : ['bm45inj',['11.d1m','12.rst2.c1M1']],
  '1L2' : ['quad60',['12.q1l2n6'],'plus'],
  '1M2' : ['bm45inj',['11.d1m','12.rst2.c1M2']],
  '1L3' : ['quad60',['12.q1l3n5'],'minus'],
  '1L4' : ['quad60q',['12.q1l4n8','12.rst2.c1L4_Q'],'plus'],
  '1L5' : ['quad60',['12.q1l3n5'],'minus'],
  '1M3' : ['bm45inj',['11.d1m','12.rst2.c1M3']],
  '1L6' : ['quad60',['12.q1l2n6'],'plus'],
  '1M4' : ['bm45inj',['11.d1m','12.rst2.c1M4']],
  '1L7' : ['quad60q',['12.q1l7n9','12.rst2.c1L7_Q'],'minus'],
  '1L8' : ['quad60',['12.q1l4n8'],'plus'],
  '1L9' : ['quad60',['12.q1l7n9'],'minus'],
  '1L10' : ['quad60',['12.q1l10'],'plus'],
  '1M5' : ['bm20inj',['12.d1m5t7','12.rst2.c1M5']],
  '1M6' : ['bm20inj',['12.d1m5t7','12.rst2.c1M6']],
  '1L11' : ['quad60',['12.q1l11'],'plus'],
  '1M7' : ['bm20inj',['12.d1m5t7','12.rst2.c1M7']],
  'SM1' : ['septum',['12.dsm','12.rst4.cSM1'],'plus'],
  'c1L0x' : ['dcorr60',['12.rst2.c1L0_x'],'plus','H'],
  'c1L1z' : ['dcorr60',['12.rst2.c1L1_z'],'plus','V'],
  'c1L3z' : ['dcorr60',['12.rst2.c1L3_z'],'plus','V'],
  'c1L4z' : ['dcorr60',['12.rst2.c1L4_x'],'plus','V'],
  'c1L7z' : ['dcorr60',['12.rst2.c1L7_x'],'plus','V'],
  'c1L8x' : ['dcorr60',['12.rst2.c1L8_z'],'plus','H'],
  'c1L11x': ['dcorr60',['12.rst2.c1L11_x'],'plus','H'],
  '2L1' : ['quad60',['12.q2l1'],'plus'],
  '2L2' : ['quad60',['12.q2l2'],'minus'],
  '2L3' : ['quad60',['12.q2l3'],'plus'],
  '2L4' : ['quad60',['12.q2l4'],'minus'],
  '2M1' : ['bm20inj',['12.d1m5t7','12.rst2.c2M1']],
  '2M2' : ['bm20inj',['12.d1m5t7','12.rst2.c2M2']],
  '2L5' : ['quad60',['12.q2l5'],'plus'],
  '2M3' : ['bm20inj',['12.d1m5t7','12.rst2.c2M3']],
  '2Cx' : ['corr',['12.c2C_x'],'minus'],
  'SM2' : ['septum',['12.dsm','12.rst4.cSM2'],'plus'],
  'c2L1z' : ['dcorr60',['12.rst2.c2L1_z'],'plus','V'],
  'c2L2x' : ['dcorr60',['12.rst2.c2L2_x'],'plus','H'],
  'c2L3z' : ['dcorr60',['12.rst2.c2L3_z'],'plus','V'],
  'c2L4x' : ['dcorr60',['12.rst2.c2L4_x'],'plus','H'],
  'c2L5x' : ['dcorr60',['12.rst2.c2L5_x'],'plus','H'],
  'RM1_d' : ['ringmag_d',['12.drm','12.rst2.cRM1']],
  'RM2_d' : ['ringmag_d',['12.drm','12.rst2.cRM2']],
  'RM3_d' : ['ringmag_d',['12.drm','12.rst2.cRM3']],
  'RM4_d' : ['ringmag_d',['12.drm','12.rst2.cRM4']],
  'RM5_d' : ['ringmag_d',['12.drm','12.rst2.cRM5']],
  'RM6_d' : ['ringmag_d',['12.drm','12.rst2.cRM6']],
  'RM7_d' : ['ringmag_d',['12.drm','12.rst2.cRM7']],
  'RM8_d' : ['ringmag_d',['12.drm','12.rst2.cRM8']],
  'RM1_q' : ['ringmag_q',['12.drm','12.rst2.cRM1']],
  'RM2_q' : ['ringmag_q',['12.drm','12.rst2.cRM2']],
  'RM3_q' : ['ringmag_q',['12.drm','12.rst2.cRM3']],
  'RM4_q' : ['ringmag_q',['12.drm','12.rst2.cRM4']],
  'RM5_q' : ['ringmag_q',['12.drm','12.rst2.cRM5']],
  'RM6_q' : ['ringmag_q',['12.drm','12.rst2.cRM6']],
  'RM7_q' : ['ringmag_q',['12.drm','12.rst2.cRM7']],
  'RM8_q' : ['ringmag_q',['12.drm','12.rst2.cRM8']],
  'Q1D1' : ['quad60q',['12.qd1','12.rst3.c1D1_Q'],'minus'],
  'Q1F1' : ['quad60q',['12.qf1n2','12.rst3.c1F1_Q'],'plus'],
  'Q1F4' : ['quad60q',['12.qf4','12.rst3.c1F4_Q'],'plus'],
  'Q1F2' : ['quad60q',['12.qf1n2','12.rst3.c1F2_Q'],'plus'],
  'Q1D2' : ['quad80q',['12.qd2','12.rst3.c1D2_Q'],'minus'],
  'Q1D3' : ['quad80q',['12.qd3','12.rst3.c1D3_Q'],'minus'],
  'Q1F3' : ['quad80q',['12.qf3','12.rst3.c1F3_Q'],'plus'],
  'SY2_1F4' : ['sext',['12.rst3.Sy2_1F4']],
  'SX2_1F4' : ['sext',['12.rst3.Sx2_1F4']],
  'SX1_1F4' : ['sext',['12.rst3.Sx1_1F4']],
  'SY1_1F4' : ['sext',['12.rst3.Sy1_1F4']],
  'c1D1' : ['dcorr60',['12.rst2.c1D1_z'],'plus','V'],
  'c1F1' : ['dcorr60',['12.rst2.c1F1_x'],'plus','H'],
  'c1F4z' : ['dcorr60',['12.rst4.c1F4_z'],'minus','V'],
  'c1F2' : ['dcorr60',['12.rst2.c1F2_x'],'plus','H'],
  'c1D2' : ['dcorr80',['12.rst2.c1D2_z'],'plus','V'],
  'c1D3' : ['dcorr80',['12.rst4.c1D3_z'],'plus','V'],
  'c1F3' : ['dcorr80',['12.rst4.c1F3_x'],'plus','H'],
  'Q2D1' : ['quad60q',['12.qd1','12.rst3.c2D1_Q'],'minus'],
  'Q2F1' : ['quad60q',['12.qf1n2','12.rst3.c2F1_Q'],'plus'],
  'Q2F4' : ['quad60q',['12.qf4','12.rst3.c2F4_Q'],'plus'],
  'Q2F2' : ['quad60q',['12.qf1n2','12.rst3.c2F2_Q'],'plus'],
  'Q2D2' : ['quad80q',['12.qd2','12.rst3.c2D2_Q'],'minus'],
  'Q2D3' : ['quad80q',['12.qd3','12.rst3.c2D3_Q'],'minus'],
  'Q2F3' : ['quad80q',['12.qf3','12.rst3.c2F3_Q'],'plus'],
  'SY2_2F4' : ['sext',['12.rst3.Sy2_2F4']],
  'SX2_2F4' : ['sext',['12.rst3.Sx2_2F4']],
  'SX1_2F4' : ['sext',['12.rst3.Sx1_2F4']],
  'SY1_2F4' : ['sext',['12.rst3.Sy1_2F4']],
  'c2D1' : ['dcorr60',['12.rst2.c2D1_z'],'plus','V'],
  'c2F1' : ['dcorr60',['12.rst2.c2F1_x'],'plus','H'],
  'c2F4z' : ['dcorr60',['12.rst4.c2F4_z'],'plus','V'],
  'c2F2' : ['dcorr60',['12.rst2.c2F2_x'],'plus','H'],
  'c2D2' : ['dcorr80',['12.rst2.c2D2_z'],'plus','V'],
  'c2D3' : ['dcorr80',['12.rst4.c2D3_z'],'plus','V'],
  'c2F3' : ['dcorr80',['12.rst4.c2F3_x'],'plus','H'],
  'Q3D1' : ['quad60q',['12.qd1','12.rst3.c3D1_Q'],'minus'],
  'Q3F1' : ['quad60q',['12.qf1n2','12.rst3.c3F1_Q'],'plus'],
  'Q3F4' : ['quad60q',['12.qf4','12.rst3.c3F4_Q'],'plus'],
  'Q3F2' : ['quad60q',['12.qf1n2','12.rst3.c3F2_Q'],'plus'],
  'Q3D2' : ['quad80q',['12.qd2','12.rst3.c3D2_Q'],'minus'],
  'Q3D3' : ['quad80q',['12.qd3','12.rst3.c3D3_Q'],'minus'],
  'Q3F3' : ['quad80q',['12.qf3','12.rst3.c3F3_Q'],'plus'],
  'SY2_3F4' : ['sext',['12.rst3.Sy2_3F4']],
  'SX2_3F4' : ['sext',['12.rst3.Sx2_3F4']],
  'SX1_3F4' : ['sext',['12.rst3.Sx1_3F4']],
  'SY1_3F4' : ['sext',['12.rst3.Sy1_3F4']],
  'c3D1' : ['dcorr60',['12.rst2.c3D1_z'],'plus','V'],
  'c3F1' : ['dcorr60',['12.rst2.c3F1_x'],'plus','H'],
  'c3F4z' : ['dcorr60',['12.rst4.c3F4_z'],'plus','V'],
  'c3F2' : ['dcorr60',['12.rst2.c3F2_x'],'plus','H'],
  'c3D2' : ['dcorr80',['12.rst2.c3D2_z'],'plus','V'],
  'c3D3' : ['dcorr80',['12.rst3.c3D3_z'],'plus','V'],
  'c3F3' : ['dcorr80',['12.rst3.c3F3_x'],'plus','H'],
  'Q4D1' : ['quad60q',['12.qd1','12.rst3.c4D1_Q'],'minus'],
  'Q4F1' : ['quad60q',['12.qf1n2','12.rst3.c4F1_Q'],'plus'],
  'Q4F4' : ['quad60q',['12.qf4','12.rst3.c4F4_Q'],'plus'],
  'Q4F2' : ['quad60q',['12.qf1n2','12.rst3.c4F2_Q'],'plus'],
  'Q4D2' : ['quad80q',['12.qd2','12.rst3.c4D2_Q'],'minus'],
  'Q4D3' : ['quad80q',['12.qd3','12.rst3.c4D3_Q'],'minus'],
  'Q4F3' : ['quad80q',['12.qf3','12.rst3.c4F3_Q'],'plus'],
  'SY2_4F4' : ['sext',['12.rst3.Sy2_4F4']],
  'SX2_4F4' : ['sext',['12.rst3.Sx2_4F4']],
  'SX1_4F4' : ['sext',['12.rst3.Sx1_4F4']],
  'SY1_4F4' : ['sext',['12.rst3.Sy1_4F4']],
  'c4D1' : ['dcorr60',['12.rst2.c4D1_z'],'plus','V'],
  'c4F1' : ['dcorr60',['12.rst2.c4F1_x'],'plus','H'],
  'c4F4z' : ['dcorr60',['12.rst4.c4F4_z'],'plus','V'],
  'c4F2' : ['dcorr60',['12.rst2.c4F2_x'],'plus','H'],
  'c4D2' : ['dcorr80',['12.rst2.c4D2_z'],'plus','V'],
  'c4D3' : ['dcorr80',['12.rst3.c4D3_z'],'plus','V'],
  'c4F3' : ['dcorr80',['12.rst3.c4F3_x'],'plus','H'],
  'c4C1x'  : ['corr',['12.rst4.c4C1_x'],'plus','H'],
  '4M1' : ['bm20ext',['12.d4m1t3','12.rst4.c4M1']],
  '4L1' : ['quad20',['12.rst4.q4l1'],'plus'],
  '4L2' : ['quad20',['12.rst4.q4l2'],'plus'],
  '4M2' : ['bm20ext',['12.d4m1t3','12.rst4.c4M2']],
  '4M3' : ['bm20ext',['12.d4m1t3','12.rst4.c4M3']],
  '4L3' : ['quad20',['12.rst4.q4l3'],'plus'],
  '4L4' : ['quad20',['12.rst4.q4l4'],'plus'],
  '4M4' : ['bm20ext',['12.d4m4t5','12.rst4.c4M4']],
  '4L5' : ['quad20',['12.rst4.q4l5'],'plus'],
  '4M5' : ['bm20ext',['12.d4m4t5','12.rst4.c4M5']],
  '4L6' : ['quad20',['12.rst4.q4l6'],'plus'],
  '4L7' : ['quad20',['12.rst4.q4l7'],'plus'],
  'c4L4z' : ['dcorr20',['12.rst4.c4l4_z'],'plus'],
  'c4L7x' : ['dcorr20',['12.rst4.c4l7_x'],'minus'],
  '3L6p' : ['quad20',['12.rst4.q3l6'],'plus'],
  '3L7p' : ['quad20',['12.rst4.q3l7'],'plus'],
  'c3L7zp' : ['dcorr20',['12.rst4.c3l7_z'],'plus'],
  '3M1' : ['bm20ext',['12.d3m1t3','12.rst4.c3M1']],
  '3L1' : ['quad20',['12.rst4.q4l1'],'minus'],
  '3L2' : ['quad20',['12.rst4.q4l2'],'minus'],
  '3M2' : ['bm20ext',['12.d3m1t3','12.rst4.c3M2']],
  '3M3' : ['bm20ext',['12.d3m1t3','12.rst4.c3M3']],
  '3L3' : ['quad20',['12.rst4.q3l3'],'minus'],
  '3L4' : ['quad20',['12.rst4.q3l4'],'minus'],
  '3M4' : ['bm20ext',['12.d3m4t5','12.rst4.c3M4']],
  '3L5' : ['quad20',['12.rst4.q3l5'],'minus'],
  '3M5' : ['bm20ext',['12.d3m4t5','12.rst4.c3M5']],
  '3L6e' : ['quad20',['12.rst4.q3l6'],'minus'],
  '3L7e' : ['quad20',['12.rst4.q3l7'],'minus'],
  'c3C2x'  : ['corr',['12.rst4.c3C2_x'],'plus'],
  'c3L4x' : ['dcorr20',['12.rst4.c3l4_x'],'plus'],
  'c3L7ze' : ['dcorr20',['12.rst4.c3l7_z'],'minus']
}

AmperTurns = {
  'quad60q' : 1.5,
  'quad80q' : 1.36,
  'quad60c' : 5.0,
  'quad80c' : 5.45,
  'ringmag' : 6.67,
  'bm20inj'  : 1.1477,
  'bm45inj'  : 1.208,
  'bm20ext'  : 1.065,
  'bm45ext'  : 1.02
}

Rbends = {
  'ringmag' : 1.12,
  'bm20inj'  : 1.118,
  'bm45inj'  : 1.118,
  'bm20ext'  : 1.118,
  'bm45ext'  : 1.118,
  'sept'     : 2.334,
  'corr'     : 6.3
}


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
        """
        :param currents: main current, then corrector current
        :return: the value of the field
        """
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
        """
        :param currents: main current, then corrector current
        :return: the value of the field
        """
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
        """
        :param currents: main current, then corrector current
        :return: the value of the field
        """
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
        """
        :param currents: main current, then corrector current
        :return: the value of the field
        """
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
