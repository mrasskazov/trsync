#-*- coding: utf-8 -*-

import datetime
import os

from trsync.utils import utils as utils

from trsync.objects.rsync_remote import RsyncRemote
from trsync.utils.utils import TimeStamp


class TRsync(RsyncRemote):
    # TODO: possible check that rsync url is exists
    def __init__(self,
                 rsync_url,
                 snapshot_dir='snapshots',
                 latest_successful_postfix='latest',
                 save_latest_days=14,
                 init_directory_structure=True,
                 timestamp=None,
                 **kwargs
                 ):
        super(TRsync, self).__init__(rsync_url, **kwargs)
        self.logger = utils.logger.getChild('TRsync.' + rsync_url)
        self.timestamp = TimeStamp(timestamp)
        self.logger.info('Using timestamp {}'.format(self.timestamp))
        self.snapshot_dir = self.url.a_dir(snapshot_dir)
        self.latest_successful_postfix = latest_successful_postfix
        self.save_latest_days = save_latest_days

        if init_directory_structure is True:
            self.init_directory_structure()

    def init_directory_structure(self):
        dir_full_name = self.url.a_dir(self.url.path, self.snapshot_dir)
        if self.url.url_type != 'path':
            server_root = RsyncRemote(self.url.root)
            return server_root.mkdir(dir_full_name)
        else:
            if not os.path.isdir(dir_full_name):
                return os.makedirs(dir_full_name)
        return True


    def push(self, source, repo_name, symlinks=[], extra=None, save_diff=True):
        repo_basename = os.path.split(repo_name)[-1]
        latest_path = self.url.a_file(
            self.snapshot_dir,
            '{}-{}'.format(self.url.a_file(repo_basename),
                           self.latest_successful_postfix)
        )

        symlinks = list(symlinks)
        symlinks.insert(0, latest_path)

        snapshot_name = self.url.a_file(
            '{}-{}'.format(self.url.a_file(repo_basename), self.timestamp)
        )
        repo_path = self.url.a_file(self.snapshot_dir, snapshot_name)

        extra = '--link-dest={}'.format(
            self.url.a_file(self.url.path, latest_path)
        )

        # TODO: split transaction run (push or pull), and
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
            result = super(TRsync, self).push(source, repo_path, extra)
            transaction.append(lambda p=repo_path: self.rm_all(p))
            self.logger.info('{}'.format(result))

            if save_diff is True:
                diff_file = self.tmp.get_file(content='{}'.format(result))
                diff_file_name = '{}.diff.txt'.format(repo_path)
                super(TRsync, self).push(diff_file, diff_file_name, extra)
                transaction.append(lambda f=diff_file_name: self.rm_all(f))
                self.logger.debug('Diff file {} created.'
                                  ''.format(diff_file_name))

            for symlink in symlinks:
                try:
                    tgt = [_[1] for _ in self.ls_symlinks(symlink)][0]
                    self.logger.info('Previous {} -> {}'.format(symlink, tgt))
                    undo = lambda l=symlink, t=tgt: self.symlink(l, t)
                except:
                    undo = lambda l=symlink: self.rm_all(l)
                # TODO: implement detection of target relative symlink
                if symlink.startswith(self.snapshot_dir):
                    self.symlink(symlink, snapshot_name)
                else:
                    self.symlink(symlink, repo_path)
                transaction.append(undo)

        except RuntimeError:
            self.logger.error("Rollback transaction because some of sync"
                              "operation failed")
            [_() for _ in reversed(transaction)]
            raise

        try:
            # deleting of old snapshots ignored when assessing the transaction
            # only warning
            self._remove_old_snapshots(repo_name)
        except RuntimeError:
            self.logger.warn("Old snapshots are not deleted. Ignore. "
                             "May be next time.")

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
                self.timestamp.snapshot_stamp_regexp
            )
        )
        links = self.ls_symlinks(self.url.a_dir())
        links += self.ls_symlinks(self.url.a_dir(self.snapshot_dir))
        snapshots_to_remove = list()
        new_snapshots = list()
        for s in snapshots:
            s_date = datetime.datetime.strptime(
                s,
                '{}-{}'.format(repo_name,
                               self.timestamp.snapshot_stamp_format)
            )
            s_date = datetime.datetime.combine(s_date, datetime.time(0))
            s_path = self.url.a_file(self.snapshot_dir, s)
            if s_date < warn_date:
                s_links = [_[0] for _ in links
                           if _[1] == s
                           or _[1].endswith('/{}'.format(s))
                           ]
                if not s_links:
                    snapshots_to_remove.append(s_path)
                    snapshots_to_remove.append(s_path + '.diff.txt')
                else:
                    self.logger.info('Skip deletion of "{}" because there are '
                                     'symlinks found: {}'.format(s, s_links))
            else:
                new_snapshots.append(s)

        if new_snapshots:
            self.logger.info('Skip deletion of snapshots newer than '
                             '{} days: {}'.format(save_latest_days,
                                                  str(new_snapshots)))

        if snapshots_to_remove:
            self.logger.info('Removing old snapshots (older then {} days): {}'
                            ''.format(save_latest_days, str(snapshots_to_remove)))
            self.rm_all(snapshots_to_remove)
