#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import pyqtgraph as pg


class TurnsPlot(pg.PlotWidget):
    def __init__(self, parent):
        super(TurnsPlot, self).__init__(parent=parent)
        self.showGrid(x=True, y=True)
        self.setLogMode(False, False)
        self.setLabel('left', "Current", units='a.u.')
        self.setLabel('bottom', "Turn", units='num')
        self.setRange(yRange=[0, 40])
        self.setRange(xRange=[0, 1024])

    def turns_plot(self, data):
        self.clear()
        self.plot(data, pen=pg.mkPen('g', width=1))


if __name__ == "__main__":
    app = QApplication(['turns_plot'])
    w = TurnsPlot(None)
    sys.exit(app.exec_())
