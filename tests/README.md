# Markio 测试套件

## 概述

这是Markio项目的完整测试套件，使用真实的文档文件进行测试，确保测试的准确性和可靠性。

## 🆕 改进内容

### 从Mock数据到真实文件
- **之前**: 使用模拟数据和虚拟文件路径
- **现在**: 使用`tests/test_docs/`目录中的真实文档文件
- **优势**: 更真实的测试环境，更好的错误检测，更可靠的性能测试

### 测试文件类型
测试套件支持以下真实文档格式：
- **PDF**: `test_pdf1.pdf` (9.8MB), `test_pdf2.pdf` (1.3MB), `test_pdf3.pdf` (43KB)
- **Word**: `test_doc.doc` (314KB), `test_docx.docx` (131KB)
- **Excel**: `test_xlsx.xlsx` (12KB)
- **PowerPoint**: `test_ppt.ppt` (7.7MB), `test_pptx.pptx` (4.7MB)
- **HTML**: `test_html.html` (5.6MB)
- **EPUB**: `test_epub.epub` (652KB)

## 📁 清理后的文件结构

```
tests/
├── __init__.py                    # 测试包初始化
├── conftest.py                    # pytest配置和测试fixtures
├── pytest.ini                     # pytest配置文件
├── README.md                      # 本说明文档
├── run_tests.py                   # 🚀 统一的测试运行脚本（支持多种模式）
├── test_api_endpoints.py          # 📡 API端点测试（已改进）
├── test_integration.py            # 🔗 集成测试（已改进）
├── test_concurrency.py            # ⚡ 并发测试（已改进）
├── test_utils.py                  # 🛠️ 工具测试（已改进）
└── test_docs/                     # 📚 测试文档目录
    ├── test_pdf1.pdf             # 大PDF文件 (9.8MB)
    ├── test_pdf2.pdf             # 中PDF文件 (1.3MB)
    ├── test_pdf3.pdf             # 小PDF文件 (43KB)
    ├── test_doc.doc              # Word文档 (314KB)
    ├── test_docx.docx            # Word文档 (131KB)
    ├── test_xlsx.xlsx            # Excel文件 (12KB)
    ├── test_ppt.ppt              # PowerPoint (7.7MB)
    ├── test_pptx.pptx            # PowerPoint (4.7MB)
    ├── test_html.html            # HTML文件 (5.6MB)
    └── test_epub.epub            # EPUB文件 (652KB)
```

## 🚀 快速开始

### 1. 环境检查
```bash
cd tests
python run_tests.py --check
```

### 2. 运行完整测试套件
```bash
python run_tests.py --full
```

### 3. 运行快速演示
```bash
python run_tests.py --demo
```

### 4. 默认运行（完整测试套件）
```bash
python run_tests.py
```

### 5. 查看帮助
```bash
python run_tests.py --help
```

### 6. 运行特定测试类型
```bash
# API端点测试
pytest test_api_endpoints.py -v -m real_files

# 集成测试
pytest test_integration.py -v -m real_files

# 并发测试
pytest test_concurrency.py -v -m real_files

# 工具测试
pytest test_utils.py -v -m real_files
```

### 7. 运行所有真实文件测试
```bash
pytest -v -m real_files --tb=short
```

## 📋 测试分类

### 1. API端点测试 (`test_api_endpoints.py`)
测试所有FastAPI端点的功能：
- ✅ PDF解析接口 (`/v1/parse_pdf_file`)
- ✅ DOCX解析接口 (`/v1/parse_docx_file`)
- ✅ XLSX解析接口 (`/v1/parse_xlsx_file`)
- ✅ HTML解析接口 (`/v1/parse_html_file`)
- ✅ EPUB解析接口 (`/v1/parse_epub_file`)
- ✅ PPT解析接口 (`/v1/parse_ppt_file`)
- ✅ PPTX解析接口 (`/v1/parse_pptx_file`)
- ✅ DOC解析接口 (`/v1/parse_doc_file`)
- ✅ 文件上传验证
- ✅ 错误处理

### 2. 集成测试 (`test_integration.py`)
测试端到端工作流：
- ✅ 完整PDF处理工作流
- ✅ 批量处理工作流
- ✅ 并发处理器工作流
- ✅ 混合文件类型集成
- ✅ 错误恢复集成
- ✅ 大规模集成处理
- ✅ 内存效率集成

### 3. 并发测试 (`test_concurrency.py`)
测试系统并发处理能力：
- ✅ 并发PDF解析
- ✅ 信号量控制的并发处理
- ✅ 批量处理性能
- ✅ 混合文件类型并发
- ✅ 压力测试
- ✅ 内存使用监控
- ✅ 错误处理

### 4. 工具测试 (`test_utils.py`)
测试工具函数：
- ✅ 文件大小计算
- ✅ 文件扩展名获取
- ✅ 文件类型验证
- ✅ 输出目录创建
- ✅ 文件系统扫描
- ✅ 参数适配器
- ✅ 日志配置

## 🏷️ 测试标记

### 主要标记
- `@pytest.mark.real_files`: 标记使用真实文件的测试
- `@pytest.mark.integration`: 标记集成测试
- `@pytest.mark.api`: 标记API接口测试

### 运行特定标记的测试
```bash
# 只运行真实文件测试
pytest -m real_files

# 只运行集成测试
pytest -m integration

# 只运行API测试
pytest -m api

# 组合标记
pytest -m "real_files and integration"
```

