#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys

from trsync import TRsync

if len(sys.argv) < 3:
    print 'Using: {} <rsync_repo_url> <symlink_path>'.format(__file__)
    sys.exit(1)

server = sys.argv[1]
symlink_path = sys.argv[2]

remote = TRsync(server,
                save_latest_days=365 * 2,
                init_directory_structure=False)
print remote.symlink_target(symlink_path)
