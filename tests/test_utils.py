"""
工具函数测试
测试各种工具函数的功能，使用真实的测试文件
"""
import json
import tempfile
from pathlib import Path
import shutil

import pytest

from markio.utils.file_utils import (
    calculate_file_size,
    ensure_output_directory,
    get_all_files,
    get_file_extension,
    is_valid_file_type,
    parameter_adapter,
)
from markio.utils.logger_config import get_logger


class TestFileUtils:
    """文件工具函数测试类"""
    
    def test_calculate_file_size(self, real_test_files):
        """测试文件大小计算 - 使用真实文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 测试文件大小计算
        file_size = calculate_file_size(pdf_file_path.stat().st_size)
        
        # 验证结果
        assert isinstance(file_size, str)
        assert "KB" in file_size or "MB" in file_size or "B" in file_size
        print(f"文件大小: {file_size}")
    
    def test_get_file_extension(self, real_test_files):
        """测试文件扩展名获取 - 使用真实文件"""
        # 测试各种文件类型
        test_cases = [
            (real_test_files["pdf"], ".pdf"),
            (real_test_files["docx"], ".docx"),
            (real_test_files["xlsx"], ".xlsx"),
            (real_test_files["html"], ".html"),
            (real_test_files["epub"], ".epub"),
        ]
        
        for file_path, expected_ext in test_cases:
            if file_path.exists():
                ext = get_file_extension(str(file_path))
                assert ext == expected_ext, f"文件 {file_path} 的扩展名应该是 {expected_ext}，实际是 {ext}"
    
    def test_is_valid_file_type(self, real_test_files):
        """测试文件类型验证 - 使用真实文件"""
        # 测试有效文件类型
        valid_cases = [
            (real_test_files["pdf"], "pdf"),
            (real_test_files["docx"], "docx"),
            (real_test_files["xlsx"], "xlsx"),
            (real_test_files["html"], "html"),
            (real_test_files["epub"], "epub"),
        ]
        
        for file_path, file_type in valid_cases:
            if file_path.exists():
                is_valid = is_valid_file_type(str(file_path), file_type)
                assert is_valid, f"文件 {file_path} 应该被识别为有效的 {file_type} 类型"
        
        # 测试无效文件类型
        pdf_file_path = real_test_files["pdf"]
        if pdf_file_path.exists():
            is_valid = is_valid_file_type(str(pdf_file_path), "docx")
            assert not is_valid, f"PDF文件不应该被识别为DOCX类型"
    
    def test_ensure_output_directory(self, temp_dir):
        """测试输出目录创建"""
        # 测试创建新目录
        new_dir = temp_dir / "new_output"
        result_dir = ensure_output_directory(str(new_dir))
        
        assert Path(result_dir).exists(), "新目录应该被创建"
        assert Path(result_dir).is_dir(), "创建的路径应该是目录"
        
        # 测试已存在的目录
        existing_dir = temp_dir / "existing_output"
        existing_dir.mkdir()
        
        result_dir = ensure_output_directory(str(existing_dir))
        assert Path(result_dir).exists(), "已存在的目录应该保持存在"
    
    @pytest.mark.real_files
    def test_get_all_files_with_real_filesystem(self, temp_dir, real_test_files):
        """测试获取所有文件 - 使用真实文件系统"""
        # 创建测试目录结构
        test_dir = temp_dir / "file_scan_test"
        test_dir.mkdir()
        
        # 创建子目录
        subdir1 = test_dir / "subdir1"
        subdir2 = test_dir / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()
        
        # 复制真实文件到不同目录
        files_to_copy = [
            (real_test_files["pdf"], test_dir / "root.pdf"),
            (real_test_files["docx"], subdir1 / "sub1.docx"),
            (real_test_files["xlsx"], subdir1 / "sub1.xlsx"),
            (real_test_files["html"], subdir2 / "sub2.html"),
            (real_test_files["epub"], subdir2 / "sub2.epub"),
        ]
        
        for source, target in files_to_copy:
            if source.exists():
                shutil.copy2(source, target)
        
        # 测试获取所有文件
        all_files = get_all_files(str(test_dir))
        
        # 验证结果
        assert len(all_files) > 0, "应该找到一些文件"
        
        # 检查文件路径
        file_paths = [Path(f) for f in all_files]
        assert any(f.name == "root.pdf" for f in file_paths), "应该找到根目录的PDF文件"
        assert any(f.name == "sub1.docx" for f in file_paths), "应该找到子目录的DOCX文件"
        
        print(f"找到的文件数量: {len(all_files)}")
        for file_path in all_files:
            print(f"  - {file_path}")
    
    @pytest.mark.real_files
    def test_parameter_adapter_with_real_files(self, real_test_files):
        """测试参数适配器 - 使用真实文件"""
        # 测试文件路径参数
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        # 测试文件路径参数
        adapted_params = parameter_adapter({
            "file_path": str(pdf_file_path),
            "save_parsed_content": "true",
            "output_dir": "/tmp/test"
        })
        
        # 验证参数适配
        assert "file_path" in adapted_params, "应该包含file_path参数"
        assert adapted_params["save_parsed_content"] is True, "布尔值应该被正确转换"
        assert adapted_params["output_dir"] == "/tmp/test", "输出目录应该被保留"
        
        # 测试URL参数
        adapted_params = parameter_adapter({
            "url": "https://example.com",
            "save_parsed_content": "false"
        })
        
        assert "url" in adapted_params, "应该包含url参数"
        assert adapted_params["save_parsed_content"] is False, "布尔值应该被正确转换"
        
        # 测试混合参数
        adapted_params = parameter_adapter({
            "file_path": str(pdf_file_path),
            "max_workers": "4",
            "batch_size": "10"
        })
        
        assert adapted_params["max_workers"] == 4, "数字应该被正确转换"
        assert adapted_params["batch_size"] == 10, "数字应该被正确转换"
    
    def test_parameter_adapter_edge_cases(self):
        """测试参数适配器的边界情况"""
        # 测试空参数
        adapted_params = parameter_adapter({})
        assert adapted_params == {}, "空参数应该返回空字典"
        
        # 测试None值
        adapted_params = parameter_adapter({"key": None})
        assert adapted_params["key"] is None, "None值应该被保留"
        
        # 测试无效数字
        adapted_params = parameter_adapter({"invalid_num": "not_a_number"})
        assert adapted_params["invalid_num"] == "not_a_number", "无效数字应该保持原值"
        
        # 测试特殊布尔值
        test_cases = [
            ("true", True),
            ("false", False),
            ("True", True),
            ("False", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
        ]
        
        for input_val, expected in test_cases:
            adapted_params = parameter_adapter({"test_bool": input_val})
            assert adapted_params["test_bool"] == expected, f"'{input_val}' 应该被转换为 {expected}"


class TestLoggerConfig:
    """日志配置测试类"""
    
    def test_get_logger(self):
        """测试日志器获取"""
        logger = get_logger("test_logger")
        
        # 验证日志器基本属性
        assert logger is not None, "日志器不应该为None"
        assert hasattr(logger, "info"), "日志器应该有info方法"
        assert hasattr(logger, "error"), "日志器应该有error方法"
        assert hasattr(logger, "debug"), "日志器应该有debug方法"
        
        # 测试日志记录
        try:
            logger.info("测试信息日志")
            logger.debug("测试调试日志")
            logger.warning("测试警告日志")
            logger.error("测试错误日志")
        except Exception as e:
            pytest.fail(f"日志记录应该正常工作，但出现了异常: {e}")


class TestFileOperations:
    """文件操作测试类"""
    
    @pytest.mark.real_files
    def test_file_copy_operations(self, temp_dir, real_test_files):
        """测试文件复制操作 - 使用真实文件"""
        # 创建测试目录
        test_dir = temp_dir / "copy_test"
        test_dir.mkdir()
        
        # 复制各种类型的文件
        copied_files = []
        for file_type, source_file in real_test_files.items():
            if source_file.exists():
                target_file = test_dir / f"copied_{file_type}{source_file.suffix}"
                shutil.copy2(source_file, target_file)
                copied_files.append(target_file)
        
        if not copied_files:
            pytest.skip("没有可用的测试文件进行复制测试")
        
        # 验证复制结果
        for copied_file in copied_files:
            assert copied_file.exists(), f"复制的文件 {copied_file} 应该存在"
            assert copied_file.stat().st_size > 0, f"复制的文件 {copied_file} 应该有内容"
        
        print(f"成功复制了 {len(copied_files)} 个文件")
    
    @pytest.mark.real_files
    def test_file_validation_operations(self, real_test_files):
        """测试文件验证操作 - 使用真实文件"""
        # 测试文件存在性验证
        for file_type, file_path in real_test_files.items():
            if file_path.exists():
                # 验证文件存在
                assert file_path.exists(), f"测试文件 {file_path} 应该存在"
                
                # 验证文件大小
                file_size = file_path.stat().st_size
                assert file_size > 0, f"测试文件 {file_path} 应该有内容"
                
                # 验证文件类型
                assert file_path.suffix in [".pdf", ".docx", ".xlsx", ".html", ".epub", ".ppt", ".pptx", ".doc"], \
                    f"测试文件 {file_path} 应该有正确的扩展名"
                
                print(f"文件 {file_path.name}: 大小 {file_size} 字节, 类型 {file_path.suffix}")
    
    def test_temp_file_operations(self, temp_dir):
        """测试临时文件操作"""
        # 创建临时文件
        temp_file = temp_dir / "temp_test.txt"
        test_content = "这是一个临时测试文件的内容"
        
        # 写入内容
        temp_file.write_text(test_content, encoding="utf-8")
        
        # 验证写入
        assert temp_file.exists(), "临时文件应该被创建"
        assert temp_file.read_text(encoding="utf-8") == test_content, "文件内容应该正确"
        
        # 测试文件大小
        file_size = temp_file.stat().st_size
        expected_size = len(test_content.encode("utf-8"))
        assert file_size == expected_size, f"文件大小应该是 {expected_size} 字节，实际是 {file_size} 字节"
        
        # 清理
        temp_file.unlink()
        assert not temp_file.exists(), "临时文件应该被删除"


class TestJSONOperations:
    """JSON操作测试类"""
    
    def test_json_file_creation_and_parsing(self, temp_dir):
        """测试JSON文件的创建和解析"""
        # 创建测试JSON文件
        json_file = temp_dir / "test_data.json"
        test_data = {
            "string": "测试字符串",
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3, "测试"],
            "object": {
                "nested_key": "嵌套值",
                "nested_number": 123
            }
        }
        
        # 写入JSON文件
        json_file.write_text(json.dumps(test_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 验证文件创建
        assert json_file.exists(), "JSON文件应该被创建"
        
        # 读取并解析JSON
        loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
        
        # 验证数据完整性
        assert loaded_data == test_data, "加载的数据应该与原始数据一致"
        
        # 验证特定字段
        assert loaded_data["string"] == "测试字符串", "字符串字段应该正确"
        assert loaded_data["number"] == 42, "数字字段应该正确"
        assert loaded_data["boolean"] is True, "布尔字段应该正确"
        assert len(loaded_data["array"]) == 4, "数组字段应该正确"
        assert loaded_data["object"]["nested_key"] == "嵌套值", "嵌套对象应该正确"
        
        print("JSON文件创建和解析测试通过")
    
    def test_json_error_handling(self, temp_dir):
        """测试JSON错误处理"""
        # 测试无效JSON
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text('{"key": "value", "unclosed": "quote}')
        
        # 尝试解析无效JSON
        try:
            json.loads(invalid_json_file.read_text())
            pytest.fail("应该抛出JSON解析错误")
        except json.JSONDecodeError:
            # 预期的错误
            pass
        
        # 测试空文件
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("")
        
        try:
            json.loads(empty_file.read_text())
            pytest.fail("应该抛出JSON解析错误")
        except json.JSONDecodeError:
            # 预期的错误
            pass
        
        print("JSON错误处理测试通过")
