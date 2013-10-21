#!/usr/bin/env python
#
# Author: Lei Xu <eddyxu@gmail.com>
# License: BSD

"""OS-related helper functions.
"""

import glob
import os
import platform
import sys
from subprocess import check_call


def check_root_or_exit(exit_value=0):
    """Check the user who run this script is root.
    Otherwise, it exits this program.
    """
    if os.getuid() != 0:
        print >> sys.stderr, "Must run this script with root privilege."
        sys.exit(exit_value)


def check_os_or_exit(osname, exit_value=0):
    """Only allow to run this script on particular platform.

    @param osname the OS name (e.g. Darwin/Linux/FreeBSD)
    @param exit_value the return value by sys.exit()
    """
    if platform.system() != osname:
        print >> sys.stderr, "Must run this script on %s" % osname
        sys.exit(exit_value)


def mount_disk_to_path(dev, mnt, filesystem='ext4'):
    """make a file system on a disk and then mount it
    """
    if filesystem == 'xfs':
        check_call("mkfs.%s -f %s" % (filesystem, dev), shell=True)
    else:
        check_call("mkfs.%s %s" % (filesystem, dev), shell=True)
    check_call("mount -t %s %s %s" % (filesystem, dev, mnt), shell=True)


def umount_all(root_path):
    """Unmount all subdirectories under a given root path
    """
    subdirs = os.listdir(root_path)
    for sub in subdirs:
        sub_dir_path = os.path.join(root_path, sub)
        if os.path.ismount(sub_dir_path):
            check_call("umount %s" % sub_dir_path)


def parse_cores(cores):
    """Parse cores from given parameter, similiar to taskset(1).
    Accepted parameters:
    0  - core 0
    0,1,2,3  - cores 0,1,2,3
    0-12,13-15,18,19
    """
    result = set()
    sequences = cores.split(',')
    for seq in sequences:
        if not '-' in seq:
            if not seq.isdigit():
                raise ValueError('%s is not digital' % seq)
            result.add(int(seq))
        else:
            core_range = seq.split('-')
            if len(core_range) != 2 or not core_range[0].isdigit() \
                    or not core_range[1].isdigit():
                raise ValueError('Core Range Error')
            result.update(range(int(core_range[0]), int(core_range[1]) + 1))
    return result

def get_all_cpus():
    """Get all available cpus in the system.
    """
    cpu_dirs = glob.glob('/sys/devices/system/cpu/cpu*')
    result = set()
    for cpu_dir in cpu_dirs:
        cpu_path = cpu_dir.split('/')[-1]
        cpu_id = cpu_path[3:]
        if cpu_id.isdigit():
            result.add(int(cpu_id))
    return result

def get_online_cpus():
    online_cpu_string = ''
    with open('/sys/devices/system/cpu/online') as fobj:
        online_cpu_string = fobj.read()
    online_cpu_string = online_cpu_string.strip()
    online_cpus = parse_cores(online_cpu_string)
    return online_cpus
