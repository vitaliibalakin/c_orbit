#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5 import uic
from PyQt5 import QtCore, QtGui
import sys
import re
import pyqtgraph as pg
import os
import json
import numpy as np
import pycx4.qcda as cda

from bpm_plot.aux_mod.wrapper_tunes import LinesPlot, TunesMarker, Converter


class TunesControl(QMainWindow):
    def __init__(self):
        super(TunesControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        direc = os.getcwd()
        direc = re.sub('bpm_plot', 'uis', direc)
        uic.loadUi(direc + "/wp's.ui", self)
        self.setWindowTitle('Tunes Plot')
        self.show()

        self.mode = ''
        self.cur_tunes = np.zeros(2)
        self.dir = os.getcwd()

        self.tunes_plot = pg.PlotWidget()
        p = QVBoxLayout()
        self.wp_plot.setLayout(p)
        p.addWidget(self.tunes_plot)

        # res_diag tune properties set
        self.tunes_plot.setRange(yRange=[0, 1])
        self.tunes_plot.setRange(xRange=[0, 1])
        self.tunes_plot.addItem(LinesPlot(Converter.res_diag(4), order=4, color=QtGui.QColor('#852EBA')))
        self.tunes_plot.addItem(LinesPlot(Converter.res_diag(3), order=3, color=QtGui.QColor('#B5FBDD')))
        self.tunes_plot.addItem(LinesPlot(Converter.res_diag(2), order=2, color=QtGui.QColor('#FFA96B')))
        self.tunes_plot.addItem(LinesPlot(Converter.res_diag(1), order=1, color=QtCore.Qt.black))
        self.tunes = {'e2v4': TunesMarker(color=QtGui.QColor('#55ffff')),
                      'p2v4': TunesMarker(color=QtGui.QColor('#ff86ff')),
                      'e2v2': TunesMarker(color=QtGui.QColor('#75ff91')),
                      'p2v2': TunesMarker(color=QtGui.QColor('#ff6b6b')),
                      'cur': TunesMarker(color=QtGui.QColor('#808285'))}
        for t_type, tune_marker in self.tunes.items():
            self.tunes_plot.addItem(tune_marker)
        self.legend = pg.LegendItem()
        self.legend.setParentItem(self.tunes_plot.getPlotItem())

        self.btn_dict = {'e2v4': self.btn_sel_e2v4, 'p2v4': self.btn_sel_p2v4, 'e2v2': self.btn_sel_e2v2,
                         'p2v2': self.btn_sel_p2v2}
        for key, btn in self.btn_dict.items():
            btn.clicked.connect(self.load_file_)
        self.btn_save.clicked.connect(self.save_file_)
        self.colors = {'e2v4': 'background-color:#55ffff;', 'p2v4': 'background-color:#ff86ff;',
                       'e2v2': 'background-color:#75ff91;', 'p2v2': 'background-color:#ff6b6b;'}
        self.lbl_dict = {'e2v4': self.lbl_e2v4, 'p2v4': self.lbl_p2v4, 'e2v2': self.lbl_e2v2, 'p2v2': self.lbl_p2v2,
                         'cur': self.lbl_cur}

        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2, on_update=1)
        self.chan_tunes.valueMeasured.connect(self.tunes_update)
        # put IC mode tunes into their place on res_diag
        self.chan_cmd.setValue((json.dumps({'cmd': 'start_tunes', 'service': 'tunes'})))

    def mode_changed(self, chan):
        self.mode = chan.val
        for key in self.btn_dict:
            self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
        self.btn_dict[self.mode].setStyleSheet(self.colors[self.mode])

    def tunes_update(self, tunes):
        self.tunes[self.mode].update_pos(tunes)
        self.lbl_dict[self.mode].setText(str(round(tunes[0], 3)) + " | " + str(round(tunes[1], 3)))

    def load_file_(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_tunes',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue((json.dumps({'cmd': 'load_tunes', 'service': 'tunes', 'act': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(exc)

    def save_file_(self):
        try:
            sv_file = QFileDialog.getSaveFileName(parent=self, directory=os.getcwd() + '/saved_tunes',
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = sv_file[0]
                file_name = re.sub('.txt', '', file_name)
                file_name = file_name + '.txt'
                self.chan_cmd.setValue((json.dumps({'cmd': 'save_tunes', 'service': 'tunes', 'act': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(exc)


if __name__ == "__main__":
    app = QApplication(['tunes_ctrl'])
    w = TunesControl()
    sys.exit(app.exec_())
