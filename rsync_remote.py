#-*- coding: utf-8 -*-

import os
import re

import utils

from tempfiles import TempFiles
from shell import Shell
from rsync_url import RsyncUrl


class RsyncRemote(object):
    def __init__(self,
                 rsync_url,
                 rsync_extra_params='-v --no-owner --no-group',
                 ):
        # TODO: retry parameters for rsync
        self.logger = utils.logger.getChild('RsyncRemote.' + rsync_url)
        self.tmp = TempFiles()
        self.shell = Shell(self.logger)
        self.root = RsyncUrl(rsync_url)
        self.rsync_extra_params = rsync_extra_params

    def _do_rsync(self, source='', dest=None, opts='', extra=None):
        # TODO: retry for rsync
        # TODO: locking:
        # https://review.openstack.org/#/c/147120/4/utils/simple_http_daemon.py
        # create lock-files on remotes during operations
        # for reading and writing
        # special option for ignore lock-files (for manual fixing)
        # all high-level functions (like ls) specify type of lock(read or
        # write), and _do_rsync creates special lock file on remote.
        # also _do_rsync uses retry for waiting wnen resource will be unlocked
        # TODO: check for url compatibility (local->remote, remote->local,
        # local->local)
        # TODO: push method - upstream mirrors
        dest = self.root.urljoin(dest)
        allextra = self.rsync_extra_params
        if extra is not None:
            allextra = ' '.join((allextra, extra))
        cmd = 'rsync {opts} {allextra} {source} {dest}'.format(**(locals()))
        return self.shell.shell(cmd)[1]

    def _rsync_ls(self, dirname=None, pattern=r'.*', opts=''):
        extra = '--no-v'
        out = self._do_rsync(dest=dirname, opts=opts, extra=extra)
        regexp = re.compile(pattern)
        out = [_ for _ in out.splitlines()
               if (_.split()[-1] != '.') and
               (regexp.match(_.split()[-1]) is not None)]
        return out

    def ls(self, dirname=None, pattern=r'.*'):
        self.logger.debug('ls on "{}", pattern="{}"'.format(dirname, pattern))
        out = self._rsync_ls(dirname, pattern=pattern)
        out = [_.split()[-1] for _ in out]
        return out

    def ls_dirs(self, dirname=None, pattern=r'.*'):
        self.logger.debug('ls dirs on "{}", pattern="{}"'
                          ''.format(dirname, pattern))
        out = self._rsync_ls(dirname, pattern=pattern)
        out = [_.split()[-1] for _ in out if _.startswith('d')]
        return out

    def ls_symlinks(self, dirname=None, pattern=r'.*'):
        self.logger.debug('ls symlinks on "{}", pattern="{}"'
                          ''.format(dirname, pattern))
        out = self._rsync_ls(dirname, pattern=pattern, opts='-l')
        out = [_.split()[-3:] for _ in out if _.startswith('l')]
        out = [[_[0], _[-1]] for _ in out]
        return out

    def rmfile(self, filename):
        '''Removes file on rsync_url.'''
        report_name = filename
        dirname, filename = os.path.split(filename)
        dirname = self.root.dirname(dirname)
        source = self.root.dirname(self.tmp.empty_dir)
        opts = "-r --delete --include={} '--exclude=*'".format(filename)
        self.logger.info('Removing file "{}"'.format(report_name))
        return self._do_rsync(source=source, dest=dirname, opts=opts)

    def cleandir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        dirname = self.root.dirname(dirname)
        source = self.root.dirname(self.tmp.empty_dir)
        opts = "-a --delete"
        self.logger.info('Cleaning directory "{}"'.format(dirname))
        return self._do_rsync(source=source, dest=dirname, opts=opts)

    def rmdir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        self.logger.info('Removing directory "{}"'.format(dirname))
        self.cleandir(dirname)
        return self.rmfile(self.root.filename(dirname))

    def mkdir(self, dirname):
        '''Creates directories (recirsive, like mkdir -p) on rsync_url'''
        source = self.root.dirname(self.tmp.get_temp_dir(dirname))
        opts = "-a"
        self.logger.info('Creating directory "{}"'.format(dirname))
        return self._do_rsync(source=source, opts=opts)

    def symlink(self, symlink, target):
        '''Creates symlink targeted to target'''
        source = self.tmp.get_symlink_to(target)
        symlink = self.root.filename(symlink)
        opts = "-l"
        self.rmfile(symlink)
        self.logger.info('Creating symlink "{}" -> "{}"'
                         ''.format(symlink, target))
        return self._do_rsync(source=source, dest=symlink, opts=opts)

    def push(self, source, dest=None, extra=None):
        '''Push source to destination'''
        opts = '--archive --force --ignore-errors --delete'
        self.logger.info('Push "{}" to "{}"'.format(source, dest))
        return self._do_rsync(source=source, dest=dest, opts=opts, extra=extra)