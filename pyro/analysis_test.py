#!/usr/bin/env python
#
# Unittest for analysis.py
#
# Copyright: 2011 (c) Lei Xu <eddyxu@gmail.com>
# License: BSD License

"""Unit tests for febench.analysis
"""
import analysis
import unittest

class TestResult(unittest.TestCase):
    def test_get_item(self):
        result = analysis.Result()
        result[1, 2, 3] = 4
        self.assertEquals(4, result[1, 2, 3])
        self.assertEquals({3: 4}, result[1, 2])
        self.assertEquals(3, result.depth)

    def test_one_level_dict(self):
        result = analysis.Result()
        result[1] = 1
        result[2] = 2
        self.assertEquals(2, result[2])
        self.assertEquals(1, result[1])
        self.assertEquals(1, result.depth)

    def test_empty_item(self):
        result = analysis.Result()
        self.assertEquals(None, result[1, 2, 4])
        self.assertEquals(0, result.depth)

    def test_collect(self):
        test_data = {'a': {1: 2, 3: 4},
            'b': {'b0': {'m': 5, 'n': 10}, 'b1': {'m': 15, 'n': 20}}}
        result = analysis.Result()
        result.data_ = test_data
        self.assertEquals([5, 10, 15, 20], result.collect('b'))
        self.assertEquals([5, 10], result.collect('b', 'b0'))


class TestAnalysis(unittest.TestCase):
    def test_are_all_zeros(self):
        # test list
        self.assertTrue(analysis.are_all_zeros([0, 0, 0, 0]))
        self.assertFalse(analysis.are_all_zeros([0, 1, 0, 0]))
        self.assertFalse(analysis.are_all_zeros([1, 2, 3, 4]))

        # test dict
        self.assertTrue(analysis.are_all_zeros({1: 0, 2: 0, 0: 0, 3: 0}))
        self.assertFalse(analysis.are_all_zeros({1: 0, 2: 2, 0: 0, 3: 0}))
        self.assertFalse(analysis.are_all_zeros({1: 1, 2: 2, 3: 3, 4: 4}))

    def test_trans_top_data_to_curves(self):
        data = {1: {'a': 100, 'b': 1000},
                2: {'a': 40, 'b': 200, 'c': 300},
                3: {'a': 50, 'd': 20 }}
        # Only output common part
        curves = analysis.trans_top_data_to_curves(data)
        self.assertEquals([ ([1, 2, 3], [100, 40, 50], 'a') ], curves)

        # All fields ever occured
        expected_curves = [ ([1, 2, 3], [100, 40, 50], 'a'),
                            ([1, 2, 3], [1000, 200, 0], 'b'),
                            ([1, 2, 3], [0, 300, 0], 'c'),
                            ([1, 2, 3], [0, 0, 20], 'd') ]
        curves = analysis.trans_top_data_to_curves(data, show_all=True)
        for curve in curves:
            self.assertTrue(curve in expected_curves)
        self.assertTrue(len(curves), len(expected_curves))


if __name__ == "__main__":
    unittest.main()
