#!/usr/bin/env python3

from PyQt5.QtWidgets import QVBoxLayout

# some tree-db things
from acc_db.sys_dev_tree import SysTreeWidget
from accdb.models import Sys, Dev, Devtype, Chan, Protocol, Namesys


class TreeTableCom:
    def __init__(self, table, top_id, widget):
        super(TreeTableCom, self).__init__()
        self.table, self.widget = table, widget
        self.dev_choosed = set()
        self.tree = SysTreeWidget(show_devs=True, top_id=top_id)
        p = QVBoxLayout()
        self.widget.setLayout(p)
        p.addWidget(self.tree)

        # self.tree.itemClicked.connect(self.tree_item)
        self.tree.devsSelectionChanged.connect(self.tree_dev)

    def tree_item(self, item):
        if item.db_type != 'dev':
            return
        dev_id = item.db_id
        if dev_id not in self.dev_choosed:
            self.dev_choosed.add(dev_id)
            d = Dev.objects.get(pk=dev_id)
            ns = d.namesys
            c_name = '.'.join([ns.name, d.name])
            self.table.add_row(name=c_name, id=dev_id)
        else:
            self.dev_choosed.remove(dev_id)
            self.table.remove_row(dev_id)

    def tree_dev(self, dev_set):
        for dev_id in dev_set:
            if dev_id in self.dev_choosed:
                pass
            else:
                d = Dev.objects.get(pk=dev_id)
                ns = d.namesys
                c_name = '.'.join([ns.name, d.name])
                self.table.add_row(name=c_name, id=dev_id)
        for dev_id in self.dev_choosed:
            if dev_id in dev_set:
                pass
            else:
                self.table.remove_row(dev_id)
        self.dev_choosed = dev_set.copy()
