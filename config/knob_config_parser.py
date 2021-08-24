import re

def load_config_knob(conf_name):
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

    i = 0
    while i < len(configuration):
        if configuration[i] == '[chans_list]\n':
            control_sum += 1
            i_next, chans_config_sett = load_chans(i + 1, configuration)
            i = i_next
        i += 1

    if control_sum == 1:
        return {'chans_conf': chans_config_sett}
    else:
        print('wrong control_sum: orbitd config file is incomplete')
