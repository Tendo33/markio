#!/usr/bin/env python3
"""
Markio API Concurrent Test Launcher
Runs concurrent performance tests
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def check_service_health():
    """Check service health status."""
    import httpx

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("http://0.0.0.0:8000/")
            if response.status_code in [200, 307]:
                print("✅ Markio service is running normally")
                return True
            else:
                print(f"❌ Service response error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Unable to connect to Markio service: {e}")
        print("Please ensure service is running at http://0.0.0.0:8000")
        return False


def run_concurrent_tests(concurrent_users=None, test_duration=None, verbose=False):
    """Run concurrent tests."""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ Concurrent test file does not exist: {test_file}")
        return False

    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",  # Verbose output
        "-s",  # Show print output
    ]

    # Add verbose output options
    if verbose:
        cmd.extend(["--tb=long", "--durations=10"])

    print(f"🚀 Starting concurrent tests: {' '.join(cmd)}")
    print(f"📁 Test file: {test_file}")
    print(f"👥 Concurrent users: {concurrent_users or 'Default configuration'}")
    print(f"⏱️  Test duration: {test_duration or 'Default configuration'}")
    print("-" * 50)

    # Record start time
    start_time = time.time()

    try:
        # Run tests
        result = subprocess.run(cmd, capture_output=False, text=True)

        # Calculate runtime
        end_time = time.time()
        duration = end_time - start_time

        print("-" * 50)
        print(f"⏱️  Concurrent tests completed, duration: {duration:.2f} seconds")

        if result.returncode == 0:
            print("✅ Concurrent tests passed!")
            return True
        else:
            print(f"❌ Concurrent tests failed, exit code: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  Concurrent tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error occurred while running concurrent tests: {e}")
        return False


def run_specific_concurrent_test(test_name, verbose=False):
    """Run specific concurrent test."""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ Concurrent test file does not exist: {test_file}")
        return False

    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        f"TestConcurrentPerformance::{test_name}",
        "-v",  # Verbose output
        "-s",  # Show print output
    ]

    # Add verbose output options
    if verbose:
        cmd.extend(["--tb=long", "--durations=10"])

    print(f"🚀 Starting specific concurrent test: {test_name}")
    print(f"📁 Test file: {test_file}")
    print(f"🔧 Test method: {test_name}")
    print("-" * 50)

    # Record start time
    start_time = time.time()

    try:
        # Run tests
        result = subprocess.run(cmd, capture_output=False, text=True)

        # Calculate runtime
        end_time = time.time()
        duration = end_time - start_time

        print("-" * 50)
        print(f"⏱️  Test completed, duration: {duration:.2f} seconds")

        if result.returncode == 0:
            print("✅ Test passed!")
            return True
        else:
            print(f"❌ Test failed, exit code: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error occurred while running test: {e}")
        return False


def list_available_tests():
    """List available concurrent tests."""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ Concurrent test file does not exist: {test_file}")
        return

    print("📋 Available concurrent tests:")
    print("-" * 30)

    available_tests = [
        "test_single_endpoint_concurrent - Single endpoint concurrent test (5 concurrent users)",
        "test_mixed_endpoints_concurrent - Mixed endpoint concurrent test (5 different types)",
        "test_load_test_small_files - Load test (10 concurrent users, small files)",
        "test_stress_test_large_files - Stress test (3 concurrent users, large files)",
    ]

    for i, test in enumerate(available_tests, 1):
        print(f"{i}. {test}")

    print("\n💡 Use --test parameter to run specific test, for example:")
    print("   python run_concurrent_tests.py --test test_single_endpoint_concurrent")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Markio API Concurrent Test Launcher")
    parser.add_argument("--test", "-t", help="Run specific concurrent test method")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available concurrent tests"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output mode"
    )
    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip service health checks"
    )
    parser.add_argument(
        "--concurrent-users",
        type=int,
        help="Number of concurrent users (requires test code modification)",
    )
    parser.add_argument(
        "--test-duration",
        type=int,
        help="Test duration (requires test code modification)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Markio API Concurrent Test Suite")
    print("=" * 60)

    # Check current directory
    if not Path(__file__).parent.exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # List available tests
    if args.list:
        list_available_tests()
        sys.exit(0)

    # Execute pre-checks
    if not args.skip_checks:
        print("\n🔍 Executing pre-checks...")

        if not check_service_health():
            print("\n❌ Service check failed, please ensure Markio service is running")
            sys.exit(1)

        print("✅ Pre-checks passed")

    # Run tests
    if args.test:
        print(f"\n🎯 Starting specific concurrent test: {args.test}")
        success = run_specific_concurrent_test(
            test_name=args.test, verbose=args.verbose
        )
    else:
        print("\n🎯 Starting all concurrent tests...")
        success = run_concurrent_tests(
            concurrent_users=args.concurrent_users,
            test_duration=args.test_duration,
            verbose=args.verbose,
        )

    # Output results
    if success:
        print("\n🎉 Concurrent test execution successful!")
        print("\n📊 Performance metrics summary:")
        print("   - Response time: Check detailed data in test output")
        print("   - Success rate: Check statistics in test output")
        print("   - Throughput: Check performance data in test output")
        sys.exit(0)
    else:
        print("\n💥 Concurrent test execution failed!")
        print("\n🔍 Troubleshooting suggestions:")
        print("   - Check if service is running normally")
        print("   - Review error information in test output")
        print("   - Try reducing number of concurrent users")
        print("   - Check system resource usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
