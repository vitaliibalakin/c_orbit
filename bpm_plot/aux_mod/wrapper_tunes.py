#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
import sys

import pyqtgraph as pg


class Converter:
    def __init__(self):
        super(Converter, self).__init__()

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
