#!/usr/bin/python
# encoding=utf-8
from __future__ import print_function

import math
import os
import time
from threading import Thread

import requests
from blessings import Terminal
from progressive.bar import Bar
from progressive.tree import BarDescriptor, ProgressTree, Value
from requests.packages import urllib3

urllib3.disable_warnings()


class ExitFlag(Exception):
    is_exit = False

    def check(self):
        if self.is_exit:
            raise ExitFlag('Exited')

    def exit(self):
        self.is_exit = True


class StreamInfo(object):
    def __init__(self, name):
        self.name = name
        self.total = 0
        self.size = 0
        self.speed = 0
        self.progress = 0

    def info(self, total, size):
        self.total = total
        self.size = size
        self.speed += CHUNK_SIZE
        self.progress = size * 100 / total

    def clear_speed(self):
        self.speed = 0


TEMP_EXT_NAME = '.dce-tool.tmp'
USER_AGENT = 'dce-tool'
CHUNK_SIZE = 2048
PROGRESS_INTERVAL = 0.5


def convertSize(size):
    if (size == 0):
        return '0B'
    size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])


def touch(filename):
    open(filename, 'ab+').close()


def get_default_filename(name):
    return name.split('/')[-1].split('?')[0]


def download(url, filename=None, path='', stream_info=None, exit_flag=None):
    """
    :param exit_flag: if cancel download
    :type exit_flag: ExitFlag
    """
    ensure_path(path)
    exit_flag = exit_flag or ExitFlag()
    stream_info = stream_info or StreamInfo(url)
    finished = False
    filename = os.path.join(path, filename or get_default_filename(url))
    tmp_filename = filename + TEMP_EXT_NAME
    if os.path.isfile(tmp_filename):
        with open(tmp_filename, 'rb') as f:
            start = int(f.read())
    else:
        start = 0
    size = start + 1
    headers = {
        'User-Agent': USER_AGENT,
        'Range': 'bytes=%d-' % start
    }
    r = requests.get(url, stream=True, verify=False, headers=headers)
    if not 'content-range' in r.headers:
        start = 0
        total = int(r.headers.get('content-length', 0))
    else:
        total = int(r.headers.get('content-range', '0').split('/')[-1])
    with open(filename, 'ab+') as f:
        if start == 0 and f.tell() == total:
            stream_info.info(total, total)
            return
        f.seek(start)
        f.truncate()
        touch(tmp_filename)
        try:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                exit_flag.check()
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
                    f.flush()
                stream_info.info(total, size)
            finished = True
            os.remove(tmp_filename)
        except (ExitFlag, KeyboardInterrupt):
            print("Download thread %s exited." % filename)
        finally:
            if not finished:
                with open(tmp_filename, 'wb') as tmp:
                    tmp.write(str(size))


def ensure_path(path):
    if path and not os.path.isdir(path):
        if os.path.isfile(path):
            raise NameError("Path %s already exist and it's not a dir." % path)
        os.mkdir(path)


class MultiDownloader(object):
    def __init__(self, urls, path=''):
        """
        :param urls: list of urls
        """
        self.path = path
        self.urls = urls
        self.exit_flag = ExitFlag()

    def build_progress_tree(self, info_list):
        """
        :type info_list: list of StreamInfo
        """
        tree = {}
        for index, i in enumerate(info_list):
            filename = get_default_filename(i.name)
            size = convertSize(i.size / 1024)
            total = convertSize(i.total / 1024)
            name = '{index}.  {file}{space}{size}/{total}{space3}'.format(
                index=index + 1,
                file=filename,
                space=' ' * (50 - len(filename)),
                size=size,
                total=total,
                space3=' ' * 5
            )
            tree[name] = BarDescriptor(value=Value(i.progress), type=Bar)
        speed = convertSize(sum([i.speed for i in info_list]) / 1024 / PROGRESS_INTERVAL) + '/s'
        [i.clear_speed() for i in info_list]
        title = 'Total:'
        if speed:
            title = 'Total:%s%s' % (' ' * (40 - len(title) - len(speed)), speed)
        return {title: tree}

    def download(self):
        ensure_path(self.path)
        threads = []
        info_list = []
        try:
            for index, url in enumerate(self.urls):
                info = StreamInfo(url)
                info_list.append(info)
                thread = Thread(target=download, args=(url, None, self.path, info, self.exit_flag))
                thread.start()
                threads.append(thread)
            running = lambda: bool([t for t in threads if t.isAlive()])
            term = Terminal()
            progress = ProgressTree(term=term)
            progress.make_room(self.build_progress_tree(info_list))
            while running():
                time.sleep(PROGRESS_INTERVAL)
                progress.cursor.restore()
                progress.draw(self.build_progress_tree(info_list))
            print('\nDone.')
        except KeyboardInterrupt:
            self.exit_flag.exit()
            print("\nCanceling...")
            [t.join() for t in threads]


if __name__ == '__main__':
    MultiDownloader(['https://dn-dao-get.qbox.me/docker/docker-1.12.0-ubuntu-16.04.tar.gz',
                     'http://dao-get.daocloud.io/dce/dce-1.4.0.tar.gz'], 'dl').download()
    # MultiDownloader(['https://dn-dao-get.qbox.me/docker/docker-1.12.0-ubuntu-16.04.tar.gz'], 'dl').download()
    # download('http://dao-get.daocloud.io/dce/dce-1.4.0.tar.gz')
