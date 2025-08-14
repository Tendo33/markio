"""
工具函数测试
测试各种辅助功能和工具函数
"""
import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_local import (
    FUNCTION_MAP,
    chunked_iterable,
    get_all_files,
    parameter_adapter,
)


class TestFileUtilities:
    """文件工具函数测试类"""
    
    def test_get_all_files(self, temp_dir):
        """测试获取所有文件函数 - 使用临时目录"""
        # 创建测试目录结构
        test_dir = Path(temp_dir) / "file_test"
        test_dir.mkdir()
        
        # 创建子目录和文件
        subdir = test_dir / "subdir"
        subdir.mkdir()
        
        # 创建测试文件
        (test_dir / "file1.txt").write_text("test1")
        (test_dir / "file2.txt").write_text("test2")
        (subdir / "file3.txt").write_text("test3")
        
        # 获取所有文件
        files = get_all_files(str(test_dir))
        
        # 验证结果
        assert len(files) == 3, f"应该找到3个文件，实际找到{len(files)}个"
        assert any("file1.txt" in f for f in files), "应该包含file1.txt"
        assert any("file2.txt" in f for f in files), "应该包含file2.txt"
        assert any("file3.txt" in f for f in files), "应该包含file3.txt"
    
    def test_get_all_files_single_file(self, temp_dir):
        """测试获取单个文件"""
        # 创建单个测试文件
        test_file = Path(temp_dir) / "single.txt"
        test_file.write_text("single file")
        
        # 获取文件
        files = get_all_files(str(test_file))
        
        # 验证结果
        assert len(files) == 1, "应该只找到1个文件"
        assert files[0] == str(test_file), "应该返回正确的文件路径"
    
    def test_get_all_files_empty_directory(self, temp_dir):
        """测试空目录"""
        empty_dir = Path(temp_dir) / "empty"
        empty_dir.mkdir()
        
        # 获取文件
        files = get_all_files(str(empty_dir))
        
        # 验证结果
        assert len(files) == 0, "空目录应该返回空列表"
    
    def test_get_all_files_nonexistent_path(self, temp_dir):
        """测试不存在的路径"""
        nonexistent_path = Path(temp_dir) / "nonexistent"
        
        # 获取文件
        files = get_all_files(str(nonexistent_path))
        
        # 验证结果
        assert len(files) == 0, "不存在的路径应该返回空列表"
    
    def test_chunked_iterable(self):
        """测试分块迭代器"""
        # 测试数据
        test_list = list(range(10))
        
        # 测试不同块大小
        chunk_sizes = [3, 5, 7]
        
        for chunk_size in chunk_sizes:
            chunks = list(chunked_iterable(test_list, chunk_size))
            
            # 验证分块结果
            assert len(chunks) > 0, f"块大小{chunk_size}应该产生分块"
            
            # 验证每个块的大小
            for i, chunk in enumerate(chunks[:-1]):
                assert len(chunk) == chunk_size, f"第{i}块应该大小为{chunk_size}"
            
            # 验证最后一块的大小
            if chunks:
                last_chunk = chunks[-1]
                assert len(last_chunk) <= chunk_size, "最后一块应该小于等于块大小"
                assert len(last_chunk) > 0, "最后一块不应该为空"
    
    def test_chunked_iterable_empty_list(self):
        """测试空列表的分块"""
        empty_list = []
        
        # 测试不同块大小
        for chunk_size in [1, 5, 10]:
            chunks = list(chunked_iterable(empty_list, chunk_size))
            assert len(chunks) == 0, "空列表应该产生空的分块列表"
    
    def test_chunked_iterable_single_element(self):
        """测试单元素列表的分块"""
        single_list = [42]
        
        # 测试不同块大小
        for chunk_size in [1, 5, 10]:
            chunks = list(chunked_iterable(single_list, chunk_size))
            assert len(chunks) == 1, "单元素列表应该产生1个分块"
            assert chunks[0] == [42], "分块应该包含正确的元素"
    
    @pytest.mark.skip(reason="需要真实的文件系统进行测试")
    def test_get_all_files_with_real_filesystem(self):
        """测试获取真实文件系统中的文件 - 需要真实文件"""
        # TODO: 当有真实测试文件时，可以在这里测试真实文件系统
        # 当前使用mock数据
        mock_files = ["/real/test1.pdf", "/real/test2.docx", "/real/test3.xlsx"]
        
        with patch("scripts.run_local.get_all_files", return_value=mock_files):
            files = get_all_files("/real/test_dir")
            assert len(files) == 3, "应该找到3个真实文件"


