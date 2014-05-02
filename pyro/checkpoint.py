#!/usr/bin/env python
#
# Author: Lei Xu <eddyxu@gmail.com>

import os


class Checkpoint(object):
    """A simple check point facality for running tests.
    """
    OUTDIR_PREFIX = 'CHK DIR:'
    START_PREFIX = 'CHK START:'
    DONE_PREFIX = 'CHK DONE:'

    def __init__(self, logpath):
        self.steps = 0
        self.outdir = ''
        if os.path.exists(logpath):
            with open(logpath, 'r') as logfile:
                for line in logfile:
                    if line.startswith(self.DONE_PREFIX):
                        fields = line.split()
                        if len(fields) != 3:
                            break
                        self.steps = int(fields[2])
                    if line.startswith(self.OUTDIR_PREFIX):
                        fields = line.split()
                        if len(fields) != 3:
                            break
                        self.outdir = fields[2]

        self.logfile = open(logpath, 'a')

    def __del__(self):
        if self.logfile:
            self.logfile.close()

    def set_outdir(self, outdir):
        self.outdir = outdir
        self.logfile.write('{} {}\n'.format(self.OUTDIR_PREFIX, outdir))
        self.logfile.flush()

    def start(self):
        """Call this function to indicate that a step has started.
        """
        self.logfile.write('{} {}\n'.format(self.START_PREFIX, self.steps + 1))
        self.logfile.flush()

    def done(self):
        """Indicates that a step has successfully finished.
        """
        self.steps += 1
        self.logfile.write('{} {}\n'.format(self.DONE_PREFIX, self.steps))
        self.logfile.flush()

    def should_skip(self, steps):
        """Returns True if this step should be skipped.
        """
        return self.steps >= steps
