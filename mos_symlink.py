#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys

from trsync import TRsync

servers = [
    'osci-mirror-msk.msk.mirantis.net::mirror-sync/mos',
    'osci-mirror-kha.kha.mirantis.net::mirror-sync/mos',
    'osci-mirror-srt.srt.mirantis.net::mirror-sync/mos',
    'osci-mirror-poz.infra.mirantis.net::mirror-sync/mos',
    'seed-cz1.fuel-infra.org::mirror-sync/mos',
    'seed-us1.fuel-infra.org::mirror-sync/mos',
]


if len(sys.argv) < 3:
    print 'Using: {} <symlink_name> <symlink_target>'
    sys.exit(1)
else:
    symlink_name = sys.argv[1]
    symlink_target = sys.argv[2]


def main():

    for server in servers:
        remote = TRsync(server,
                        init_directory_structure=False)

        try:
            target = remote.symlink_target(symlink_target)
            remote.symlink(symlink_name, target)
        except:
            continue


if __name__ == '__main__':
    main()
