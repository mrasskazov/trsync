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

import unittest

from trsync.utils import utils as utils


logger = utils.logger.getChild('TestUtils')


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.gen10 = self.get_generator(10)

    def get_generator(self, max):
        for i in xrange(max):
            yield i

    def test_retry_3_from_5(self):
        res = utils.Retry(timeout=1,
                          attempts=5).wait_result(self.gen10.next, 3)
        self.assertEqual(res, 3)

    def test_retry_failed(self):
        retryer = utils.Retry(timeout=1, attempts=3)
        self.assertRaises(utils.ResultNotProduced,
                          retryer.wait_result, self.gen10.next, 5)

if __name__ == '__main__':
    unittest.main()
