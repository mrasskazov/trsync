#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016, Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import sys

from cliff import app
from cliff import command
from cliff import commandmanager

import trsync

from trsync.objects import rsync_mirror
from trsync.objects import rsync_ops
from trsync.objects import rsync_url


class PushCmd(command.Command):
    log = logging.getLogger(__name__)

    def get_description(self):
        return "push SRC to several DST with snapshots"

    def get_parser(self, prog_name):
        parser = super(PushCmd, self).get_parser(prog_name)
        parser.add_argument('source',
                            help='Source rsync url (local, rsyncd, remote '
                            'shell). Mean that it is a directory, not a file.')
        parser.add_argument('mirror_name',
                            help='Mirror name. Will contain the source/ '
                            'content on remote.')
        parser.add_argument('-d', '--dest',
                            nargs='+',
                            required=True,
                            help='Destination rsync url(s)')
        parser.add_argument('-t', '--timestamp',
                            required=False,
                            help='Specified timestamp will be used for '
                            'snapshot. Will be generated automaticaly by '
                            'default. Format:yyyy-mm-dd-hhMMSS')
        parser.add_argument('--snapshots-dir', '--snapshot-dir',
                            required=False,
                            default='snapshots',
                            help='Directory name for snapshots relative '
                            '"destination". "snapshots" by default')
        parser.add_argument('--init-directory-structure',
                            action='store_true',
                            required=False,
                            default=False,
                            help='It specified, all directories including'
                            '"snapshots-dir" will be created on remote '
                            'location. Disabled by default.')
        parser.add_argument('--snapshot-lifetime', '--save-latest-days',
                            required=False,
                            default=61,
                            help='Snapshots for specified number of days will '
                            'be saved. All older will be removed. 61 by '
                            'default. 0 mean that old snapshots will not be '
                            'deleted, "None" mean that all snapshots '
                            'excluding latest will be deleted')
        parser.add_argument('--latest-successful-postfix',
                            required=False,
                            default='latest',
                            help='Postfix for symlink to latest successfully '
                            'synced snapshot. Also used as --link-dest '
                            'target. "latest" by default.')
        parser.add_argument('-s', '--symlinks',
                            nargs='+',
                            required=False,
                            default=[],
                            help='Update additional symlinks relative '
                            'destination. Only "latest" by default.')
        parser.add_argument('--extra',
                            required=False,
                            default='',
                            help='String with additional rsync parameters. '
                            'For example it may be "\--dry-run '
                            '--any-rsync-option".Use "\\" to disable '
                            'argparse to parse extra value.')

        return parser

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
        source_url = properties.pop('source', None)
        mirror_name = properties.pop('mirror_name', None).strip('/')
        symlinks = properties.pop('symlinks', None)
        servers = properties.pop('dest', None)
        if properties['extra'].startswith('\\'):
            properties['extra'] = properties['extra'][1:]
        properties['rsync_extra_params'] = properties.pop('extra')
        properties['snapshot_lifetime'] = \
            None if properties['snapshot_lifetime'] == 'None' \
            else int(properties['snapshot_lifetime'])

        report = dict()
        exitcode = 0
        for server in servers:
            source = rsync_ops.RsyncOps(source_url)
            source_url = source.url.url_dir()
            report[server] = dict()
            try:
                remote = rsync_mirror.TRsync(server, **properties)
                remote.push(source_url, mirror_name, symlinks=symlinks)
                report[server]['success'] = True
            except Exception as e:
                report[server]['success'] = False
                report[server]['log'] = e.message
                exitcode = 1

        for srv, msg in report.items():
            if msg['success']:
                self.log.info('Push %s to %s: SUCCESS' % (source_url, srv))
            else:
                self.log.error('Push %s to %s: FAILED' % (source_url, srv))
                self.log.error(msg['log'])

        sys.exit(exitcode)


