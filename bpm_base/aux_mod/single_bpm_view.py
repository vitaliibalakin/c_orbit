#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPainter, QBrush, QRadialGradient, QPen, QColor
import sys
import pyqtgraph as pg
import pycx4.qcda as cda

class Cross(pg.GraphicsObject):
    def __init__(self, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = pg.QtGui.QPicture()
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.width = 2
        self.cross_widget()

    def cross_widget(self):
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QPen(pg.mkPen('#0f14a6'))
        pen.setWidth(self.width)
        p.setPen(pen)
        lines = [
            QtCore.QLineF(QtCore.QPointF(self.x - 3, self.y),
                          QtCore.QPointF(self.x + 3, self.y)),
            QtCore.QLineF(QtCore.QPointF(self.x, self.y - 3),
                          QtCore.QPointF(self.x, self.y + 3))
        ]
        p.drawLines(lines)
        p.end()

    def update_pos(self, x, y):
        self.setPos(x, y)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())

class AperPlot(pg.GraphicsObject):
    def __init__(self, xaper, zaper):
        pg.GraphicsObject.__init__(self)
        self.picture = pg.QtGui.QPicture()
        self.width = 2
        self.aper_widget(xaper, zaper)

    def aper_widget(self, xaper, zaper):
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QPen(pg.mkPen('#83848a'))
        pen.setWidth(self.width)
        p.setPen(pen)
        p.drawEllipse(QtCore.QPointF(0.0, 0.0), xaper, zaper)
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


class BPMCircle(pg.GraphicsObject):
    def __init__(self, xname, zname, **kwargs):
        pg.GraphicsObject.__init__(self)
        self.picture = pg.QtGui.QPicture()
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.color = kwargs.get('color', QtCore.Qt.darkCyan)

        self.chan_x = cda.DChan(name=xname)
        self.chan_x.valueMeasured.connect(self.new_x)
        self.chan_z = cda.DChan(name=zname)
        self.chan_z.valueMeasured.connect(self.new_z)

        self.point_obj()

    def point_obj(self):
        p = pg.QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        gradient = QRadialGradient(QtCore.QPointF(self.x, self.y), 5)
        gradient.setColorAt(0, QColor('#fc030b'))
        gradient.setColorAt(1, QColor('#9065e0'))
        p.setBrush(gradient)
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(self.x, self.y), 3, 3)
        p.end()

    def update_pos(self, x, y):
        self.setPos(x, y)

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())

    def new_x(self, chan):
        self.x = chan.val
        self.update_pos(self.x, self.y)

    def new_z(self, chan):
        self.y = chan.val
        self.update_pos(self.x, self.y)


class BPMPlot(pg.PlotWidget):
    def __init__(self, parent, xname, zname, xaper=30, zaper=30):
        super().__init__(parent=parent)
        self.showGrid(x=True, y=True)
        # self.setLabel('left', "Z", units='mm')
        # self.setLabel('bottom', "X", units='mm')
        self.setRange(xRange=[-40, 40], yRange=[-40, 40])
        self.getAxis('bottom').setStyle(showValues=False)
        self.getAxis('left').setStyle(showValues=False)

        self.marker = BPMCircle(xname, zname)
        self.addItem(self.marker)
        self.aper = AperPlot(xaper, zaper)
        self.addItem(self.aper)
        self.cross = Cross()
        self.addItem(self.cross)
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().disableAutoRange(True)
        # self.getPlotItem().hideAxis('bottom')
        # self.getPlotItem().hideAxis('left')

        self.scene().sigMouseClicked.connect(self.mouse_clicked)
        # self.scene().sigMouseMoved.connect(self.mouseMoved)

    def update_marker_pos(self, x, y):
        self.marker.update_pos(x, y)

    def update_cross_pos(self, x, y):
        self.cross.update_pos(x, y)

    def mouse_clicked(self, event):
        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        #print('clicked plot 0x{:x}, event: {}'.format(id(self), event.double()))
        if event.double():
            pos = event.scenePos()
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            self.update_cross_pos(mousePoint.x(), mousePoint.y())


