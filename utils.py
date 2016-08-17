# encoding=utf-8
import functools
import inspect
import json
import string


def print_dict(d, prefix=''):
    """
    :type d: dict
    """
    for k, v in d.items():
        if isinstance(v, dict):
            print('%s%s:' % (prefix, k))
            print_dict(v, prefix + ' ' * 4)
        else:
            print('%s%s = %s' % (prefix, k, v))


def memoize(fn):
    cache = fn.cache = {}

    @functools.wraps(fn)
    def _memoize(*args, **kwargs):
        kwargs.update(dict(zip(inspect.getargspec(fn).args, args)))
        key = tuple(kwargs.get(k, None) for k in inspect.getargspec(fn).args)
        if key not in cache:
            cache[key] = fn(**kwargs)
        return cache[key]

    return _memoize


def load_json_from(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def dump_to(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


class Template(string.Template):
    delimiter = '^^'


def load_template(filename):
    with open(filename, 'r') as f:
        s = f.read()
        return Template(s).substitute
