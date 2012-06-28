#!/usr/bin/env python
#
# Lei Xu <eddyxu@gmail.com>
#

"""Performance Test result analyse."""

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

