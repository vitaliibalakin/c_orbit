#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPainter, QBrush, QRadialGradient
import sys
import pyqtgraph as pg


class BPMCircle(pg.GraphicsObject):
    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.color = kwargs.get('color', QtCore.Qt.darkCyan)
        self.point_obj()

    def point_obj(self):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setBrush(QBrush(QRadialGradient(QtCore.QPointF(self.x, self.y), 5)))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(self.x, self.y), 3, 3)
        p.end()

    def update_pos(self, x, y):
        self.setPos(x, y)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class BPMPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(BPMPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        self.setLabel('left', "Z", units='mm')
        self.setLabel('bottom', "X", units='mm')
        self.setRange(xRange=[-40, 40])
        self.setRange(yRange=[-40, 40])

        self.marker = BPMCircle(x=-3, y=5, color=QtCore.Qt.blue)
        self.addItem(self.marker)

    def update_pos(self, x, y):
        self.marker.update_pos(x, y)
