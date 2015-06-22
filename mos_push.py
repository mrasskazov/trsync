#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
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


workspace = os.environ.get('HOME', '.')
repos_dir = os.path.join(workspace, 'repos/')
if len(sys.argv) < 2:
    print 'Using: {} <mirror_name>'
    sys.exit(1)
else:
    mirror_name = sys.argv[1]


def main():

    for server in servers:
        symlink = os.path.join(repos_dir, mirror_name + '/')
        symlink_tgt = os.path.realpath(symlink)
        timestamp = symlink_tgt[-17:]
        remote = TRsync(server,
                        timestamp=timestamp,
                        init_directory_structure=False)
        try:
            remote.push(symlink, mirror_name)
        except Exception as e:
            print e.message


if __name__ == '__main__':
    main()
