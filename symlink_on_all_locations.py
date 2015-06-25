#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys

from trsync import TRsync

servers = [_.strip() for _ in os.environ.get('LOCATIONS').split()]

if len(sys.argv) < 3:
    print 'Using: {} <symlink>/ <target>'
    sys.exit(1)

symlink = sys.argv[1]
target = sys.argv[2]

failed = list()
for server in servers:
    remote = TRsync(server,
                    save_latest_days=365 * 2,
                    init_directory_structure=False)
    try:
        remote.symlink(symlink, target)
    except Exception as e:
        print e.message
        failed.append(server)

if failed:
    print "Failed to create symlink on {}".format(str(failed))
    sys.exit(1)
