import numpy as np
import json
import matplotlib.pyplot as plt


def assymetry(lenses, elem_list, beta_data):
    sig_list = {}
    av_list = {}
    delta_list = {}
    for lens in lenses:
        k = 0
        i = 0
        av = 0
        c = 0
        for cor in elem_list:
            if cor[-2:] == lens:
                av += beta_data[i]
                k += 1
            i += 1
        avv = av / k
        i = 0
        for cor in elem_list:
            if cor[-2:] == lens:
                c += (beta_data[i] - avv) ** 2
            i += 1
        sigma = np.sqrt(1 / k * c)
        i = 0
        for cor in elem_list:
            if cor[-2:] == lens:
                delta_list[cor] = abs(beta_data[i] - avv)
                av_list[cor] = avv
                sig_list[cor] = sigma
            i += 1
    return av_list, delta_list, sig_list

def to_plot_measured(names, cor_list, x_mod):
    av_arr, delta_arr, sig_arr = [], [], []
    for name in names:
        if name not in cor_list:
            av_arr.append(0)
            delta_arr.append(0)
            sig_arr.append(0)
        else:
            av_arr.append(x_mod[0][name])
            delta_arr.append(x_mod[1][name])
            sig_arr.append(x_mod[2][name])
    return av_arr, delta_arr, sig_arr


beta_x = []
beta_y = []
main_lenses = ['d1', 'f1', 'd2', 'f2', 'd3', 'f3', 'f4']
names = ['3f3', '3d3', '3d2', '3f2', '3f4', '3f1',
         '3d1', '4d1', '4f1', '4f4', '4f2', '4d2',
         '4d3', '4f3', '1f3', '1d3', '1d2', '1f2',
         '1f4', '1f1', '1d1', '2d1', '2f1', '2f4',
         '2f2', '2d2', '2d3', '2f3']
dict_beta_x = {quad: [] for quad in names}
dict_beta_y = {quad: [] for quad in names}
av_beta_x = []
av_beta_y = []
with open("beta-coords.sdds", "r") as f:
    j = 0
    for line in f.readlines():
        if j > 13:
            list_ = line.split(" ")
            dict_beta_x[list_[6][1:4].lower()].append(float(list_[3]))
            dict_beta_y[list_[6][1:4].lower()].append(float(list_[5]))
        j += 1
    for quad in names:
        av_beta_x.append(np.mean(np.array(dict_beta_x[quad])))
        av_beta_y.append(np.mean(np.array(dict_beta_y[quad])))

# x_mod = assymetry(main_lenses, names, av_beta_x)
# y_mod = assymetry(main_lenses, names, av_beta_y)
# print('x_mod:', x_mod)
# print('y_mod:', y_mod)

a = np.loadtxt('saved_rms/saved_beta.txt', skiprows=1)
b = open('saved_rms/saved_beta.txt', 'r')
cor_list = json.loads(b.readline().split('#')[-1])
b.close()

av_arr, delta_arr, sig_arr = to_plot_measured(names, cor_list, assymetry(main_lenses, cor_list, a[0]))

# print(len(x_mod_1[0]), x_mod_1[0])
# y_mod = assymetry(main_lenses, cor_list, a[1])
# print('x:', assymetry(main_lenses, cor_list, a[0]))
# print('y:', assymetry(main_lenses, cor_list, a[1]))

n_bins = np.arange(28)
bw = 0.2
plt.title('Lens group square deviation', fontsize=20)
plt.bar(n_bins, av_arr, bw, color='c', label='Average_x')
plt.bar(n_bins + bw, delta_arr, bw, color='m', label='Delta_x')
plt.bar(n_bins + 2*bw, sig_arr, bw, color='y', label='Sigma_x')
plt.legend(loc=2)
plt.xticks(n_bins + 1.5*bw, names)
plt.grid(True)
plt.show()

# n_bins = np.arange(28)
# bw = 0.2
# plt.title('Lens group square deviation', fontsize=20)
# plt.bar(n_bins, y_mod[0], bw, color='c', label='Average_x')
# plt.bar(n_bins + bw, y_mod[1], bw, color='m', label='Delta_x')
# plt.bar(n_bins + 2*bw, y_mod[2], bw, color='y', label='Sigma_x')
# plt.legend(loc=2)
# plt.xticks(n_bins + 1.5*bw, names)
# plt.grid(True)
# plt.show()

# plt.title('Lens group square deviation', fontsize=20)
# plt.bar(n_bins, y_mod[0], bw, color='y', label='Sigma')
# plt.bar(n_bins + bw, y_mod[1], bw, color='m', label='Beta_y')
# plt.legend(loc=2)
# plt.xticks(n_bins, main_lenses)
# plt.show()

# n_bins = np.arange(28)
# bw = 0.2
# plt.title('Lens group square deviation', fontsize=20)
# plt.bar(n_bins, y_mod[2], bw, color='g', label='Sigma')
# # plt.bar(n_bins + bw, y_mod[2], bw, color='r', label='Beta_y')
# plt.legend(loc=2)
# plt.xticks(n_bins, names)
# plt.show()