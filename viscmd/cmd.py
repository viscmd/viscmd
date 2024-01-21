import fnmatch
import glob
import json
import re
import sys
from collections import OrderedDict

from .config import config
from .type import *


class Argument:
    def __init__(self):
        self.keyword = ""
        self.alias = ""
        self.required = False

        self.separator = " "
        self.variable = ""
        self.type = ""
        self.choices = []
        self.default = None

        self.repeatable = False
        self.group = ""
        self.help = ""
        self.display_order = None
        self.file_extensions = []
        self.one_of = []
        self.args = []

    def load(self, data: dict):
        for k, v in data.items():
            if k == '' or k.startswith('_'):
                continue
            if k == 'one_of' or k == 'arguments':
                args = []
                for arg_dict in v:
                    arg = Argument()
                    arg.load(arg_dict)
                    args.append(arg)
                if k == 'arguments':
                    self.args = args
                else:
                    self.one_of = args
            else:
                setattr(self, k, v)

    def get_choices(self):
        if len(self.choices) > 0:
            return self.choices

        get_choices = all_get_choices.get(self.type)
        if get_choices is not None:
            return get_choices()

        return []

    def dump(self, values, indent):
        sys.stdout.write('%s%s kw: %s var: %s' % (indent, id(self), self.keyword, self.variable))
        arg_values: OrderedDict
        arg_values = values.get(self)
        if arg_values is not None:
            a = []
            for arg_value in arg_values.values():
                if arg_value.value is not None:
                    checked = '[Y]' if arg_value.checked else '[ ]'
                    a.append("%s: %s" % (checked, arg_value.value))
            sys.stdout.write(' values: { %s }' % ', '.join(a))

        print()

        if self.args:
            for arg in self.args:
                arg.dump(values, indent + '    ')
        if self.one_of:
            for arg in self.args:
                arg.dump(values, indent + '    ')


class ArgValue:
    def __init__(self):
        self.arg: Argument = None
        self.value = None
        self.checked: bool = False
        self.sub_arg_values = {}

    def new_arg_value(self, arg: Argument):
        values = self.sub_arg_values
        if arg not in values:
            values[arg] = OrderedDict()

        av = ArgValue()
        av.arg = arg
        values[arg][av] = av
        return av

    def update_status(self, checked: bool):
        self.checked = checked

    def set_value(self, value):
        self.value = value


def get_args_ordered(args):
    if args is None:
        return []
    ordered = [arg for arg in args if arg.display_order is not None]
    ordered.sort(key=lambda arg: arg.display_order)
    ordered.extend([arg for arg in args if arg.display_order is None])
    return ordered


def generate(args, arg_values) -> str:
    ss = []
    for arg in args:
        avs: OrderedDict = arg_values.get(arg)
        if avs is None:
            continue
        av: ArgValue
        for av in avs.values():
            if not av.checked:
                continue
            s = arg.keyword
            if arg.variable != "":
                if s != '':
                    s += arg.separator
                if av.value is not None:
                    s += av.value
                else:
                    s += arg.variable  # use the name as variable value
            ss.append(s)
            if arg.args or arg.one_of:
                if arg.args:
                    s = generate(arg.args, av.sub_arg_values)
                    if s != '':
                        ss.append(s)
                if arg.one_of:
                    s = generate(arg.one_of, av.sub_arg_values)
                    if s != '':
                        ss.append(s)

    return ' '.join(ss)


class Command:
    def __init__(self):
        self.name = ''
        self.args = []  # argument definitions
        self.values = {}  # argument values
        self.subcommands = OrderedDict()
        self.groups = OrderedDict()

    def load(self, data):
        self.name = data['command']
        if data.get('arguments') is not None:
            groups = {}
            for a in data['arguments']:
                arg = Argument()
                arg.load(a)
                self.args.append(arg)
                group = groups.get(arg.group, [])
                group.append(arg)
                groups.setdefault(arg.group, group)
            group_names = groups.keys()
            for name in sorted(group_names):
                if len(group_names) > 1 and name == '':
                    self.groups['(default)'] = groups[name]
                else:
                    self.groups[name] = groups[name]
        if data.get('subcommands') is not None:
            for sub in data['subcommands']:
                c = Command()
                c.load(sub)
                self.subcommands[c.name] = c

    def get_cmd_line(self) -> str:
        return f"{self.name} {generate(self.args, self.values)}"

    def new_arg_value(self, arg: Argument) -> ArgValue:
        values = self.values
        if arg not in values:
            values[arg] = OrderedDict()

        av = ArgValue()
        av.arg = arg
        values[arg][av] = av
        return av

    def get_group(self, group):
        args = self.groups.get(group)
        if args is None:
            return []
        return get_args_ordered(args)

    def dump(self):
        print('----------------------------------------------------------------')
        arg: Argument
        for arg in self.args:
            arg.dump(self.values, '')
        print('----------------------------------------------------------------')


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
