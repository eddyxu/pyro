#!/usr/bin/env python
#
# Author: Lei Xu <eddyxu@gmail.com>
# License: BSD License

"""Unit test for perftest
"""

from pyro import perftest
import unittest


class TestPerfTest(unittest.TestCase):
    def test_trans_top_data_to_curves(self):
        data = {1: {'a': 100, 'b': 1000},
                2: {'a': 40, 'b': 200, 'c': 300},
                3: {'a': 50, 'd': 20}}
        # Only output common part
        curves = perftest.trans_top_data_to_curves(data)
        self.assertEquals([([1, 2, 3], [100, 40, 50], 'a')], curves)

        # All fields ever occured
        expected_curves = [([1, 2, 3], [100, 40, 50], 'a'),
                           ([1, 2, 3], [1000, 200, 0], 'b'),
                           ([1, 2, 3], [0, 300, 0], 'c'),
                           ([1, 2, 3], [0, 0, 20], 'd')]
        curves = perftest.trans_top_data_to_curves(data, show_all=True)
        for curve in curves:
            self.assertTrue(curve in expected_curves)
        self.assertTrue(len(curves), len(expected_curves))


if __name__ == '__main__':
    unittest.main()
