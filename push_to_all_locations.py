#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys

from trsync import TRsync

servers = [_.strip() for _ in os.environ.get('LOCATIONS').split()]

if len(sys.argv) < 3:
    print 'Using: {} <source_dir>/ <target_mirror_name>'
    sys.exit(1)

source_dir = sys.argv[1]
mirror_name = sys.argv[2]

failed = list()
for server in servers:
    source_dir += '/'
    remote = TRsync(server,
                    save_latest_days=365 * 2,
                    init_directory_structure=False)
    try:
        remote.push(source_dir, mirror_name)
    except Exception as e:
        print e.message
        failed.append(server)

if failed:
    print "Failed to push to {}".format(str(failed))
    sys.exit(1)
