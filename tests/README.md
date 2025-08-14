# Markio 测试套件

本测试套件为 Markio 项目提供全面的测试覆盖，包括接口功能测试、并发性能测试、集成测试和工具函数测试。

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和测试夹具
├── test_api_endpoints.py    # API接口功能测试
├── test_concurrency.py      # 并发性能测试
├── test_integration.py      # 集成测试
├── test_utils.py            # 工具函数测试
├── pytest.ini              # pytest配置文件
├── requirements-test.txt     # 测试依赖
├── run_tests.py             # 测试运行脚本
└── README.md                # 本文件
```

## 测试分类

### 1. API接口功能测试 (`test_api_endpoints.py`)
- **测试目标**: 验证所有API接口是否正常运行
- **测试内容**:
  - 欢迎接口和文档接口
  - 各种文件格式的解析接口 (PDF, DOCX, HTML, 图片, XLSX, URL等)
  - 错误处理和参数验证
  - 文件类型验证和大小限制

### 2. 并发性能测试 (`test_concurrency.py`)
- **测试目标**: 测试接口的并发处理能力和性能表现
- **测试内容**:
  - 不同并发数下的性能对比
  - 信号量控制的并发处理
  - 批处理性能测试
  - 混合文件类型的并发处理
  - 压力测试和内存使用监控
  - API接口的并发请求处理

### 3. 集成测试 (`test_integration.py`)
- **测试目标**: 测试整个系统的端到端功能
- **测试内容**:
  - 完整的PDF处理工作流
  - 批量处理工作流
  - 并发处理器工作流
  - 文件合并工作流
  - 混合文件类型的系统集成
  - 错误恢复和资源管理

### 4. 工具函数测试 (`test_utils.py`)
- **测试目标**: 测试各种辅助功能和工具函数
- **测试内容**:
  - 文件工具函数 (get_all_files, chunked_iterable)
  - 参数适配器 (parameter_adapter)
  - 函数映射 (FUNCTION_MAP)
  - 错误处理和边界情况

## 安装和运行

### 1. 安装测试依赖
```bash
pip install -r tests/requirements-test.txt
```

### 2. 运行所有测试
```bash
# 使用pytest
pytest tests/ -v

# 使用测试脚本
python tests/run_tests.py --all
```

### 3. 运行特定测试
```bash
# 只运行API测试
python tests/run_tests.py --api

# 只运行并发测试
python tests/run_tests.py --concurrency

# 只运行集成测试
python tests/run_tests.py --integration

# 只运行单元测试
python tests/run_tests.py --unit
```

### 4. 运行性能测试
```bash
# 运行性能测试
python tests/run_tests.py --performance

# 运行压力测试
python tests/run_tests.py --stress
```

### 5. 生成覆盖率报告
```bash
python tests/run_tests.py --coverage
```

## 测试配置

### pytest配置 (`pytest.ini`)
- 自动检测异步测试
- 生成覆盖率报告
- 忽略警告信息
- 支持测试标记

### 测试夹具 (`conftest.py`)
- FastAPI测试客户端
- 异步测试客户端
- 临时目录管理
- 示例文件生成

## 测试标记

- `@pytest.mark.slow`: 标记为慢速测试
- `@pytest.mark.integration`: 标记为集成测试
- `@pytest.mark.unit`: 标记为单元测试
- `@pytest.mark.asyncio`: 标记为异步测试

## 性能基准

### 并发性能目标
- 4线程应该比单线程快
- 8线程应该比4线程快
- 支持16线程并发处理

### 吞吐量目标
- 单线程: 基础性能基准
- 多线程: 线性性能提升
- 批处理: 批量优化效果

### 内存使用目标
- 内存增长应该合理
- 支持长时间运行
- 资源管理稳定

## 注意事项

1. **测试文件**: 使用模拟的测试文件，避免依赖真实文档
2. **异步支持**: 所有测试都支持异步执行
3. **错误处理**: 测试包含预期的错误情况
4. **资源清理**: 自动清理临时文件和目录
5. **性能监控**: 包含内存使用和响应时间监控

## 故障排除

### 常见问题
1. **导入错误**: 确保在项目根目录运行测试
2. **依赖缺失**: 安装 `requirements-test.txt` 中的依赖
3. **权限问题**: 确保有创建临时目录的权限
4. **内存不足**: 减少并发测试的规模

### 调试模式
```bash
# 详细输出
pytest tests/ -v -s

# 只运行失败的测试
pytest tests/ --lf

# 调试特定测试
pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_pdf_parse_endpoint -v -s
```

## 持续集成

测试套件设计支持CI/CD环境：
- 自动依赖安装
- 并行测试执行
- 覆盖率报告生成
- 测试结果报告
