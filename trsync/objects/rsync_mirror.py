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

import datetime
import logging
import os

from trsync.utils import utils as utils

from trsync.objects.rsync_ops import RsyncOps
from trsync.objects.rsync_remote import RsyncRemote
from trsync.utils.utils import TimeStamp

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel('DEBUG')


class TRsync(RsyncRemote):
    # TODO(mrasskazov): possible check that rsync url is exists
    def __init__(self,
                 rsync_url,
                 snapshots_dir='snapshots',
                 latest_successful_postfix='latest',
                 snapshot_lifetime=14,
                 init_directory_structure=True,
                 timestamp=None,
                 **kwargs
                 ):
        super(TRsync, self).__init__(
            rsync_url,
            init_directory_structure=init_directory_structure,
            **kwargs)
        self._log = utils.logger.getChild('TRsync' + rsync_url)
        self._snapshots_dir = self.url.a_dir(snapshots_dir)
        self._latest_successful_postfix = latest_successful_postfix
        self._snapshot_lifetime = snapshot_lifetime

        self.timestamp = TimeStamp(timestamp)
        self._log.info('Using timestamp {}'.format(self.timestamp))

        if init_directory_structure is True:
            super(TRsync, self)._init_directory_structure()
            self._init_snapshots_dir()

    def _init_snapshots_dir(self):
        dir_full_name = self.url.a_dir(self.url.path, self._snapshots_dir)
        if dir_full_name not in ['', '/']:
            if self.url.url_type != 'path':
                rsync_root = RsyncOps(self.url.root)
                rsync_root.mk_dir(dir_full_name)
            else:
                if not os.path.isdir(dir_full_name):
                    os.makedirs(dir_full_name)
        return True

    def push(self, source, repo_name, symlinks=[], extra=None, save_diff=True):
        repo_basename = os.path.split(repo_name)[-1]
        latest_path = self.url.a_file(
            self._snapshots_dir,
            '{}-{}'.format(self.url.a_file(repo_basename),
                           self._latest_successful_postfix)
        )

        symlinks = list(symlinks)
        symlinks.insert(0, latest_path)

        snapshot_name = self.url.a_file(
            '{}-{}'.format(self.url.a_file(repo_basename), self.timestamp)
        )
        repo_path = self.url.a_file(self._snapshots_dir, snapshot_name)

        extra = '--link-dest={}'.format(
            self.url.path_relative(latest_path, repo_path)
        )

        # TODO(mrasskazov): split transaction run (push or pull), and
        # commit/rollback functions. transaction must has possibility to
        # rollback after commit for implementation of working with pool
        # of servers. should be something like this:
        #     transactions = list()
        #     result = True
        #     for server in servers:
        #         transactions.append(server.push(source, repo_name))
        #         result = result and transactions[-1].success
        #     if result is True:
        #         for transaction in transactions:
        #             transaction.commit()
        #             result = result and transactions[-1].success
        #     if result is False:
        #         for transaction in transactions:
        #             transaction.rollback()
        transaction = list()
        try:
            # start transaction
            transaction.append(lambda p=repo_path: self.rsync.rm_all(p))
            result = super(TRsync, self).push(self.url.a_dir(source),
                                              repo_path,
                                              extra)
            self._log.info('{}'.format(result))

            if save_diff is True:
                diff_file = self._tmp.get_file(content='{}'.format(result))
                diff_file_name = '{}.diff.txt'.format(repo_path)
                transaction.append(
                    lambda f=diff_file_name: self.rsync.rm_all(f)
                )
                super(TRsync, self).push(diff_file, diff_file_name)
                self._log.debug('Diff file {} created.'
                                ''.format(diff_file_name))

            for symlink in symlinks:
                try:
                    tgt = self.rsync.symlink_target(symlink, recursive=False)
                    self._log.info('Previous {} -> {}'.format(symlink, tgt))
                    undo = lambda l=symlink, t=tgt: self.rsync.symlink(l, t)
                except Exception:
                    undo = lambda l=symlink: self.rsync.rm_all(l)
                transaction.append(undo)
                self.rsync.symlink(
                    symlink,
                    self.url.path_relative(
                        os.path.join(self._snapshots_dir, snapshot_name),
                        os.path.split(symlink)[0]
                    )
                )

        except RuntimeError:
            self._log.error("Rollback transaction because some of sync"
                            "operation failed")
            [func() for func in reversed(transaction)]
            raise

        try:
            # deleting of old snapshots ignored when assessing the transaction
            # only warning
            self._remove_old_snapshots(repo_name)
        except RuntimeError:
            self._log.warn("Old snapshots are not deleted. Ignore. "
                           "May be next time.")

        return result

    def _remove_old_snapshots(self, repo_name, snapshot_lifetime=None):
        if snapshot_lifetime is None:
            snapshot_lifetime = self._snapshot_lifetime
        if snapshot_lifetime is None or snapshot_lifetime is False:
            # delete all snapshots
            self._log.info('Deletion all of the old snapshots '
                           '(snapshot_lifetime == {})'
                           ''.format(snapshot_lifetime))
            snapshot_lifetime = -1
        elif snapshot_lifetime == 0:
            # skipping deletion
            self._log.info('Skip deletion of old snapshots '
                           '(snapshot_lifetime == {})'
                           ''.format(snapshot_lifetime))
            return
        else:
            # delete snapshots older than
            self._log.info('Deletion all of the unlinked snapshots older '
                           'than {0} days (snapshot_lifetime == {0})'
                           ''.format(snapshot_lifetime))
        warn_date = \
            self.timestamp.now - datetime.timedelta(days=snapshot_lifetime)
        warn_date = datetime.datetime.combine(warn_date, datetime.time(0))
        snapshots = self.rsync.ls_dirs(
            self.url.a_dir(self._snapshots_dir),
            pattern=r'^{}-{}$'.format(
                repo_name,
                self.timestamp.snapshot_stamp_pattern
            )
        )
        links = self.rsync.ls_symlinks(self.url.a_dir())
        links += self.rsync.ls_symlinks(self.url.a_dir(self._snapshots_dir))
        snapshots_to_remove = list()
        new_snapshots = list()
        for s in snapshots:
            s_date = datetime.datetime.strptime(
                s,
                '{}-{}'.format(repo_name,
                               self.timestamp.snapshot_stamp_format)
            )
            s_date = datetime.datetime.combine(s_date, datetime.time(0))
            s_path = self.url.a_file(self._snapshots_dir, s)
            if s_date < warn_date:
                s_links = [_[0] for _ in links
                           if _[1] == s
                           or _[1].endswith('/{}'.format(s))
                           ]
                if not s_links:
                    snapshots_to_remove.append(s_path)
                    snapshots_to_remove.append(s_path + '.diff.txt')
                else:
                    self._log.info('Skip deletion of "{}" because there are '
                                   'symlinks found: {}'.format(s, s_links))
            else:
                new_snapshots.append(s)

        if new_snapshots:
            self._log.info('Skip deletion of snapshots newer than '
                           '{} days: {}'.format(snapshot_lifetime,
                                                str(new_snapshots)))

        if snapshots_to_remove:
            self._log.info('Removing old snapshots (older then {} days): {}'
                           ''.format(snapshot_lifetime,
                                     str(snapshots_to_remove)))
            self.rsync.rm_all(snapshots_to_remove)
