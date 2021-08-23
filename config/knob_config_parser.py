import re

def load_config_knob(conf_name):
    config_sett = {}
    conf_file = open(conf_name, "r")
    for line in conf_file.readlines():
        if line[0] == '#':
            pass
        else:
            result = re.match(r'(\w+)', line)
            if result:
                chan_name = result.group()
                config_sett[chan_name] = {}
                config_sett[chan_name].update({elem.split('=')[0]: elem.split('=')[1]
                                               for elem in re.findall(r'\s(\S+=\w+:\S+)', line)})
                config_sett[chan_name].update({elem.split('=')[0]: int(elem.split('=')[1])
                                               for elem in re.findall(r'\s(\S+=\d+)', line)})

    return config_sett
