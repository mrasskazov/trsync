#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command

from trsync.objects.rsync_mirror import TRsync

class PushCmd(Command):
    log = logging.getLogger(__name__)

    def get_description(self):
        return "push SRC to several DST with snapshots"

    def get_parser(self, prog_name):
        parser = super(PushCmd, self).get_parser(prog_name)
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

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
        source_dir = properties.pop('source', None)
        mirror_name = properties.pop('mirror_name', None)
        symlinks = properties.pop('symlinks', None)
        servers = properties.pop('dest', None)
        if properties['extra'].startswith('\\'):
            properties['extra'] = properties['extra'][1:]
        properties['rsync_extra_params'] = properties.pop('extra')
        properties['save_latest_days'] = \
            None if properties['save_latest_days'] == 'None' \
                else int(properties['save_latest_days'])

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
            #self.app.stdout.write(parsed_args.arg + "\n")

class RemoveCmd(Command):
    log = logging.getLogger(__name__)

    def get_description(self):
        return "remove all specified paths from several DST recursively"

    def get_parser(self, prog_name):
        parser = super(RemoveCmd, self).get_parser(prog_name)

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
                            help='String with additional rsync parameters. For '
                            'example it may be "\--dry-run --any-rsync-option".'
                            'Use "\\" to disable argparse to parse extra value.')
        return parser

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
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
            print "Failed to remove {}".format(str(failed))
            sys.exit(1)

class TRsyncApp(App):
    log = logging.getLogger(__name__)

    def __init__(self):
        super(TRsyncApp, self).__init__(
            description='TRsync',
            version=trsync.__version__,
            command_manager=CommandManager('trsync'),
            deferred_help=True,
            )

def main(argv=sys.argv[1:]):
    app = TRsyncApp()
    return app.run(argv)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
