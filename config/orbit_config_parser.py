import re

def load_config_orbit(conf_name, DIR):
    conf_file = open(conf_name, "r")
    configuration = conf_file.readlines()
    control_sum = 0

    def load_chans(i_b, data):
        chans_sett = {}
        while True:
            result = re.match(r'(\w+)', data[i_b])
            if result:
                chan_name = result.group()
                chans_sett[chan_name] = {}
                chans_sett[chan_name].update({elem.split('=')[0]: elem.split('=')[1]
                                               for elem in re.findall(r'\s(\S+=\w+:\S+)', data[i_b])})
                chans_sett[chan_name].update({elem.split('=')[0]: int(elem.split('=')[1])
                                               for elem in re.findall(r'\s(\S+=\d+)', data[i_b])})
            i_b += 1
            if data[i_b] == '[end]\n' or data[i_b] == '[end]':
                return i_b, chans_sett

    def load_list(i_b, data):
        d_str = ''
        d_list = []
        while True:
            d_str += data[i_b][:-1]
            i_b += 1
            if data[i_b] == '[end]\n' or data[i_b] == '[end]':
                d_list = d_str.split(',')
                return i_b, d_list

    def load_coor(i_b, data):
        d_str = ''
        d_list = []
        coor_list = []
        while True:
            d_str += data[i_b][:-1]
            i_b += 1
            if data[i_b] == '[end]\n' or data[i_b] == '[end]':
                d_list = d_str.split(',')
                for elem in d_list:
                    coor_list.append(float(elem))
                return i_b, coor_list

    def load_mode_filenames(i_b, data):
        mode_d = {}
        while True:
            mode_d[re.findall(r'(\S+)', data[i_b])[0]] = DIR + '/' + re.findall(r'(\S+)', data[i_b])[1]
            i_b += 1
            if data[i_b] == '[end]\n' or data[i_b] == '[end]':
                return i_b, mode_d

    i = 0
    while i < len(configuration):
        if configuration[i] == '[chans_list]\n':
            control_sum += 1
            i_next, chans_config_sett = load_chans(i + 1, configuration)
            i = i_next
        elif configuration[i] == '[bpm_list]\n':
            control_sum += 1
            i_next, bpm_config_sett = load_list(i + 1, configuration)
            i = i_next
        elif configuration[i] == '[bpm_coor]\n':
            control_sum += 1
            i_next, bpm_coor = load_coor(i + 1, configuration)
            i = i_next
        elif configuration[i] == '[client_list]\n':
            control_sum += 1
            i_next, client_config_sett = load_list(i + 1, configuration)
            i = i_next
        elif configuration[i] == '[mode_files]\n':
            control_sum += 1
            i_next, mode_d = load_mode_filenames(i + 1, configuration)
            i = i_next
        i += 1

    if control_sum == 5:
        return {'chans_conf': chans_config_sett, 'bpm_conf': bpm_config_sett, 'client_conf': client_config_sett,
                'mode_d': mode_d, 'bpm_coor': bpm_coor}
    else:
        print('wrong control_sum: orbitd config file is incomplete')