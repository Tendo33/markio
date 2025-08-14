"""
Markio API 测试套件

本包包含用于测试 Markio 文档解析服务 API 功能和并发性能的测试用例。

主要模块:
- test_all_parsers: 所有解析接口的功能测试
- test_concurrent: 并发性能测试
- conftest: pytest配置和共享fixtures

使用方法:
1. 确保 Markio 服务正在 http://0.0.0.0:8000 运行
2. 运行测试: pytest tests/ -v
3. 或使用提供的脚本: python tests/run_tests.py
"""

__version__ = "1.0.0"
__author__ = "Markio Team"
__description__ = "Markio API 测试套件"
