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

from time import sleep

from trsync.objects.rsync_mirror import TRsync
from trsync.tests import rsync_base
from trsync.utils.tempfiles import TempFiles


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TestRsyncMirror(rsync_base.TestRsyncBase):

    """Test case class for rsync_mirror module"""

    def test__init_directory_structure(self):
        for remote in self.rsyncd[self.testname]:
            path = '/initial_test_path/test-subdir'
            url = remote.url + path
            rsync = TRsync(url, init_directory_structure=True)
            self.assertTrue(os.path.isdir(remote.path + path + '/snapshots'))
            del rsync

    def test_push(self):
        for remote in self.rsyncd[self.testname]:
            # create test data file
            temp_dir = TempFiles()
            src_dir = temp_dir.last_temp_dir
            self.getDataFile(os.path.join(src_dir,
                                          'dir1/dir2/dir3/test_data.txt'))

            # First snapshot
            rsync = TRsync(remote.url)
            out = rsync.push(os.path.join(src_dir, 'dir1'), 'dir1')
            timestamp1 = rsync.timestamp.snapshot_stamp
            snapshot1_path = remote.path + '/snapshots/dir1-{}'\
                ''.format(timestamp1)
            latest_path = remote.path + '/snapshots/dir1-latest'
            self.assertDirsEqual(snapshot1_path, src_dir + '/dir1')
            self.assertTrue(os.path.isdir(remote.path + '/snapshots/'))
            self.assertTrue(os.path.islink(latest_path))
            self.assertEqual(snapshot1_path, os.path.realpath(latest_path))
            with open(snapshot1_path + '.diff.txt') as diff_file:
                self.assertEqual(out, diff_file.read())
            with open(latest_path + '.target.txt') as target_file:
                self.assertEqual(
                    ['dir1-' + timestamp1],
                    target_file.read().splitlines()
                )
            # test_data.txt has only one hardlinks
            self.assertEqual(
                1,
                os.stat(os.path.join(snapshot1_path,
                                     'dir2/dir3/test_data.txt')).st_nlink
            )

            # Second snapshot
            sleep(1)
            rsync = TRsync(remote.url)
            out = rsync.push(os.path.join(src_dir, 'dir1'), 'dir1')
            timestamp2 = rsync.timestamp.snapshot_stamp
            self.assertNotEqual(timestamp1, timestamp2)
            snapshot2_path = remote.path + '/snapshots/dir1-{}'\
                ''.format(timestamp2)
            self.assertDirsEqual(snapshot2_path, src_dir + '/dir1')
            self.assertDirsEqual(snapshot1_path, snapshot2_path)
            self.assertTrue(os.path.islink(latest_path))
            self.assertEqual(snapshot2_path, os.path.realpath(latest_path))
            with open(snapshot2_path + '.diff.txt') as diff_file:
                self.assertEqual(out, diff_file.read())
            with open(latest_path + '.target.txt') as target_file:
                self.assertEqual(
                    ['dir1-' + timestamp2,
                     'dir1-' + timestamp1],
                    target_file.read().splitlines()
                )
            # test_data.txt has two hardlinks in both snapshots
            self.assertEqual(
                2,
                os.stat(os.path.join(snapshot1_path,
                                     'dir2/dir3/test_data.txt')).st_nlink
            )
            self.assertEqual(
                2,
                os.stat(os.path.join(snapshot2_path,
                                     'dir2/dir3/test_data.txt')).st_nlink
            )

            # TODO(mrasskazov) implement VVV
            # Push to existent snapshot raise RuntimeError
            # rsync = TRsync(remote.url, timestamp=timestamp1)
            # self.assertRaises(
            #     RuntimeError,
            #     rsync.push,
            #     os.path.join(src_dir, 'dir1'),
            #     'dir1'
            # )
            # CLI parameters: --raise-if-snapshot-exists,
            # --update-existent-snapshot

            # TODO(mrasskazov) implement VVV
            # Push new snapshot during locked remote mirror - wait for finish
            # previous operation or fail (optional)
            # CLI parameters: --raise-if-locked, --wait-if-locked,
            # --ignore-locking
