import re

def load_config_bpm(conf_name, bpm_name):
    conf_file = open(conf_name, "r")
    configuration = conf_file.readlines()
    bpm_find = False

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
        if configuration[i] == '[' + bpm_name + ']\n':
            bpm_find = True
            i_next, chans_config_sett = load_chans(i + 1, configuration)
            i = i_next
        i += 1

    if bpm_find:
        return chans_config_sett
    else:
        print(bpm_name + ' is absent in config file')