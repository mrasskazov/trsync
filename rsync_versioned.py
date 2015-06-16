#-*- coding: utf-8 -*-

import datetime
import os

import utils

from rsync_remote import RsyncRemote
from utils import singleton


@singleton
class TimeStamp(object):
    def __init__(self):
        self.now = datetime.datetime.utcnow()
        self.staging_snapshot_stamp_format = r'%Y-%m-%d-%H%M%S'
        self.staging_snapshot_stamp_regexp = \
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{6}'
        self.staging_snapshot_stamp = \
            self.now.strftime(self.staging_snapshot_stamp_format)

    def __str__(self):
        return self.staging_snapshot_stamp


class RsyncVersioned(RsyncRemote):
    # retry and other function with mirror
    # add all the needed directory functions here, like mkdir, ls, rm etc
    # possible check that rsync url is exists
    def __init__(self,
                 rsync_url,
                 snapshot_dir='snapshots',
                 latest_successful_postfix='latest',
                 save_latest_days=14,
                 init_directory_structure=True,
                 ):
        super(RsyncVersioned, self).__init__(rsync_url)
        self.logger = utils.logger.getChild('RsyncVersioned.' + rsync_url)
        self.timestamp = TimeStamp()
        self.logger.info('Using timestamp {}'.format(self.timestamp))
        self.snapshot_dir = self.url.a_dir(snapshot_dir)
        self.latest_successful_postfix = latest_successful_postfix
        self.save_latest_days = save_latest_days

        if init_directory_structure is True:
            self.init_directory_structure()

    def init_directory_structure(self):
        # TODO: self.rsyncRemote.mkdir
        if self.url.url_type != 'path':
            server_root = RsyncRemote(self.url.root)
            return server_root.mkdir(
                self.url.a_dir(self.url.path, self.snapshot_dir)
            )

    def push(self, source, repo_name, extra=None):
        latest_path = self.url.a_file(
            self.snapshot_dir,
            '{}-{}'.format(self.url.a_file(repo_name),
                           self.latest_successful_postfix)
        )
        snapshot_name = self.url.a_file(
            '{}-{}'.format(self.url.a_file(repo_name), self.timestamp)
        )
        repo_path = self.url.a_file(self.snapshot_dir, snapshot_name)

        extra = '--link-dest={}'.format(
            self.url.a_file(self.url.path, latest_path)
        )
        result = super(RsyncVersioned, self).push(source, repo_path, extra)
        self.symlink(repo_name, repo_path)
        self.symlink(latest_path, snapshot_name)
        self._remove_old_snapshots(repo_name)
        return result

    def _remove_old_snapshots(self, repo_name, save_latest_days=None):
        if save_latest_days is None:
            save_latest_days = self.save_latest_days
        if save_latest_days is None or save_latest_days is False:
            # delete all snapshots
            self.logger.info('Deletion all of the old snapshots '
                             '(save_latest_days == {})'
                             ''.format(save_latest_days))
            save_latest_days = -1
        elif save_latest_days == 0:
            # skipping deletion
            self.logger.info('Skip deletion of old snapshots '
                             '(save_latest_days == {})'
                             ''.format(save_latest_days))
            return
        else:
            # delete snapshots older than
            self.logger.info('Deletion all of the unlinked snapshots older '
                             'than {0} days (save_latest_days == {0})'
                             ''.format(save_latest_days))
        warn_date = \
            self.timestamp.now - datetime.timedelta(days=save_latest_days)
        warn_date = datetime.datetime.combine(warn_date, datetime.time(0))
        snapshots = self.ls_dirs(
            self.url.a_dir(self.snapshot_dir),
            pattern=r'^{}-{}$'.format(
                repo_name,
                self.timestamp.staging_snapshot_stamp_regexp
            )
        )
        links = self.ls_symlinks(self.url.a_dir())
        links += self.ls_symlinks(self.url.a_dir(self.snapshot_dir))
        for s in snapshots:
            s_date = datetime.datetime.strptime(
                s,
                '{}-{}'.format(repo_name,
                               self.timestamp.staging_snapshot_stamp_format)
            )
            s_date = datetime.datetime.combine(s_date, datetime.time(0))
            s_path = self.url.a_dir(self.snapshot_dir, s)
            if s_date < warn_date:
                s_links = [_[0] for _ in links
                           if _[1] == s
                           or _[1].endswith('/{}'.format(s))
                           ]
                if not s_links:
                    self.rmdir(s_path)
                else:
                    self.logger.info('Skip deletion of "{}" because there are '
                                     'symlinks found: {}'.format(s, s_links))
            else:
                self.logger.info('Skip deletion of "{}" because it newer than '
                                 '{} days'.format(s, save_latest_days))
