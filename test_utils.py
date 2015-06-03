#-*- coding: utf-8 -*-

import unittest

import utils


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
