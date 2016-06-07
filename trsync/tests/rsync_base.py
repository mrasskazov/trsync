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

import filecmp
import os
import pkgutil

from trsync.tests import base
from trsync.tests import rsync_remotes as remotes
from trsync.utils import utils as utils


logger = utils.logger.getChild('TestRsyncUrl')


class TestRsyncBase(base.TestCase):

    """Test case base class for all functional tests"""
    rsyncd = utils.bunch()

    @property
    def testname(self):
        return self.__module__ + "." + self.__class__.__name__ + \
            "." + self._get_test_method().__name__

    def getDataFile(self, name):
        path, _ = os.path.split(name)
        if not os.path.isdir(path):
            os.makedirs(path)
        with open(name, 'w') as outf:
            outf.write('TEST DATA')
        return name

    def setUp(self):
        super(TestRsyncBase, self).setUp()
        self.rsyncd[self.testname] = list()
        for importer, modname, ispkg in \
                pkgutil.iter_modules(remotes.__path__, remotes.__name__ + '.'):
            module = __import__(modname, fromlist='dummy')
            self.rsyncd[self.testname].append(module.Instance(self.testname))

    def tearDown(self):
        super(TestRsyncBase, self).tearDown()
        for module in self.rsyncd[self.testname]:
            module.stop()

    def assertDirsEqual(self, left, right):
        diff = filecmp.dircmp(left, right)
        self.assertListEqual(diff.diff_files, [])
        self.assertListEqual(diff.left_only, [])
        self.assertListEqual(diff.right_only, [])
