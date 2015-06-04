#-*- coding: utf-8 -*-

import unittest
import yaml

import rsync_url
import utils


logger = utils.logger.getChild('TestRsyncUrl')


class TestRsyncUrl(unittest.TestCase):

    def log_locals(self, url):
        if url.match:
            logger.info('RE: "{}"'.format(url.match.pattern))
        logger.info('user "{}", host "{}", port "{}", module "{}", '
                    'path "{}"'.format(url.user, url.host, url.port,
                                       url.module, url.path))

    def exact_match_num(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        matching_regexps = url._get_all_matching_regexps()
        self.assertEqual(len(matching_regexps), expected_result)

    def classed(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.url_type, expected_result)

    def parsed(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(
            [url.user, url.host, url.path],
            expected_result
        )

    def parsed_rsync(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(
            [url.user, url.host, url.port, url.module, url.path],
            expected_result
        )

    def valid(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.is_valid, expected_result)

    def url(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        self.assertEqual(url.url, expected_result)

    def url_in(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            self.assertEqual(url.url_in(par), er)

    def url_is(self, remote, expected_result):
        logger.info('"{}" - {}'.format(remote, expected_result))
        url = rsync_url.RsyncUrl(remote)
        self.log_locals(url)
        for par, er in expected_result.items():
            self.assertEqual(url.url_is(par), er)

testdata = yaml.load(open('test_rsync_url.yaml'))

index = 1
for remote, tests in testdata.items():

    for test, expected in tests.items():

        print index, test, expected

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
