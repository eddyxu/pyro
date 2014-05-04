#!/usr/bin/env python
#
# Copyright 2014 (c) Lei Xu <eddyxu@gmail.com>
# License: BSD License.

"""Offers a set of functions to analysis benchmark results.
"""

import numpy as np
import os
import operator


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


def sorted_by_value(data, reverse=True):
    """Sorted a directory by its value

    @param data a directory
    @return a sorted list of tuples: [ (k0, v0), (k1, v1) ]

    @see http://bit.ly/gh7OA
    """
    return sorted(data.items(), key=operator.itemgetter(1),
                  reverse=reverse)


def are_all_zeros(data):
    """are all items in the given data zeros.
    """
    if type(data) == dict:
        for _, value in data.items():
            if value != 0:
                return False
    else:
        for item in data:
            if item != 0:
                return False
    return True


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
                if key not in data:
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
            leaves = []
            for key in sorted(tree.keys()):
                node = tree[key]
                if type(node) in [dict, list, set, tuple]:
                    leaves.extend(collect_leaf(node, leaf))
                elif not targeted_key or key == leaf:
                    leaves.append(node)
            return leaves

        results = []
        node = self.__getitem__(index)
        if type(node) == dict:
            targeted_key = None
            if 'key' in kwargs:
                targeted_key = kwargs['key']
            results = collect_leaf(node, targeted_key)
        return results
