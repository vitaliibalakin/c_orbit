#!/usr/bin/env python3

from PyQt5.QtWidgets import QVBoxLayout

# some tree-db things
from acc_db.sys_dev_tree import SysTreeWidget
from accdb.models import Sys, Dev, Devtype, Chan, Protocol, Namesys

# states
UNSELECTED, SELECTED, PARTLY = 0, 1, 2


class TreeTableCom:
    def __init__(self, table, top_id, widget):
        super(TreeTableCom, self).__init__()
        self.table, self.widget = table, widget
        self.dev_choosed = set()
        self.dev_item_list = []
        self.sys_item_list = []
        self.tree = SysTreeWidget(show_devs=True, top_id=top_id)
        p = QVBoxLayout()
        self.widget.setLayout(p)
        p.addWidget(self.tree)

        self.tree.devsSelectionChanged.connect(self.tree_dev)
        # self.tree.itemClicked.connect(self.tree_item)
        # self.tree.sysSelectionChanged.connect()

    def tree_item(self, item):
        # print('item', item)
        if item.db_type == 'sys':
            if item not in self.sys_item_list:
                self.sys_item_list.append(item)
            else:
                self.sys_item_list.remove(item)
        elif item.db_type == 'dev':
            if item not in self.dev_item_list:
                self.dev_item_list.append(item)
            else:
                self.dev_item_list.remove(item)
        else:
            return

    def tree_dev(self, dev_set):
        # print(dev_set, self.dev_choosed)
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

    def set_item_selected(self, it_id):
        self.tree.set_item_state(self.tree.dev_id_ws[it_id][0], SELECTED)
        self.dev_choosed.add(it_id)

    def free_dev_set(self):
        for it_id in self.dev_choosed:
            self.tree.item_click_cb(self.tree.dev_id_ws[it_id][0], '')

        # self.tree_dev(set())
        # for it_id in self.dev_choosed:
        #     self.tree.set_item_state(self.tree.dev_id_ws[it_id][0], UNSELECTED)
        # self.dev_choosed = set()
