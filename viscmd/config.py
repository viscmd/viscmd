# static config
import json
import os.path


def _get_config_path():
    return '$HOME/.config/viscmd.json'


_config_path = os.path.expandvars(_get_config_path())


class Config:
    def __init__(self):
        self.cmd_dir = '/var/lib/viscmd'
        self.lang_prefer = 'en_US'
        self.lang_alt = 'zh_CN'

        self._keys = ['cmd_dir', 'lang_prefer', 'lang_alt']

    def load(self):
        with open(_config_path) as f:
            data = json.load(f)
        for key in self._keys:
            v = data.get(key, '')
            if v != '':
                setattr(self, key, v)
        self.cmd_dir = os.path.expandvars(self.cmd_dir)

    def save(self):
        data = {}
        for key in self._keys:
            data[key] = getattr(self, key)
        with open(_config_path, 'w') as f:
            json.dump(data, f, indent=4)


config = Config()


def _init():
    global config

    if os.path.exists(_config_path):
        config.load()
    else:
        config.save()


_init()
