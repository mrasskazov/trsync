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

from trsync.objects.rsync_ops import RsyncOps
from trsync.tests import rsync_base
from trsync.utils.tempfiles import TempFiles


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TestRsyncOps(rsync_base.TestRsyncBase):

    """Test case class for rsync_ops module"""

    def test_pull_file(self):
        for remote in self.rsyncd[self.testname]:
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            # pull it to the temp directory
            temp_dir = TempFiles()
            ops = RsyncOps(remote.url)
            ops._pull('file1.txt', temp_dir.last_temp_dir)
            # compare the directories
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)

    def test_pull_dir(self):
        for remote in self.rsyncd[self.testname]:
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path,
                             'dir1/dir2/dir3/test_data.txt'))
            # pull it to the temp directory
            temp_dir = TempFiles()
            ops = RsyncOps(remote.url)
            ops._pull('dir1', temp_dir.last_temp_dir, opts='-r')
            # compare the directories
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)

    def test_push_file(self):
        for remote in self.rsyncd[self.testname]:
            # create some data on temp dir
            temp_dir = TempFiles()
            filepath = self.getDataFile(
                os.path.join(temp_dir.last_temp_dir, 'file1.txt')
            )
            # push it to the rsync remote
            ops = RsyncOps(remote.url)
            ops.push(filepath)
            # compare the directories
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)

    def test_push_dir(self):
        for remote in self.rsyncd[self.testname]:
            # create some data on temp dir
            temp_dir = TempFiles()
            self.getDataFile(os.path.join(temp_dir.last_temp_dir,
                             'dir1/dir2/dir3/test_data.txt'))
            # push it to the rsync remote
            ops = RsyncOps(remote.url)
            ops.push(os.path.join(temp_dir.last_temp_dir, 'dir1'), opts='-r')
            # compare the directories
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)

    def test_ls(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # compare empty lists
            self.assertListEqual(ops.ls(), [])
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertSetEqual(set(ops.ls()),
                                set(['file1.txt', 'dir1', 'symlink1']))

    def test_ls_dirs(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # compare empty lists
            self.assertSetEqual(set(ops.ls_dirs()),
                                set([]))
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertSetEqual(set(ops.ls_dirs()),
                                set(['dir1']))

    def test_ls_symlinks(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # compare empty lists
            self.assertListEqual(ops.ls_symlinks(), [])
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertListEqual(ops.ls_symlinks(),
                                 [['symlink1', 'dir1']])

    def test__symlink_abs_target(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            os.makedirs(os.path.join(remote.path, 'snapshots/dir1'))

            os.symlink('dir1',
                       os.path.join(remote.path, 'snapshots/symlink1'))
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink1'),
                             'snapshots/dir1')

            os.symlink('symlink1',
                       os.path.join(remote.path, 'snapshots/symlink2'))
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink2',
                                                     recursive=False),
                             'snapshots/symlink1')
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink2'),
                             'snapshots/dir1')

            os.makedirs(os.path.join(remote.path, 'dir2'))
            os.symlink('../dir2',
                       os.path.join(remote.path, 'snapshots/symlink3'))
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink3'),
                             'dir2')

            os.makedirs(os.path.join(remote.path, 'snapshots2/dir3'))
            os.symlink('../snapshots2/dir3',
                       os.path.join(remote.path, 'snapshots/symlink4'))
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink4'),
                             'snapshots2/dir3')

            os.symlink('../snapshots2_dir3',
                       os.path.join(remote.path, 'snapshots/symlink5'))
            os.symlink('snapshots2/dir3',
                       os.path.join(remote.path, 'snapshots2_dir3'))
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink5',
                                                     recursive=False),
                             'snapshots2_dir3')
            self.assertEqual(ops._symlink_abs_target('snapshots/symlink5'),
                             'snapshots2/dir3')

    def test_symlink_target(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            os.makedirs(os.path.join(remote.path, 'snapshots/dir1'))

            os.symlink('dir1',
                       os.path.join(remote.path, 'snapshots/symlink1'))
            self.assertEqual(ops.symlink_target('snapshots/symlink1'),
                             'dir1')

            os.symlink('symlink1',
                       os.path.join(remote.path, 'snapshots/symlink2'))
            self.assertEqual(ops.symlink_target('snapshots/symlink2',
                                                recursive=False),
                             'symlink1')
            self.assertEqual(ops.symlink_target('snapshots/symlink2'), 'dir1')

            os.makedirs(os.path.join(remote.path, 'dir2'))
            os.symlink('../dir2',
                       os.path.join(remote.path, 'snapshots/symlink3'))
            self.assertEqual(ops.symlink_target('snapshots/symlink3'),
                             '../dir2')

            os.makedirs(os.path.join(remote.path, 'snapshots2/dir3'))
            os.symlink('../snapshots2/dir3',
                       os.path.join(remote.path, 'snapshots/symlink4'))
            self.assertEqual(ops.symlink_target('snapshots/symlink4'),
                             '../snapshots2/dir3')

            os.symlink('../snapshots2_dir3',
                       os.path.join(remote.path, 'snapshots/symlink5'))
            os.symlink('snapshots2/dir3',
                       os.path.join(remote.path, 'snapshots2_dir3'))
            self.assertEqual(ops.symlink_target('snapshots/symlink5',
                                                recursive=False),
                             '../snapshots2_dir3')
            self.assertEqual(ops.symlink_target('snapshots/symlink5'),
                             '../snapshots2/dir3')

    def test_rm_file(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertSetEqual(set(ops.ls()),
                                set(['file1.txt', 'dir1', 'symlink1']))
            ops.rm_file('file1.txt')
            self.assertSetEqual(set(ops.ls()),
                                set(['dir1', 'symlink1']))
            ops.rm_file('dir1')
            self.assertSetEqual(set(ops.ls()),
                                set(['symlink1']))
            ops.rm_file('symlink1')
            self.assertSetEqual(set(ops.ls()),
                                set([]))

    def test_rm_all(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1/dir2/dir3'))
            self.getDataFile(os.path.join(remote.path, 'dir2/file1.txt'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertSetEqual(set(ops.ls()),
                                set(['file1.txt', 'dir1', 'dir2', 'symlink1']))
            ops.rm_all(['file1.txt', 'dir1', 'symlink1'])
            self.assertSetEqual(set(ops.ls()), set(['dir2']))

    def test_clean_dir(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            os.makedirs(os.path.join(remote.path, 'dir1/dir2/dir3'))
            self.getDataFile(os.path.join(remote.path, 'dir2/file1.txt'))
            os.symlink('dir1', os.path.join(remote.path, 'dir2/symlink1'))
            ops.clean_dir('dir1')
            # compare the directories
            self.assertSetEqual(set(ops.ls('dir1/')), set([]))
            ops.clean_dir('dir2')
            # compare the directories
            self.assertSetEqual(set(ops.ls('dir2/')), set([]))

    def test_rm_dir(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on rsync remote
            self.getDataFile(os.path.join(remote.path, 'file1.txt'))
            os.makedirs(os.path.join(remote.path, 'dir1/dir2/dir3'))
            self.getDataFile(os.path.join(remote.path, 'dir2/file1.txt'))
            os.symlink('dir1', os.path.join(remote.path, 'symlink1'))
            # compare the lists
            self.assertSetEqual(set(ops.ls()),
                                set(['file1.txt', 'dir1', 'dir2', 'symlink1']))
            ops.rm_dir('dir1')
            self.assertSetEqual(set(ops.ls()),
                                set(['file1.txt', 'dir2', 'symlink1']))

    def test_mk_dir(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create some data on temp dir
            temp_dir = TempFiles()
            os.makedirs(os.path.join(temp_dir.last_temp_dir, 'dir1'))
            # push it to the rsync remote
            ops.mk_dir('dir1')
            # compare the directories
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)
            # recursive dir
            ops.mk_dir('snapshots/dir1')
            self.assertDirsEqual(os.path.join(remote.path, 'snapshots/'),
                                 temp_dir.last_temp_dir)

    def test_symlink(self):
        for remote in self.rsyncd[self.testname]:
            ops = RsyncOps(remote.url)
            # create symlink with existent target
            os.makedirs(os.path.join(remote.path, 'snapshots/dir1'))
            ops.symlink('snapshots/symlink1', 'dir1')
            self.assertSetEqual(
                set(ops.ls('snapshots/')),
                set(['dir1', 'symlink1', 'symlink1.target.txt'])
            )
            self.assertEqual(ops.symlink_target('snapshots/symlink1'), 'dir1')
            with open(os.path.join(remote.path,
                                   'snapshots/symlink1') + '.target.txt') \
                    as target_file:
                self.assertEqual(['dir1'],
                                 target_file.read().splitlines())

            # create symlink with absent target
            self.assertRaises(RuntimeError,
                              ops.symlink, 'snapshots/symlink2', 'dir2')

            # update existent symlink
            os.makedirs(os.path.join(remote.path, 'snapshots/dir2'))
            ops.symlink('snapshots/symlink1', 'dir2')
            self.assertSetEqual(
                set(ops.ls('snapshots/')),
                set(['dir1', 'dir2', 'symlink1', 'symlink1.target.txt']))
            self.assertEqual(ops.symlink_target('snapshots/symlink1'), 'dir2')
            with open(os.path.join(remote.path, 'snapshots/symlink1') + '.target.txt') \
                    as target_file:
                self.assertEqual(['dir2', 'dir1'],
                                 target_file.read().splitlines())

            # update symlink with absent target
            self.assertRaises(RuntimeError,
                              ops.symlink, 'snapshots/symlink1', 'dir3')
