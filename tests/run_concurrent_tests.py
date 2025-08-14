#!/usr/bin/env python3
"""
Markio API 并发测试启动脚本
用于运行并发性能测试
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def check_service_health():
    """检查服务健康状态"""
    import httpx

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("http://0.0.0.0:8000/")
            if response.status_code in [200, 307]:
                print("✅ Markio 服务运行正常")
                return True
            else:
                print(f"❌ 服务响应异常: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 无法连接到 Markio 服务: {e}")
        print("请确保服务正在 http://0.0.0.0:8000 运行")
        return False


def run_concurrent_tests(concurrent_users=None, test_duration=None, verbose=False):
    """运行并发测试"""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ 并发测试文件不存在: {test_file}")
        return False

    # 构建pytest命令
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",  # 详细输出
        "-s",  # 显示print输出
    ]

    # 添加详细输出选项
    if verbose:
        cmd.extend(["--tb=long", "--durations=10"])

    print(f"🚀 开始运行并发测试: {' '.join(cmd)}")
    print(f"📁 测试文件: {test_file}")
    print(f"👥 并发用户: {concurrent_users or '默认配置'}")
    print(f"⏱️  测试时长: {test_duration or '默认配置'}")
    print("-" * 50)

    # 记录开始时间
    start_time = time.time()

    try:
        # 运行测试
        result = subprocess.run(cmd, capture_output=False, text=True)

        # 计算运行时间
        end_time = time.time()
        duration = end_time - start_time

        print("-" * 50)
        print(f"⏱️  并发测试完成，耗时: {duration:.2f} 秒")

        if result.returncode == 0:
            print("✅ 并发测试通过！")
            return True
        else:
            print(f"❌ 并发测试失败，退出码: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  并发测试被用户中断")
        return False
    except Exception as e:
        print(f"❌ 运行并发测试时发生错误: {e}")
        return False


def run_specific_concurrent_test(test_name, verbose=False):
    """运行特定的并发测试"""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ 并发测试文件不存在: {test_file}")
        return False

    # 构建pytest命令
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        f"TestConcurrentPerformance::{test_name}",
        "-v",  # 详细输出
        "-s",  # 显示print输出
    ]

    # 添加详细输出选项
    if verbose:
        cmd.extend(["--tb=long", "--durations=10"])

    print(f"🚀 开始运行特定并发测试: {test_name}")
    print(f"📁 测试文件: {test_file}")
    print(f"🔧 测试方法: {test_name}")
    print("-" * 50)

    # 记录开始时间
    start_time = time.time()

    try:
        # 运行测试
        result = subprocess.run(cmd, capture_output=False, text=True)

        # 计算运行时间
        end_time = time.time()
        duration = end_time - start_time

        print("-" * 50)
        print(f"⏱️  测试完成，耗时: {duration:.2f} 秒")

        if result.returncode == 0:
            print("✅ 测试通过！")
            return True
        else:
            print(f"❌ 测试失败，退出码: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return False
    except Exception as e:
        print(f"❌ 运行测试时发生错误: {e}")
        return False


def list_available_tests():
    """列出可用的并发测试"""
    test_file = Path(__file__).parent / "test_concurrent.py"

    if not test_file.exists():
        print(f"❌ 并发测试文件不存在: {test_file}")
        return

    print("📋 可用的并发测试:")
    print("-" * 30)

    available_tests = [
        "test_single_endpoint_concurrent - 单接口并发测试 (5个并发用户)",
        "test_mixed_endpoints_concurrent - 混合接口并发测试 (5个不同类型)",
        "test_load_test_small_files - 负载测试 (10个并发用户，小文件)",
        "test_stress_test_large_files - 压力测试 (3个并发用户，大文件)",
    ]

    for i, test in enumerate(available_tests, 1):
        print(f"{i}. {test}")

    print("\n💡 使用 --test 参数运行特定测试，例如:")
    print("   python run_concurrent_tests.py --test test_single_endpoint_concurrent")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Markio API 并发测试启动脚本")
    parser.add_argument("--test", "-t", help="运行特定的并发测试方法")
    parser.add_argument("--list", "-l", action="store_true", help="列出可用的并发测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    parser.add_argument("--skip-checks", action="store_true", help="跳过服务健康检查")
    parser.add_argument(
        "--concurrent-users", type=int, help="并发用户数量 (需要修改测试代码支持)"
    )
    parser.add_argument(
        "--test-duration", type=int, help="测试持续时间 (需要修改测试代码支持)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Markio API 并发测试套件")
    print("=" * 60)

    # 检查当前目录
    if not Path(__file__).parent.exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)

    # 列出可用测试
    if args.list:
        list_available_tests()
        sys.exit(0)

    # 执行预检查
    if not args.skip_checks:
        print("\n🔍 执行预检查...")

        if not check_service_health():
            print("\n❌ 服务检查失败，请确保 Markio 服务正在运行")
            sys.exit(1)

        print("✅ 预检查通过")

    # 运行测试
    if args.test:
        print(f"\n🎯 开始运行特定并发测试: {args.test}")
        success = run_specific_concurrent_test(
            test_name=args.test, verbose=args.verbose
        )
    else:
        print("\n🎯 开始运行所有并发测试...")
        success = run_concurrent_tests(
            concurrent_users=args.concurrent_users,
            test_duration=args.test_duration,
            verbose=args.verbose,
        )

    # 输出结果
    if success:
        print("\n🎉 并发测试执行成功！")
        print("\n📊 性能指标总结:")
        print("   - 响应时间: 查看测试输出中的详细数据")
        print("   - 成功率: 查看测试输出中的统计信息")
        print("   - 吞吐量: 查看测试输出中的性能数据")
        sys.exit(0)
    else:
        print("\n💥 并发测试执行失败！")
        print("\n🔍 故障排除建议:")
        print("   - 检查服务是否正常运行")
        print("   - 查看测试输出中的错误信息")
        print("   - 尝试减少并发用户数量")
        print("   - 检查系统资源使用情况")
        sys.exit(1)


if __name__ == "__main__":
    main()
