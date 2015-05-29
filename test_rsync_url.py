#-*- coding: utf-8 -*-

import rsync_url
import unittest
import yaml


class TestRsyncUrl(unittest.TestCase):

    def exact_match_num(self, remote, expected_result):
        url = rsync_url.RsyncUrl(remote)
        matching_regexps = url._get_all_matching_regexps()
        self.assertEqual(len(matching_regexps), expected_result)

    def classed(self, remote, expected_result):
        url = rsync_url.RsyncUrl(remote)
        self.assertEqual(url.url_type, expected_result)

    def parsed(self, remote, expected_result):
        url = rsync_url.RsyncUrl(remote)
        self.assertEqual(
            [url.user, url.host, url.port, url.path],
            expected_result
        )


testdata = yaml.load(open('test_rsync_url.yaml'))

index = 1
for remote, tests in testdata.items():

    for test, expected in tests.items():

        print index, test, expected

        def test_function(self, test=test,
                          remote=remote, expected_result=expected):
            getattr(self, test)(remote, expected_result)

        test_function.__name__ = \
            'test_{}_{}_{}'.format(index, tests['classed'], test)
        test_function.__doc__ = test_function.__name__
        setattr(TestRsyncUrl, test_function.__name__, test_function)
        del test_function

    index += 1


if __name__ == '__main__':
    unittest.main()
