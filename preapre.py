# encoding=utf-8
import os
import re
from copy import copy

import requests
from blessings import Terminal

from download import MultiDownloader
from download import ensure_path
from download import get_default_filename
from utils import dump_to
from utils import load_json_from
from utils import load_template
from utils import memoize
from utils import print_dict

TOOL_PATH = os.path.abspath(os.path.dirname(__file__))
DIST_PATH = 'dist'
DIST_CONFIG = os.path.join(DIST_PATH, 'config.json')

DCE_OFFLINE = 'http://get.daocloud.io/dce/'
DOCKER_OFFLINE = 'https://get.daocloud.io/docker-offline'
COMPOSE_URL = 'https://get.daocloud.io/docker/compose/releases/download/{version}/docker-compose-Linux-x86_64'
DCE_OFFLINE_RE = r'<a href="(?P<url>.*?)">dce-(?P<version>\d+.\d+.\d+).*</a>'
DOCKER_OFFLINE_RE = r'<a href="(?P<url>.*?)">docker-(?P<version>\d+.\d+.\d+)-(?P<lsb>\w*)-(?P<lsb_version>\d+.\d+).*</a>'


class NoSuchVersion(Exception):
    def __init__(self, name):
        self.message = 'no such version of %s' % name


@memoize
def get_releases_of_compose():
    tags_url = 'https://api.github.com/repos/docker/compose/releases'
    r = requests.get(tags_url)
    return [
        {
            'version': i['tag_name'],
            'url': COMPOSE_URL.format(version=i['tag_name'])
        }
        for i in r.json()
        ]


def _get_releases_of(name, url, regex):
    r = requests.get(url)
    return [m.groupdict() for m in re.finditer(regex, r.content)]


@memoize
def get_releases_of_docker():
    return _get_releases_of('docker', DOCKER_OFFLINE, DOCKER_OFFLINE_RE)


@memoize
def get_releases_of_dce():
    return _get_releases_of('dce', DCE_OFFLINE, DCE_OFFLINE_RE)


def latest(r):
    return r[0]


def make_config(config=None):
    """
    :type config: dict
    """
    if not config:
        if os.path.isfile(DIST_CONFIG):
            config = load_json_from(DIST_CONFIG)
        else:
            config = {}

    def get_url(name, conf, releases=None):
        if not conf:
            return latest(releases())
        if 'url' in conf:
            return conf
        if isinstance(conf, (str, unicode)):
            for r in releases():
                if r['version'].lower() == conf.lower():
                    return r
            raise NoSuchVersion(name)
        for r in releases():
            count = len(conf)
            for k, v in conf.items():
                if r.get(k).lower() == v.lower():
                    count -= 1
            if not count:
                return r
        raise NoSuchVersion(name)

    _config = copy(config)
    _config['dce'] = get_url('dce', config.get('dce'), get_releases_of_dce)
    _config['docker'] = get_url('docker', config.get('docker'), get_releases_of_docker)
    _config['compose'] = get_url('compose', config.get('compose'), get_releases_of_compose)
    return _config


def prepare(config=None):
    term = Terminal()
    print("Preparing urls ...\n")
    config = make_config(config)
    ensure_path(DIST_PATH)
    urls = {k: v['url'] for k, v in config.items() if hasattr(v, '__iter__') and 'url' in v}
    print('=' * 50 + '\n')
    print_dict({k: v for k, v in config.items() if k in urls})
    print('\n' + '=' * 50)
    print("\nStart Downloading ...\n")
    dump_to(config, DIST_CONFIG)
    try:
        MultiDownloader(urls.values(), DIST_PATH).download()
    except:
        pass
    print("\nGenerating install.sh ...\n")
    n = {k: get_default_filename(v) for k, v in urls.items()}
    install_template = load_template('installer_template.sh')
    install_script = install_template(n)
    with open(os.path.join(DIST_PATH, 'install.sh'), 'w') as f:
        f.write(install_script)
        os.fchmod(f.fileno(), 0b111101101)
    print(term.green("All Done!\nNow you can run install to setup you cluster!"))


def main():
    prepare(load_json_from('config.json'))


if __name__ == '__main__':
    main()