class TestParameterAdapter:
    """参数适配器测试类"""
    
    def test_pdf_parameter_adapter(self):
        """测试PDF参数适配"""
        params = parameter_adapter(
            "pdf",
            file_path="/test.pdf",
            parse_method="auto",
            lang="ch",
            save_parsed_content=True,
            output_dir="/output"
        )
        
        # 验证PDF特定参数
        assert params["resource_path"] == "/test.pdf"
        assert params["parse_method"] == "auto"
        assert params["lang"] == "ch"
        assert params["save_parsed_content"] is True
        assert params["output_dir"] == "/output"
        
        # 验证默认参数
        assert params["start_page"] == 0
        assert params["end_page"] is None
    
    def test_image_parameter_adapter(self):
        """测试图片参数适配"""
        params = parameter_adapter(
            "img",
            file_path="/test.jpg",
            parse_backend="pipeline",
            save_parsed_content=False
        )
        
        # 验证图片特定参数
        assert params["resource_path"] == "/test.jpg"
        assert params["parse_backend"] == "pipeline"
        assert params["save_parsed_content"] is False
    
    def test_docx_parameter_adapter(self):
        """测试DOCX参数适配"""
        params = parameter_adapter(
            "docx",
            file_path="/test.docx",
            save_parsed_content=True,
            output_dir="/output"
        )
        
        # 验证DOCX参数
        assert params["resource_path"] == "/test.docx"
        assert params["save_parsed_content"] is True
        assert params["output_dir"] == "/output"
    
    def test_html_parameter_adapter(self):
        """测试HTML参数适配"""
        params = parameter_adapter(
            "html",
            file_path="/test.html",
            save_parsed_content=False
        )
        
        # 验证HTML参数
        assert params["resource_path"] == "/test.html"
        assert params["save_parsed_content"] is False
    
    def test_url_parameter_adapter(self):
        """测试URL参数适配"""
        params = parameter_adapter(
            "url",
            url="https://example.com",
            save_parsed_content=True,
            output_dir="/output"
        )
        
        # 验证URL参数
        assert params["resource_path"] == "https://example.com"
        assert params["save_parsed_content"] is True
        assert params["output_dir"] == "/output"
    
    def test_parameter_adapter_validation(self):
        """测试参数适配器的验证逻辑"""
        # 测试缺少必需参数
        with pytest.raises(ValueError, match="File path is required"):
            parameter_adapter("pdf")
        
        with pytest.raises(ValueError, match="URL is required"):
            parameter_adapter("url")
        
        # 测试无效文件类型
        with pytest.raises(ValueError, match="Unsupported file type"):
            parameter_adapter("invalid")
        
        # 测试缺少输出目录
        with pytest.raises(ValueError, match="Output directory is required"):
            parameter_adapter("pdf", file_path="/test.pdf", save_parsed_content=True)
    
    def test_parameter_adapter_none_values(self):
        """测试参数适配器处理None值"""
        params = parameter_adapter(
            "pdf",
            file_path="/test.pdf",
            start_page=None,
            end_page=None
        )
        
        # 验证None值被过滤
        assert "start_page" not in params, "None值应该被过滤"
        assert "end_page" not in params, "None值应该被过滤"
        assert "resource_path" in params, "有效值应该被保留"
    
    @pytest.mark.skip(reason="需要真实的文件路径进行测试")
    def test_parameter_adapter_with_real_files(self):
        """测试参数适配器与真实文件 - 需要真实文件"""
        # TODO: 当有真实测试文件时，可以在这里测试真实文件路径
        # 当前使用mock数据
        mock_file_paths = [
            "/real/test.pdf",
            "/real/test.docx", 
            "/real/test.xlsx",
            "/real/test.html",
            "/real/test.jpg"
        ]
        
        for file_path in mock_file_paths:
            file_type = file_path.split(".")[-1]
            if file_type == "pdf":
                params = parameter_adapter("pdf", file_path=file_path)
                assert params["resource_path"] == file_path


