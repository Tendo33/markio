"""
Concurrent performance tests for markio API endpoints
"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import pytest


class TestConcurrentPerformance:
    """Test class for concurrent performance testing"""

    def test_single_endpoint_concurrent(
        self, test_files_dir, test_files, api_endpoints
    ):
        """Test concurrent requests to a single endpoint (PDF)"""
        endpoint = api_endpoints["pdf"]
        test_file = test_files_dir / test_files["pdf"]

        assert test_file.exists(), f"Test PDF file not found: {test_file}"

        # Test parameters
        concurrent_users = 5
        results = []
        errors = []

        def make_request(user_id):
            """Make a single request"""
            try:
                start_time = time.time()

                with open(test_file, "rb") as f:
                    files = {"file": (test_files["pdf"], f, "application/pdf")}
                    data = {"config": json.dumps({"save_parsed_content": False})}

                    with httpx.Client(
                        base_url="http://0.0.0.0:8000", timeout=120.0
                    ) as client:
                        response = client.post(endpoint, files=files, data=data)

                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200:
                    results.append(
                        {
                            "user_id": user_id,
                            "response_time": response_time,
                            "status_code": response.status_code,
                            "success": True,
                        }
                    )
                else:
                    errors.append(
                        {
                            "user_id": user_id,
                            "status_code": response.status_code,
                            "error": response.text,
                            "success": False,
                        }
                    )

            except Exception as e:
                errors.append({"user_id": user_id, "error": str(e), "success": False})

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(make_request, i) for i in range(concurrent_users)
            ]

            for future in as_completed(futures):
                future.result()  # This will raise any exceptions

        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = errors

        # Performance metrics
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            print("\n=== Single Endpoint Concurrent Test Results ===")
            print(f"Concurrent Users: {concurrent_users}")
            print(f"Successful Requests: {len(successful_requests)}")
            print(f"Failed Requests: {len(failed_requests)}")
            print(
                f"Success Rate: {len(successful_requests) / concurrent_users * 100:.1f}%"
            )
            print(f"Average Response Time: {avg_response_time:.2f}s")
            print(f"Min Response Time: {min_response_time:.2f}s")
            print(f"Max Response Time: {max_response_time:.2f}s")

            # Assertions
            assert len(successful_requests) >= concurrent_users * 0.8, (
                f"Success rate too low: {len(successful_requests)}/{concurrent_users}"
            )
            assert avg_response_time < 30.0, (
                f"Average response time too high: {avg_response_time}s"
            )
        else:
            pytest.fail("No successful requests in concurrent test")

    def test_mixed_endpoints_concurrent(
        self, test_files_dir, test_files, api_endpoints
    ):
        """Test concurrent requests to different endpoints"""
        # Select different file types for mixed testing
        test_cases = [
            ("pdf", test_files["pdf"]),
            ("docx", test_files["docx"]),
            ("xlsx", test_files["xlsx"]),
            ("html", test_files["html"]),
            ("epub", test_files["epub"]),
        ]

        results = []
        errors = []

        def make_mixed_request(test_case):
            """Make a request to a specific endpoint"""
            file_type, filename = test_case
            endpoint = api_endpoints[file_type]
            test_file = test_files_dir / filename

            try:
                start_time = time.time()

                with open(test_file, "rb") as f:
                    files = {"file": (filename, f, "application/octet-stream")}
                    data = {"config": json.dumps({"save_parsed_content": False})}

                    with httpx.Client(
                        base_url="http://0.0.0.0:8000", timeout=120.0
                    ) as client:
                        response = client.post(endpoint, files=files, data=data)

                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200:
                    results.append(
                        {
                            "file_type": file_type,
                            "filename": filename,
                            "response_time": response_time,
                            "status_code": response.status_code,
                            "success": True,
                        }
                    )
                else:
                    errors.append(
                        {
                            "file_type": file_type,
                            "filename": filename,
                            "status_code": response.status_code,
                            "error": response.text,
                            "success": False,
                        }
                    )

            except Exception as e:
                errors.append(
                    {
                        "file_type": file_type,
                        "filename": filename,
                        "error": str(e),
                        "success": False,
                    }
                )

        # Execute mixed concurrent requests
        with ThreadPoolExecutor(max_workers=len(test_cases)) as executor:
            futures = [
                executor.submit(make_mixed_request, test_case)
                for test_case in test_cases
            ]

            for future in as_completed(futures):
                future.result()

        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = errors

        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)

            print("\n=== Mixed Endpoints Concurrent Test Results ===")
            print(f"Total Test Cases: {len(test_cases)}")
            print(f"Successful Requests: {len(successful_requests)}")
            print(f"Failed Requests: {len(failed_requests)}")
            print(
                f"Success Rate: {len(successful_requests) / len(test_cases) * 100:.1f}%"
            )
            print(f"Average Response Time: {avg_response_time:.2f}s")

            # Print individual results
            for result in successful_requests:
                print(f"  {result['file_type']}: {result['response_time']:.2f}s")

            # Assertions
            assert len(successful_requests) >= len(test_cases) * 0.8, (
                f"Success rate too low: {len(successful_requests)}/{len(test_cases)}"
            )
        else:
            pytest.fail("No successful requests in mixed concurrent test")

    def test_load_test_small_files(self, test_files_dir, test_files, api_endpoints):
        """Test load handling with small files (XLSX, HTML)"""
        # Use smaller files for load testing
        small_files = [("xlsx", test_files["xlsx"]), ("html", test_files["html"])]

        # Simulate higher load
        concurrent_users = 10
        results = []
        errors = []

        def make_load_request(user_id, test_case):
            """Make a load test request"""
            file_type, filename = test_case
            endpoint = api_endpoints[file_type]
            test_file = test_files_dir / filename

            try:
                start_time = time.time()

                with open(test_file, "rb") as f:
                    files = {"file": (filename, f, "application/octet-stream")}
                    data = {"config": json.dumps({"save_parsed_content": False})}

                    with httpx.Client(
                        base_url="http://0.0.0.0:8000", timeout=60.0
                    ) as client:
                        response = client.post(endpoint, files=files, data=data)

                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200:
                    results.append(
                        {
                            "user_id": user_id,
                            "file_type": file_type,
                            "response_time": response_time,
                            "success": True,
                        }
                    )
                else:
                    errors.append(
                        {
                            "user_id": user_id,
                            "file_type": file_type,
                            "status_code": response.status_code,
                            "error": response.text,
                            "success": False,
                        }
                    )

            except Exception as e:
                errors.append(
                    {
                        "user_id": user_id,
                        "file_type": file_type,
                        "error": str(e),
                        "success": False,
                    }
                )

        # Execute load test
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                # Distribute requests across different file types
                test_case = small_files[user_id % len(small_files)]
                futures.append(executor.submit(make_load_request, user_id, test_case))

            for future in as_completed(futures):
                future.result()

        # Analyze load test results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = errors

        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)

            print("\n=== Load Test Results (Small Files) ===")
            print(f"Concurrent Users: {concurrent_users}")
            print(f"Successful Requests: {len(successful_requests)}")
            print(f"Failed Requests: {len(failed_requests)}")
            print(
                f"Success Rate: {len(successful_requests) / concurrent_users * 100:.1f}%"
            )
            print(f"Average Response Time: {avg_response_time:.2f}s")
            print(
                f"Throughput: {len(successful_requests) / max(response_times):.2f} requests/second"
            )

            # Assertions for load test
            assert len(successful_requests) >= concurrent_users * 0.7, (
                f"Load test success rate too low: {len(successful_requests)}/{concurrent_users}"
            )
            assert avg_response_time < 20.0, (
                f"Load test average response time too high: {avg_response_time}s"
            )
        else:
            pytest.fail("No successful requests in load test")

    def test_stress_test_large_files(self, test_files_dir, test_files, api_endpoints):
        """Test stress handling with large files (PDF, PPT)"""
        # Use larger files for stress testing
        large_files = [("pdf", test_files["pdf"]), ("ppt", test_files["ppt"])]

        # Simulate stress conditions
        concurrent_users = 3  # Fewer users for large files
        results = []
        errors = []

        def make_stress_request(user_id, test_case):
            """Make a stress test request"""
            file_type, filename = test_case
            endpoint = api_endpoints[file_type]
            test_file = test_files_dir / filename

            try:
                start_time = time.time()

                with open(test_file, "rb") as f:
                    files = {"file": (filename, f, "application/octet-stream")}
                    data = {"config": json.dumps({"save_parsed_content": False})}

                    with httpx.Client(
                        base_url="http://0.0.0.0:8000", timeout=180.0
                    ) as client:
                        response = client.post(endpoint, files=files, data=data)

                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200:
                    results.append(
                        {
                            "user_id": user_id,
                            "file_type": file_type,
                            "response_time": response_time,
                            "success": True,
                        }
                    )
                else:
                    errors.append(
                        {
                            "user_id": user_id,
                            "file_type": file_type,
                            "status_code": response.status_code,
                            "error": response.text,
                            "success": False,
                        }
                    )

            except Exception as e:
                errors.append(
                    {
                        "user_id": user_id,
                        "file_type": file_type,
                        "error": str(e),
                        "success": False,
                    }
                )

        # Execute stress test
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                # Distribute requests across different file types
                test_case = large_files[user_id % len(large_files)]
                futures.append(executor.submit(make_stress_request, user_id, test_case))

            for future in as_completed(futures):
                future.result()

        # Analyze stress test results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = errors

        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)

            print("\n=== Stress Test Results (Large Files) ===")
            print(f"Concurrent Users: {concurrent_users}")
            print(f"Successful Requests: {len(successful_requests)}")
            print(f"Failed Requests: {len(failed_requests)}")
            print(
                f"Success Rate: {len(successful_requests) / concurrent_users * 100:.1f}%"
            )
            print(f"Average Response Time: {avg_response_time:.2f}s")

            # Assertions for stress test
            assert len(successful_requests) >= concurrent_users * 0.6, (
                f"Stress test success rate too low: {len(successful_requests)}/{concurrent_users}"
            )
            # Large files may take longer, so we're more lenient with response time
            assert avg_response_time < 60.0, (
                f"Stress test average response time too high: {avg_response_time}s"
            )
        else:
            pytest.fail("No successful requests in stress test")
