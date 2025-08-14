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
def test_docs_dir():
    """测试文档目录fixture - 使用真实的测试文件"""
    # 获取项目根目录下的tests/test_docs文件夹
    project_root = Path(__file__).parent.parent
    test_docs_path = project_root / "tests" / "test_docs"
    
    if not test_docs_path.exists():
        pytest.skip("测试文档目录不存在")
    
    return test_docs_path


@pytest.fixture
def real_test_files(test_docs_dir):
    """真实测试文件路径fixture"""
    return {
        "pdf": test_docs_dir / "test_pdf1.pdf",
        "pdf_small": test_docs_dir / "test_pdf3.pdf",
        "docx": test_docs_dir / "test_docx.docx",
        "doc": test_docs_dir / "test_doc.doc",
        "xlsx": test_docs_dir / "test_xlsx.xlsx",
        "html": test_docs_dir / "test_html.html",
        "epub": test_docs_dir / "test_epub.epub",
        "ppt": test_docs_dir / "test_ppt.ppt",
        "pptx": test_docs_dir / "test_pptx.pptx"
    }


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


# 标记需要真实文件的测试
def pytest_collection_modifyitems(config, items):
    """修改测试收集，标记需要真实文件的测试"""
    for item in items:
        # 检查测试是否在需要真实文件的列表中
        if any(test_name in item.name for test_name in [
            "test_pdf_parse_endpoint",
            "test_docx_parse_endpoint", 
            "test_xlsx_parse_endpoint",
            "test_html_parse_endpoint",
            "test_epub_parse_endpoint",
            "test_ppt_parse_endpoint",
            "test_pptx_parse_endpoint",
            "test_doc_parse_endpoint"
        ]):
            # 标记为需要真实文件的测试
            item.add_marker(pytest.mark.real_files)
        
        # 标记为集成测试
        if "integration" in item.name or "workflow" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # 标记为API测试
        if "endpoint" in item.name or "api" in item.name:
            item.add_marker(pytest.mark.api)


# 自定义标记
pytest_plugins = []


def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "real_files: 标记需要真实文件的测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "api: 标记API接口测试"
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
