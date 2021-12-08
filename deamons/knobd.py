#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys

import numpy as np
import pycx4.pycda as cda
import json
import os
import re
import datetime
from cservice import CXService
from c_orbit.config.knob_config_parser import load_config_knob


class HandlesProc:
    def __init__(self):
        super(HandlesProc, self).__init__()
        self.handles: dict = {}
        self.handle_descr: dict = {}
        self.orbit_rma_knob = {}

        self.cell_col: dict = {0: 'name', 1: 'descr'}
        self.client_list: list = ['handle', 'rm_proc', 'inj_vs_handles', 'orbitd']
        self.cmd_table: dict = {
            'add_handle': self.add_handle_, 'handle_complete': self.handle_complete_, 'add_cor': self.add_cor_,
            'delete_handle': self.delete_handle_, 'edit_item': self.edit_item_,
            'step_up': self.step_up_, 'cst_step_up': self.cst_step_up_,
            'step_down': self.step_down_, 'cst_step_down': self.cst_step_down_,
            'add_orbit_rma_knob': self.add_orbit_rma_knob_, 'orbit_rma_step_up': self.orbit_rma_step_up_,
            'orbit_rma_step_down': self.orbit_rma_step_down_, 'add_orbit_rma_corr': self.add_orbit_rma_corr_,
            'orbit_rma_knob_complete': self.orbit_rma_knob_complete_
        }
        self.knob_is_adding: bool = False
        self.knob_orbit_is_adding: bool = False
        self.tmp = {}
        self.i = 0

        soft_conf = load_config_knob(CONF + '/knobd_conf.txt')
        chan_conf = soft_conf['chans_conf']
        for chan in ['res', 'cmd']:
            if chan not in chan_conf:
                print(chan + ' is absent in knobd_conf')

        self.chan_cmd = cda.StrChan(**chan_conf['cmd'])
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan(**chan_conf['res'])

        self.load_handles()
        print('start')

    #########################################################
    #                     command part                      #
    #########################################################

    def cmd(self, chan):
        if chan.val:
            cmd = json.loads(chan.val)
            print(cmd)
            command = cmd.get('cmd', 'no_cmd')
            client = cmd.get('client', 'no_serv')
            if client in self.client_list:
                self.cmd_table[command](**cmd)

    def add_orbit_rma_knob_(self, **kwargs):
        if not self.knob_orbit_is_adding:
            client = kwargs.get('client')
            self.orbit_rma_knob = {}
            self.knob_orbit_is_adding = True
            self.chan_res.setValue(json.dumps({'client': client, 'res': 'knob_receiving'}))

    def add_orbit_rma_corr_(self, **kwargs):
        cor = kwargs.get('cor')
        channel = cda.DChan(cor['name'] + '.Iset', private=1)
        self.orbit_rma_knob[cor['name'].split('.')[-1]] = [channel, cor['step']]

    def orbit_rma_knob_complete_(self, **kwargs):
        client = kwargs.get('client')
        if self.knob_orbit_is_adding:
            self.knob_orbit_is_adding = False
            self.chan_cmd.setValue('')
            self.chan_res.setValue(json.dumps({'client': client, 'res': 'orbit_knob_added'}))

    def orbit_rma_step_up_(self, **kwargs):
        for key, k_val in self.orbit_rma_knob.items():
            new_curr = k_val[0].val + k_val[1]
            k_val[0].setValue(new_curr)
        print('rma_stepped up')
        self.chan_cmd.setValue('')

    def orbit_rma_step_down_(self, **kwargs):
        for key, k_val in self.orbit_rma_knob.items():
            new_curr = k_val[0].val - k_val[1]
            k_val[0].setValue(new_curr)
        print('rma_stepped down')
        self.chan_cmd.setValue('')

    def add_handle_(self, **kwargs):
        if not self.knob_is_adding:
            name = kwargs.get('name')
            descr = kwargs.get('descr')
            client = kwargs.get('client')
            self.handles_renum()
            self.handles[0] = {}
            self.handle_descr[0] = {'name': name, 'descr': descr, 'cor_list': []}
            self.knob_is_adding = True
            self.chan_res.setValue(json.dumps({'client': client, 'res': 'handle_receiving'}))

    def add_cor_(self, **kwargs):
        cor = kwargs.get('cor')
        self.handle_descr[0]['cor_list'].append(cor)
        if cor['name'].split('.')[-1][0] == 'G':
            channel = cda.DChan(cor['name'] + '.Uset', private=1)
        else:
            channel = cda.DChan(cor['name'] + '.Iset', private=1)
        self.handles[0][cor['name'].split('.')[-1]] = [channel, cor['step']]
            # self.handles[0][cor['name'].split('.')[-1]][0].valueMeasured.connect(self.connection_check)
        # print('connection added')

    def connection_check(self, chan):
        pass
        # print(chan.val)

    def handle_complete_(self, **kwargs):
        client = kwargs.get('client')
        if self.knob_is_adding:
            self.knob_is_adding = False
            self.save_changes()
            self.chan_cmd.setValue('')
            self.chan_res.setValue(json.dumps({'client': client, 'res': 'handle_added'}))

    def delete_handle_(self, **kwargs):
        row = kwargs.get('row')
        client = kwargs.get('client')
        for k in range(row, len(self.handles) - 1):
            self.handles[k] = self.handles[k + 1]
            self.handle_descr[k] = self.handle_descr[k + 1]
        del(self.handles[len(self.handles) - 1])
        del(self.handle_descr[len(self.handle_descr) - 1])
        self.save_changes()
        self.chan_res.setValue(json.dumps({'client': client, 'res': 'handle_deleted', 'row': row}))
        self.chan_cmd.setValue('')

    def edit_item_(self, **kwargs):
        row = kwargs.get('item')[0]
        col = kwargs.get('item')[1]
        client = kwargs.get('client')
        text = kwargs.get('text')
        self.handle_descr[row][self.cell_col[col]] = text
        self.save_changes()
        self.chan_res.setValue(json.dumps({'client': client, 'res': 'handle_edited'}))
        self.chan_cmd.setValue('')

    def step_up_(self, **kwargs):
        row = kwargs.get('row')
        handle = self.handles[row]
        for key, k_val in handle.items():
            new_curr = k_val[0].val + k_val[1]
            k_val[0].setValue(new_curr)
        self.chan_cmd.setValue('')

    def step_down_(self, **kwargs):
        row = kwargs.get('row')
        handle = self.handles[row]
        for key, k_val in handle.items():
            new_curr = k_val[0].val - k_val[1]
            k_val[0].setValue(new_curr)
        self.chan_cmd.setValue('')

    def cst_step_up_(self, **kwargs):
        row = kwargs.get('row')
        factor = kwargs.get('factor')
        handle = self.handles[row]
        for key, k_val in handle.items():
            new_curr = k_val[0].val + k_val[1] * factor
            k_val[0].setValue(new_curr)
        self.chan_cmd.setValue('')

    def cst_step_down_(self, **kwargs):
        row = kwargs.get('row')
        factor = kwargs.get('factor')
        handle = self.handles[row]
        for key, k_val in handle.items():
            new_curr = k_val[0].val - k_val[1] * factor
            k_val[0].setValue(new_curr)
        self.chan_cmd.setValue('')

    def handles_renum(self):
        for i in reversed(range(len(self.handles))):
            self.handle_descr[i + 1] = self.handle_descr.pop(i)
            self.handles[i + 1] = self.handles.pop(i)

    def save_changes(self):
        f = open(DIR + '/saved_handles.txt', 'w')
        f.write(json.dumps(self.handle_descr))
        f.close()

    def load_handles(self):
        f = open(DIR + '/saved_handles.txt', 'r')
        handles_s = f.readline()
        if handles_s:
            handles = json.loads(handles_s)
            for row_num, knob in handles.items():
                self.load_handle_(knob)
        f.close()

    def load_handle_(self, knob):
        handle_params = {}
        self.handles_renum()
        self.handle_descr[0] = knob
        for cor in knob['cor_list']:
            if cor['name'].split('.')[-1][0] == 'G':
                handle_params[cor['name'].split('.')[-1]] = [cda.DChan(cor['name'] + '.Uset', private=1), cor['step']]
            else:
                handle_params[cor['name'].split('.')[-1]] = [cda.DChan(cor['name'] + '.Iset', private=1), cor['step']]
        self.handles[0] = handle_params
        self.save_changes()
        self.chan_res.setValue(json.dumps({'client': 'handle', 'res': 'handles_loaded'}))
        self.chan_cmd.setValue('')

PATH = os.getcwd()
DIR = re.sub('deamons', 'knobs', PATH)
CONF = re.sub('deamons', 'config', PATH)


# class KMService(CXService):
#     def main(self):
#         print('run main')
#         self.w = HandlesProc()
#
#     def clean(self):
#         self.log_str('exiting handles_proc')
#
#
# bp = KMService("knobd")

if __name__ == "__main__":
    w = HandlesProc()
    cda.main_loop()
