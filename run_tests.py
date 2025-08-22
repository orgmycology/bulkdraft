#!/usr/bin/env python3
"""
Test runner for DraftSend test suite.

This script runs all tests and provides options for running specific test suites.
"""

import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_offline_tests():
    """Run only offline tests (no IMAP connection required)."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all offline test modules
    offline_modules = [
        'tests.test_config',
        'tests.test_template', 
        'tests.test_context',
        'tests.test_email_builder',
        'tests.test_calendar',
        'tests.test_imap_offline',
        'tests.test_cli'
    ]
    
    for module in offline_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except ImportError as e:
            print(f"Warning: Could not load {module}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_online_tests():
    """Run only online tests (require IMAP connection)."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add online test modules
    online_modules = [
        'tests.test_imap_online'
    ]
    
    for module in online_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except ImportError as e:
            print(f"Warning: Could not load {module}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests (offline + online)."""
    print("Running offline tests...")
    offline_success = run_offline_tests()
    
    print("\n" + "="*60)
    print("Running online tests...")
    online_success = run_online_tests()
    
    return offline_success and online_success


def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DraftSend Test Runner')
    parser.add_argument(
        '--mode', 
        choices=['all', 'offline', 'online'], 
        default='all',
        help='Test mode to run (default: all)'
    )
    parser.add_argument(
        '--module',
        help='Run specific test module (e.g., test_config)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.module:
        # Run specific module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.{args.module}')
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)
        success = result.wasSuccessful()
    else:
        # Run test suite based on mode
        if args.mode == 'offline':
            success = run_offline_tests()
        elif args.mode == 'online':
            success = run_online_tests()
        else:
            success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()