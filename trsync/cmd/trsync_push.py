#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys
import argparse


from trsync.objects.rsync_mirror import TRsync


def get_argparser():
    # sync --option1 --opt2 SRC MIRROR --dest DEST --dest DEST

    parser = argparse.ArgumentParser(prog='trsync_push.py',
                                     description='push SRC to several DST '
                                     'with snapshots')

    parser.add_argument('source', help='Source path')
    parser.add_argument('mirror_name', help='Mirror name')

    parser.add_argument('-d', '--dest',
                        nargs='+',
                        required=True,
                        help='Destination rsync url')

    parser.add_argument('-t', '--timestamp',
                        required=False,
                        help='Specified timestamp will be used for snapshot.'
                        'Format:yyyy-mm-dd-hhMMSS')

    parser.add_argument('--snapshot-dir',
                        required=False,
                        default='snapshots',
                        help='Directory name for snapshots. "snapshots" '
                        'by default')

    parser.add_argument('--init-directory-structure',
                        action='store_true',
                        required=False,
                        default=False,
                        help='It specified, all directories including'
                        '"snapshots-dir" will be created on remote location')

    parser.add_argument('--save-latest-days',
                        required=False,
                        default=61,
                        help='Snapshots for specified number of days will be '
                        'saved. All older will be removed. 61 by default. '
                        '0 mean that old snapshots will not be deleted, '
                        '"None" mean that all snapshots excluding latest '
                        'will be deleted')

    parser.add_argument('--latest-successful-postfix',
                        required=False,
                        default='latest',
                        help='Postfix for symlink to latest successfully '
                        'synced snapshot. Also used as --link-dest target. '
                        '"latest" by default.')

    parser.add_argument('-s', '--symlinks',
                        nargs='+',
                        required=False,
                        default=[],
                        help='Update additional symlinks relative destination')

    parser.add_argument('--extra',
                        required=False,
                        default='',
                        #action='store_const',
                        help='String with additional rsync parameters. For '
                        'example it may be "\--dry-run --any-rsync-option".'
                        'Use "\\" to disable argparse to parse extra value.')

    return parser


def main():

    parser = get_argparser()
    options = parser.parse_args()
    properties = vars(options)
    source_dir = properties.pop('source', None)
    mirror_name = properties.pop('mirror_name', None).strip('/')
    symlinks = properties.pop('symlinks', None)
    servers = properties.pop('dest', None)
    if properties['extra'].startswith('\\'):
        properties['extra'] = properties['extra'][1:]
    properties['rsync_extra_params'] = properties.pop('extra')
    properties['save_latest_days'] = \
        None if options.save_latest_days == 'None' \
            else int(options.save_latest_days)

    failed = list()
    for server in servers:
        source_dir = os.path.realpath(source_dir)
        if not source_dir.endswith('/'):
            source_dir += '/'
        remote = TRsync(server, **properties)
        try:
            remote.push(source_dir, mirror_name, symlinks=symlinks)
        except Exception as e:
            print e.message
            failed.append(server)

    if failed:
        print "Failed to push to {}".format(str(failed))
        sys.exit(1)


if __name__ == '__main__':
    main()
