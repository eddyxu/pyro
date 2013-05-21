#!/usr/bin/env python
#
# Author: U{Lei Xu<mailto:eddyxu@gmail.com>}
# Copyright: 2011 (c) Lei Xu <eddyxu@gmail.com>
# License: BSD License

from __future__ import print_function
import functools
import os
import time


class memorized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


class before(object):
    """Run some functions before the actual execution of the decorated
    function. A typical example, preparing the test environment before running
    performance tests.
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args

    def __call__(self, func):
        self.func(self.args)
        return func


class after(object):
    """After the execution, run some tests.
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args

    def __call__(self, func):
        pass


class benchmark(object):
    """Run a function as benchmark for several times.

    Usage:
     >>> @benchmark(times=1)  # times is a optional parameter.
     >>> def awesome_benchmark(arg1, arg2):
         >>> # do awesome benchmarks.

    @param times How many times should this benchmark run. Optional.
    @param timeout Set the timeout in seconds.
    @param silence If true, it do not generate output.
    """
    def __init__(self, **kwargs):
        self.times = kwargs.get('times', 1)
        # Timeout in seconds
        self.timeout = kwargs.get('timeout', 0)
        self.silence = kwargs.get('silence', False)

    def __call__(self, func):
        def benchmark_func(*args):
            times_start = os.times()
            for i in range(self.times):
                func(*args)
            times_end = os.times()
            user_time = times_end[0] - times_start[0]
            sys_time = times_end[1] - times_start[1]
            if not self.silence:
                print("Run benchmark %s for %d times.",
                      func.__name__, self.times)
                print("Total: user time: %fs system time: %fs.",
                      user_time, sys_time)
                print("Average: user time: %fs system time %fs.",
                      user_time / self.times, sys_time / self.times)
        return benchmark_func
