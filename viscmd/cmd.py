
import json
import os
from collections import OrderedDict

from .config import config
from .type import *


class Argument:
    def __init__(self):
        self.keyword = ""
        self.alias = ""
        self.required = False

        self.seperator = " "
        self.variable = ""
        self.type = ""
        self.choices = []
        self.default = None

        self.repeat = False
        self.section = ""
        self.help = ""

    def load(self, data: dict):
        for k, v in data.items():
            if k == '' or k.startswith('_'):
                continue
            setattr(self, k, v)

    def get_values(self):
        if len(self.choices) > 0:
            return self.choices

        get_values = all_get_values.get(self.type)
        if get_values is not None:
            return get_values()

        return []


class ArgValue:
    def __init__(self):
        self.ad: Argument = None
        self.value = None
        self.checked: bool = False

    def update_status(self, checked: bool):
        self.checked = checked

    def set_value(self, value):
        self.value = value

    def get_value_str(self):
        if self.value is None:
            return self.ad.variable  # use the name as variable value
        if ' ' in self.value:
            return "'" + self.value + "'"
        else:
            return self.value

    def __str__(self):
        if self.ad.variable is None:
            return self.ad.keyword
        if self.ad.keyword == '':
            return self.get_value_str()
        else:
            return '%s%s%s' % (self.ad.keyword, self.ad.seperator, self.get_value_str())


class Command:
    def __init__(self):
        self.name = ''
        self.args = []  # argument definitions
        self.values = {}  # argument values
        self.subcommands = OrderedDict()
        self.sections = OrderedDict()

    def load(self, data):
        self.name = data['command']
        if data.get('arguments') is not None:
            for a in data['arguments']:
                ad = Argument()
                ad.load(a)
                self.args.append(ad)
                section = self.sections.get(ad.section, [])
                section.append(ad)
                self.sections.setdefault(ad.section, section)
        if data.get('subcommands') is not None:
            for sub in data['subcommands']:
                c = Command()
                c.load(sub)
                self.subcommands[c.name] = c

    def get_cmd_line(self) -> str:
        return f"{self.name} {self.get_arg_line()}"

    def get_arg_line(self) -> str:
        ss = []
        for ad in self.args:
            avs: OrderedDict = self.values.get(ad)
            if avs is None:
                continue
            av: ArgValue
            for av in avs.values():
                if not av.checked:
                    continue
                ss.append(str(av))
        return ' '.join(ss)

    def new_arg_value(self, ad: Argument) -> ArgValue:
        if ad not in self.values:
            self.values[ad] = OrderedDict()
        av = ArgValue()
        av.ad = ad
        self.values[ad][av] = av
        return av

    def del_arg_value(self, av: ArgValue):
        if self.values[av.ad] is None:
            return
        self.values[av.ad].pop(av, None)


def load_command(name: str):
    basename = name.split()[0]
    filename = f'{basename}.json'
    path_found = ''
    for d in [config.cmd_dir_user, config.cmd_dir_sys]:
        for lang in [config.lang_prefer, config.lang_alt]:
            path = os.path.join(d, lang, filename)
            if os.path.exists(path):
                path_found = path
                break
    if path_found == '':
        return
    with open(path_found) as f:
        data = json.load(f)
    cmd = Command()
    cmd.load(data)

    if cmd.name == name:
        return cmd
    if cmd.subcommands is not None:
        for sub in cmd.subcommands:
            if sub.name == name:
                return sub
    return None

