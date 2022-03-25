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
from bpm_base.aux_mod.wrapper_tunes import LinesPlot, TunesMarker, Converter
from c_orbit.config.orbit_config_parser import load_config_orbit


class TunesControl(QMainWindow):
    def __init__(self):
        super(TunesControl, self).__init__()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        path = os.getcwd()
        conf = re.sub('bpm_plot', 'config', path)
        direc = re.sub('bpm_plot', 'uis', path)
        uic.loadUi(direc + "/wp's.ui", self)
        self.setWindowTitle('Tunes Plot')
        self.show()

        self.ic_mode = ''
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

        soft_conf = load_config_orbit(conf + '/orbitd_conf.txt', path)
        chans_conf = soft_conf['chans_conf']

        for chan in ['tunes', 'cmd', 'res', 'control_tunes', 'modet']:
            if chan not in chans_conf:
                print(chan + ' is absent in orbitd_conf')
                sys.exit(app.exec_())

        self.chan_mode = cda.StrChan(**chans_conf['modet'])
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        self.chan_tunes = cda.VChan(**chans_conf['tunes'])
        self.chan_tunes.valueMeasured.connect(self.tunes_update)
        self.chan_ctrl_tunes = cda.StrChan(**chans_conf['control_tunes'])
        self.chan_ctrl_tunes.valueMeasured.connect(self.ctrl_tunes_update)
        self.chan_cmd = cda.StrChan(**chans_conf['cmd'])
        self.chan_res = cda.StrChan(**chans_conf['res'])
        self.chan_res.valueMeasured.connect(self.cmd_result)
        # put IC mode tunes into their place on res_diag
        self.chan_cmd.setValue((json.dumps({'cmd': 'start_tunes', 'client': 'tunes'})))

    def cmd_result(self, chan):
        if chan.val:
            client = json.loads(chan.val).get('client', 'no_client')
            if client == 'tunes':
                action = json.loads(chan.val).get('action')
                time_stamp = json.loads(chan.val).get('time_stamp')
                self.status_bar.showMessage(str(time_stamp) + ' ' + str(action))

    def mode_changed(self, chan):
        self.ic_mode = chan.val
        # self.ic_mode = 'p2v2'  # delete after tests
        try:
            for key in self.btn_dict:
                self.btn_dict[key].setStyleSheet("background-color:rgb(255, 255, 255);")
            self.btn_dict[self.ic_mode].setStyleSheet(self.colors[self.ic_mode])
        except KeyError:
            self.status_bar.showMessage('wrong IC mode channel value')

    def tunes_update(self, chan):
        tunes = chan.val
        if tunes.any():
            self.tunes['cur'].update_pos(tunes)
            self.lbl_dict['cur'].setText(str(round(tunes[0], 5)) + " | " + str(round(tunes[1], 5)))
        else:
            self.status_bar.showMessage('empty tunes channel data')

    def ctrl_tunes_update(self, chan):
        try:
            tunes_dict = json.loads(chan.val)
            for k, v in tunes_dict.items():
                self.tunes[k].update_pos(v)
                self.lbl_dict[k].setText(str(round(v[0], 3)) + " | " + str(round(v[1], 3)))
        except Exception as exc:
            self.status_bar.showMessage(str(exc))

    def load_file_(self):
        try:
            file_name = QFileDialog.getOpenFileName(parent=self, directory=os.getcwd() + '/saved_tunes',
                                                    filter='Text Files (*.txt)')[0]
            self.chan_cmd.setValue((json.dumps({'cmd': 'load_tunes', 'client': 'tunes', 'file_name': file_name,
                                                'mode': self.sender().text()})))
        except Exception as exc:
            self.status_bar.showMessage(str(exc))

    def save_file_(self):
        try:
            sv_file = QFileDialog.getSaveFileName(parent=self, directory=os.getcwd() + '/saved_tunes',
                                                  filter='Text Files (*.txt)')
            if sv_file:
                file_name = sv_file[0]
                file_name = re.sub('.txt', '', file_name)
                file_name = file_name + '.txt'
                self.chan_cmd.setValue((json.dumps({'cmd': 'save_tunes', 'client': 'tunes', 'file_name': file_name})))
        except Exception as exc:
            self.status_bar.showMessage(str(exc))


if __name__ == "__main__":
    app = QApplication(['tunes'])
    w = TunesControl()
    sys.exit(app.exec_())
