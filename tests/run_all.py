#!/usr/bin/env python3
import unittest
import os
import sys

def run_tests():
    # Root of the tests directory
    start_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add root to sys.path so 'tests' module is resolvable
    root = os.path.dirname(start_dir)
    sys.path.insert(0, root)
    
    # Discover and load tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with non-zero if failures occurred
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_tests()
