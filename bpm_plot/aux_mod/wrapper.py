#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
import sys
import numpy as np
import math
from scipy import interpolate
import pandas as pd
import subprocess
from io import StringIO

import holoviews as hv
from bokeh.models import HoverTool

import pyqtgraph as pg


class Converter:
    def __init__(self):
        super(Converter, self).__init__()

    def sdds_to_pandas(self, *colnames, file='results/beamline.mag'):
        try:
            cmd_str = self._names_parser(colnames)
            out = subprocess.Popen(['sdds2stream', file, cmd_str, '-pipe=out'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = out.communicate()
            output = stdout.decode('utf-8').splitlines()
            data = StringIO("\n".join(output))
            data_frame = pd.read_csv(data, names=colnames, delim_whitespace=True)

            return data_frame
        except Exception as exp:
            print(exp)
            return None

    def sdds_par(self, file='results/twiss.twi', par='nux'):
        out = subprocess.Popen(['sdds2stream', file, '-par=' + par],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        return float(stdout)

    def acc_view(self, file='results/xyz.sdds'):
        try:
            df_xyz = self.sdds_to_pandas(*['ElementName', 's', 'X', 'Y', 'Z', 'theta'], file=file)
            theta = interpolate.interp1d(df_xyz.s.values, df_xyz.theta.values, fill_value=(0, 0), bounds_error=False)
            x0 = interpolate.interp1d(df_xyz.s.values, df_xyz.X.values, fill_value=(0, 0), bounds_error=False)
            z0 = interpolate.interp1d(df_xyz.s.values, df_xyz.Z.values, fill_value=(0, 0), bounds_error=False)

            data_frame = self.sdds_to_pandas('ElementName', 's', 'Profile')
            s = data_frame.s.values
            nx = np.cos(theta(s))
            nz = -np.sin(theta(s))
            element_width = 0.5  # m
            data_frame['X'] = x0(s) + element_width * data_frame['Profile'] * nx
            data_frame['Z'] = z0(s) + element_width * data_frame['Profile'] * nz
            return data_frame
        except Exception as exp:
            print(exp)
            return None

    @staticmethod
    def res_diag(order=3):
        # [nux_b, nuy_b, nux_e, nuy_e]
        lines_coor = []
        # add vertical and horizontal lines
        for i in range(1, order):
            lines_coor.append([(0.0, i / order), (1.0, i / order)])
            lines_coor.append([(i / order, 0.0), (i / order, 1.0)])
        # add other lines
        for n in range(0, order + 1):
            for i in range(1, order):
                nu_b = n / (order - i)
                nu_e = (n - i) / (order - i)
                if 0 <= nu_b <= 1:
                    if 0 <= nu_e <= 1:
                        lines_coor.append([(0.0, nu_b), (1.0, nu_e)])
                        lines_coor.append([(nu_b, 0.0), (nu_e, 1.0)])
                    elif nu_e < 0:
                        lines_coor.append([(0.0, nu_b), (n / i, 0.0)])
                        lines_coor.append([(1.0 - nu_b, 1.0), (1.0, 1.0 - n / i)])

        for n in range(0, order + 1):
            for i in range(1, order):
                nu_b = n / (order - i)
                nu_e = (n + i) / (order - i)
                if 0 <= nu_b <= 1:
                    if 0 <= nu_e <= 1:
                        lines_coor.append([(0.0, nu_b), (1.0, nu_e)])
                        lines_coor.append([(nu_b, 0.0), (nu_e, 1.0)])
                    elif nu_e > 1:
                        lines_coor.append([(0.0, nu_b), (-1 * (n - order + i) / i, 1.0)])
                        lines_coor.append([(nu_b, 0.0), (1.0, -1 * (n - order + i) / i)])
        return lines_coor

    #####################
    # class system part #
    #####################

    @staticmethod
    def _names_parser(names):
        cmd_str = '-col='
        for elem in names:
            cmd_str = cmd_str + elem + ','
        return cmd_str[:-1]


class HvGraphics:
    def __init__(self, extension='bokeh'):
        super(HvGraphics, self).__init__()
        hv.extension(extension)

    def plot_structure(self, to_plot):
        if isinstance(to_plot, pd.DataFrame):
            return self._plot_stru(to_plot)
        if isinstance(to_plot, str):
            data_frame = Converter().sdds_to_pandas(*['ElementName', 's', 'Profile'], file=to_plot)
            return self._plot_stru(data_frame)

    def plot_function(self, to_plot, func='betax', color='red', label='βx'):
        if isinstance(to_plot, pd.DataFrame):
            return self._plot_func(to_plot, func, color, label)
        elif isinstance(to_plot, str):
            data_frame = Converter().sdds_to_pandas(*['ElementName', 's', func], file=to_plot)
            return self._plot_func(data_frame, func, color, label)

    def acc_view_plot(self, to_plot):
        if isinstance(to_plot, pd.DataFrame):
            return self._view_plot(to_plot)
        if isinstance(to_plot, str):
            data_frame = Converter().sdds_to_pandas(file=to_plot)
            return self._view_plot(data_frame)

    @staticmethod
    def tunes(bet_x, bet_y):
        bet_x -= math.floor(bet_x)
        bet_y -= math.floor(bet_y)
        color = '#30d5c8'
        path = hv.Path([[(bet_x-0.05, bet_y), (bet_x+0.05, bet_y)], [(bet_x, bet_y-0.05), (bet_x, bet_y+0.05)]])
        path.opts(color=color, line_width=4)
        return path

    @staticmethod
    def res_diag(points_list, color='red'):
        x = hv.Dimension('ν_x', range=(0, 1))
        y = hv.Dimension('ν_y', range=(0, 1))
        path = hv.Path(points_list, [x, y])
        path.opts(width=700, height=700, color=color, line_width=1)
        return path

    #####################
    # class system part #
    #####################

    @staticmethod
    def _plot_stru(data_frame):
        dim_s = hv.Dimension('s', unit='m', label="s")
        # data = getattr(data_frame, 'Profile')
        hover = HoverTool(tooltips="@ElementName")
        mag = hv.Curve(data_frame, kdims=dim_s, vdims=['Profile', 'ElementName'], group='mag')
        mag.opts(width=700, height=70, show_frame=False, show_title=False, xaxis=None, yaxis=None, show_grid=True,
                 tools=['box_zoom', 'pan', 'wheel_zoom', 'reset', hover], color='black', alpha=0.3)
        return mag

    @staticmethod
    def _plot_func(data_frame, func, color, label):
        dim_s = hv.Dimension('s', unit='m', label="s")
        data = getattr(data_frame, func)
        dim_y = hv.Dimension(func, unit='m', label=label, range=(0, 1.1 * max(data)))
        curve = hv.Curve((data_frame.s, data), label=label, kdims=dim_s, vdims=dim_y)
        curve.opts(color=color, alpha=0.7, line_width=3, width=700, height=300, show_grid=True,
                   tools=['box_zoom', 'pan', 'wheel_zoom', 'reset'])
        return curve

    @staticmethod
    def _view_plot(data_frame):
        dim_x = hv.Dimension('X', label='X', unit='m')
        dim_z = hv.Dimension('Z', label='Z', unit='m', range=(-32, +32))
        curve = hv.Curve((data_frame.Z, data_frame.X), kdims=dim_z, vdims=dim_x)
        curve.opts(width=700, height=400, show_frame=False, show_title=False, xaxis=None, yaxis=None,
                   show_grid=True, tools=['box_zoom', 'pan', 'wheel_zoom', 'reset'], color='blue', alpha=0.3)
        return curve

################################
# tools for pyqtgraph plotting #
################################


class LinesPlot(pg.GraphicsObject):
    def __init__(self, lines_coor, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.lines_coor = lines_coor
        self.order = kwargs.get('order', 3)
        self.color = kwargs.get('color', QtCore.Qt.darkCyan)
        self.point_obj()

    def point_obj(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setPen(QtGui.QPen(self.color, 0.005 / self.order))
        lines = [QtCore.QLineF(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1)),
                 QtCore.QLineF(QtCore.QPointF(0, 0), QtCore.QPointF(1, 0)),
                 QtCore.QLineF(QtCore.QPointF(1, 1), QtCore.QPointF(0, 1)),
                 QtCore.QLineF(QtCore.QPointF(1, 1), QtCore.QPointF(1, 0))]
        for line_coor in self.lines_coor:
            lines.append(QtCore.QLineF(QtCore.QPointF(line_coor[0][0], line_coor[0][1]),
                                       QtCore.QPointF(line_coor[1][0], line_coor[1][1])))
        p.drawLines(lines)
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class TunesMarker(pg.GraphicsObject):
    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.color = kwargs.get('color', QtCore.Qt.red)
        self.point_obj()

    def point_obj(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setPen(QtGui.QPen(self.color, 0.0075, QtCore.Qt.SolidLine))
        lines = [
            QtCore.QLineF(QtCore.QPointF(self.x - 0.015, self.y - 0.015),
                          QtCore.QPointF(self.x + 0.015, self.y + 0.015)),
            QtCore.QLineF(QtCore.QPointF(self.x + 0.015, self.y - 0.015),
                          QtCore.QPointF(self.x - 0.015, self.y + 0.015))
        ]
        p.drawLines(lines)
        p.end()

    def update_pos(self, pos):
        self.setPos(pos[0], pos[1])

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


if __name__ == "__main__":
    app = QApplication(['eltools'])
    w = Converter()
    sys.exit(app.exec_())
