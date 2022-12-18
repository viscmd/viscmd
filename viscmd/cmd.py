import fnmatch
import glob
import json
import os
import re
import subprocess
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

        self.repeatable = False
        self.section = ""
        self.help = ""
        self.display_order = None

    def load(self, data: dict):
        for k, v in data.items():
            if k == '' or k.startswith('_'):
                continue
            setattr(self, k, v)

    def get_choices(self):
        if len(self.choices) > 0:
            return self.choices

        get_choices = all_get_choices.get(self.type)
        if get_choices is not None:
            return get_choices()

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
        return self.value

    def __str__(self):
        if self.ad.variable is None:
            return self.ad.keyword
        if self.ad.keyword == '':
            return self.get_value_str()
        else:
            return '%s%s%s' % (self.ad.keyword, self.ad.seperator, self.get_value_str())


def get_args_ordered(args):
    if args is None:
        return []
    ordered = [arg for arg in args if arg.display_order is not None]
    ordered.sort(key=lambda arg: arg.display_order)
    ordered.extend([arg for arg in args if arg.display_order is None])
    return ordered


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

    def get_section(self, section_name):
        args = self.sections.get(section_name)
        if args is None:
            return []
        return get_args_ordered(args)


_version_pattern_3 = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_version_pattern_2 = re.compile(r"(\d+)\.(\d+)")


def version_sort_key(s: str):
    m = _version_pattern_3.match(s)
    if m:
        return int(m.group(1)) * 1000000 + int(m.group(2)) * 1000 + int(m.group(3))
    m = _version_pattern_2.match(s)
    if m:
        return int(m.group(1)) * 1000000 + int(m.group(2)) * 1000
    else:
        raise


# https://stackoverflow.com/questions/23681948/get-index-of-closest-value-with-binary-search
# by Yaguang
def binarySearch(data, val):
    lo, hi = 0, len(data) - 1
    best_ind = lo
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if data[mid] < val:
            lo = mid + 1
        elif data[mid] > val:
            hi = mid - 1
        else:
            best_ind = mid
            break
        # check if data[mid] is closer to val than data[best_ind]
        if abs(data[mid] - val) < abs(data[best_ind] - val):
            best_ind = mid
    return best_ind


def find_closest_version(versions, version):
    vermap = {}
    verkeys = []
    for v in versions:
        k = version_sort_key(v)
        verkeys.append(k)
        vermap[k] = v

    i = binarySearch(sorted(verkeys), version_sort_key(version))
    k = verkeys[i]
    return vermap[k]


def locate_and_load(name: str, lang: str):
    prev_show_version = ""
    current_version = ""
    selected_path = ""
    selected_data = ""
    version_list = []
    version_map = {}
    file_pattern = f'{config.cmd_dir}/{lang}/{name}@*.json'
    for path in glob.glob(file_pattern):
        with open(path) as f:
            data = json.load(f)
        show_version = data.get('show_version', '')
        if show_version == '':
            continue
        if show_version != prev_show_version:
            prev_show_version = show_version
            current_version = subprocess.getoutput(show_version)
        for v in data['supported_versions']:
            if current_version == v:
                selected_path = path
                selected_data = data
                break
            if v.find('*') >= 0:
                if fnmatch.fnmatch(current_version, v):
                    selected_path = path
                    selected_data = data
                    break
            else:
                version_list.append(v)
                version_map[v] = {
                    'data': data,
                    'path': path
                }
        if selected_path != "":
            break

    if selected_path == "":
        # no definition found
        if len(version_list) == 0:
            return None

        if re.match(r"\d+\.\d+", current_version):
            v = find_closest_version(version_list, current_version)
        else:
            v = sorted(version_list)[-1]
        selected_data = version_map[v]['data']
        selected_path = version_map[v]['path']

    symlink = f'{config.cmd_dir}/{lang}/{name}.json'
    os.symlink(os.path.basename(selected_path), symlink)
    return selected_data


def load_command(name: str, lang: str):
    basename = name.split()[0]
    cmd_file = f'{basename}.json'
    path = os.path.join(config.cmd_dir, lang, cmd_file)
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = locate_and_load(basename, lang)
        if data is None:
            return None

    cmd = Command()
    cmd.load(data)

    if cmd.name == name:
        return cmd
    return None
