#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic, QtCore

import sys
import psycopg2
import pycx4.qcda as cda


class MAGNETIZATION:
    """
    make DR correctors magnetization process
    """
    def __init__(self):
        super(MAGNETIZATION, self).__init__()
        try:
            self.conn = psycopg2.connect(dbname='icdata', user='postgres', host='pg10-srv', password='')
            print("Connected to DB")
        except:
            print("No access to DB")




if __name__ == "__main__":
    app = QApplication(['BPM'])
    w = MAGNETIZATION()
    sys.exit(app.exec_())
