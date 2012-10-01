# Copyright 2012 (c) Lei Xu <eddyxu@gmail.com>
#

"""Helper routines to analyse various forms of data."""

import numpy as np
import operator
import re


def are_all_zeros(data):
    """Returns True if all items in the given container are zeros.
    """
    if type(data) == dict:
        for key in data:
            if data[key] != 0:
                return False
    else:
        for item in data:
            if item != 0:
                return False
    return True


def average_for_each_key(data):
    """Calculate the average values of each fields

    It accept input data from two forms:
     1) dict(key1: [values...], key2: [values]...)
     2) [{key1:value1, key2,value2}, {key1:value3, key2:value4}...]

    @param data
    @return avarage values of each field:
        {key1: avg(values), key2: avg(values), ...}
    """
    if not data:
        return {}
    results = {}
    if type(data) == list:
        keys = data[0].keys()
        for key in keys:
            total = 0.0
            count = 0
            for item in data:
                total += item[key]
                count += 1
            results[key] = float(total) / count
    elif type(data) == dict:
        for key in data.keys():
            results[key] = np.average(data[key])
    else:
        assert False
    return results


def sorted_by_value(data, reverse=True):
    """Sorted a directory by its value

    @param data a directory
    @return a sorted list of tuples: [ (k0, v0), (k1, v1) ]

    @see http://bit.ly/gh7OA
    """
    return sorted(data.iteritems(), key=operator.itemgetter(1),
                  reverse=reverse)


def parse_procstat_data(filename):
    """ parse /proc/stat data, return system time, user time, etc.
    @param filename the path of proc stat output.
    @return delta value of sys time, user time, iowait in a dict.
    """
    real_time_ratio = 100
    result = {}
    temp = 0
    temp_before = {}
    with open(filename) as fobj:
        for line in fobj:
            items = line.split()
            if temp == 0:
                temp_before['user'] = float(items[1])
                temp_before['system'] = float(items[3])
                temp_before['idle'] = float(items[4])
                temp_before['iowait'] = float(items[5])
                temp = temp + 1
            else:
                result['user'] = (float(items[1]) - temp_before['user']) * \
                    real_time_ratio
                result['system'] = (float(items[3]) - temp_before['system']) *\
                    real_time_ratio
                result['idle'] = (float(items[4]) - temp_before['idle']) * \
                    real_time_ratio
                result['iowait'] = (float(items[5]) - temp_before['iowait']) *\
                    real_time_ratio
    return result


def parse_lockstat_data(filepath):
    """
    @param filepath the lock stat file.
    @return delta values of each lock contetions
    """
    def _fetch_data(fname):
        """Read a lock stat file and extract data
        """
        result = {}
        with open(fname) as fobj:
            for line in fobj:
                match = re.match(r'.+:', line)
                if match:
                    items = line.split(':')
                    key = items[0][:-1].strip()
                    result[key] = np.array(
                        [float(x) for x in items[1].split()])
        return result

    results = {}
    raw_data = _fetch_data(filepath)
    fields = ['con-bounces', 'contentions',
              'waittime-min', 'waittime-max', 'waittime-total',
              'acq-bounces', 'acquisitions',
              'holdtime-min', 'holdtime-max', 'holdtime-total']
    for k, v in raw_data.iteritems():
        if are_all_zeros(v):
            continue
        if len(v) < fields:
            v = list(v)
            v.extend([0] * (len(fields) - len(v)))
        results[k] = dict(zip(fields, v))
    return results


def parse_oprofile_data(filename):
    """Parse data from oprofile output
    """
    result = {}
    with open(filename) as fobj:
        events = []
        for line in fobj:
            if re.match('^[0-9]+', line):
                data = line.split()
                symname = data[-1]
                result[symname] = {}
                for i in xrange(len(events)):
                    evt = events[i]
                    abs_value = int(data[i * 2])
                    percent = float(data[i * 2 + 1])
                    result[symname][evt] = {
                        'count': abs_value,
                        '%': percent
                    }
                continue
            if re.match('^Counted', line):
                events.append(line.split()[1])
                continue
    return result


def parse_postmark_data(filename):
    """Parse postmark result data
    """
    result = {}
    with open(filename) as fobj:
        for line in fobj:
            matched = re.search(
                r'Deletion alone: [0-9]+ files \(([0-9]+) per second\)', line)
            if matched:
                result['deletion'] = float(matched.group(1))

            matched = re.search(
                r'Creation alone: [0-9]+ files \(([0-9]+) per second\)', line)
            if matched:
                result['creation'] = float(matched.group(1))

            matched = re.search(
                r'[0-9\.]+ [a-z]+ read \(([0-9\.]+) ([a-z]+) per second\)',
                line)
            if matched:
                unit = matched.group(2)
                read_speed = float(matched.group(1))
                if unit == 'megabytes':
                    read_speed *= 1024
                result['read'] = read_speed

            matched = re.search(
                r'[0-9\.]+ [a-z]+ written \(([0-9\.]+) ([a-z]+) per second\)',
                line)
            if matched:
                unit = matched.group(2)
                write_speed = float(matched.group(1))
                if unit == 'megabytes':
                    write_speed *= 1024
                result['write'] = write_speed
    return result


class Result(object):
    """A simple way to present result
    TODO(eddyxu): Move this class to a more appropriate file.
    """
    def __init__(self, meta=None):
        """@param meta a string to describe the hierachical of result tree
        For example, a five-level hierachich could be:
            "workload.filesystem.disks.threads.iops"
        """
        self.data_ = {}
        self.depth = 0
        self.meta = []
        if meta:
            self.meta = meta.split('.')

    def __getitem__(self, keys):
        if type(keys) == tuple:
            data = self.data_
            for key in keys:
                if not key in data:
                    return None
                data = data[key]
            return data
        else:
            return self.data_[keys]

    def __setitem__(self, keys, value):
        if type(keys) != tuple:
            keys = tuple([keys])
        data = self.__prepare_data(keys[:-1])
        data[keys[-1]] = value
        if len(keys) > self.depth:
            self.depth = len(keys)

    def __prepare_data(self, keys):
        """Create the sub directionaries if they are not existed.
        """
        tmp = self.data_
        for key in keys:
            if not key in tmp:
                tmp[key] = {}
            tmp = tmp[key]
        return tmp

    def __iter__(self):
        return self.data_.__iter__()

    @property
    def data(self):
        """Access the underlying data.
        """
        return self.data_

    def keys(self):
        """Return a list of the keys in the underlying directory.
        """
        return self.data_.keys()

    def collect(self, *index, **kwargs):
        """Collect all values according to the given criterials.
        """
        def collect_leaf(tree, leaf):
            """Collect the leaf of a tree
            """
            results = []
            for key in tree.keys():
                node = tree[key]
                if type(node) in [dict, list, set, tuple]:
                    results.extend(collect_leaf(node, leaf))
                elif not targeted_key or key == leaf:
                    results.append(node)
            return results

        results = []
        node = self.__getitem__(index)
        if type(node) == dict:
            targeted_key = None
            if 'key' in kwargs:
                targeted_key = kwargs['key']
            results = collect_leaf(node, targeted_key)
        return results
