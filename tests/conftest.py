"""
Pytest配置文件
提供通用的测试fixtures和配置
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# 导入应用
from markio.main import app


@pytest.fixture
def client():
    """FastAPI测试客户端"""
    return TestClient(app)


@pytest.fixture
def async_client():
    """异步测试客户端（如果需要）"""
    # 这里可以配置异步测试客户端
    return Mock()


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_files_dir(temp_dir):
    """示例文件目录fixture"""
    # 创建示例文件目录结构
    sample_dir = temp_dir / "sample_files"
    sample_dir.mkdir()
    
    # 创建子目录
    (sample_dir / "pdf").mkdir()
    (sample_dir / "docx").mkdir()
    (sample_dir / "xlsx").mkdir()
    (sample_dir / "html").mkdir()
    (sample_dir / "images").mkdir()
    
    yield sample_dir


@pytest.fixture
def mock_pdf_content():
    """Mock PDF内容"""
    return b"%PDF-1.4\n%Mock PDF content for testing\n%%EOF"


@pytest.fixture
def mock_docx_content():
    """Mock DOCX内容"""
    return b"Mock DOCX content for testing"


@pytest.fixture
def mock_xlsx_content():
    """Mock XLSX内容"""
    return b"Mock XLSX content for testing"


@pytest.fixture
def mock_html_content():
    """Mock HTML内容"""
    return b"<html><body><h1>Test HTML</h1><p>Mock HTML content for testing</p></body></html>"


@pytest.fixture
def mock_image_content():
    """Mock图片内容"""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"


@pytest.fixture
def test_file_paths(sample_files_dir):
    """测试文件路径fixture"""
    return {
        "pdf": str(sample_files_dir / "pdf" / "test.pdf"),
        "docx": str(sample_files_dir / "docx" / "test.docx"),
        "xlsx": str(sample_files_dir / "xlsx" / "test.xlsx"),
        "html": str(sample_files_dir / "html" / "test.html"),
        "image": str(sample_files_dir / "images" / "test.jpg")
    }


# 标记需要真实文件的测试
def pytest_collection_modifyitems(config, items):
    """修改测试收集，标记需要真实文件的测试"""
    for item in items:
        # 检查测试是否在需要真实文件的列表中
        if any(test_name in item.name for test_name in [
            "test_pdf_parse_endpoint",
            "test_docx_parse_endpoint",
            "test_image_parse_endpoint",
            "test_html_parse_endpoint",
            "test_xlsx_parse_endpoint",
            "test_concurrent_pdf_parsing",
            "test_concurrent_processing_with_semaphore",
            "test_batch_processing_performance",
            "test_mixed_file_types_concurrency",
            "test_concurrent_processing_stress_test",
            "test_memory_usage_under_concurrency",
            "test_concurrent_error_handling",
            "test_complete_pdf_workflow",
            "test_batch_processing_workflow",
            "test_concurrent_processor_workflow",
            "test_mixed_file_types_integration",
            "test_error_recovery_integration",
            "test_resource_management_integration",
            "test_large_scale_integration",
            "test_memory_efficiency_integration",
            "test_get_all_files_with_real_filesystem",
            "test_parameter_adapter_with_real_files"
        ]):
            item.add_marker(pytest.mark.real_files)


# 测试配置
def pytest_configure(config):
    """配置pytest"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "real_files: 标记需要真实文件的测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记运行较慢的测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )


# 测试会话配置
def pytest_sessionstart(session):
    """测试会话开始时的配置"""
    print("\n🚀 开始测试会话")
    print("📋 测试配置:")
    print("   - 使用临时目录进行文件测试")
    print("   - 需要真实文件的测试将被跳过")
    print("   - 使用mock数据进行功能测试")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的配置"""
    print("\n🏁 测试会话结束")
    print(f"📊 退出状态: {exitstatus}")
    
    if exitstatus == 0:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    
    print("\n💡 下一步建议:")
    print("   1. 检查被跳过的测试（需要真实文件）")
    print("   2. 准备真实测试文件")
    print("   3. 更新测试数据准备函数")
    print("   4. 移除@pytest.mark.skip装饰器")
