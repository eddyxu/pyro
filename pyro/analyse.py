# Copyright 2012 (c) Lei Xu <eddyxu@gmail.com>
#

"""Helper routines to analyse various forms of data."""

import numpy as np
import operator

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

    @see http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
    """
    return sorted(data.iteritems(), key=operator.itemgetter(1),
                  reverse=reverse)
