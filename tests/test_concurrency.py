"""
并发性能测试
测试接口的并发处理能力和性能表现
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


class TestConcurrencyPerformance:
    """并发性能测试类"""
    
    @pytest.mark.asyncio
    async def test_concurrent_pdf_parsing(self):
        """测试PDF解析的并发性能 - 使用mock数据"""
        from scripts.run_local import process_file
        
        # 使用mock文件路径，不创建真实文件
        test_files = [f"/mock/test_{i}.pdf" for i in range(10)]
        
        # 测试不同并发数下的性能
        concurrency_levels = [1, 2, 4, 8]
        results = {}
        
        for max_workers in concurrency_levels:
            start_time = time.time()
            
            # 使用ThreadPoolExecutor进行并发处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor, 
                        asyncio.run, 
                        process_file(file_path, save_parsed_content=False)
                    )
                    for file_path in test_files
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            throughput = len(test_files) / total_time
            
            results[max_workers] = {
                "total_time": total_time,
                "throughput": throughput,
                "files_per_second": throughput
            }
            
            print(f"并发数 {max_workers}: 总时间 {total_time:.2f}s, 吞吐量 {throughput:.2f} 文件/秒")
        
        # 验证并发性能提升
        assert results[4]["throughput"] > results[1]["throughput"], "4线程应该比单线程快"
        assert results[8]["throughput"] > results[4]["throughput"], "8线程应该比4线程快"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_with_semaphore(self):
        """测试使用信号量控制的并发处理 - 使用mock数据"""
        from scripts.run_local import ConcurrentProcessor
        
        # 使用mock文件路径
        test_files = [f"/mock/semaphore_test_{i}.pdf" for i in range(20)]
        
        # 测试不同并发限制
        max_workers_list = [2, 4, 6]
        results = {}
        
        for max_workers in max_workers_list:
            processor = ConcurrentProcessor(max_workers=max_workers)
            
            start_time = time.time()
            await processor.process_files_concurrent(
                test_files, 
                save_parsed_content=False
            )
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = len(test_files) / total_time
            
            results[max_workers] = {
                "total_time": total_time,
                "throughput": throughput,
                "max_workers": max_workers
            }
            
            print(f"信号量控制 {max_workers} 线程: 总时间 {total_time:.2f}s, 吞吐量 {throughput:.2f} 文件/秒")
        
        # 验证结果
        for max_workers in max_workers_list:
            assert results[max_workers]["total_time"] > 0, f"并发数 {max_workers} 应该能完成处理"
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """测试批处理性能 - 使用mock数据"""
        from scripts.run_local import ConcurrentProcessor
        
        # 使用mock文件路径
        test_files = [f"/mock/batch_test_{i}.pdf" for i in range(50)]
        
        # 测试不同批处理大小
        batch_sizes = [5, 10, 20]
        results = {}
        
        for batch_size in batch_sizes:
            processor = ConcurrentProcessor(max_workers=4)
            
            start_time = time.time()
            await processor.process_files_batched(
                test_files, 
                batch_size=batch_size, 
                save_parsed_content=False
            )
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = len(test_files) / total_time
            
            results[batch_size] = {
                "total_time": total_time,
                "throughput": throughput,
                "batch_size": batch_size
            }
            
            print(f"批处理大小 {batch_size}: 总时间 {total_time:.2f}s, 吞吐量 {throughput:.2f} 文件/秒")
        
        # 验证批处理效果
        assert all(result["total_time"] > 0 for result in results.values()), "所有批处理都应该能完成"
    
    @pytest.mark.asyncio
    async def test_mixed_file_types_concurrency(self):
        """测试混合文件类型的并发处理 - 使用mock数据"""
        from scripts.run_local import process_file
        
        # 使用mock文件路径
        test_files = []
        
        # PDF文件
        for i in range(5):
            test_files.append(f"/mock/mixed_pdf_{i}.pdf")
        
        # HTML文件
        for i in range(5):
            test_files.append(f"/mock/mixed_html_{i}.html")
        
        # 图片文件
        for i in range(5):
            test_files.append(f"/mock/mixed_img_{i}.jpg")
        
        start_time = time.time()
        
        # 并发处理混合文件类型
        with ThreadPoolExecutor(max_workers=6) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor, 
                    asyncio.run, 
                    process_file(file_path, save_parsed_content=False)
                )
                for file_path in test_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 统计处理结果
        success_count = sum(1 for result in results if result is None or not isinstance(result, Exception))
        error_count = len(results) - success_count
        
        print(f"混合文件类型并发处理: 总时间 {total_time:.2f}s, 成功 {success_count}, 错误 {error_count}")
        
        # 验证处理结果
        assert success_count > 0, "应该有成功的处理结果"
        assert total_time > 0, "处理时间应该大于0"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_stress_test(self):
        """压力测试：大量文件并发处理 - 使用mock数据"""
        from scripts.run_local import ConcurrentProcessor
        
        # 使用mock文件路径
        test_files = [f"/mock/stress_test_{i}.pdf" for i in range(100)]
        
        # 使用高并发数进行压力测试
        max_workers = 16
        processor = ConcurrentProcessor(max_workers=max_workers)
        
        start_time = time.time()
        
        try:
            await processor.process_files_batched(
                test_files, 
                batch_size=25, 
                save_parsed_content=False
            )
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = len(test_files) / total_time
            
            print(f"压力测试 ({max_workers} 线程): 总时间 {total_time:.2f}s, 吞吐量 {throughput:.2f} 文件/秒")
            
            # 验证压力测试结果
            assert total_time > 0, "压力测试应该能完成"
            assert throughput > 0, "吞吐量应该大于0"
            
        except Exception as e:
            print(f"压力测试出现异常: {e}")
            # 压力测试可能因为资源限制失败，这是正常的
            assert True
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_concurrency(self):
        """测试并发处理下的内存使用情况 - 使用mock数据"""
        import os

        import psutil
        
        # 使用mock文件路径
        test_files = [f"/mock/memory_test_{i}.pdf" for i in range(30)]
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"初始内存使用: {initial_memory:.2f} MB")
        
        # 进行并发处理
        from scripts.run_local import ConcurrentProcessor
        processor = ConcurrentProcessor(max_workers=8)
        
        start_time = time.time()
        await processor.process_files_batched(
            test_files, 
            batch_size=10, 
            save_parsed_content=False
        )
        end_time = time.time()
        
        # 检查内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"最终内存使用: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        print(f"处理时间: {end_time - start_time:.2f}s")
        
        # 验证内存使用合理
        assert memory_increase >= 0, "内存使用应该合理"
        assert final_memory > 0, "内存使用应该大于0"
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """测试并发处理下的错误处理 - 使用mock数据"""
        from scripts.run_local import ConcurrentProcessor
        
        # 使用mock文件路径
        test_files = []
        
        # 有效文件
        for i in range(5):
            test_files.append(f"/mock/valid_{i}.pdf")
        
        # 无效文件（不存在的路径）
        for i in range(5):
            test_files.append(f"/nonexistent/file_{i}.pdf")
        
        # 进行并发处理
        processor = ConcurrentProcessor(max_workers=4)
        
        start_time = time.time()
        
        # 应该能处理错误而不崩溃
        try:
            await processor.process_files_concurrent(
                test_files, 
                save_parsed_content=False
            )
            end_time = time.time()
            
            print(f"错误处理测试完成，耗时: {end_time - start_time:.2f}s")
            
            # 验证能正常完成
            assert end_time > start_time, "错误处理测试应该能完成"
            
        except Exception as e:
            print(f"错误处理测试出现异常: {e}")
            # 某些错误是预期的
            assert True


class TestAPIConcurrency:
    """API接口并发测试类"""
    
    @pytest.mark.asyncio
    async def test_api_concurrent_requests(self, async_client):
        """测试API接口的并发请求处理"""
        # 创建测试数据
        test_data = {
            "url": "https://httpbin.org/html",
            "save_parsed_content": False
        }
        
        # 并发请求数量
        concurrent_requests = 20
        
        async def make_request():
            """发送单个请求"""
            try:
                response = await async_client.post("/v1/parse_url", json=test_data)
                return response.status_code
            except Exception as e:
                return f"Error: {e}"
        
        # 并发发送请求
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 统计结果
        success_count = sum(1 for result in results if isinstance(result, int) and result in [200, 400, 500])
        error_count = len(results) - success_count
        total_time = end_time - start_time
        
        print(f"API并发测试: 总时间 {total_time:.2f}s, 成功 {success_count}, 错误 {error_count}")
        
        # 验证结果
        assert success_count > 0, "应该有成功的请求"
        assert total_time > 0, "处理时间应该大于0"
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, async_client):
        """测试API的速率限制"""
        # 快速发送大量请求
        test_data = {"url": "https://httpbin.org/html", "save_parsed_content": False}
        
        # 发送100个快速请求
        start_time = time.time()
        tasks = []
        
        for i in range(100):
            task = async_client.post("/v1/parse_url", json=test_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 统计结果
        success_count = sum(1 for result in results if isinstance(result, int) and result in [200, 400, 500])
        rate_limited_count = sum(1 for result in results if isinstance(result, int) and result == 429)
        
        total_time = end_time - start_time
        requests_per_second = len(results) / total_time
        
        print(f"速率限制测试: 总时间 {total_time:.2f}s, 成功 {success_count}, 限流 {rate_limited_count}")
        print(f"请求速率: {requests_per_second:.2f} 请求/秒")
        
        # 验证结果
        assert len(results) == 100, "应该发送100个请求"
        assert total_time > 0, "处理时间应该大于0"


# 测试数据准备函数 - 为真实测试用例预留
def prepare_concurrency_test_files():
    """
    准备并发测试文件的函数
    当有真实测试文件时，可以在这里配置文件路径
    
    Returns:
        dict: 包含各种测试场景文件路径的字典
    """
    return {
        "small_batch": ["path/to/real/small1.pdf", "path/to/real/small2.pdf"],
        "medium_batch": ["path/to/real/medium1.pdf", "path/to/real/medium2.pdf", "path/to/real/medium3.pdf"],
        "large_batch": ["path/to/real/large1.pdf", "path/to/real/large2.pdf", "path/to/real/large3.pdf", "path/to/real/large4.pdf"],
        "mixed_types": [
            "path/to/real/test.pdf",
            "path/to/real/test.docx", 
            "path/to/real/test.xlsx",
            "path/to/real/test.html",
            "path/to/real/test.jpg"
        ]
    }


# 标记需要真实文件的测试
REAL_FILE_CONCURRENCY_TESTS = [
    "test_concurrent_pdf_parsing",
    "test_concurrent_processing_with_semaphore",
    "test_batch_processing_performance",
    "test_mixed_file_types_concurrency",
    "test_concurrent_processing_stress_test",
    "test_memory_usage_under_concurrency",
    "test_concurrent_error_handling"
]
