#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行方式和选项
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 成功!")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败! 退出码: {e.returncode}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False


def install_test_dependencies():
    """安装测试依赖"""
    print("安装测试依赖...")
    requirements_file = Path(__file__).parent / "requirements-test.txt"
    
    if requirements_file.exists():
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        return run_command(cmd, "安装测试依赖")
    else:
        print("❌ 测试依赖文件不存在")
        return False


def run_unit_tests():
    """运行单元测试"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_utils.py",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "单元测试")


def run_api_tests():
    """运行API接口测试"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_api_endpoints.py",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "API接口测试")


def run_concurrency_tests():
    """运行并发性能测试"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_concurrency.py",
        "-v",
        "--tb=short",
        "-m", "not slow"
    ]
    return run_command(cmd, "并发性能测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py",
        "-v",
        "--tb=short",
        "-m", "integration"
    ]
    return run_command(cmd, "集成测试")


def run_all_tests():
    """运行所有测试"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/",
        "-v",
        "--tb=short",
        "--cov=markio",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing"
    ]
    return run_command(cmd, "所有测试")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Markio 测试运行器")
    parser.add_argument(
        "--install-deps", 
        action="store_true", 
        help="安装测试依赖"
    )
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="运行单元测试"
    )
    parser.add_argument(
        "--api", 
        action="store_true", 
        help="运行API接口测试"
    )
    parser.add_argument(
        "--concurrency", 
        action="store_true", 
        help="运行并发性能测试"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="运行集成测试"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="运行所有测试"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # 检查是否在正确的目录
    if not Path("tests").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    success_count = 0
    total_count = 0
    
    # 安装依赖
    if args.install_deps:
        total_count += 1
        if install_test_dependencies():
            success_count += 1
    
    # 运行测试
    if args.unit:
        total_count += 1
        if run_unit_tests():
            success_count += 1
    
    if args.api:
        total_count += 1
        if run_api_tests():
            success_count += 1
    
    if args.concurrency:
        total_count += 1
        if run_concurrency_tests():
            success_count += 1
    
    if args.integration:
        total_count += 1
        if run_integration_tests():
            success_count += 1
    
    if args.all:
        total_count += 1
        if run_all_tests():
            success_count += 1
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"测试完成! 成功: {success_count}/{total_count}")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("🎉 所有测试都通过了!")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
