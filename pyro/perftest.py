# Useful routines for doing performance testing.
# Author: Lei Xu <eddyxu@gmail.com>

"""Performance Test related functions.
"""

import sys
import platform
import osutil
from subprocess import check_call as call


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
