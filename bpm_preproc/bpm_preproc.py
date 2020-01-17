#!/usr/bin/env python3
# bpm delay is 20527.89 (???) ns in pickup2 channel - check

import numpy as np
import pycx4.pycda as cda
import json
from aux.service_daemon import CXService


class BPM:
    def __init__(self, bpm, receiver):
        super(BPM, self).__init__()
        self.receiver = receiver
        self.name = bpm
        self.turns_mes = 0
        self.act_state = 1
        self.marker = 0
        self.coor = (0, 0)
        self.sigma = (0, 0)

        self.chan_turns = cda.VChan('cxhw:4.bpm_preproc.turns', max_nelems=131072)
        self.chan_fft = cda.VChan('cxhw:4.bpm_preproc.fft', max_nelems=262144)
        self.chan_datatxzi = cda.VChan('cxhw:37.ring.' + bpm + '.datatxzi', max_nelems=4096)
        self.chan_numpts = cda.DChan('cxhw:37.ring.' + bpm + '.numpts')
        self.chan_marker = cda.DChan('cxhw:37.ring.' + bpm + '.marker')
        self.chan_datatxzi.valueMeasured.connect(self.data_proc)
        self.chan_marker.valueMeasured.connect(self.marker_proc)

    def marker_proc(self, chan):
        print(chan.val)
        self.marker = 1
        self.receiver()

    def data_proc(self, chan):
        data_len = len(chan.val)
        if self.turns_mes:
            self.chan_fft.setValue(chan.val[data_len:3 * data_len])
            self.chan_turns.setValue(chan.val[3*data_len:4*data_len])
            self.coor = (np.mean(chan.val[data_len:2 * data_len]), np.mean(chan.val[2 * data_len:3 * data_len]))
            self.sigma = (np.std(chan.val[data_len:2 * data_len]), np.std(chan.val[2 * data_len:3 * data_len]))


class BpmPreproc:
    def __init__(self):
        super(BpmPreproc, self).__init__()
        self.fft_bpm = 'bpm15'
        self.turns_bpm = 'bpm15'

        self.bpms_list = ['bpm01', 'bpm02', 'bpm03', 'bpm04', 'bpm05', 'bpm07', 'bpm08', 'bpm09', 'bpm10', 'bpm11',
                          'bpm12', 'bpm13', 'bpm14', 'bpm15', 'bpm16', 'bpm17']
        self.bpms = [BPM(bpm, self.bpm_marker) for bpm in self.bpms_list]

        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)
        self.chan_cmd = cda.StrChan('cxhw:4.bpm_preproc.cmd', max_nelems=1024, on_update=1)
        self.chan_act_bpm = cda.StrChan('cxhw:4.bpm_preproc.act_bpm', max_nelems=1024)
        self.chan_res = cda.StrChan('cxhw:4.bpm_preproc.res', max_nelems=1024)

        self.chan_act_bpm.valueMeasured.connect(self.act_bpm)
        self.chan_cmd.valueMeasured.connect(self.cmd)
        print('start')

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

    def cmd(self, chan):
        cmd = json.loads(chan.val)
        try:
            for bpm in self.bpms:
                if bpm.name == cmd['turn_bpm']:
                    bpm.turns_mes = 1
                else:
                    bpm.turns_mes = 0
        except KeyError:
            pass

        try:
            self.update_num_pts(cmd['num_pts'])
        except KeyError:
            pass

    def act_bpm(self, chan):
        try:
            act_bpm = json.loads(chan.val)['cur_bpms']
            for bpm in self.bpms:
                if bpm.name in act_bpm:
                    bpm.act_state = 1
                else:
                    bpm.act_state = 0
        except Exception as exc:
            print(exc)

    def update_num_pts(self, num_pts):
        for bpm in self.bpms:
            if bpm.turns_mes:
                bpm.chan_numpts.setValue(num_pts)


class KMService(CXService):
    def main(self):
        print('run main')
        self.w = BpmPreproc()

    def clean(self):
        self.log_str('exiting bpm_prepoc')


bp = KMService("bpm_preproc")
