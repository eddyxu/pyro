# Useful routines for doing performance testing.
# Author: Lei Xu <eddyxu@gmail.com>
# License: BSD

"""Performance Test related functions.
"""

from subprocess import check_call as call
from pyro import osutil
import matplotlib.pyplot as plt
import numpy as np
import platform
import pyro.plot as mfsplot
from pyro.analysis import are_all_zeros, sorted_by_value
import re
import sys


def clear_cache():
    """Dump all dirty data and clear file system cache
    (including directory cache)..
    """
    osutil.check_root_or_exit('No enough privilege to clear cache')
    system = platform.system()
    if system == 'Linux':
        status = call('sync', shell=True)
        if status:
            print >> sys.stderr, 'clear_cache: error on do sync'
            return -1
        status = call('echo 3 > /proc/sys/vm/drop_caches', shell=True)
        if status:
            print >> sys.stderr, 'clear_cache: error on drop caches'
    else:
        print >> sys.stderr, \
            'Error: clear_cache(): unsupported system: %s' % system
        sys.exit(1)


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
                    last_colon = line.rfind(':')
                    key = line[:last_colon].strip()
                    values = line[last_colon + 1:].strip()
                    result[key] = np.array(
                        [float(x) for x in values.split()])
        return result

    results = {}
    raw_data = _fetch_data(filepath)
    fields = ['con-bounces', 'contentions',
              'waittime-min', 'waittime-max', 'waittime-total',
              'acq-bounces', 'acquisitions',
              'holdtime-min', 'holdtime-max', 'holdtime-total']
    for k, v in raw_data.items():
        if are_all_zeros(v):
            continue
        if len(v) < len(fields):
            v = list(v)
            v.extend([0] * (len(fields) - len(v)))
        results[k] = dict(zip(fields, v))
    return results


def parse_perf_data(filename, **kwargs):
    """Parses data from linux perf tool.

    @param filename the perf output file path.
    """
    top = kwargs.get('top', 10)
    result = {}
    with open(filename) as fobj:
        k = top
        event = None
        event_result = []
        for line in fobj:
            line = line.strip()
            if not event:
                if re.match(r'^# Samples:.*', line):
                    #print('matched: {}'.format(line))
                    event_name = line.split()[-1]
                    event = event_name.strip("'")
                continue
            if event and line[0] == '#':
                continue
            fields = line.split()
            percent = float(fields[0][:-1]) / 100
            event_result.append((percent, fields[1], fields[-1]))
            k -= 1
            if not k:
                result[event] = event_result
                event_result = []
                event = None
                k = top
                continue
    return result


def plot_top_perf_functions(data, event, top_n, outfile, **kwargs):
    """Plot the event curves for the top functions observed from Linux perf
    tool.

    @param data a dictionary of perf data, { thread: perf_data, ...}. The key
    of this directory is the number of process/thread/cpus to observed the
    data. The keys of this directory will be used as x axis of the figure.
    @param event event name
    @param top_n only draw top N functions.
    @param outfile the output file path.

    Optional args:
    @param title the title of the plot (default: 'Perf (EVENT_NAME)')
    @param xlabel the label on x-axes (default: '# of Cores')
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
    title = kwargs.get('title', 'Perf (%s)' % event)
    xlabel = kwargs.get('xlabel', '# of Cores')
    ylabel = kwargs.get('ylabel', 'Samples (%)')
    show_all = kwargs.get('show_all', False)
    threshold = kwargs.get('threshold', 0)
    loc = kwargs.get('loc', 'upper left')
    ncol = kwargs.get('ncol', 2)

    plot_data = data[event]
    keys = sorted(plot_data.keys())

    func_names = set()
    for v in plot_data.values():
        func_names |= v.keys()

    curves = []
    for func in func_names:
        yvalues = []
        for x in keys:
            try:
                yvalues.append(plot_data[x][func])
            except KeyError:
                yvalues.append(0)
        if not show_all and threshold > 0 and max(yvalues) < threshold:
            continue
        curves.append((keys, yvalues, func))
    mfsplot.plot(curves, title, xlabel, ylabel, outfile, ncol=ncol, loc=loc,
                 ylim=(0, 0.5))


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

    @param data a dictionary of oprofile data, { thread: oprofile_data, ... }
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
    @param field specify one field to sort (e.g. waittime-total,
    acquisitions and etc.)
    @param n only return the top N values

    Optional arguments
    @param percentage if set to True, returns the percentage of the specified
    field.
    @param in_second if set to True, returns the value in seconds.

    TODO: add support for sorting values per acquisition
    """
    percentage = kwargs.get('percentage', False)
    in_second = kwargs.get('in_second', False)
    assert not (percentage and in_second)

    temp = {}
    for lockname, values in data.items():
        temp[lockname] = values[field]

    if percentage:
        total_value = sum(temp.values())
        for lockname, value in temp.items():
            temp[lockname] = 1.0 * value / total_value
    elif in_second:
        # Returns values in second
        for lockname, value in temp.items():
            temp[lockname] = value / (10.0 ** 6)
    return dict(sorted_by_value(temp, reverse=True)[:n])
