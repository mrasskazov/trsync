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
import os
import re

from trsync.utils import utils as utils

from trsync.objects.rsync_url import RsyncUrl as RsyncUrl
from trsync.utils.shell import Shell
from trsync.utils.tempfiles import TempFiles


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel('DEBUG')


class RsyncOps(object):
    def __init__(self, rsync_url, rsync_extra_params=''):
        # TODO(mrasskazov): retry parameters for rsync
        self._log = utils.logger.getChild('RsyncOps.' + rsync_url)
        self._tmp = TempFiles()
        self._shell = Shell(self._log)
        self._rsync_extra_params = ' '.join(['-v --no-owner --no-group',
                                            rsync_extra_params])
        self.url = RsyncUrl(rsync_url)

    def _pull(self, source='', dest='', opts='', extra=None,
              no_dry_run=False, raise_error=False):
        cmd = 'rsync {opts} {allextra} {source.url}'
        source = RsyncUrl(self.url.urljoin(source))
        if dest:
            dest = RsyncUrl(dest)
            cmd += ' {dest.url}'
        allextra = self._rsync_extra_params
        if extra is not None:
            allextra = ' '.join((allextra, extra))
        cmd = cmd.format(**(locals()))
        if no_dry_run:
            cmd.replace('--dry-run', '')
        self._log.debug(cmd)
        return self._shell.shell(cmd, raise_error=raise_error)[1]

    def push(self, source='', dest='', opts='', extra=None):
        # TODO(mrasskazov): retry for rsync
        # TODO(mrasskazov): locking:
        # https://review.openstack.org/#/c/147120/4/utils/simple_http_daemon.py
        # create lock-files on remotes during operations
        # symlink dir-timestamp.lock -> dir-timestamp
        # for reading and writing
        # special option for ignore lock-files (for manual fixing)
        # all high-level functions (like ls) specify type of lock(read or
        # write), and push creates special lock file on remote.
        # also push uses retry for waiting wnen resource will be
        # unlocked
        # TODO(mrasskazov): check for url compatibility
        # (local->remote, remote->local, local->local)
        cmd = 'rsync {opts} {allextra} {source.url} {dest.url}'
        source = RsyncUrl(source)
        dest = RsyncUrl(self.url.urljoin(dest))
        allextra = self._rsync_extra_params
        if extra is not None:
            allextra = ' '.join((allextra, extra))
        cmd = cmd.format(**(locals()))
        self._log.debug(cmd)
        return self._shell.shell(cmd)[1]

    def _ls(self, path=None, pattern=r'.*', opts=''):
        extra = '--no-v'
        try:
            out = self._pull(source=path, opts=opts, extra=extra,
                             no_dry_run=True, raise_error=False)
        except RuntimeError:
            out = ''
        pattern = re.compile(pattern)
        out = [_ for _ in out.splitlines()
               if (_.split()[-1] != '.') and
               (pattern.match(_.split()[-1]) is not None)]
        return out

    def ls(self, path=None, pattern=r'.*'):
        out = self._ls(path, pattern=pattern)
        out = [_.split()[-1] for _ in out]
        return out

    def ls_dirs(self, path=None, pattern=r'.*'):
        out = self._ls(path, pattern=pattern)
        out = [_.split()[-1] for _ in out if _.startswith('d')]
        return out

    def ls_symlinks(self, path=None, pattern=r'.*'):
        out = self._ls(path, pattern=pattern, opts='-l')
        out = [_.split()[-3:] for _ in out if _.startswith('l')]
        out = [[_[0], _[-1]] for _ in out]
        return out

    def _symlink_abs_target(self, symlink, recursive=True):
        target = symlink
        try:
            path, name = os.path.split(target)
            target = self.ls_symlinks(symlink)[-1][-1]
            abs_target = os.path.normpath(os.path.join(path, target))
            if not recursive:
                return abs_target
            return self._symlink_abs_target(abs_target)
        except Exception:
            return target

    def symlink_target(self, symlink, recursive=True, absolute=False):
        if absolute:
            return self._symlink_abs_target(symlink, recursive=recursive)
        else:
            return os.path.relpath(
                self._symlink_abs_target(symlink, recursive=recursive),
                os.path.dirname(symlink)
            )

    def rm_file(self, filename):
        '''Removes file on rsync_url.'''
        report_name = filename
        dirname, filename = os.path.split(filename)
        dirname = self.url.a_dir(dirname)
        source = self.url.a_dir(self._tmp.empty_dir)
        opts = "-r --delete --include={} '--exclude=*'".format(filename)
        self._log.info('Removing file "{}"'.format(report_name))
        return self.push(source=source, dest=dirname, opts=opts)

    def rm_all(self, names=[]):
        '''Remove all files and dirs (recursively)

        on list as single rsync operation
        '''

        if type(names) not in (list, tuple):
            if type(names) is str:
                names = [names]
            else:
                raise RuntimeError('rsync_remote.rm_all has wrong parameter '
                                   '"names" == "{}"'.format(names))

        source = self.url.a_dir(self._tmp.empty_dir)

        # group files by directories
        dest_dirs = dict()
        for name in names:
            dirname, filename = os.path.split(name)
            if dirname not in dest_dirs.keys():
                dest_dirs[dirname] = list()
            dest_dirs[dirname].append(filename)

        for dest_dir, filenames in dest_dirs.items():
            # prepare filter file for every dest_dir
            content = ''
            for filename in filenames:
                content += '+ {}\n'.format(filename)
            content += '- *'
            filter_file = self._tmp.get_file(content=content)
            # removing specified files on dest_dir
            self._log.debug('Removing objects on "{}" directory: {}'
                            ''.format(dest_dir, str(filenames)))
            opts = "--recursive --delete --filter='merge,p {}'"\
                   "".format(filter_file)
            self.push(source=source, dest=dest_dir, opts=opts)

    def clean_dir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        dirname = self.url.a_dir(dirname)
        source = self.url.a_dir(self._tmp.empty_dir)
        opts = "-a --delete"
        self._log.info('Cleaning directory "{}"'.format(dirname))
        return self.push(source=source, dest=dirname, opts=opts)

    def rm_dir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        self._log.info('Removing directory "{}"'.format(dirname))
        return self.rm_all(self.url.a_file(dirname))

    def mk_dir(self, dirname):
        '''Creates directories (recirsive, like mkdir -p) on rsync_url'''
        source = self.url.a_dir(self._tmp.get_temp_dir(dirname))
        opts = "-r"
        self._log.info('Creating directory "{}"'.format(dirname))
        return self.push(source=source, opts=opts)

    def symlink(self, symlink, target,
                create_target_file=True, store_history=True):
        '''Creates symlink targeted to target'''

        temp_dir = self._tmp.get_temp_dir()
        remote_path, symlink = os.path.split(self.url.a_file(symlink))
        # check that target is exists on remote
        if not self.ls(os.path.join(remote_path, target)):
            raise RuntimeError('Target {} does not exists'.format(target))
        path = os.path.join(temp_dir, remote_path)
        if not os.path.isdir(path):
            os.makedirs(path)
        os.symlink(target, os.path.join(path, symlink))

        if create_target_file is True:
            infofile = '{}.target.txt'\
                ''.format(os.path.join(remote_path, symlink))
            if store_history is True:
                try:
                    self._pull(source=infofile, dest=self.url.a_dir(path),
                               no_dry_run=True, raise_error=False)
                    with open(os.path.join(temp_dir, infofile), 'r') as inf:
                        content = '{}\n{}'.format(target, inf.read())
                except IOError:
                    content = target
                with open(os.path.join(temp_dir, infofile), 'w') as outf:
                    outf.write(content)
            self._log.debug('Creating informaion file "{}"'.format(infofile))

        opts = "-rl"
        self._log.info('Creating symlink "{}" -> "{}"'.format(symlink, target))
        return self.push(source=self.url.a_dir(path),
                         dest=self.url.a_dir(remote_path),
                         opts=opts)
