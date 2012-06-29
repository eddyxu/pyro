#!/usr/bin/env python
#
# Unittest for decorator.py
# Author: U{Lei Xu<mailto:eddyxu@gmail.com>
#
# Copyright: 2011 (c) Lei Xu
# License: BSD License
#

"""
"""
import decorator
import unittest

class TestDecorators(unittest.TestCase):
    def test_memoized(self):
        self.call_count = 0

        @decorator.memorized
        def foo_func(obj):
            obj.call_count += 1

        foo_func(self)
        self.assertEqual(1, self.call_count)
        foo_func(self)
        self.assertEqual(1, self.call_count)

if __name__ == "__main__":
    unittest.main()