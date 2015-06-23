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
        self.url = RsyncUrl(rsync_url)
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
        dest = self.url.urljoin(dest)
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

    def symlink_target(self, symlink):
        target = symlink
        while True:
            try:
                target_path = os.path.split(target)[0]
                target = self.ls_symlinks(target)[0][1]
                target = os.path.join(target_path, target)
            except:
                return target

    def rmfile(self, filename):
        '''Removes file on rsync_url.'''
        report_name = filename
        dirname, filename = os.path.split(filename)
        dirname = self.url.a_dir(dirname)
        source = self.url.a_dir(self.tmp.empty_dir)
        opts = "-r --delete --include={} '--exclude=*'".format(filename)
        self.logger.info('Removing file "{}"'.format(report_name))
        return self._do_rsync(source=source, dest=dirname, opts=opts)

    def cleandir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        dirname = self.url.a_dir(dirname)
        source = self.url.a_dir(self.tmp.empty_dir)
        opts = "-a --delete"
        self.logger.info('Cleaning directory "{}"'.format(dirname))
        return self._do_rsync(source=source, dest=dirname, opts=opts)

    def rmdir(self, dirname):
        '''Removes directories (recursive) on rsync_url'''
        self.logger.info('Removing directory "{}"'.format(dirname))
        self.cleandir(dirname)
        return self.rmfile(self.url.a_file(dirname))

    def mkdir(self, dirname):
        '''Creates directories (recirsive, like mkdir -p) on rsync_url'''
        source = self.url.a_dir(self.tmp.get_temp_dir(dirname))
        opts = "-a"
        self.logger.info('Creating directory "{}"'.format(dirname))
        return self._do_rsync(source=source, opts=opts)

    def symlink(self, symlink, target, create_target_file=True):
        '''Creates symlink targeted to target'''

        symlink = self.url.a_file(symlink)
        if create_target_file is True:
            infofile = self.url.a_file('{}.target.txt'.format(symlink))
            source = self.tmp.get_file(content='{}'.format(target))
            temp_dir = self.tmp.last_temp_dir
            self.rmfile(infofile)
            self.logger.info('Creating informaion file "{}"'.format(infofile))
            self._do_rsync(source=source, dest=infofile)
        else:
            temp_dir = self.tmp.get_temp_dir()

        opts = "-l"
        source = self.tmp.get_symlink_to(target, temp_dir=temp_dir)
        self.rmfile(symlink)
        self.logger.info('Creating symlink "{}" -> "{}"'
                         ''.format(symlink, target))
        return self._do_rsync(source=source, dest=symlink, opts=opts)

    def push(self, source, repo_name=None, extra=None):
        '''Push source to destination'''
        opts = '--archive --force --ignore-errors --delete'
        self.logger.info('Push "{}" to "{}"'.format(source, repo_name))
        return self._do_rsync(source=source,
                              dest=repo_name,
                              opts=opts,
                              extra=extra)