class SymlinkCmd(command.Command):
    log = logging.getLogger(__name__)

    def get_description(self):
        return "Create (or update) symlinks on remote"

    def get_parser(self, prog_name):
        parser = super(SymlinkCmd, self).get_parser(prog_name)
        parser.add_argument('-d', '--dest',
                            nargs='+',
                            required=True,
                            help='Destination rsync url (local, rsyncd, '
                            'remote shell).')
        parser.add_argument('-t', '--target',
                            required=True,
                            help='All the symlinks will target to (relative '
                            'symlink name). Url by default.')
        parser.add_argument('-s', '--symlinks',
                            nargs='+',
                            required=True,
                            default=[],
                            help='Update specified symlinks (names relative '
                            'dest).')
        parser.add_argument('--update',
                            action='store_true',
                            required=False,
                            default=False,
                            help='It specified, all existent symlinks will be '
                            'updated. Will be skiped otherwise. Disabled by '
                            'default.')
        parser.add_argument('--extra',
                            required=False,
                            default='',
                            help='String with additional rsync parameters. '
                            'For example it may be "\--dry-run '
                            '--any-rsync-option".Use "\\" to disable '
                            'argparse to parse extra value.')

        return parser

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
        symlinks = properties.pop('symlinks', [])
        for symlink in symlinks:
            if symlink.startswith('/') or symlink.startswith('../'):
                self.log.error('Symlink name outside the root url: %s',
                               symlink)
                raise RuntimeError('Symlink name the root url: {}'
                                   ''.format(symlink))
        servers = properties.pop('dest', None)
        target = properties.pop('target', None)
        if properties['extra'].startswith('\\'):
            properties['extra'] = properties['extra'][1:]
        properties['rsync_extra_params'] = properties.pop('extra')
        update = properties.pop('update', None)

        report = dict()
        exitcode = 0

        for server in servers:
            report[server] = dict()
            try:
                remote = rsync_ops.RsyncOps(server, **properties)
                for symlink in symlinks:
                    remote.symlink(symlink, target, update=update)
                report[server]['success'] = True
            except Exception as e:
                report[server]['success'] = False
                report[server]['log'] = e.message
                exitcode = 1

        for srv, msg in report.items():
            if msg['success']:
                self.log.info('Creating symlinks %s targeted to %s on %s: '
                              'SUCCESS' % (str(symlinks), target, srv))
            else:
                self.log.error('Creating symlinks %s targeted to %s on %s: '
                               'FAILED' % (str(symlinks), target, srv))
                self.log.error(msg['log'])

        sys.exit(exitcode)


class RemoveCmd(command.Command):
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
                            help='String with additional rsync parameters. '
                            'For example it may be "\--dry-run '
                            '--any-rsync-option". Use "\\" to disable '
                            'argparse to parse extra value.')
        return parser

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
        servers = properties.pop('dest', None)
        path = properties.pop('path', None)
        if properties['extra'].startswith('\\'):
            properties['extra'] = properties['extra'][1:]
        properties['rsync_extra_params'] = properties.pop('extra')

        report = dict()
        exitcode = 0
        for server in servers:
            report[server] = dict()
            self.log.info("Removing items {}".format(str(path)))
            try:
                remote = rsync_ops.RsyncOps(server, **properties)
                remote.rm_all(path)
                report[server]['success'] = True
            except Exception as e:
                report[server]['success'] = False
                report[server]['log'] = e.message
                exitcode = 1

        for srv, msg in report.items():
            if msg['success']:
                self.log.info('Remove %s: SUCCESS' % (path))
            else:
                self.log.error('Remove %s: FAILED' % (path))

        sys.exit(exitcode)


class GetTargetCmd(command.Command):
    log = logging.getLogger(__name__)

    def get_description(self):
        return "Evaluate the target for specified symlink "\
            "(optional recursively)"

    def get_parser(self, prog_name):
        parser = super(GetTargetCmd, self).get_parser(prog_name)

        parser.add_argument('symlink_url',
                            help='Symlink url to resolve (supported by rsync)')
        parser.add_argument('-r', '--recursive',
                            action='store_true',
                            required=False,
                            default=False,
                            help='It specified, the symlink will be resolved '
                            'recursively (if the symlink targeted to other '
                            'symlinks tree - they will be resolved too). '
                            'Disabled by default.')
        return parser

    def take_action(self, parsed_args):
        properties = vars(parsed_args)
        symlink_url = properties.pop('symlink_url', None)
        recursive = properties.pop('recursive', False)

        url = rsync_url.RsyncUrl(symlink_url)
        remote = rsync_ops.RsyncOps(url.root, **properties)
        target = remote.symlink_target(url.path, recursive=recursive)
        print(target)


class TRsyncApp(app.App):
    log = logging.getLogger(__name__)

    def __init__(self):
        super(TRsyncApp, self).__init__(
            description='TRsync',
            version=trsync.__version__,
            command_manager=commandmanager.CommandManager('trsync'),
            deferred_help=True,
            )


def main(argv=sys.argv[1:]):
    app = TRsyncApp()
    return app.run(argv)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
