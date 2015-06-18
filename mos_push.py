#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os

from trsync import TRsync

servers = [
    'osci-mirror-msk.msk.mirantis.net::mirror-sync/mos',
    'osci-mirror-kha.kha.mirantis.net::mirror-sync/mos',
    'osci-mirror-srt.srt.mirantis.net::mirror-sync/mos',
    'osci-mirror-poz.infra.mirantis.net::mirror-sync/mos',
    'seed-cz1.fuel-infra.org::mirror-sync/mos',
    'seed-us1.fuel-infra.org::mirror-sync/mos',
]


workspace = os.environ.get('WORKSPACE', '.')
repos_dir = os.path.join(workspace, 'repos/')


def main():

    for server in servers:
        for source in ('ubuntu/', 'centos-6/'):
            symlink = os.path.join(repos_dir, source)
            symlink_tgt = os.path.realpath(symlink)
            timestamp = symlink_tgt[-17:]
            remote = TRsync(server,
                            timestamp=timestamp,
                            init_directory_structure=False)
            repo_name = source.strip('/')
            remote.push(symlink, repo_name)


if __name__ == '__main__':
    main()