## 🔧 测试配置

### pytest.ini
```ini
[tool:pytest]
markers =
    real_files: 标记需要真实文件的测试
    integration: 标记集成测试
    api: 标记API接口测试
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### conftest.py
提供通用测试fixtures：
- `client`: FastAPI测试客户端
- `temp_dir`: 临时目录
- `test_docs_dir`: 测试文档目录
- `real_test_files`: 真实测试文件路径字典

## 📊 测试结果示例

### 成功运行
```
🚀 启动完整Markio测试套件
==================================================
📁 测试文档目录包含 10 个文件:
   1. test_ppt.ppt (7.7 MB)
   2. test_pdf3.pdf (0.0 MB)
   3. test_xlsx.xlsx (0.0 MB)
   4. test_pptx.pptx (4.7 MB)
   5. test_doc.doc (0.3 MB)
   6. test_docx.docx (0.1 MB)
   7. test_pdf1.pdf (9.8 MB)
   8. test_html.html (5.6 MB)
   9. test_epub.epub (0.7 MB)
  10. test_pdf2.pdf (1.3 MB)

==================================================
🔍 运行API端点测试...
✅ API端点测试通过

🔍 运行集成测试...
✅ 集成测试通过

🔍 运行并发测试...
✅ 并发测试通过

🔍 运行工具测试...
✅ 工具测试通过

==================================================
📊 测试结果摘要:
==================================================
API端点测试: ✅ 通过
集成测试: ✅ 通过
并发测试: ✅ 通过
工具测试: ✅ 通过
所有真实文件测试: ✅ 通过

总计: 5/5 个测试类别通过
🎉 所有测试类别都通过了！
```

## 🚨 故障排除

### 常见问题

#### 1. 测试文件不存在
```
❌ 错误: 测试文档目录不存在
   期望路径: /path/to/tests/test_docs
```
**解决方案**: 确保`tests/test_docs/`目录存在并包含测试文件

#### 2. 依赖缺失
```
❌ Pytest未安装
```
**解决方案**: 安装pytest
```bash
pip install pytest
```

#### 3. 测试跳过
```
test_pdf_parse_endpoint ... SKIPPED: 测试PDF文件不存在: /path/to/test_pdf1.pdf
```
**解决方案**: 检查测试文件是否完整，确保所有引用的文件都存在

### 调试模式
```bash
# 详细输出
pytest -v -s -m real_files

# 显示跳过原因
pytest -rs -m real_files

# 显示最慢的测试
pytest --durations=10 -m real_files
```

## 📈 性能监控

### 测试执行时间
- **API端点测试**: 通常 < 30秒
- **集成测试**: 通常 < 2分钟
- **并发测试**: 通常 < 3分钟
- **工具测试**: 通常 < 10秒

### 内存使用
- 测试过程中会监控内存使用情况
- 大文件测试会特别关注内存效率
- 并发测试会验证内存管理

## 🔄 持续集成

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    cd tests
    python run_tests.py --full
```

### 本地开发
```bash
# 开发时快速测试
pytest test_api_endpoints.py::TestAPIEndpoints::test_pdf_parse_endpoint -v

# 完整测试套件
python run_tests.py --full

# 快速演示
python run_tests.py --demo

# 环境检查
python run_tests.py --check
```

## 📝 添加新测试

### 1. 创建测试文件
```python
@pytest.mark.real_files
def test_new_feature(self, real_test_files):
    """测试新功能 - 使用真实文件"""
    # 使用真实测试文件
    test_file = real_test_files["pdf"]
    # ... 测试逻辑
```

### 2. 添加测试标记
在`conftest.py`中添加新标记：
```python
if any(test_name in item.name for test_name in [
    # ... 现有测试
    "test_new_feature"
]):
    item.add_marker(pytest.mark.real_files)
```

### 3. 更新README
在相应的测试分类中添加新测试的描述。

## 🤝 贡献指南

1. **测试覆盖**: 新功能必须包含相应的测试用例
2. **真实文件**: 优先使用真实文档文件而非mock数据
3. **错误处理**: 测试应该包含正常情况和异常情况
4. **性能考虑**: 大文件测试应该考虑执行时间
5. **文档更新**: 更新README和测试说明

## 📞 支持

如果遇到测试问题：
1. 检查测试环境配置
2. 验证测试文件完整性
3. 查看详细的错误日志
4. 提交issue描述问题

---

## 🧹 清理说明

**已删除的冗余文件：**
- ❌ `quick_test.py` - 旧的快速测试脚本
- ❌ `run_improved_tests.py` - 旧的改进测试脚本
- ❌ `quick_demo.py` - 旧的演示脚本

**合并后的统一脚本：**
- ✅ `run_tests.py` - 统一的测试运行脚本，支持多种模式：
  - `--full`: 运行完整测试套件
  - `--demo`: 运行快速演示
  - `--check`: 只检查环境
  - 默认: 运行完整测试套件

**保留的核心文件：**
- ✅ 所有改进后的测试文件（使用真实文档文件）
- ✅ 完整的测试配置和fixtures
- ✅ 统一的测试运行脚本
- ✅ 详细的文档说明

**注意**: 这些测试使用真实的文档文件，确保在运行前有足够的磁盘空间和内存。
