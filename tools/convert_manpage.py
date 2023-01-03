#!/usr/bin/env python3

import json
import re
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('require arg: <cmd>\n')
        sys.exit(1)
    cmd = sys.argv[1]
    status, output = subprocess.getstatusoutput(f"man {cmd} | col -b")
    if status != 0:
        sys.stderr.write("failed to read man page")
        return
    lines = output.splitlines()
    args = []
    arg_pattern = re.compile(
        r"^\s*(-[\w-]+)?(\s+|=)?([^\s]+)?(,\s*(-[\w-]+)?(\s+|=)?([^\s]+)?)?(\s{3,}([^\s].*)?$|\s*$)")
    arg = None
    version_arg = None
    begin_parsing = False
    for i in range(len(lines)):
        raw_line = lines[i].rstrip()
        if len(raw_line) == 0:
            arg = None
            continue
        if not raw_line[0].isspace():
            if raw_line.startswith('OPTIONS') \
                    or raw_line.startswith('ARGUMENTS') \
                    or raw_line.startswith('DESCRIPTION'):
                begin_parsing = True
            arg = None
            continue
        if not begin_parsing:
            arg = None
            continue
        line = raw_line.strip()
        if line.isspace() or line == '':
            arg = None
            continue
        sys.stderr.write(raw_line)
        m = arg_pattern.match(line)
        if m:
            kw = m.group(1)
            alias = m.group(5)
            sep = m.group(6) or m.group(2)
            varname = m.group(7) or m.group(3)
            helpstr = m.group(9)
            if kw is not None or (varname is not None and varname.isupper()):
                sys.stderr.write('\t# found arg\n')
                arg = {}
                if kw:
                    arg['keyword'] = kw
                if alias:
                    arg['alias'] = alias
                if varname:
                    arg['variable'] = varname.strip('<>[]')
                    if sep is not None and not sep.isspace():
                        arg['seperator'] = sep
                if helpstr:
                    arg['help'] = helpstr.strip()
                args.append(arg)
                continue
            else:
                sys.stderr.write('\t# match but no arg\n')
        else:
            sys.stderr.write('\t# not match\n')
        if arg is not None:
            if 'help' not in arg:
                arg['help'] = line.lstrip()
            else:
                arg['help'] += line.strip('\r\n\t')

    cmd_obj = {
        "command": cmd,
        "show_version": "",
        "supported_versions": [],
        "arguments": args,
    }

    for arg in args:
        if 'help' in arg and 'version' in arg['help'] and arg['keyword'].lower() in ['-v', '-version', '--version']:
            version_arg = arg
            break

    if version_arg is not None:
        status, output = subprocess.getstatusoutput(
            f"{cmd} {version_arg['keyword']} | head -n1")
        if status != 0:
            sys.stderr.write("failed to get version")
            return
        version = output.strip()
        cmd_obj["show_version"] = f"{cmd} {version_arg['keyword']}"
        cmd_obj["supported_versions"] = [version]

    json.dump(cmd_obj, sys.stdout, indent=2)


if __name__ == '__main__':
    main()
