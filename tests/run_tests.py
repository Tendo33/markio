#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行选项，包括单元测试、集成测试、性能测试等
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ 命令执行成功!")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败 (退出码: {e.returncode})")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False

def main():
    """主函数"""
    print("🧪 Markio 测试套件")
    print("=" * 60)
    
    # 检查是否在正确的目录
    project_root = Path(__file__).parent.parent
    if not (project_root / "markio").exists():
        print("❌ 错误: 请在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 切换到项目根目录
    os.chdir(project_root)
    print(f"📁 工作目录: {os.getcwd()}")
    
    # 检查测试依赖
    print("\n🔍 检查测试依赖...")
    try:
        import pytest
        print(f"✅ pytest 版本: {pytest.__version__}")
    except ImportError:
        print("❌ pytest 未安装，正在安装...")
        if not run_command("pip install pytest", "安装pytest"):
            print("❌ 无法安装pytest，请手动安装")
            sys.exit(1)
    
    try:
        from fastapi.testclient import TestClient
        print("✅ FastAPI TestClient 可用")
    except ImportError:
        print("❌ FastAPI TestClient 不可用")
        sys.exit(1)
    
    # 显示可用的测试选项
    print("\n📋 可用的测试选项:")
    print("1. 运行所有测试")
    print("2. 运行API端点测试")
    print("3. 运行集成测试")
    print("4. 运行性能测试")
    print("5. 运行安全测试")
    print("6. 运行特定测试文件")
    print("7. 生成测试覆盖率报告")
    print("8. 退出")
    
    while True:
        try:
            choice = input("\n请选择测试选项 (1-8): ").strip()
            
            if choice == "1":
                print("\n🔍 运行所有测试...")
                run_command("python -m pytest tests/ -v", "运行所有测试")
                
            elif choice == "2":
                print("\n🔍 运行API端点测试...")
                run_command("python -m pytest tests/test_api_endpoints.py -v", "运行API端点测试")
                
            elif choice == "3":
                print("\n🔍 运行集成测试...")
                run_command("python -m pytest tests/ -m integration -v", "运行集成测试")
                
            elif choice == "4":
                print("\n🔍 运行性能测试...")
                run_command("python -m pytest tests/test_api_endpoints.py::TestPerformanceAndLimits -v", "运行性能测试")
                
            elif choice == "5":
                print("\n🔍 运行安全测试...")
                run_command("python -m pytest tests/test_api_endpoints.py::TestSecurityFeatures -v", "运行安全测试")
                
            elif choice == "6":
                test_file = input("请输入测试文件路径 (例如: tests/test_api_endpoints.py): ").strip()
                if test_file and Path(test_file).exists():
                    run_command(f"python -m pytest {test_file} -v", f"运行测试文件: {test_file}")
                else:
                    print("❌ 测试文件不存在")
                    
            elif choice == "7":
                print("\n🔍 生成测试覆盖率报告...")
                # 检查是否安装了pytest-cov
                try:
                    import pytest_cov
                    print("✅ pytest-cov 已安装")
                except ImportError:
                    print("📦 安装 pytest-cov...")
                    run_command("pip install pytest-cov", "安装pytest-cov")
                
                run_command(
                    "python -m pytest tests/ --cov=markio --cov-report=html --cov-report=term",
                    "生成测试覆盖率报告"
                )
                print("\n📊 覆盖率报告已生成，请查看 htmlcov/index.html")
                
            elif choice == "8":
                print("\n👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请输入 1-8")
                
        except KeyboardInterrupt:
            print("\n\n👋 测试被中断，再见!")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
    
    print("\n💡 提示:")
    print("- 使用 'python -m pytest tests/ -v' 运行所有测试")
    print("- 使用 'python -m pytest tests/ -k test_name' 运行特定测试")
    print("- 使用 'python -m pytest tests/ -m marker' 运行标记的测试")
    print("- 使用 'python -m pytest tests/ --tb=short' 显示简短错误信息")

if __name__ == "__main__":
    main()
