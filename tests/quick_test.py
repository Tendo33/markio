#!/usr/bin/env python3
"""
快速测试脚本
用于快速验证测试环境是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试基本导入"""
    print("🔍 测试基本导入...")
    
    try:
        # 测试核心模块导入
        from markio.main import app
        print("✅ FastAPI应用导入成功")
        
        from scripts.run_local import FUNCTION_MAP, parameter_adapter
        print("✅ 核心函数导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n🔍 测试基本功能...")
    
    try:
        from scripts.run_local import FUNCTION_MAP, parameter_adapter
        
        # 测试参数适配器
        params = parameter_adapter("pdf", file_path="/test.pdf")
        assert "resource_path" in params, "参数适配器应该返回resource_path"
        print("✅ 参数适配器工作正常")
        
        # 测试函数映射
        assert "pdf" in FUNCTION_MAP, "PDF解析器应该在函数映射中"
        assert callable(FUNCTION_MAP["pdf"]), "PDF解析器应该是可调用的"
        print("✅ 函数映射工作正常")
        
        return True
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False


def test_test_environment():
    """测试测试环境"""
    print("\n🔍 测试测试环境...")
    
    try:
        import pytest
        print(f"✅ pytest版本: {pytest.__version__}")
        
        import pytest_asyncio
        print("✅ pytest-asyncio可用")
        
        # 检查测试文件
        test_files = [
            "test_api_endpoints.py",
            "test_concurrency.py", 
            "test_integration.py",
            "test_utils.py"
        ]
        
        for test_file in test_files:
            test_path = Path(__file__).parent / test_file
            if test_path.exists():
                print(f"✅ {test_file} 存在")
            else:
                print(f"❌ {test_file} 不存在")
        
        return True
    except ImportError as e:
        print(f"❌ 测试环境检查失败: {e}")
        return False


def test_mock_data_preparation():
    """测试mock数据准备功能"""
    print("\n🔍 测试mock数据准备...")
    
    try:
        # 测试各个测试模块的数据准备函数
        from tests.test_api_endpoints import prepare_test_files
        from tests.test_concurrency import prepare_concurrency_test_files
        from tests.test_integration import prepare_integration_test_files
        from tests.test_utils import prepare_utils_test_files
        
        # 验证数据准备函数存在且可调用
        assert callable(prepare_test_files), "API测试数据准备函数应该存在"
        assert callable(prepare_concurrency_test_files), "并发测试数据准备函数应该存在"
        assert callable(prepare_integration_test_files), "集成测试数据准备函数应该存在"
        assert callable(prepare_utils_test_files), "工具测试数据准备函数应该存在"
        
        print("✅ 所有测试数据准备函数可用")
        return True
        
    except ImportError as e:
        print(f"❌ Mock数据准备测试失败: {e}")
        return False


def test_skipped_tests_info():
    """显示被跳过的测试信息"""
    print("\n🔍 检查被跳过的测试...")
    
    try:
        # 导入测试模块中的跳过测试列表
        from tests.test_api_endpoints import REAL_FILE_TESTS
        from tests.test_concurrency import REAL_FILE_CONCURRENCY_TESTS
        from tests.test_integration import REAL_FILE_INTEGRATION_TESTS
        from tests.test_utils import REAL_FILE_UTILS_TESTS
        
        total_skipped = (
            len(REAL_FILE_TESTS) + 
            len(REAL_FILE_CONCURRENCY_TESTS) + 
            len(REAL_FILE_INTEGRATION_TESTS) + 
            len(REAL_FILE_UTILS_TESTS)
        )
        
        print(f"📊 总共需要真实文件的测试: {total_skipped}")
        print("📋 需要真实文件的测试列表:")
        
        if REAL_FILE_TESTS:
            print(f"  - API测试: {len(REAL_FILE_TESTS)} 个")
        if REAL_FILE_CONCURRENCY_TESTS:
            print(f"  - 并发测试: {len(REAL_FILE_CONCURRENCY_TESTS)} 个")
        if REAL_FILE_INTEGRATION_TESTS:
            print(f"  - 集成测试: {len(REAL_FILE_INTEGRATION_TESTS)} 个")
        if REAL_FILE_UTILS_TESTS:
            print(f"  - 工具测试: {len(REAL_FILE_UTILS_TESTS)} 个")
        
        print("\n💡 要运行这些测试，请:")
        print("   1. 准备相应的真实测试文件")
        print("   2. 更新测试数据准备函数中的文件路径")
        print("   3. 移除@pytest.mark.skip装饰器")
        
        return True
        
    except ImportError as e:
        print(f"❌ 跳过测试信息检查失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 Markio 快速测试启动")
    print("=" * 50)
    
    # 检查Python版本
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查工作目录
    current_dir = Path.cwd()
    print(f"📁 当前工作目录: {current_dir}")
    
    if not (current_dir / "tests").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 运行测试
    tests = [
        ("基本导入", test_imports),
        ("基本功能", test_basic_functionality),
        ("测试环境", test_test_environment),
        ("Mock数据准备", test_mock_data_preparation),
        ("跳过测试信息", test_skipped_tests_info)
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            success_count += 1
        print()
    
    # 显示结果
    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试都通过了! 测试环境准备就绪。")
        print("\n💡 下一步:")
        print("   1. 安装测试依赖: pip install -r tests/requirements-test.txt")
        print("   2. 运行完整测试: python tests/run_tests.py --all")
        print("   3. 运行特定测试: python tests/run_tests.py --unit")
        print("   4. 准备真实测试文件并更新测试数据准备函数")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查环境配置。")
        sys.exit(1)


if __name__ == "__main__":
    main()
