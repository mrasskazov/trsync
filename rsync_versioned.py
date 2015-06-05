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
                 snapshot_dir='files',
                 latest_successful_postfix='staging',
                 save_latest_days=14,
                 init_directory_structure=True,
                 ):
        super(RsyncVersioned, self).__init__(rsync_url)
        self.logger = utils.logger.getChild('RsyncVersioned.' + rsync_url)
        self.timestamp = TimeStamp()
        self.logger.info('Using timestamp {}'.format(self.timestamp))
        self.snapshot_dir = self.url.dirname(snapshot_dir)
        self.latest_successful_postfix = latest_successful_postfix
        self.save_latest_days = save_latest_days

        # TODO: mirror_name - name of synced directory
        # it located inside rsync_url/
        # UPD: not needed - take it in self.push.dest patameter
        self.mirror_name = os.path.split(rsync_url)[1]

        if init_directory_structure is True:
            self.init_directory_structure()

    def init_directory_structure(self):
        # TODO: self.rsyncRemote.mkdir
        #if self.root.url_type != 'path':
        #server_root = rsyncRemote(self.root.urlroot)
        #server_root.mkdir(self.root.path)
        pass

    def push(self, source, repo_name, extra=None):
        latest_path = self.url.filename(
            self.snapshot_dir,
            '{}-{}'.format(self.url.filename(repo_name),
                           self.latest_successful_postfix)
        )
        snapshot_name = self.url.filename(
            '{}-{}'.format(self.url.filename(repo_name), self.timestamp)
        )
        repo_path = self.url.filename(self.snapshot_dir, snapshot_name)

        extra = '--link-dest={}'.format(
            self.url.filename(self.url.path, latest_path)
        )
        result = super(RsyncVersioned, self).push(source, repo_path, extra)
        super(RsyncVersioned, self).symlink(repo_name, repo_path)
        super(RsyncVersioned, self).symlink(latest_path, snapshot_name)
        return result
