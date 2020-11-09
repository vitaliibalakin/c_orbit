#!/usr/bin/env python3

import pyqtgraph as pg


class AperPlot(pg.GraphicsObject):
    def __init__(self, aper):
        pg.GraphicsObject.__init__(self)
        self.picture = pg.QtGui.QPicture()
        self.aper_widget(aper)

    def aper_widget(self, aper):
        p = pg.QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('b'))
        for i in range(0, len(aper[0])-1):
            p.drawLine(pg.QtCore.QPointF(aper[0][i], aper[1][i]*1000),
                       pg.QtCore.QPointF(aper[0][i + 1], aper[1][i + 1]*1000))
        for i in range(0, len(aper[0])-1):
            p.drawLine(pg.QtCore.QPointF(aper[0][i], aper[1][i]*(-1000)),
                       pg.QtCore.QPointF(aper[0][i + 1], aper[1][i + 1]*(-1000)))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())
