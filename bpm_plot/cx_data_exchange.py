#!/usr/bin/env python3

import pycx4.qcda as cda


class CXDataExchange:
    def __init__(self, data_receiver):
        super(CXDataExchange, self).__init__()
        self.data_receiver = data_receiver
        self.chan_orbit = cda.VChan('cxhw:4.bpm_preproc.orbit', max_nelems=64)

        self.chan_orbit.valueMeasured.connect(self.data_proc)

    def data_proc(self, chan):
        # print(chan.val)
        self.data_receiver(chan.val[:32], std=chan.val[32:48], which='cur')
