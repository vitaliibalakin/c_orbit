#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
import sys
import pyqtgraph as pg


class BPMMarker(pg.GraphicsObject):
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
        # p.setFont(QtGui.QFont('Arial', 1))
        # p.drawText(QtCore.QPointF(0, 0), 'kek')
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        p.setBrush(self.color)
        p.setPen(QtCore.Qt.NoPen)
        points = [
            QtCore.QPointF(self.x - 0.5, self.y),
            QtCore.QPointF(self.x - 0.5, self.y + 2),
            QtCore.QPointF(self.x - 0.25, self.y + 0.5),
            QtCore.QPointF(self.x + 0.25, self.y + 0.5),
            QtCore.QPointF(self.x + 0.5, self.y + 2),
            QtCore.QPointF(self.x + 0.5, self.y - 2),
            QtCore.QPointF(self.x + 0.25, self.y - 0.5),
            QtCore.QPointF(self.x - 0.25, self.y - 0.5),
            QtCore.QPointF(self.x - 0.5, self.y - 2),
            QtCore.QPointF(self.x - 0.5, self.y)]
        poly = QtGui.QPolygonF(points)
        p.drawPolygon(poly)
        p.end()

    def update_pos(self, y_pos):
        self.setPos(0, y_pos)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


if __name__ == "__main__":
    app = QApplication(['bpm_point'])
    w = BPMMarker()
    sys.exit(app.exec_())
