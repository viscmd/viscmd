import os
import subprocess

string = "string"
file = "file"
savefile = "savefile"
directory = "directory"
netdev = 'netdev'
netns = 'netns'
bridge = 'bridge'


def list_netdev():
    return os.listdir('/sys/class/net')


def list_netns():
    return os.listdir('/run/netns')


def list_bridge():
    return subprocess.getoutput("ip -br link show type bridge | awk '{print $1}'").splitlines()


all_get_choices = {
    netdev: list_netdev,
    netns: list_netns,
    bridge: list_bridge,
}
