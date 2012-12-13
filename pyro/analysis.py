#!/usr/bin/env python
#
# Copyright 2012 (c) Lei Xu <eddyxu@gmail.com>
# License: BSD License.

"""Offers a set of functions to analysis benchmark results.
"""

import numpy as np
import operator
import os
import plot as mfsplot
import re


def average_for_each_key(data):
    """Calculate the average values of each fields

    It accept input data from two forms:
     1) dict(key1: [values...], key2: [values]...)
     2) [{key1:value1, key2,value2}, {key1:value3, key2:value4}...]

    @param data
    @return avarage value of each field
    """
    if not data:
        return {}
    results = {}
    if type(data) == list:
        for key in data[0]:
            total = 0.0
            count = 0
            for item in data:
                total += item[key]
                count += 1
            results[key] = float(total) / count
    elif type(data) == dict:
        for key, value in data.iteritems():
            results[key] = np.average(value)
    else:
        assert False
    return results


def auto_label(axe, rects):
    """Automatically add value labels to bars

    @param axe
    @param rects
    """
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        axe.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                '%0.2f%%' % float(height), ha='center', va='bottom')


def sorted_by_value(data, reverse=True):
    """Sorted a directory by its value

    @param data a directory
    @return a sorted list of tuples: [ (k0, v0), (k1, v1) ]

    @see http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
    """
    return sorted(data.iteritems(), key=operator.itemgetter(1),
                  reverse=reverse)


def are_all_zeros(data):
    """are all items in the given data zeros.
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


def parse_procstat_data(filename):
    """ parse /proc/stat data, return system time, user time, etc.
    @param before_file
    @param after_file
    @return delta value of sys time, user time, iowait in a dict
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
                result['user'] = (float(items[1]) - temp_before['user']) \
                                    * real_time_ratio
                result['system'] = (float(items[3]) - temp_before['system'])\
                                    * real_time_ratio
                result['idle'] = (float(items[4]) - temp_before['idle']) \
                                    * real_time_ratio
                result['iowait'] = (float(items[5]) - temp_before['iowait'])\
                                    * real_time_ratio

    return result


def parse_lockstat_data(filepath):
    """
    @param before_file
    @param after_file
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


def get_top_n_funcs_in_oprofile(data, event, topn):
    """Extract top N results of oprofile data

    @param data the oprofile parsed data
    @param event event name
    @param n top N
    """
    temp = {}
    for func_name in data.keys():
        temp[func_name] = data[func_name][event]['%']
    return dict(sorted_by_value(temp, reverse=True)[:topn])


def trans_top_data_to_curves(data, **kwargs):
    """Form the top curves

    @param data Preprocessed top N data. A dictionary:
                { thread: {field0: value, field1: value...}, ...}

    Optional arguments:
    @param show_all If it is set to True, then show the universal set of all
                    fields occured in all thread configurations. Otherwise,
                    Only show the common part (intersection) in all
                    configurations. Default value is False.

    @return a list of curves
        [ ([threads], [values], field0), ([threads], [values], field1), ...]
    """
    show_all = kwargs.get('show_all', False)
    threshold = kwargs.get('threshold', 0)

    fields = set()
    for field_data in data.values():
        # field_data is {field0: value, field1: value} for each thread/core
        # configuration.
        data_fields = set(field_data.keys())
        if not fields:
            fields = data_fields
            continue

        if show_all:
            # Universal set
            fields |= data_fields
        else:
            # Intersection
            fields &= data_fields

    threads = sorted(data)
    curves = []
    for field in fields:
        values = []
        for thd in threads:
            try:
                values.append(data[thd][field])
            except KeyError:
                values.append(0)
        if threshold and not filter(lambda x: x > threshold, values):
            continue
        curves.append((threads, values, field))
    return curves


def draw_top_functions(data, event, top_n, outfile, **kwargs):
    """Draw top N functions on one oprofile event

    @param data a directory of oprofile data, { thread: oprofile_data, ... }
    @param event event name
    @param top_n only draw top N functions
    @param outfile output file path

    Optional args:
    @param title the title of the plot (default: 'Oprofile (EVENT_NAME)')
    @param xlabel the label on x-axes (default: 'Number of Threads')
    @param ylabel the label on y-axes (default: 'Samples (%)')
    @param show_all If set to True, shows all functions occured on any oprofile
       outputs. Otherwise, it only shows the common functions occured on all
       oprofile outputs. The default value is False.
    @param threshold Only output the functions that have values larger than the
        threshold
    @param loc set legend location.
    @param ncol set the number of columns of legend.
    """
    # Preprocess optional args
    title = kwargs.get('title', 'Oprofile (%s)' % event)
    xlabel = kwargs.get('xlabel', '# of Cores')
    ylabel = kwargs.get('ylabel', 'Samples (%)')
    show_all = kwargs.get('show_all', False)
    threshold = kwargs.get('threshold', 0)
    loc = kwargs.get('loc', 'upper left')
    ncol = kwargs.get('ncol', 2)

    top_n_data = {}
    for thd, op_data in data.iteritems():
        top_n_data[thd] = get_top_n_funcs_in_oprofile(op_data, event, top_n)

    curves = trans_top_data_to_curves(top_n_data, show_all=show_all,
                                     threshold=threshold)

    mfsplot.plot(curves, title, xlabel, ylabel, outfile, ncol=ncol, loc=loc)


def get_top_n_locks(data, field, n, **kwargs):
    """Get top n locks according to the statistic on a field

    @param data the data from parse_lockstat_data
    @param field specify one field to sort (e.g. waittime-total, acquisitions and etc.)
    @param n only return the top N values

    Optional arguments
    @param percentage if set to True, returns the percentage of the specified field.
    @param in_second if set to True, returns the value in seconds.

    TODO: add support for sorting values per acquisition
    """
    percentage = kwargs.get('percentage', False)
    in_second = kwargs.get('in_second', False)
    assert not (percentage and in_second)

    temp = {}
    for lockname, values in data.iteritems():
        temp[lockname] = values[field]

    if percentage:
        total_value = sum(temp.values())
        for lockname, value in temp.iteritems():
            temp[lockname] = 1.0 * value / total_value
    elif in_second:
        # Returns values in second
        for lockname, value in temp.iteritems():
            temp[lockname] = value / (10.0**6)
    return dict(sorted_by_value(temp, reverse=True)[:n])


def split_filename(fname, sep='_'):
    """Split filename into a meaningful slices
    """
    basename = os.path.basename(fname)
    results = os.path.splitext(basename)[0].split(sep)
    return results


class Result(object):
    """A simple way to present result
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
        """Create the sub directionaries if they are not existed
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
        """Access the underlying data
        """
        return self.data_

    def keys(self):
        """Return a list of the keys in the underlying directory
        """
        return self.data_.keys()

    def collect(self, *index, **kwargs):
        """Collect all values according to the given criterials
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
