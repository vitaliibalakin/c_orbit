#!/usr/bin/env python3
# bpm delay is 20527.89 (???) ns in pickup2 channel - check

from PyQt5.QtWidgets import QApplication
import sys

import numpy as np
import pycx4.pycda as cda
from scipy import optimize
import json
import os
import re
import datetime
from cservice import CXService
from bpm_base.bpm import BPM
from c_orbit.config.orbit_config_parser import load_config_orbit


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        chans_conf, bpms_list, self.client_list, self.mode_d  = load_config_orbit(CONF + '/orbitd_conf.txt', DIR)

        # checking config
        for chan in ['tunes', 'control_tunes', 'fft', 'coor', 'cmd', 'res', 'orbit', 'one_turn', 'control_orbit',
                     'turns', 'turns_matrix', 'modet']:
            if chan not in chans_conf:
                print(chan + ' is absent in orbitd_conf')

        self.bpms_zeros = np.zeros(2 * len(bpms_list),)
        self.bpms_deviation = np.zeros(2 * len(bpms_list),)
        self.ic_mode: str
        self.bckgr_proc: bool = False
        self.bckrg_counter: int = 0
        self.bckgr_it_num: int = 0
        self.current_orbit = np.empty(0)
        self.current_tunes = np.empty(0)
        self.bpms: list = [BPM(bpm, self.collect_orbit, self.collect_tunes, self.collect_current,
                         self.collect_fft, self.collect_coor, CONF) for bpm in bpms_list]

        self.fft_bpm: str = 'bpm15'
        self.turns_bpm: str = 'bpm15'
        for bpm in self.bpms:
            if bpm.name == 'bpm15':
                bpm.turns_mes = 1

        self.inj_bpms: dict = {'p2v2': ['bpm12', 'bpm11'], 'p2v4': ['bpm12', 'bpm11'],
                               'e2v2': ['bpm07', 'bpm08'], 'e2v4': ['bpm07', 'bpm08']}
        self.inj_coors: dict = {'bpm07': [], 'bpm08': [], 'bpm11': [], 'bpm12': []}
        self.m_x1_septum: list = []
        self.m_x2_septum: list = []

        self.chan_tunes = cda.VChan(**chans_conf['tunes'])
        self.chan_ctrl_tunes = cda.StrChan(**chans_conf['control_tunes'])
        # order: p2v2, e2v2, p2v4, e2v4
        self.chan_fft = cda.VChan(**chans_conf['fft'])
        self.chan_coor = cda.VChan(**chans_conf['coor'])
        self.chan_cmd = cda.StrChan(**chans_conf['cmd'])
        self.chan_cmd.valueMeasured.connect(self.cmd)
        self.chan_res = cda.StrChan(**chans_conf['res'])
        self.chan_orbit = cda.VChan(**chans_conf['orbit'])
        self.chan_one_turn = cda.VChan(**chans_conf['one_turn'])
        self.chan_ctrl_orbit = cda.VChan(**chans_conf['control_orbit'])
        self.chan_turns = cda.VChan(**chans_conf['turns'])
        self.chan_turns_matrix = cda.VChan(**chans_conf['turns_matrix'])
        self.chan_mode = cda.StrChan(**chans_conf['modet'])
        self.chan_mode.valueMeasured.connect(self.mode_changed)
        # self.chan_inj = cda.VChan('cxhw:4.bpm_preproc.injection_par', max_nelems=4)

        self.cmd_table = {
            'load_orbit': self.load_file_, 'load_tunes': self.load_file_,
            'load_inj_matrix': self.load_file_,
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
            turns_matrix = np.array([])
            for bpm in self.bpms:
                bpm.marker = 0
                if bpm.act_state:
                    one_turn_x = np.append(one_turn_x, bpm.turn_slice[0])
                    one_turn_z = np.append(one_turn_z, bpm.turn_slice[1])
                    x_orbit = np.append(x_orbit, bpm.coor[0])
                    x_orbit_sigma = np.append(x_orbit_sigma, bpm.sigma[0])
                    z_orbit = np.append(z_orbit, bpm.coor[1])
                    z_orbit_sigma = np.append(z_orbit_sigma, bpm.sigma[1])
                    turns_matrix = np.append(turns_matrix, bpm.turn_arrays)
                    if bpm.name in self.inj_bpms[self.ic_mode]:
                        self.inj_coors[bpm.name] = [bpm.turn_arrays[0], bpm.turn_arrays[bpm.data_len]]
                else:
                    one_turn_x = np.append(one_turn_x, 100)
                    one_turn_z = np.append(one_turn_z, 100)
                    x_orbit = np.append(x_orbit, 100.0)
                    x_orbit_sigma = np.append(x_orbit_sigma, 0.0)
                    z_orbit = np.append(z_orbit, 100.0)
                    z_orbit_sigma = np.append(z_orbit_sigma, 0.0)
                    turns_matrix = np.append(turns_matrix, np.ones(bpm.data_len * 2) * 100.0)
            orbit = np.concatenate([x_orbit, z_orbit])
            std = np.concatenate([x_orbit_sigma, z_orbit_sigma])
            self.current_orbit = np.concatenate([orbit - self.bpms_zeros, std])
            self.calc_inj_param()

            if self.bckgr_proc:
                self.bpms_deviation += orbit
                self.bckrg_counter -= 1
                if self.bckrg_counter == 0:
                    self.bckrg_stop_()
                return
            self.chan_orbit.setValue(np.concatenate([orbit - self.bpms_zeros, std]))
            print(orbit)
            self.chan_one_turn.setValue(np.concatenate([one_turn_x, one_turn_z]))
            self.chan_turns_matrix.setValue(turns_matrix)


    def collect_tunes(self, tunes):
        self.current_tunes = tunes
        self.chan_tunes.setValue(tunes)

    def collect_current(self, data):
        self.chan_turns.setValue(data)

    def collect_fft(self, data):
        self.chan_fft.setValue(data)

    def collect_coor(self, data):
        self.chan_coor.setValue(data)

    def calc_inj_param(self):
        # x corr from first bpm on beam way
        x1 = self.inj_coors[self.inj_bpms[self.ic_mode][0]][0]
        # x corr from second bpm on beam way
        x2 = self.inj_coors[self.inj_bpms[self.ic_mode][1]][0]
        # # y corr from first bpm on beam way
        # y1 = self.inj_coors[self.inj_bpms[self.ic_mode][0]][1]
        # # y corr from second bpm on beam way
        # y2 = self.inj_coors[self.inj_bpms[self.ic_mode][1]][1]
        if self.m_x1_septum and self.m_x2_septum:
            coord = (self.m_x2_septum[0][1] * x1 - self.m_x1_septum[0][1] * x2) \
                    / (self.m_x2_septum[0][1] * self.m_x1_septum[0][0] - self.m_x1_septum[0][1] * self.m_x2_septum[0][0])
            angle = (self.m_x1_septum[0][0] * x2 - self.m_x2_septum[0][0] * x1) \
                    / (self.m_x2_septum[0][1] * self.m_x1_septum[0][0] - self.m_x1_septum[0][1] * self.m_x2_septum[0][0])
            # self.chan_inj.setValue(np.array([coord, angle]))
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
        self.bpms_zeros = np.zeros([32, ])
        self.bpms_deviation = np.zeros([32, ])
        client = kwargs.get('client', 'no_client')
        self.send_cmd_res_(**{'action': 'bckgr_discarded', 'client': client})

    def bckgr_start_(self, **kwargs):
        self.bckgr_it_num, self.bckrg_counter = kwargs.get('count', 5), kwargs.get('count', 5)
        self.bpms_zeros = np.zeros([32, ])
        self.bpms_deviation = np.zeros([32, ])
        self.bckgr_proc = True

    def bckrg_stop_(self):
        self.bpms_zeros = self.bpms_deviation / self.bckgr_it_num
        # print(self.bpms_zeros)
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
            # print(data)
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
                self.send_cmd_res_(**{'action': 'load -> loaded', 'client': client})
            else:
                if client == 'orbit':
                    data = np.zeros(64)
                elif client == 'tunes':
                    data = np.zeros(2)
                elif client == 'inj':
                    data = np.ones([2,2])
                self.send_cmd_res_(**{'action': 'load -> file error', 'client': client})
            file.close()
            if client == 'orbit':
                self.chan_ctrl_orbit.setValue(data)
            elif client == 'tunes':
                self.chan_ctrl_tunes.setValue(json.dumps({mode: np.ndarray.tolist(data)}))
            elif client == 'inj':
                self.m_x1_septum = data[0:2, :]
                self.m_x2_septum = data[2:, :]
            self.mode_file_edit_(file_name, self.mode_d[client])
        except Exception as exc:
            self.send_cmd_res_(**{'action': 'loading_' + exc, 'client': client})


PATH = os.getcwd()
DIR = re.sub('deamons', 'bpm_plot', PATH)
CONF = re.sub('deamons', 'config', PATH)


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
    w = BpmPreproc()
    cda.main_loop()
    # load_config('config/orbitd_conf.txt')

