#!/usr/bin/env python
#-*- coding: utf-8 -*-

print ("WARNING!!!\n"
       "Script potentialy very DANGEROUS. \n"
       "Don't run if you aren't sure what are you doing.")
exit(1)

from trsync import TRsync

servers = [
    'osci-mirror-msk.msk.mirantis.net::mirror-sync/mos',
    'osci-mirror-kha.kha.mirantis.net::mirror-sync/mos',
    'osci-mirror-srt.srt.mirantis.net::mirror-sync/mos',
    'osci-mirror-poz.infra.mirantis.net::mirror-sync/mos',
    'seed-cz1.fuel-infra.org::mirror-sync/mos',
    'seed-us1.fuel-infra.org::mirror-sync/mos',
]


def main():
    remotes = [
        TRsync(
            s,
            init_directory_structure=False,
            timestamp='2015-06-18-000000',
        )
        for s in servers
    ]

    source = '/root/trusty/'
    for remote in remotes:
        remote.symlink('snapshots/trusty-latest', '../ubuntu')
        print remote.ls_symlinks('snapshots/')
        remote.push(source, 'trusty')
        print remote.ls_symlinks('snapshots/')
        remote.rmdir('ubuntu')
        remote.symlink('ubuntu', 'trusty')
        print remote.ls_symlinks('/')

    source = '/root/centos-6/'
    for remote in remotes:
        remote.rmdir('centos-6')
        remote.push(source, 'centos-6')
        print remote.ls_symlinks('snapshots/')
        remote.symlink('centos', 'centos-6')
        print remote.ls_symlinks('/')


if __name__ == '__main__':
    main()
