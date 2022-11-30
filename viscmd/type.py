import os

string = "string"
file = "file"
savefile = "savefile"
directory = "directory"
netdev = 'netdev'


def list_netdev():
    return os.listdir('/sys/class/net')


all_get_values = {
    netdev: list_netdev,
}

