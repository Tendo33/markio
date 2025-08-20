#!/usr/bin/env python3
"""
Markio API Test Launcher
Runs all API functionality tests
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
        with httpx.Client(timeout=15.0) as client:
            response = client.get("http://0.0.0.0:8000/")
            if response.status_code in [200, 307]:
                print("✅ Markio service is running normally")
                return True
            else:
                print(f"❌ Service response error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Unable to connect to Markio service: {e}")
        print("Please ensure the service is running at http://0.0.0.0:8000")
        return False


def check_test_files():
    """Check if test files exist."""
    test_docs_dir = Path(__file__).parent / "test_docs"

    if not test_docs_dir.exists():
        print(f"❌ Test documents directory does not exist: {test_docs_dir}")
        return False

    required_files = [
        "test_pdf1.pdf",
        "test_doc.doc",
        "test_docx.docx",
        "test_ppt.ppt",
        "test_pptx.pptx",
        "test_xlsx.xlsx",
        "test_html.html",
        "test_epub.epub",
    ]

    missing_files = []
    for file in required_files:
        if not (test_docs_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing test files: {', '.join(missing_files)}")
        return False

    print("✅ Test file check passed")
    return True


def run_tests(test_type="all", verbose=False, output_file=None):
    """Run tests."""
    test_dir = Path(__file__).parent

    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Verbose output
        "-s",  # Show print output (don't capture)
        "--durations=10",  # Show the 10 slowest tests
        "--durations-min=0.1",  # Show all tests taking more than 0.1 seconds
    ]

    # Select test files based on test type
    if test_type == "api":
        cmd.append(str(test_dir / "test_all_parsers.py::TestAllParsers"))
    elif test_type == "concurrent":
        cmd.append(str(test_dir / "test_concurrent.py::TestConcurrentPerformance"))
    elif test_type == "all":
        cmd.append(str(test_dir))  # Run all tests
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False

    # Add verbose output options
    if verbose:
        cmd.extend(["--tb=long", "--durations=20", "--durations-min=0.05"])

    # Add output file option
    if output_file:
        cmd.extend([f"--junit-xml={output_file}"])

    print(f"🚀 Starting test run: {' '.join(cmd)}")
    print(f"📁 Test directory: {test_dir}")
    print(f"🔧 Test type: {test_type}")
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
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ Tests failed, exit code: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error occurred while running tests: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Markio API Test Launcher")
    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "api", "concurrent"],
        default="all",
        help="Test type: all(complete), api(API functions), concurrent(performance)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output mode"
    )
    parser.add_argument("--output", "-o", help="Test report output file path")
    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip service health and file checks"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Markio API Test Suite")
    print("=" * 60)

    # Check current directory
    if not Path(__file__).parent.exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Execute pre-checks
    if not args.skip_checks:
        print("\n🔍 Executing pre-checks...")

        if not check_service_health():
            print("\n❌ Service check failed, please ensure Markio service is running")
            sys.exit(1)

        if not check_test_files():
            print("\n❌ Test file check failed")
            sys.exit(1)

        print("✅ Pre-checks passed")

    # Run tests
    print(f"\n🎯 Starting {args.type} tests...")
    success = run_tests(
        test_type=args.type, verbose=args.verbose, output_file=args.output
    )

    # Output results
    if success:
        print("\n🎉 Test execution successful!")
        sys.exit(0)
    else:
        print("\n💥 Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
