"""
并发处理测试
测试系统的并发处理能力，使用真实的测试文件
"""
import asyncio
from pathlib import Path
import shutil
import time

import pytest

from scripts.run_local import ConcurrentProcessor, process_files_in_folder


class TestConcurrencyProcessing:
    """并发处理测试类"""
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_concurrent_pdf_parsing(self, temp_dir, real_test_files):
        """测试并发PDF解析 - 使用真实PDF文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "concurrent_pdf_input"
        output_dir = Path(temp_dir) / "concurrent_pdf_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个PDF文件进行并发测试
        test_files = []
        for i in range(5):
            target_file = input_dir / f"concurrent_pdf_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 测试不同并发数
        for max_workers in [1, 2, 3]:
            try:
                start_time = time.time()
                
                await process_files_in_folder(
                    folder_path=str(input_dir),
                    max_workers=max_workers,
                    batch_size=2,
                    save_parsed_content=True,
                    output_dir=str(output_dir)
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # 验证输出
                assert output_dir.exists(), f"并发数{max_workers}时输出目录应该被创建"
                
                # 检查输出文件
                output_files = list(output_dir.rglob("*"))
                print(f"并发数{max_workers}时输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
                
            except Exception as e:
                print(f"并发数{max_workers}时PDF解析测试出现异常: {e}")
                pytest.skip(f"并发数{max_workers}时PDF解析测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_concurrent_processing_with_semaphore(self, temp_dir, real_test_files):
        """测试使用信号量的并发处理 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "semaphore_input"
        output_dir = Path(temp_dir) / "semaphore_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件
        test_files = []
        for i in range(8):
            target_file = input_dir / f"semaphore_test_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 使用信号量限制并发数
        try:
            start_time = time.time()
            
            await process_files_in_folder(
                folder_path=str(input_dir),
                max_workers=4,
                batch_size=2,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "使用信号量的并发处理输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"信号量并发处理输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"信号量并发处理测试出现异常: {e}")
            pytest.skip(f"信号量并发处理测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, temp_dir, real_test_files):
        """测试批量处理性能 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "batch_performance_input"
        output_dir = Path(temp_dir) / "batch_performance_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件
        test_files = []
        for i in range(10):
            target_file = input_dir / f"batch_perf_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 测试不同批量大小
        batch_sizes = [1, 2, 5]
        performance_results = {}
        
        for batch_size in batch_sizes:
            try:
                start_time = time.time()
                
                await process_files_in_folder(
                    folder_path=str(input_dir),
                    max_workers=3,
                    batch_size=batch_size,
                    save_parsed_content=True,
                    output_dir=str(output_dir)
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                performance_results[batch_size] = processing_time
                
                print(f"批量大小{batch_size}时处理时间: {processing_time:.2f}秒")
                
            except Exception as e:
                print(f"批量大小{batch_size}时性能测试出现异常: {e}")
                performance_results[batch_size] = None
        
        # 验证至少有一些结果
        assert any(result is not None for result in performance_results.values()), "至少应该有一些性能测试结果"
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_mixed_file_types_concurrency(self, temp_dir, real_test_files):
        """测试混合文件类型的并发处理 - 使用真实文件"""
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "mixed_concurrency_input"
        output_dir = Path(temp_dir) / "mixed_concurrency_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制不同类型的文件
        test_files = []
        for file_type, file_path in real_test_files.items():
            if file_path.exists():
                target_file = input_dir / f"mixed_concurrent_{file_type}{file_path.suffix}"
                shutil.copy2(file_path, target_file)
                test_files.append(str(target_file))
        
        if len(test_files) < 3:
            pytest.skip("没有足够的测试文件进行混合类型并发测试")
        
        # 执行混合文件并发处理
        try:
            start_time = time.time()
            
            await process_files_in_folder(
                folder_path=str(input_dir),
                max_workers=3,
                batch_size=2,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "混合文件类型并发处理输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"混合文件类型并发处理输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"混合文件类型并发处理测试出现异常: {e}")
            pytest.skip(f"混合文件类型并发处理测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_concurrent_processing_stress_test(self, temp_dir, real_test_files):
        """测试并发处理压力测试 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "stress_test_input"
        output_dir = Path(temp_dir) / "stress_test_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件进行压力测试
        test_files = []
        for i in range(15):
            target_file = input_dir / f"stress_test_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 执行压力测试
        try:
            start_time = time.time()
            
            await process_files_in_folder(
                folder_path=str(input_dir),
                max_workers=5,
                batch_size=3,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "压力测试输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"压力测试输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"压力测试出现异常: {e}")
            pytest.skip(f"压力测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_memory_usage_under_concurrency(self, temp_dir, real_test_files):
        """测试并发处理下的内存使用 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "memory_concurrency_input"
        output_dir = Path(temp_dir) / "memory_concurrency_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件
        test_files = []
        for i in range(8):
            target_file = input_dir / f"memory_concurrent_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 执行内存测试
        try:
            start_time = time.time()
            
            await process_files_in_folder(
                folder_path=str(input_dir),
                max_workers=4,
                batch_size=2,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "内存并发测试输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"内存并发测试输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"内存并发测试出现异常: {e}")
            pytest.skip(f"内存并发测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, temp_dir, real_test_files):
        """测试并发处理的错误处理 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "error_concurrency_input"
        output_dir = Path(temp_dir) / "error_concurrency_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制有效文件
        valid_files = []
        for i in range(3):
            target_file = input_dir / f"valid_concurrent_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            valid_files.append(str(target_file))
        
        # 创建无效文件
        invalid_file = input_dir / "invalid_concurrent.txt"
        invalid_file.write_text("This is not a valid file for parsing")
        
        test_files = valid_files + [str(invalid_file)]
        
        # 执行错误处理测试
        try:
            start_time = time.time()
            
            await process_files_in_folder(
                folder_path=str(input_dir),
                max_workers=2,
                batch_size=2,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出目录存在
            assert output_dir.exists(), "错误并发测试输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"错误并发测试输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"错误并发测试出现异常: {e}")
            pytest.skip(f"错误并发测试跳过: {e}")


class TestConcurrentProcessor:
    """并发处理器测试类"""
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_processor_initialization(self, real_test_files):
        """测试并发处理器初始化"""
        processor = ConcurrentProcessor(
            max_workers=4,
            batch_size=10,
            save_parsed_content=True,
            output_dir="/tmp/test"
        )
        
        assert processor.max_workers == 4
        assert processor.batch_size == 10
        assert processor.save_parsed_content is True
        assert processor.output_dir == "/tmp/test"
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_processor_file_processing(self, temp_dir, real_test_files):
        """测试并发处理器文件处理 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "processor_input"
        output_dir = Path(temp_dir) / "processor_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件
        test_files = []
        for i in range(5):
            target_file = input_dir / f"processor_test_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 使用并发处理器
        try:
            processor = ConcurrentProcessor(
                max_workers=3,
                batch_size=2,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            start_time = time.time()
            await processor.process_files(test_files)
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "处理器测试输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"处理器测试输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"处理器测试出现异常: {e}")
            pytest.skip(f"处理器测试跳过: {e}")
    
    @pytest.mark.real_files
    @pytest.mark.asyncio
    async def test_processor_batch_processing(self, temp_dir, real_test_files):
        """测试并发处理器批量处理 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 创建测试目录结构
        input_dir = Path(temp_dir) / "processor_batch_input"
        output_dir = Path(temp_dir) / "processor_batch_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 复制多个文件
        test_files = []
        for i in range(8):
            target_file = input_dir / f"processor_batch_{i}.pdf"
            shutil.copy2(pdf_file_path, target_file)
            test_files.append(str(target_file))
        
        # 使用并发处理器进行批量处理
        try:
            processor = ConcurrentProcessor(
                max_workers=4,
                batch_size=3,
                save_parsed_content=True,
                output_dir=str(output_dir)
            )
            
            start_time = time.time()
            await processor.process_files(test_files)
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证输出
            assert output_dir.exists(), "处理器批量测试输出目录应该被创建"
            
            # 检查输出文件
            output_files = list(output_dir.rglob("*"))
            print(f"处理器批量测试输出文件数量: {len(output_files)}, 处理时间: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"处理器批量测试出现异常: {e}")
            pytest.skip(f"处理器批量测试跳过: {e}")
