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

import os
import unittest
import yaml

from trsync.objects import rsync_url as rsync_url
from trsync.utils import utils as utils


logger = utils.logger.getChild('TestRsyncUrl')


class TestRsyncUrl(unittest.TestCase):

    def log_locals(self, url):
        if url.match:
            logger.info('Type: {}, RE: "{}"'
                        ''.format(url.url_type, url.match.pattern))
        logger.info('user "{}", host "{}", port "{}", module "{}", '
                    'path "{}"'.format(url.user, url.host, url.port,
                                       url.module, url.path))

    def exact_match_num(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        matching_patterns = url._get_all_matching_patterns()
        self.assertEqual(len(matching_patterns), expected_result)

    def classed(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.url_type, expected_result)

    def parsed(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(
            [url.user, url.host, url.path],
            expected_result
        )

    def parsed_rsync(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(
            [url.user, url.host, url.port, url.module, url.path],
            expected_result
        )

    def valid(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.is_valid, expected_result)

    def url(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.url, expected_result)

    def parsed_url(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.parsed_url, expected_result)

    def root(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.root, expected_result)

    def netloc(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.netloc, expected_result)

    def urljoin(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.urljoin(par), er)

    def join(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.join(par), er)

    def a_dir(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.a_dir(par), er)

    def url_dir(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.url_dir(par), er)

    def a_file(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.a_file(par), er)

    def url_file(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('par = "{}", er = "{}"'.format(par, er))
            self.assertEqual(url.url_file(par), er)

    def split_path(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url._split_path(remote), expected_result)

    def path_relative(self, remote, expected_result):
        logger.info('For "{}" should be {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            logger.info('Test parameters\n%s',
                        yaml.dump({remote: expected_result},
                                  default_flow_style=False))
            self.assertEqual(url.path_relative(par), er)


cpath, cname = os.path.split(os.path.realpath(os.path.realpath(__file__)))
cname = cname.split('.')
cname[-1] = 'yaml'
cname = '.'.join(cname)
cfile = os.path.join(cpath, cname)
testdata = yaml.safe_load(open(cfile))

index = 1
for remote, tests in testdata.items():

    for test, expected in tests.items():

        def test_function(self, test=test,
                          remote=remote, expected_result=expected):
            getattr(self, test)(remote, expected_result)

        test_function.__name__ = \
            'test_rsync_url_{}_{}_{}'.format(index, tests['classed'], test)
        test_function.__doc__ = test_function.__name__
        setattr(TestRsyncUrl, test_function.__name__, test_function)
        del test_function

    index += 1


if __name__ == '__main__':
    unittest.main()
