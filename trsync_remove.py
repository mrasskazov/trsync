#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys
import argparse


from trsync import TRsync


def get_argparser():
    # sync --option1 --opt2 SRC MIRROR --dest DEST --dest DEST

    parser = argparse.ArgumentParser(prog='trsync_remove.py',
                                     description='remove all specified paths '
                                     'from several DST recursively')

    parser.add_argument('path',
                        nargs='+',
                        help='Path to remove')

    parser.add_argument('-d', '--dest',
                        nargs='+',
                        required=True,
                        help='Destination rsync url')

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
    servers = properties.pop('dest', None)
    path = properties.pop('path', None)
    if properties['extra'].startswith('\\'):
        properties['extra'] = properties['extra'][1:]
    properties['init_directory_structure'] = False
    properties['rsync_extra_params'] = properties.pop('extra')# + ' --dry-run'

    failed = list()
    for server in servers:
        remote = TRsync(server, **properties)
        try:
            print "Removing items {}".format(str(path))
            remote.rm_all(path)
        except Exception as e:
            print e.message
            failed.append(server)

    if failed:
        print "Failed to push to {}".format(str(failed))
        sys.exit(1)


if __name__ == '__main__':
    main()
