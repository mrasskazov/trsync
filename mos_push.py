#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys

from trsync import TRsync

from server_list import servers

workspace = os.environ.get('HOME', '.')
repos_dir = os.path.join(workspace, 'repos/')
if len(sys.argv) < 2:
    print 'Using: {} <mirror_name>'
    sys.exit(1)
else:
    mirror_name = sys.argv[1]


def main():

    failed = list()
    for server in servers:
        symlink = os.path.join(repos_dir, mirror_name + '/')
        symlink_tgt = os.path.realpath(symlink)
        timestamp = symlink_tgt[-17:]
        remote = TRsync(server,
                        timestamp=timestamp,
                        save_latest_days=365 * 2,
                        init_directory_structure=False)
        try:
            remote.push(symlink, mirror_name)
        except Exception as e:
            print e.message
            failed.append(server)

    if failed:
        print "Failed to push to {}".format(str(failed))
        sys.exit(1)


if __name__ == '__main__':
    main()
