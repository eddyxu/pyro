#!/usr/bin/env python
#
# Author: Lei Xu <eddyxu@gmail.com>

"""A set of utility for profiling on Linux.
"""

from __future__ import print_function
from subprocess import call, check_output


class Profiler(object):
    """The interface of a Profiler.
    """
    def start(self):
        """Start profiling using one concrete Profile.
        """
        raise NotImplementedError

    def stop(self):
        """Stop this Profiler
        """
        raise NotImplementedError

    def report(self):
        """Return the output of profiling as a string.
        """
        raise NotImplementedError

    def dump(self, outfile):
        """Dumps the report to the outfile.
        @param outfile it can be a file object or a string file path.
        """
        if type(outfile) == str:
            with open(outfile, 'w+') as fobj:
                fobj.write(self.report() + '\n')
        else:
            outfile.write(self.report() + '\n')


class NonProfiler(Profiler):
    """A Profiler that does nothing.
    """
    def start(self, cmd=''):
        if cmd:
            call(cmd, shell=True)

    def stop(self):
        pass

    def dump(self, outfile):
        pass

    def report(self):
        pass


class LockstatProfiler(Profiler):
    """The Profiler to get /proc/lock_stat data
    """
    def __init__(self):
        self.report_ = ""

    @staticmethod
    def clear_lockstat(self):
        """Clear the statistics data of kernel lock
        """
        with open('/proc/lock_stat', 'w') as fobj:
            fobj.write('0\n')

    def start(self):
        """Starts to monitor lock stat
        """
        self.clear_lockstat()

    def stop(self):
        """Stops to monitor lock stats and gather the results.
        """
        with open('/proc/lock_stat', 'r') as fobj:
            self.report_ = fobj.read()

    def report(self):
        return self.report_


class ProcStatProfiler(Profiler):
    def __init__(self):
        self.report_ = ""
        self.before = ""
        self.after = ""

    def start(self):
        with open('/proc/stat', 'r') as fobj:
            self.before = fobj.readline()

    def stop(self):
        with open('/proc/stat', 'r') as fobj:
            self.after = fobj.readline()

    def report(self):
        """Generates report.
        """
        before_fields = [int(x) for x in self.before.split()[1:]]
        after_fields = [int(x) for x in self.after.split()[1:]]
        return_fields = [str(x - y) for x, y in
                         zip(after_fields, before_fields)]
        return 'cpu ' + ' '.join(return_fields) + '\n'


class PerfProfiler(Profiler):
    """Use linux's perf utility to measure the PMU.
    """
    EVENTS = '-e cycles,cache-misses,LLC-load-misses'
    # EVENTS = '-e cycles'

    def __init__(self, perf='perf', **kwargs):
        """Constructs a PerfProfiler

        @param perf the exective of 'perf'

        Optional parameters:
        @param events the events to be recorded.
        @param vmlinux the kernel image to find symbols.
        @param kallsyms the kallsyms file.
        """
        self.perf = perf
        self.check_avail(perf)
        self.vmlinux = kwargs.get('vmlinux', '')
        self.kallsyms = kwargs.get('kallsyms', '')
        if kwargs.get('events', ''):
            self.EVENTS = '-e ' + kwargs.get('events')
        self.report_ = ""

    @staticmethod
    def check_avail(perf=''):
        if call('which {}'.format(perf), shell=True) > 0:
            raise RuntimeError('PerfProfiler can not find perf binary: \'{}\'.'
                               .format(perf))

    def start(self, cmd):
        """Start recording perf events.
        """
        print("Perf record events: {}".format(self.EVENTS))
        return call('{} record {} -a {}'.format(self.perf, self.EVENTS, cmd),
                    shell=True)

    def stop(self):
        """Collects reports from the previous running of 'perf record'
        """
        options = ''
        if self.vmlinux:
            options += ' -k {}'.format(self.vmlinux)
        if self.kallsyms:
            options += ' --kallsyms={}'.format(self.kallsyms)
        self.report_ = check_output(
            '{} report {} --stdio'.format(self.perf, options),
            shell=True).decode('utf-8')

    def report(self):
        return self.report_


class OProfiler(Profiler):
    """Use oprofiler
    """
    EVENTS = '--event=L3_CACHE_MISSES:500'

    def __init__(self, vmlinux='', events=''):
        self.vmlinux = vmlinux
        if events:
            self.events = events
        self.report_ = ""

    def start(self):
        call('opcontrol --reset', shell=True)
        call('opcontrol --init', shell=True)
        if self.vmlinux:
            call('opcontrol --vmlinux={}'.format(self.vmlinux))
        if self.EVENTS:
            call('opcontrol --setup --separate=none {}' % self.events)
        call('opcontrol --start')

    def stop(self):
        call('opcontrol --dump')
        call('opcontrol --stop')
        self.report_ = check_output('opreport -cl', shell=True).decode('utf-8')

    def report(self):
        return self.report_
