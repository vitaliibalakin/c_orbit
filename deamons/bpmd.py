#!/usr/bin/env python3
# bpm delay is 20527.89 (???) ns in pickup2 channel - check

from PyQt5.QtWidgets import QApplication
import sys

import numpy as np
import pycx4.qcda as cda
from scipy import optimize
import json
import os
import re
import datetime
from cservice import CXService
from bpm_base.bpm import BPM


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.mode_d = {'orbit': DIR + '/mode_file.txt', 'tunes': DIR + '/mode_tunes_file.txt'}
        self.ic_mode = ''
        self.bckgr_proc = False
        self.bpms_zeros = np.zeros(32,)
        self.bpms_deviation = np.zeros(32,)
        self.bckrg_counter = 0
        self.bckgr_it_num = 0
        self.current_orbit = np.empty(0)
        self.current_tunes = np.empty(0)
        self.client_list = ['orbit', 'tunes', 'turns']
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
        self.chan_one_turn = cda.VChan('cxhw:4.bpm_preproc.one_turn', max_nelems=32)
        self.chan_ctrl_orbit = cda.VChan('cxhw:4.bpm_preproc.control_orbit', max_nelems=64)
        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4, on_update=1)
        self.chan_mode.valueMeasured.connect(self.mode_changed)

        self.cmd_table = {
            'load_orbit': self.load_file_, 'load_tunes': self.load_file_,
            'save_orbit': self.save_file_, 'save_tunes': self.save_file_,
            'cur_bpms': self.act_bpm_, 'turn_bpm': self.turn_bpm_,
            'num_pts': self.turn_bpm_num_pts_, 'turn_num': self.turn_num_,
            'no_cmd': self.no_cmd_,
            'start_tunes': self.start_tunes_, 'bckgr': self.bckgr_start_,
            'bckgr_discard': self.bckgr_discard_
        }
        self.start_tunes_()
        print('start')

    #########################################################
    #                    data proc part                     #
    #########################################################

    def collect_orbit(self):
        permission = 0
        for bpm in self.bpms:
            if bpm.act_state:
                # if bpm.no_connection:
                #     self.send_cmd_res_(**{'action': 'no_connection', 'bpm': bpm.name, 'client': 'orbit'})
                # else:
                #     self.send_cmd_res_(**{'action': 'connected', 'bpm': bpm.name, 'client': 'orbit'})
                if bpm.marker:
                    permission = 1
                else:
                    permission = 0
                    break

        if permission:
            one_turn_x = np.array([])
            one_turn_z = np.array([])
            x_orbit = np.array([])
            x_orbit_sigma = np.array([])
            z_orbit = np.array([])
            z_orbit_sigma = np.array([])
            for bpm in self.bpms:
                bpm.marker = 0
                if bpm.act_state:
                    one_turn_x = np.append(one_turn_x, bpm.turn_slice[0])
                    one_turn_z = np.append(one_turn_z, bpm.turn_slice[1])
                    x_orbit = np.append(x_orbit, bpm.coor[0])
                    x_orbit_sigma = np.append(x_orbit_sigma, bpm.sigma[0])
                    z_orbit = np.append(z_orbit, bpm.coor[1])
                    z_orbit_sigma = np.append(z_orbit_sigma, bpm.sigma[1])
                else:
                    one_turn_x = np.append(one_turn_x, 100)
                    one_turn_z = np.append(one_turn_z, 100)
                    x_orbit = np.append(x_orbit, 100.0)
                    x_orbit_sigma = np.append(x_orbit_sigma, 0.0)
                    z_orbit = np.append(z_orbit, 100.0)
                    z_orbit_sigma = np.append(z_orbit_sigma, 0.0)
            orbit = np.concatenate([x_orbit, z_orbit])
            std = np.concatenate([x_orbit_sigma, z_orbit_sigma])
            self.current_orbit = np.concatenate([orbit - self.bpms_zeros, std])
            self.chan_orbit.setValue(np.concatenate([orbit - self.bpms_zeros, std]))
            self.chan_one_turn.setValue(np.concatenate([one_turn_x, one_turn_z]))
            # print(orbit, self.bpms_zeros)
            # data mining for zeros counting
            if self.bckgr_proc:
                print(self.bckrg_counter)
                self.bpms_deviation += orbit
                self.bckrg_counter -= 1
                if self.bckrg_counter == 0:
                    self.bckrg_stop_()

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
            client = chan_val.get('client', 'no_client')
            if client in self.client_list:
                self.cmd_table[command](**chan_val)

    def mode_changed(self, chan):
        self.ic_mode = chan.val
        self.to_another_ic_mode_('orbit')

    def turn_bpm_(self, **kwargs):
        turn_bpm = kwargs.get('turn_bpm')
        for bpm in self.bpms:
            if bpm.name == turn_bpm:
                bpm.turns_mes = 1
            else:
                bpm.turns_mes = 0
        self.chan_cmd.setValue('')

    def turn_num_(self, **kwargs):
        turn_num = kwargs.get('turn_num')
        for bpm in self.bpms:
            bpm.turn_num = turn_num
        self.chan_cmd.setValue('')

    def turn_bpm_num_pts_(self, **kwargs):
        num_pts = kwargs.get('num_pts')
        for bpm in self.bpms:
            if bpm.turns_mes:
                bpm.chan_numpts.setValue(num_pts)
        self.chan_cmd.setValue('')

    def act_bpm_(self, **kwargs):
        act_bpm = kwargs.get('act_bpm')
        client = kwargs.get('client', 'no_client')
        for bpm in self.bpms:
            if bpm.name in act_bpm:
                bpm.act_state = 1
            else:
                bpm.act_state = 0
        self.send_cmd_res_(**{'action': 'act_bpm', 'client': client})

    def bckgr_discard_(self, **kwargs):
        self.bpms_zeros = np.zeros([2, 16])
        self.bpms_deviation = np.zeros([2, 16])
        client = kwargs.get('client', 'no_client')
        self.send_cmd_res_(**{'action': 'bckgr_discarded', 'client': client})

    def bckgr_start_(self, **kwargs):
        self.bckgr_it_num, self.bckrg_counter = kwargs.get('count', 5), kwargs.get('count', 5)
        self.bpms_zeros = np.zeros([2, 16])
        self.bpms_deviation = np.zeros([2, 16])
        self.bckgr_proc = True

    def bckrg_stop_(self):
        self.bpms_zeros = self.bpms_deviation / self.bckgr_it_num
        print(self.bpms_zeros)
        self.bckgr_proc = False
        self.bckgr_it_num, self.bckrg_counter = 0, 0
        self.send_cmd_res_(**{'action': 'bckgr_done', 'client': 'orbit'})

    def no_cmd_(self, **kwargs):
        client = kwargs.get('client', 'no_client')
        self.send_cmd_res_(**{'action': 'no_cmd', 'client': client})

    def send_cmd_res_(self, **kwargs):
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kwargs['time_stamp'] = time_stamp
        self.chan_res.setValue(json.dumps(kwargs))
        self.chan_cmd.setValue('')

    #########################################################
    #                     file exchange                     #
    #########################################################

    def start_tunes_(self, **kwargs):
        ic_modes = ['p2v2', 'e2v2', 'p2v4', 'e2v4']
        ctrl_tunes = {}
        f = open(self.mode_d['tunes'], 'r')
        if os.fstat(f.fileno()).st_size:
            data_mode = json.loads(f.read())
            print(data_mode)
            for mode in ic_modes:
                try:
                    file = open(data_mode[mode], 'r')
                    if os.fstat(file.fileno()).st_size:
                        data = np.loadtxt(data_mode[mode])
                        ctrl_tunes[mode] = np.ndarray.tolist(data)
                    else:
                        data = np.zeros(2)
                        ctrl_tunes[mode] = np.ndarray.tolist(data)
                        self.send_cmd_res_(
                            **{'action': 'start tunes', 'error': 'file with saved tunes is empty', 'client': 'tunes'})
                    file.close()
                except FileNotFoundError:
                    ctrl_tunes[mode] = np.ndarray.tolist(np.zeros(2))
                    self.send_cmd_res_(**{'action': 'start tunes', 'error': 'no mode_tunes_file', 'client': 'tunes'})
                except KeyError:
                    ctrl_tunes[mode] = np.ndarray.tolist(np.zeros(2))
                    self.send_cmd_res_(
                        **{'action': 'start tunes', 'error': 'no ' + str(mode) + ' value', 'client': 'tunes'})
        f.close()
        self.chan_ctrl_tunes.setValue(json.dumps(ctrl_tunes))

    def mode_file_edit_(self, file_name, mode_file):
        print(mode_file)
        f = open(mode_file, 'r')
        info = f.read()
        if info:
            data_mode = json.loads(info)
        else:
            data_mode = {}
        f.close()
        data_mode[self.ic_mode] = file_name
        f = open(mode_file, 'w')
        f.write(json.dumps(data_mode))
        f.close()

    def to_another_ic_mode_(self, client):
        try:
            f = open(self.mode_d[client], 'r')
            data_mode = json.loads(f.read())
            f.close()
            self.load_file_(**{'file_name': data_mode[self.ic_mode], 'client': client})
        except Exception as exc:
            self.send_cmd_res_(**{'action': 'switch mode', 'error': str(exc), 'client': client})

    def save_file_(self, **kwargs):
        file_name = kwargs.get('file_name')
        client = kwargs.get('client')
        if client == 'orbit':
            data = self.current_orbit
            print(data)
            if data.any():
                self.chan_ctrl_orbit.setValue(data)
                np.savetxt(file_name, data)
                self.mode_file_edit_(file_name, self.mode_d[client])
                self.send_cmd_res_(**{'action': 'orbit save', 'client': client})
            else:
                self.send_cmd_res_(**{'action': 'orbit chan is empty', 'client': client})
        elif client == 'tunes':
            data = self.current_tunes
            if any(data):
                self.chan_ctrl_tunes.setValue(json.dumps({self.ic_mode: np.ndarray.tolist(data)}))
                np.savetxt(file_name, data)
                self.mode_file_edit_(file_name, self.mode_d[client])
                self.send_cmd_res_(**{'action': 'tunes save', 'client': client})
            else:
                self.send_cmd_res_(**{'action': 'tunes chan is empty', 'client': client})

    def load_file_(self, **kwargs):
        file_name = kwargs.get('file_name')
        client = kwargs.get('client')
        mode = kwargs.get('mode', 'no_mode')
        try:
            file = open(file_name, 'r')
            if os.fstat(file.fileno()).st_size:
                data = np.loadtxt(file_name)
                self.send_cmd_res_(**{'action': 'loaded', 'client': client})
            else:
                if client == 'orbit':
                    data = np.zeros(64)
                elif client == 'tunes':
                    data = np.zeros(2)
                self.send_cmd_res_(**{'action': 'load -> file error', 'client': client})
            file.close()
            if client == 'orbit':
                self.chan_ctrl_orbit.setValue(data)
            if client == 'tunes':
                self.chan_ctrl_tunes.setValue(json.dumps({mode: np.ndarray.tolist(data)}))
            self.mode_file_edit_(file_name, self.mode_d[client])
        except Exception as exc:
            print('ratatata', exc)


DIR = os.getcwd()
DIR = re.sub('deamons', 'bpm_plot', DIR)


# class KMService(CXService):
#     def main(self):
#         print('run main')
#         self.w = BpmPreproc()
#
#     def clean(self):
#         self.log_str('exiting bpm_prepoc')
#
#
# bp = KMService("bpmd")

if __name__ == "__main__":
    app = QApplication(['c_orbit'])
    w = BpmPreproc()
    sys.exit(app.exec_())


