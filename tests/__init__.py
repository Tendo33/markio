"""
Markio API Test Suite

This package contains test cases for testing Markio document parsing service API functionality and concurrent performance.

Main modules:
- test_all_parsers: Functional tests for all parsing interfaces
- test_concurrent: Concurrent performance tests
- conftest: pytest configuration and shared fixtures

Usage:
1. Ensure Markio service is running at http://0.0.0.0:8000
2. Run tests: pytest tests/ -v
3. Or use provided script: python tests/run_tests.py
"""

__version__ = "1.0.0"
__author__ = "Markio Team"
__description__ = "Markio API Test Suite"
