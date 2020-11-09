#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
import sys
import numpy as np
import pandas as pd
import subprocess
from io import StringIO

import pyqtgraph as pg


class Converter:
    def __init__(self):
        super(Converter, self).__init__()

    def sdds_to_pandas(self, *colnames, file='BeamLine.mag'):
        try:
            cmd_str = self.names_parser(colnames)
            out = subprocess.Popen(['sdds2stream', file, cmd_str, '-pipe=out'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = out.communicate()
            output = stdout.decode('utf-8').splitlines()
            data = StringIO("\n".join(output))
            data_frame = pd.read_csv(data, names=colnames, delim_whitespace=True)
            # data_frame.to_csv('mag_pd.txt')
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

    @staticmethod
    def names_parser(names):
        cmd_str = '-col='
        for elem in names:
            cmd_str = cmd_str + elem + ','
        return cmd_str[:-1]

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
        self.l_type = kwargs.get('l_type', 'res_diag')
        a = pg.TextItem('a')

        if self.l_type == 'res_diag':
            self.point_obj_res()
        else:
            self.point_obj_s()

    def point_obj_res(self):
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

    def point_obj_s(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setPen(QtGui.QPen(self.color, 0.3))
        p.drawLines([QtCore.QLineF(QtCore.QPointF(self.lines_coor[0][0], self.lines_coor[0][1]),
                                   QtCore.QPointF(self.lines_coor[1][0], self.lines_coor[1][1]))])
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class PyQtElemPlot(pg.GraphicsObject):
    def __init__(self, beg, end, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.colors = {'QUAD_F': QtCore.Qt.blue, 'QUAD_D': QtCore.Qt.blue, 'KSBEND': QtCore.Qt.green,
                       'RFCA': QtCore.Qt.red}
        self.coors = {'QUAD_F': [4, 0], 'QUAD_D': [0, -4], 'KSBEND': [2, -2], 'RFCA': [2, -2]}

        self.anchor = kwargs.get('anchor', 0)
        self.c_type = kwargs.get('c_type', 'KSBEND')
        self.point_obj(beg, end, self.c_type)

    def point_obj(self, beg, end, c_type):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(self.colors[c_type])
        coors = self.coors[c_type]
        points = [QtCore.QPointF(beg, coors[0] + self.anchor), QtCore.QPointF(end, coors[0] + self.anchor),
                  QtCore.QPointF(end, coors[0] + self.anchor), QtCore.QPointF(end, coors[1] + self.anchor),
                  QtCore.QPointF(end, coors[1] + self.anchor), QtCore.QPointF(beg, coors[1] + self.anchor),
                  QtCore.QPointF(beg, coors[1] + self.anchor), QtCore.QPointF(beg, coors[0] + self.anchor)]
        poly = QtGui.QPolygonF(points)
        p.drawPolygon(poly)
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


class TextLabel(pg.GraphicsObject):
    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 1)
        self.text = kwargs.get('text', 'UN')
        self.anchor = kwargs.get('anchor', 0)
        self.pos = kwargs.get('pos', 0)
        self.point_text()

    def point_text(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        rect = QtCore.QRectF(self.pos * 10 - 4, -self.anchor, 8, 8)
        tr = QtGui.QTransform()
        tr.setMatrix(tr.m11(), tr.m12(), tr.m13(), tr.m21(), -1, tr.m23(), tr.m31(), tr.m32(), tr.m33())
        tr.scale(0.1, 1)
        p.setTransform(tr)
        p.setFont(QtGui.QFont("Helvetica", 3))
        p.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        p.drawText(rect, self.text)
        p.end()

    def update_pos(self, y_pos):
        self.setPos(0, y_pos)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


if __name__ == "__main__":
    app = QApplication(['eltools'])
    w = Converter()
    sys.exit(app.exec_())
