#!/usr/bin/env python3
"""
Markio API 测试启动脚本
用于运行所有API功能测试
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
        with httpx.Client(timeout=15.0) as client:
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


def check_test_files():
    """检查测试文件是否存在"""
    test_docs_dir = Path(__file__).parent / "test_docs"

    if not test_docs_dir.exists():
        print(f"❌ 测试文档目录不存在: {test_docs_dir}")
        return False

    required_files = [
        "test_pdf1.pdf",
        "test_doc.doc",
        "test_docx.docx",
        "test_ppt.ppt",
        "test_pptx.pptx",
        "test_xlsx.xlsx",
        "test_html.html",
        "test_epub.epub",
    ]

    missing_files = []
    for file in required_files:
        if not (test_docs_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ 缺少测试文件: {', '.join(missing_files)}")
        return False

    print("✅ 测试文件检查通过")
    return True


def run_tests(test_type="all", verbose=False, output_file=None):
    """运行测试"""
    test_dir = Path(__file__).parent

    # 构建pytest命令
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v",  # 详细输出
    ]

    # 根据测试类型选择测试文件
    if test_type == "api":
        cmd.append("test_all_parsers.py")
    elif test_type == "concurrent":
        cmd.append("test_concurrent.py")
    elif test_type == "all":
        pass  # 运行所有测试
    else:
        print(f"❌ 未知的测试类型: {test_type}")
        return False

    # 添加详细输出选项
    if verbose:
        cmd.extend(["--tb=long", "--durations=10"])

    # 添加输出文件选项
    if output_file:
        cmd.extend([f"--junit-xml={output_file}"])

    print(f"🚀 开始运行测试: {' '.join(cmd)}")
    print(f"📁 测试目录: {test_dir}")
    print(f"🔧 测试类型: {test_type}")
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
            print("✅ 所有测试通过！")
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Markio API 测试启动脚本")
    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "api", "concurrent"],
        default="all",
        help="测试类型: all(全部), api(API功能), concurrent(并发性能)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    parser.add_argument("--output", "-o", help="测试报告输出文件路径")
    parser.add_argument(
        "--skip-checks", action="store_true", help="跳过服务健康检查和文件检查"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Markio API 测试套件")
    print("=" * 60)

    # 检查当前目录
    if not Path(__file__).parent.exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)

    # 执行预检查
    if not args.skip_checks:
        print("\n🔍 执行预检查...")

        if not check_service_health():
            print("\n❌ 服务检查失败，请确保 Markio 服务正在运行")
            sys.exit(1)

        if not check_test_files():
            print("\n❌ 测试文件检查失败")
            sys.exit(1)

        print("✅ 预检查通过")

    # 运行测试
    print(f"\n🎯 开始运行 {args.type} 测试...")
    success = run_tests(
        test_type=args.type, verbose=args.verbose, output_file=args.output
    )

    # 输出结果
    if success:
        print("\n🎉 测试执行成功！")
        sys.exit(0)
    else:
        print("\n💥 测试执行失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
