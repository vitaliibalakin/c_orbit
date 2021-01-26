#!/usr/bin/env python3
import re
import numpy as np
import subprocess


class Tune:
    def __init__(self):
        self.shift_x = 0.001
        self.shift_y = 0.001
        self.tunes = [0, 0]
        self.n_iter = 3
        self.tune_y_it = 0
        self.tune_x_it = 0
        self.nu_x_arra = np.array([])
        self.nu_y_arra = np.array([])
        self.percentage = np.array([])
        # self.d = 0

        self.lines = 0
        self.start()
        self.make_shift()

    def start(self):
        self.tunes[0] = 4.628
        self.tunes[1] = 2.752
        print('init_t', self.tunes)
        # size mesh
        self.tunes[0] += self.n_iter*self.shift_x
        self.tunes[1] -= self.n_iter*self.shift_y
        # first coordinate on mesh
        self.tune_x_it = -1*self.n_iter
        self.tune_y_it = -1*self.n_iter

    def make_shift(self):
        print(self.tunes)
        while True:
            if self.tune_x_it == self.n_iter:
                if self.tune_y_it == self.n_iter:
                    # end & save
                    print('FINISH')
                    # start params
                    self.n_iter = 1
                    self.tune_x_it = 0
                    self.tune_y_it = 0
                    break
                else:
                    # y tune shift
                    self.tunes[1] += self.shift_y
                    print('new_y', self.tunes[1])
                    self.tune_y_it += 1
                    self.tunes[0] += 2*self.n_iter*self.shift_x
                    self.tune_x_it = -1*self.n_iter
            else:
                # x tune shift
                self.tunes[0] -= self.shift_x
                self.tune_x_it += 1
            self.nu_x_arra = np.append(self.nu_x_arra, self.tunes[0])
            self.nu_y_arra = np.append(self.nu_y_arra, self.tunes[1])
            print(self.nu_x_arra, self.nu_y_arra)

            # TESTED & CORRECT
            f = open('/home/vbalakin/python_soft/elegant_calc/injection_sim/tracking/CorrectTunes.ele', 'r')
            self.lines = f.readlines()
            f.close()
            f = open('/home/vbalakin/python_soft/elegant_calc/injection_sim/tracking/CorrectTunes.ele', 'w')
            self.lines[24] = '	tune_x = ' + str(self.tunes[0]) + ',\n'
            self.lines[25] = '	tune_y = ' + str(self.tunes[1]) + ',\n'
            f.writelines(self.lines)
            f.close()



            corr = subprocess.run(['./CorrectTunes.sh'],
                                  cwd='/home/vbalakin/python_soft/elegant_calc/injection_sim/tracking/')
            if corr == 0:
                print('1')
            else:
                print('0')

            print("number  ", self.tune_x_it, self.tune_y_it)

            track = subprocess.run(['elegant', './Tracking.ele'],
                                    cwd='/home/vbalakin/python_soft/elegant_calc/injection_sim/tracking/')
            if track == 0:
                 print('11')
            else:
                 print('00')

            out = subprocess.Popen(['sdds2stream', '/home/vbalakin/python_soft/elegant_calc/injection_sim/tracking/Results/Tracking.cen', '-col=s,Particles', '-pipe=out'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = out.communicate()
            output = stdout.decode('utf-8').splitlines()
            percentage = float(output[-1].split(' ')[-1]) / float(output[0].split(' ')[-1])
            self.percentage = np.append(self.percentage, percentage)
            print('output', percentage, self.tunes[0], self.tunes[1], '\n')

        d = np.array([self.nu_x_arra, self.nu_y_arra, self.percentage]).T
        print(d)
        np.savetxt('Cur&tunes.txt', d)




a = Tune()