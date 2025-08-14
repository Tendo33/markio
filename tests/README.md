# Markio 测试套件

本目录包含了 Markio 项目的完整测试套件，涵盖了 API 接口、文件解析、错误处理、安全特性等各个方面。

## 📁 测试文件结构

```
tests/
├── conftest.py              # Pytest 配置和 fixtures
├── test_api_endpoints.py    # API 端点测试（主要测试文件）
├── test_integration.py      # 集成测试
├── test_utils.py            # 工具函数测试
├── test_concurrency.py      # 并发测试
├── run_tests.py             # 测试运行脚本
├── test_docs/               # 测试文档目录
│   ├── test_pdf1.pdf        # PDF 测试文件
│   ├── test_pdf2.pdf        # PDF 测试文件
│   ├── test_pdf3.pdf        # 小PDF测试文件
│   ├── test_docx.docx       # DOCX 测试文件
│   ├── test_doc.doc         # DOC 测试文件
│   ├── test_xlsx.xlsx       # XLSX 测试文件
│   ├── test_html.html       # HTML 测试文件
│   ├── test_epub.epub       # EPUB 测试文件
│   ├── test_ppt.ppt         # PPT 测试文件
│   └── test_pptx.pptx       # PPTX 测试文件
└── README.md                # 本文件
```

## 🧪 测试用例分类

### 1. API 端点测试 (`TestAPIEndpoints`)

测试所有主要的 API 接口功能：

- **基础接口测试**
  - `test_welcome_endpoint`: 欢迎页面
  - `test_api_docs_endpoint`: API 文档页面
  - `test_openapi_schema`: OpenAPI schema

- **文件解析接口测试**
  - `test_pdf_parse_endpoint`: PDF 文件解析
  - `test_pdf_small_parse_endpoint`: 小PDF文件解析
  - `test_docx_parse_endpoint`: DOCX 文件解析
  - `test_xlsx_parse_endpoint`: XLSX 文件解析
  - `test_html_parse_endpoint`: HTML 文件解析
  - `test_epub_parse_endpoint`: EPUB 文件解析
  - `test_ppt_parse_endpoint`: PPT 文件解析
  - `test_pptx_parse_endpoint`: PPTX 文件解析
  - `test_doc_parse_endpoint`: DOC 文件解析
  - `test_image_parse_endpoint`: 图片文件解析

- **URL 解析接口测试**
  - `test_url_parse_endpoint`: URL 内容解析

- **验证和错误处理测试**
  - `test_file_upload_validation`: 文件上传验证
  - `test_error_handling`: 错误处理
  - `test_save_parsed_content_option`: 保存选项测试

### 2. 错误处理测试 (`TestErrorHandling`)

测试各种错误情况的处理：

- `test_invalid_file_path`: 无效文件路径
- `test_malformed_request`: 格式错误的请求
- `test_unsupported_method`: 不支持的HTTP方法
- `test_invalid_content_type`: 无效的内容类型
- `test_missing_required_fields`: 缺少必需字段

### 3. 集成场景测试 (`TestIntegrationScenarios`)

测试复杂的业务场景：

- `test_multiple_file_types_parsing`: 多种文件类型解析
- `test_concurrent_file_parsing`: 并发文件解析

### 4. 性能和限制测试 (`TestPerformanceAndLimits`)

测试系统性能和限制：

- `test_response_time_limits`: 响应时间限制
- `test_memory_usage_limits`: 内存使用限制
- `test_concurrent_connections_limit`: 并发连接数限制

### 5. 健康检查和监控测试 (`TestHealthAndMonitoring`)

测试系统健康状态：

- `test_health_check_endpoint`: 健康检查端点
- `test_api_version_endpoint`: API版本端点
- `test_cors_headers`: CORS头部设置
- `test_rate_limiting`: 速率限制

### 6. 边界情况测试 (`TestEdgeCases`)

测试各种边界情况：

- `test_very_large_file_name`: 超长文件名
- `test_special_characters_in_filename`: 特殊字符文件名
- `test_empty_file_upload`: 空文件上传
- `test_malformed_multipart_data`: 格式错误的多部分数据
- `test_invalid_json_in_form_data`: 无效的JSON数据

### 7. 安全特性测试 (`TestSecurityFeatures`)

测试安全防护功能：

- `test_path_traversal_prevention`: 路径遍历攻击防护
- `test_file_type_validation`: 文件类型验证
- `test_content_length_validation`: 内容长度验证
- `test_sql_injection_prevention`: SQL注入防护

## 🚀 运行测试

### 方法1: 使用测试运行脚本（推荐）

```bash
cd tests/
python run_tests.py
```

脚本提供交互式菜单，可以选择不同类型的测试。

### 方法2: 直接使用 pytest

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_api_endpoints.py -v

# 运行特定测试类
python -m pytest tests/test_api_endpoints.py::TestAPIEndpoints -v

# 运行特定测试方法
python -m pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_pdf_parse_endpoint -v

# 运行标记的测试
python -m pytest tests/ -m real_files -v
python -m pytest tests/ -m integration -v

# 生成覆盖率报告
python -m pytest tests/ --cov=markio --cov-report=html --cov-report=term
```

## 🏷️ 测试标记

测试用例使用以下标记进行分类：

- `@pytest.mark.real_files`: 需要真实测试文件的测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.api`: API接口测试

## 📊 测试覆盖率

运行覆盖率测试后，可以在 `htmlcov/index.html` 查看详细的覆盖率报告。

## 🔧 测试配置

测试配置在 `conftest.py` 中定义，包括：

- FastAPI 测试客户端
- 测试文件路径配置
- 自定义 fixtures
- 测试标记配置

## 📝 添加新测试

### 1. 添加新的测试方法

```python
def test_new_feature(self, client: TestClient):
    """测试新功能"""
    # 测试逻辑
    response = client.get("/new/endpoint")
    assert response.status_code == 200
```

### 2. 添加新的测试类

```python
class TestNewFeature:
    """新功能测试类"""
    
    def test_feature_1(self, client: TestClient):
        """测试功能1"""
        pass
    
    def test_feature_2(self, client: TestClient):
        """测试功能2"""
        pass
```

### 3. 使用 fixtures

```python
def test_with_fixture(self, client: TestClient, real_test_files):
    """使用fixture的测试"""
    pdf_file = real_test_files["pdf"]
    # 测试逻辑
```

## 🐛 故障排除

### 常见问题

1. **测试文件不存在**
   - 确保 `tests/test_docs/` 目录中有相应的测试文件
   - 检查文件路径是否正确

2. **依赖缺失**
   - 安装 pytest: `pip install pytest`
   - 安装 pytest-cov: `pip install pytest-cov`

3. **测试超时**
   - 某些测试可能需要较长时间（如大文件解析）
   - 可以调整 pytest 的超时设置

4. **权限问题**
   - 确保有读取测试文件的权限
   - 检查临时目录的写入权限

### 调试技巧

- 使用 `-v` 参数查看详细输出
- 使用 `--tb=short` 查看简短的错误信息
- 使用 `-s` 参数显示 print 输出
- 使用 `--pdb` 在失败时进入调试器

## 📚 相关文档

- [Pytest 官方文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [项目主文档](../README.md)

## 🤝 贡献指南

1. 为新功能添加测试用例
2. 确保所有测试都能通过
3. 保持测试代码的可读性和可维护性
4. 更新相关文档

---

**注意**: 某些测试需要真实的测试文件才能运行。如果测试文件缺失，相关测试会被跳过。
