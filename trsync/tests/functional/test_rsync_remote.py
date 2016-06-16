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

from trsync.objects.rsync_remote import RsyncRemote
from trsync.tests.functional import rsync_base
from trsync.utils.tempfiles import TempFiles


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TestRsyncRemote(rsync_base.TestRsyncBase):

    """Test case class for rsync_remote module"""

    def test__init_directory_structure(self):
        for remote in self.rsyncd[self.testname]:
            url = remote.url + '/initial_test_path/test-subdir'
            rsync = RsyncRemote(url, init_directory_structure=True)
            self.assertTrue(os.path.isdir(remote.path))
            del rsync

    def test_push(self):
        for remote in self.rsyncd[self.testname]:
            # create test data file
            temp_dir = TempFiles()
            self.getDataFile(os.path.join(temp_dir.last_temp_dir,
                             'dir1/dir2/dir3/test_data.txt'))
            rsync = RsyncRemote(remote.url)
            rsync.push(os.path.join(temp_dir.last_temp_dir, 'dir1'))
            self.assertDirsEqual(remote.path, temp_dir.last_temp_dir)
