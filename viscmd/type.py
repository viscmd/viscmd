import os
import subprocess

string = "string"
file = "file"
savefile = "savefile"
directory = "directory"
netdev = 'netdev'
netns = 'netns'
bridge = 'bridge'
blockdev = 'blockdev'
disk = 'disk'


def list_netdev():
    return os.listdir('/sys/class/net')


def list_netns():
    return os.listdir('/run/netns')


def list_bridge():
    return subprocess.getoutput("ip -br link show type bridge | awk '{print $1}'").splitlines()


def list_blockdev():
    return subprocess.getoutput("lsblk -n -p -l | awk '{print $1}'").splitlines()


def list_disk():
    return subprocess.getoutput("lsblk --nodeps -n -p | awk '{print $1}'").splitlines()


all_get_choices = {
    netdev: list_netdev,
    netns: list_netns,
    bridge: list_bridge,
    blockdev: list_blockdev,
    disk: list_disk,
}
