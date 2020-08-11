#!/usr/bin/env python3
# bpm delay is 20527.89 (???) ns in pickup2 channel - check

import numpy as np
import pycx4.pycda as cda
import json
import os
import re
import datetime
from aux.service_daemon import CXService
from base_modules.bpm import BPM


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.mode_d = {'orbit': DIR + '/mode_file.txt', 'tunes': DIR + '/mode_tunes_file.txt'}
        self.ic_mode = ''
        self.current_orbit = np.empty(0)
        self.current_tunes = np.empty(0)
        self.fft_bpm = 'bpm15'
        self.turns_bpm = 'bpm15'
        self.bpms_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                          'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpms = [BPM(bpm, self.collect_orbit, self.collect_tunes, self.collect_current,
                         self.collect_fft, self.collect_coor) for bpm in self.bpms_list]
        for bpm in self.bpms:
            if bpm.name == 'bpm15':
                bpm.turns_mes = 1

        self.chan_tunes = cda.VChan('cxhw:4.bpm_preproc.tunes', max_nelems=2)
        self.chan_ctrl_tunes = cda.StrChan('cxhw:4.bpm_preproc.control_tunes', max_nelems=1024)
        # order: p2v2, e2v2, p2v4, e2v4
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)
        self.chan_coor = cda.VChan('cxhw:4.bpm_preproc.coor', max_nelems=262144)
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024, on_update=1)
        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)
        self.chan_ctrl_orbit = cda.VChan('cxhw:4.bpm_preproc.control_orbit', max_nelems=64)
        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_mode.valueMeasured.connect(self.mode_changed)

        self.cmd_table = {'load_orbit': self.load_file_, 'load_tunes': self.load_file_,
                          'save_orbit': self.save_file_, 'save_tunes': self.save_file_,
                          'cur_bpms': self.act_bpm_, 'turn_bpm': self.turn_bpm_,
                          'num_pts': self.turn_bpm_num_pts_, 'no_cmd': self.no_cmd_,
                          'start_tunes': self.start_tunes_}

        print('start')

    #########################################################
    #                    data proc part                     #
    #########################################################

    def collect_orbit(self):
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
            self.current_orbit = orbit
            self.chan_orbit.setValue(orbit)

    def collect_tunes(self, tunes):
        self.current_tunes = tunes
        self.chan_tunes.setValue(tunes)

    def collect_current(self, data):
        self.chan_turns.setValue(data)

    def collect_fft(self, data):
        self.chan_fft.setValue(data)

    def collect_coor(self, data):
        self.chan_coor.setValue(data)

    #########################################################
    #                     command part                      #
    #########################################################

    def cmd(self, chan):
        cmd = chan.val
        if cmd:
            chan_val = json.loads(cmd)
            command = chan_val.get('cmd', 'no_cmd')
            self.cmd_table[command](**chan_val)

    def mode_changed(self, chan):
        self.ic_mode = chan.val
        self.ic_mode = 'p2v2'  # for tests
        self.to_another_ic_mode_('orbit')

    def turn_bpm_(self, **kwargs):
        turn_bpm = kwargs.get('turn_bpm')
        for bpm in self.bpms:
            if bpm.name == turn_bpm:
                bpm.turns_mes = 1
            else:
                bpm.turns_mes = 0

    def turn_bpm_num_pts_(self, **kwargs):
        num_pts = kwargs.get('num_pts')
        for bpm in self.bpms:
            if bpm.turns_mes:
                bpm.chan_numpts.setValue(num_pts)

    def act_bpm_(self, **kwargs):
        act_bpm = kwargs.get('act_bpm')
        service = kwargs.get('service')
        for bpm in self.bpms:
            if bpm.name in act_bpm:
                bpm.act_state = 1
            else:
                bpm.act_state = 0
        self.send_cmd_res_('action -> act_bpm -> ', rec=service)

    def no_cmd_(self, **kwargs):
        service = kwargs.get('service', 'no_service')
        self.send_cmd_res_('action -> no_cmd ->', rec=service)

    def send_cmd_res_(self, res, rec):
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.chan_res.setValue(json.dumps({'rec': rec, 'res': res + time_stamp}))

    #########################################################
    #                     file exchange                     #
    #########################################################

    def start_tunes_(self, **kwargs):
        ic_modes = ['p2v2', 'e2v2', 'p2v4', 'e2v4']
        ctrl_tunes = {}
        msg = 'action -> load -> no action'
        f = open(self.mode_d['tunes'], 'r')
        data_mode = json.loads(f.read())
        f.close()
        for mode in ic_modes:
            try:
                data = np.loadtxt(data_mode[mode])
                ctrl_tunes[mode] = np.ndarray.tolist(data)
                msg = 'action -> load -> '
            except Exception as exc:
                data = np.zeros(2)
                ctrl_tunes[mode] = np.ndarray.tolist(data)
                msg = 'action -> load -> error ' + str(exc) + '-> '
        self.chan_ctrl_tunes.setValue(json.dumps(ctrl_tunes))
        self.send_cmd_res_(msg, rec='tunes')

    def mode_file_edit_(self, file_name, mode_file):
        f = open(mode_file, 'r')
        data_mode = json.loads(f.read())
        f.close()
        data_mode[self.ic_mode] = file_name
        f = open(mode_file, 'w')
        f.write(json.dumps(data_mode))
        f.close()

    def to_another_ic_mode_(self, service):
        try:
            f = open(self.mode_d[service], 'r')
            data_mode = json.loads(f.read())
            f.close()
            self.load_file_(**{'file_name': data_mode[self.ic_mode], 'service': service})
        except Exception as exc:
            self.send_cmd_res_('action -> switch mode (no mode file?) -> error ' + str(exc) + '-> ', rec=service)

    def save_file_(self, **kwargs):
        file_name = kwargs.get('file_name')
        service = kwargs.get('service')
        if service == 'orbit':
            data = self.current_orbit
            self.chan_ctrl_orbit.setValue(data)
            np.savetxt(file_name, data)
        elif service == 'tunes':
            data = self.current_tunes
            self.chan_ctrl_tunes.setValue(json.dumps({self.ic_mode: np.ndarray.tolist(data)}))
            np.savetxt(file_name, data)
        self.mode_file_edit_(file_name, self.mode_d[service])
        self.send_cmd_res_('action -> save -> ', rec=service)

    def load_file_(self, **kwargs):
        file_name = kwargs.get('file_name')
        service = kwargs.get('service')
        try:
            data = np.loadtxt(file_name)
            msg = 'action -> load -> '
        except Exception as exc:
            if service == 'orbit':
                data = np.zeros(64)
            elif service == 'tunes':
                data = np.zeros(2)
            msg = 'action -> load -> error ' + str(exc) + '-> '
        if service == 'orbit':
            self.chan_ctrl_orbit.setValue(data)
        if service == 'tunes':
            self.chan_ctrl_tunes.setValue(json.dumps({self.ic_mode: data}))
        self.mode_file_edit_(file_name, self.mode_d[service])
        self.send_cmd_res_(msg, rec=service)


DIR = os.getcwd()
DIR = re.sub('bpm_preproc', 'bpm_plot', DIR)


class KMService(CXService):
    def main(self):
        print('run main')
        self.w = BpmPreproc()

    def clean(self):
        self.log_str('exiting bpm_prepoc')


bp = KMService("bpm_preproc")
