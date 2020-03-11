#!/usr/bin/env python3
# bpm delay is 20527.89 (???) ns in pickup2 channel - check

import numpy as np
import pycx4.pycda as cda
import json
import os
import re
import datetime
from aux.service_daemon import CXService
from base_modules.file_data_exchange import FileDataExchange
from .bpm import BPM


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.mode = ''
        self.fft_bpm = 'bpm15'
        self.turns_bpm = 'bpm15'
        self.bpms_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                          'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpms = [BPM(bpm, self.bpm_marker) for bpm in self.bpms_list]
        for bpm in self.bpms:
            if bpm.name == 'bpm15':
                bpm.turns_mes = 1

        self.file_exchange = FileDataExchange(DIR, self.data_receiver)

        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)
        self.chan_act_bpm = cda.StrChan('cxhw:4.bpm_preproc.act_bpm', max_nelems=1024)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024)
        self.chan_ctrl_orbit = cda.VChan('cxhw:4.bpm_preproc.control_orbit', max_nelems=64)
        self.chan_tunes_range = cda.StrChan('cxhw:4.bpm_preproc.tunes_range', max_nelems=1024)

        self.orbits = {'cur': self.chan_orbit, 'eq': self.chan_ctrl_orbit}
        self.cmd_table = {'load_orbit': self.load_file_, 'save_orbit': self.save_file_, 'cur_bpms': self.act_bpm_,
                          'no_cmd': self.no_cmd_}

        print('start')

    def data_receiver(self, orbit, **kwargs):
        which = kwargs.get('which', 'cur')
        if isinstance(orbit, np.ndarray):
            pass
        elif isinstance(orbit, str):
            orbit = np.zeros(32)
        self.orbits[which].setValue(orbit)

    def bpm_marker(self):
        permission = 0
        for bpm in self.bpms:
            if bpm.act_state:
                if bpm.marker:
                    permission = 1
                else:
                    permission = 0
                    break

        if permission:
            x_orbit = np.array([])
            x_orbit_sigma = np.array([])
            z_orbit = np.array([])
            z_orbit_sigma = np.array([])
            for bpm in self.bpms:
                bpm.marker = 0
                if bpm.act_state:
                    x_orbit = np.append(x_orbit, bpm.coor[0])
                    x_orbit_sigma = np.append(x_orbit_sigma, bpm.sigma[0])
                    z_orbit = np.append(z_orbit, bpm.coor[1])
                    z_orbit_sigma = np.append(z_orbit_sigma, bpm.coor[1])
                else:
                    x_orbit = np.append(x_orbit, 100.0)
                    x_orbit_sigma = np.append(x_orbit_sigma, 0.0)
                    z_orbit = np.append(z_orbit, 100.0)
                    z_orbit_sigma = np.append(z_orbit_sigma, 0.0)
            orbit = np.array([x_orbit, z_orbit, x_orbit_sigma, z_orbit_sigma])
            self.chan_orbit.setValue(orbit)

    #########################################################
    #                     command part                      #
    #########################################################

    def cmd(self, chan):
        # cmd = chan.val
        # if cmd:
        command = json.loads(chan.val).get('cmd', 'no_cmd')
        action = json.loads(chan.val).get('act', 'act')
        self.cmd_table[command](action)
        # try:
        #     cmd = json.loads(chan.val)
        #     try:
        #         for bpm in self.bpms:
        #             if bpm.name == cmd['turn_bpm']:
        #                 bpm.turns_mes = 1
        #             else:
        #                 bpm.turns_mes = 0
        #     except KeyError:
        #         pass
        #     try:
        #         self.update_num_pts(cmd['num_pts'])
        #     except KeyError:
        #         pass
        # except Exception as exc:
        #     print(exc)

    def update_num_pts(self, num_pts):
        for bpm in self.bpms:
            if bpm.turns_mes:
                bpm.chan_numpts.setValue(num_pts)

    def mode_changed(self, chan):
        self.mode = chan.val
        self.file_exchange.change_data_from_file(self.mode)

    def load_file_(self, act):
        self.file_exchange.load_file(self, self.mode)
        self.send_cmd_res_(act + ' -> load -> ')

    def save_file_(self, act):
        self.file_exchange.save_file(self, self.chan_orbit.val, self.mode)
        self.send_cmd_res_(act + ' -> save -> ')

    def act_bpm_(self, act_bpm):
        for bpm in self.bpms:
            if bpm.name in act_bpm:
                bpm.act_state = 1
            else:
                bpm.act_state = 0

        self.send_cmd_res_('act -> act_bpm -> ')

    def no_cmd_(self, act):
        self.send_cmd_res_(act + '-> no_cmd ->')

    def send_cmd_res_(self, res):
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.chan_res.setValue(json.dumps(res + time_stamp))


DIR = os.getcwd()
DIR = re.sub('bpm_preproc', 'bpm_plot', DIR)


class KMService(CXService):
    def main(self):
        print('run main')
        self.w = BpmPreproc()

    def clean(self):
        self.log_str('exiting bpm_prepoc')


bp = KMService("bpm_preproc")