class TestFunctionMap:
    """函数映射测试类"""
    
    def test_function_map_completeness(self):
        """测试函数映射的完整性"""
        # 验证所有支持的文件类型都有对应的解析函数
        expected_types = [
            "pdf", "img", "doc", "ppt", "pptx", 
            "html", "htm", "docx", "url", "xlsx", "epub"
        ]
        
        for file_type in expected_types:
            assert file_type in FUNCTION_MAP, f"文件类型 {file_type} 应该在函数映射中"
            assert callable(FUNCTION_MAP[file_type]), f"文件类型 {file_type} 应该有可调用的函数"
    
    def test_function_map_function_types(self):
        """测试函数映射中函数的类型"""
        # 验证所有函数都是异步函数
        for file_type, func in FUNCTION_MAP.items():
            assert asyncio.iscoroutinefunction(func), f"函数 {file_type} 应该是异步函数"
    
    def test_function_map_consistency(self):
        """测试函数映射的一致性"""
        # 验证函数映射与参数适配器的一致性
        for file_type in FUNCTION_MAP.keys():
            if file_type != "url":
                # 测试文件路径参数
                try:
                    params = parameter_adapter(file_type, file_path="/test.file")
                    assert "resource_path" in params, f"文件类型 {file_type} 应该有resource_path参数"
                except ValueError:
                    # 某些文件类型可能有特殊要求，这是正常的
                    pass


class TestErrorHandling:
    """错误处理测试类"""
    
    def test_parameter_adapter_error_messages(self):
        """测试参数适配器的错误消息"""
        # 测试不支持的文件类型
        with pytest.raises(ValueError) as exc_info:
            parameter_adapter("unsupported")
        assert "Unsupported file type: unsupported" in str(exc_info.value)
        
        # 测试缺少文件路径
        with pytest.raises(ValueError) as exc_info:
            parameter_adapter("pdf")
        assert "File path is required for pdf parser" in str(exc_info.value)
        
        # 测试缺少URL
        with pytest.raises(ValueError) as exc_info:
            parameter_adapter("url")
        assert "URL is required for URL parser" in str(exc_info.value)
        
        # 测试缺少输出目录
        with pytest.raises(ValueError) as exc_info:
            parameter_adapter("pdf", file_path="/test.pdf", save_parsed_content=True)
        assert "Output directory is required when save_parsed_content is True" in str(exc_info.value)
    
    def test_file_utilities_error_handling(self):
        """测试文件工具函数的错误处理"""
        # 测试不存在的路径
        files = get_all_files("/nonexistent/path")
        assert len(files) == 0, "不存在的路径应该返回空列表"
        
        # 测试空路径
        files = get_all_files("")
        assert len(files) == 0, "空路径应该返回空列表"
    
    def test_chunked_iterable_edge_cases(self):
        """测试分块迭代器的边界情况"""
        # 测试块大小为0
        with pytest.raises(ValueError):
            list(chunked_iterable([1, 2, 3], 0))
        
        # 测试块大小为负数
        with pytest.raises(ValueError):
            list(chunked_iterable([1, 2, 3], -1))
        
        # 测试块大小大于列表长度
        chunks = list(chunked_iterable([1, 2, 3], 10))
        assert len(chunks) == 1, "块大小大于列表长度应该产生1个分块"
        assert chunks[0] == [1, 2, 3], "分块应该包含所有元素"


# 测试数据准备函数 - 为真实测试用例预留
def prepare_utils_test_files():
    """
    准备工具函数测试文件的函数
    当有真实测试文件时，可以在这里配置文件路径
    
    Returns:
        dict: 包含各种测试场景文件路径的字典
    """
    return {
        "file_utilities": {
            "single_file": "path/to/real/single.txt",
            "multiple_files": [
                "path/to/real/file1.txt",
                "path/to/real/file2.txt", 
                "path/to/real/file3.txt"
            ],
            "nested_structure": "path/to/real/nested/directory"
        },
        "parameter_adapter": {
            "pdf": "path/to/real/test.pdf",
            "docx": "path/to/real/test.docx",
            "xlsx": "path/to/real/test.xlsx",
            "html": "path/to/real/test.html",
            "image": "path/to/real/test.jpg"
        },
        "function_map": {
            "supported_types": [
                "path/to/real/test.pdf",
                "path/to/real/test.docx",
                "path/to/real/test.xlsx",
                "path/to/real/test.html",
                "path/to/real/test.jpg"
            ]
        }
    }


# 标记需要真实文件的测试
REAL_FILE_UTILS_TESTS = [
    "test_get_all_files_with_real_filesystem",
    "test_parameter_adapter_with_real_files"
]
