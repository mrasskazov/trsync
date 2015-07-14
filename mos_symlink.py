#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys

from trsync import TRsync
from server_list import servers


if len(sys.argv) < 3:
    print 'Using: {} <symlink_name> <symlink_target>'
    sys.exit(1)
else:
    symlink_name = sys.argv[1]
    symlink_target = sys.argv[2]


def main():

    failed = list()
    for server in servers:
        remote = TRsync(server,
                        init_directory_structure=False)

        try:
            remote.symlink(symlink_name, symlink_target)
        except Exception as e:
            print e.message
            failed.append(server)

    if failed:
        print "Failed to push to {}".format(str(failed))
        sys.exit(1)

if __name__ == '__main__':
    main()
