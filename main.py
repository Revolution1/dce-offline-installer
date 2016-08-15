import requests
import json
import os
import re
import inspect
import functools

TOOL_PATH = os.path.abspath(os.path.dirname(__file__))
DIST_PATH = 'dist'

DCE_OFFLINE = 'http://get.daocloud.io/dce/'
DOCKER_OFFLINE = 'https://get.daocloud.io/docker-offline'
COMPOSE_URL = 'https://get.daocloud.io/docker/compose/releases/download/{version}/docker-compose-Linux-x86_64'
DCE_OFFLINE_RE = r'<a href="(?P<url>.*?)">dce-(?P<version>\d+.\d+.\d+).*</a>'
DOCKER_OFFLINE_RE = r'<a href="(?P<url>.*?)">docker-(?P<version>\d+.\d+.\d+)-(?P<lsb>\w*)-(?P<lsb_version>\d+.\d+.\d+).*</a>'


def memoize(fn):
    cache = fn.cache = {}

    @functools.wraps(fn)
    def memoizer(*args, **kwargs):
        kwargs.update(dict(zip(inspect.getargspec(fn).args, args)))
        key = tuple(kwargs.get(k, None) for k in inspect.getargspec(fn).args)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]
    return memoizer


def get_releases_of(url, regex):
    r = requests.get(url)
    return [m.groupdict() for m in re.finditer(regex, r.content)]


def download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    return local_filename


def load_json_from(file):
    with open(file, 'r') as f:
        return json.load(f)


@memoize
def get_releases_of_compose():
    tags_url = 'https://api.github.com/repos/docker/compose/releases'
    r = requests.get(tags_url)
    return [
        {
            'version': i['tag_name'],
            'url':COMPOSE_URL.format(version=i['tag_name'])
        }
        for i in r.json()
    ]


@memoize
def get_releases_of_docker():
    return get_releases_of(DOCKER_OFFLINE, DOCKER_OFFLINE_RE)


@memoize
def get_releases_of_dce():
    return get_releases_of(DCE_OFFLINE, DCE_OFFLINE_RE)


def latest(releases):
    return releases[0]


def ensure_dist():
    if not os.path.isdir(DIST_PATH):
        os.mkdir(DIST_PATH)


def main():
    pass

if __name__ == '__main__':
    main()
