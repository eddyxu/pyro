#!/usr/bin/env python
#
# Author: Lei Xu <eddyxu@gmail.com>

"""OS-related helper functions.
"""

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
