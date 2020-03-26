#!/usr/bin/env python3

from bpm_plot.aux_mod.wrapper_tunes import PyQtElemPlot
import pyqtgraph as pg


class PyQtStructureParser(pg.PlotWidget):
    def __init__(self, structure, parent):
        super(PyQtStructureParser, self).__init__(parent=parent)
        e2draw = ['QUAD']
        line_counter = 0
        e_beg = -1
        for e_type in structure['ElementType']:
            if e_beg == -1:
                if e_type in e2draw:
                    e_beg = structure['s'][line_counter]
            elif e_type not in e2draw:
                e_end = structure['s'][line_counter - 1]
                if structure['ElementType'][line_counter - 1] == 'QUAD':
                    if structure['ElementName'][line_counter - 1][2] == 'F':
                        c_type = 'QUAD_F'
                    else:
                        c_type = 'QUAD_D'
                    self.addItem(PyQtElemPlot(e_beg, e_end, c_type))
                e_beg = -1
            line_counter += 1
