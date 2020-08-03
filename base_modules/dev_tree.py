#!/usr/bin/env python3

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QTextEdit, QLabel

# importing custom tree widget
from acc_db.sys_dev_tree import SysTreeWidget

# importing django models
# with prev imports Django already set up
from accdb.models import Sys, Dev, Devtype, Chan, Protocol, Namesys


class MyTestW(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(2, 2, 2, 2)
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(1)
        self.setLayout(self.grid)

        self.grid.addWidget(QLabel("tree"), 0, 0)
        self.grid.addWidget(QLabel("selected sys"), 0, 1)
        self.grid.addWidget(QLabel("selected devs"), 0, 2)
        self.grid.addWidget(QLabel("last dev chans"), 0, 3)

        self.tree = SysTreeWidget(show_devs=True, top_id=40)
        print(self.tree.db_tree)
        self.grid.addWidget(self.tree, 1, 0)

        self.sys_text = QTextEdit()
        self.grid.addWidget(self.sys_text, 1, 1)

        self.devs_text = QTextEdit()
        self.grid.addWidget(self.devs_text, 1, 2)

        self.devchans_text = QTextEdit()
        self.grid.addWidget(self.devchans_text, 1, 3)

        self.tree.sysSelectionChanged.connect(self.print_sys)
        self.tree.devsSelectionChanged.connect(self.print_devs)
        self.tree.itemClicked.connect(self.print_dev_chans)

    def print_sys(self, sys_set):
        self.sys_text.setText(str(sys_set))

    def print_devs(self, devs_set):
        self.devs_text.setText(str(devs_set))
        for db_id in devs_set:
            d = Dev.objects.get(pk=db_id)
            print('d:', d.name)

    def print_dev_chans(self, item):
        print(item)
        if item.db_type != "dev":
            return
        d = Dev.objects.get(pk=item.db_id)
        print('d:', d.name)
        ns = d.namesys
        print('ns:', ns)
        s_ns = Namesys.objects.get(def_soft=True)
        print('s_ns:', s_ns)
        dts = d.devtype.all()
        cnames = []
        for x in dts:
            dt_cs = x.chans.all()
            print(dt_cs)
            ns_name = s_ns.name if x.soft else ns.name
            for y in dt_cs:
                cnames.append('.'.join([ns_name, d.name, y.name]))
        self.devchans_text.setText(str(cnames))


app = QApplication(['dev_tree'])

w = MyTestW()
w.resize(1200, 800)
w.show()

app.exec_()
