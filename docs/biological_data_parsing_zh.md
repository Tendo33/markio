# 生物数据解析指南

Markio 现在支持解析生物信息学和基因组学研究中常用的生物序列数据格式。此功能允许您将 FASTA 和 GenBank 格式文件转换为结构化、可读的 Markdown 文档。

## 🔬 BioPython 集成

生物数据解析器支持**可选的 BioPython 集成**以获得增强的分析能力：

### 无 BioPython（基础模式）
- ✅ 解析 FASTA 和 GenBank 文件
- ✅ 基础序列统计
- ✅ GC 含量计算（DNA）
- ✅ 序列类型检测

### 有 BioPython（增强模式）
- ✅ **所有基础功能**
- ✅ **蛋白质属性分析：**
  - 分子量
  - 等电点 (pI)
  - 芳香性
  - 不稳定指数
  - GRAVY（疏水性）
- ✅ **增强的 GenBank 解析**，精确提取特征
- ✅ **使用 BioPython 算法的精确计算**

### 安装

**基础安装**（开箱即用）：
```bash
pip install markio
```

**包含 BioPython 支持**（推荐用于生物数据）：
```bash
pip install markio[bio]
# 或
pip install biopython>=1.80
```

解析器会**自动检测** BioPython 并在可用时启用增强功能。无需配置！

## 支持格式

### 1. FASTA 格式

FASTA 是表示核苷酸或肽序列的基于文本的格式。它是生物信息学中使用最广泛的格式之一。

**支持的文件扩展名：**
- `.fasta` - 标准 FASTA
- `.fa` - 简写形式
- `.fna` - FASTA 核酸
- `.faa` - FASTA 氨基酸
- `.ffn` - FASTA 核苷酸编码区
- `.fsa` - FASTA 序列比对
- `.fas` - 替代格式
- `.txt` - 纯文本

**功能特性：**
- 解析单个或多个序列
- 自动序列类型检测（DNA、蛋白质、未知）
- 计算序列统计：
  - 序列长度
  - GC 含量（DNA 序列）
  - 类型分布
- 以可读块格式化序列
- 提取元数据（ID、描述）
- **BioPython 增强**：分子量、蛋白质理化性质

### 2. GenBank 格式

GenBank 是 NCBI 使用的综合数据库格式，包括序列数据和广泛的生物学注释。

**支持的文件扩展名：**
- `.gb` - 标准 GenBank
- `.gbk` - GenBank
- `.genbank` - 全名
- `.gbff` - GenBank 平面文件
- `.txt` - 纯文本

**功能特性：**
- 解析完整的 GenBank 记录
- 提取元数据：
  - LOCUS 信息（名称、长度、分子类型、日期）
  - DEFINITION（描述）
  - ACCESSION 编号
  - VERSION
  - SOURCE 和 ORGANISM
- 解析特征表：
  - 特征类型（CDS、gene、mRNA 等）
  - 位置和坐标
  - 限定符（注释）
- 提取序列数据
- 计算 GC 含量
- 支持每个文件多条记录
- **BioPython 增强**：更精确的特征解析和验证

## 使用方法

### REST API

#### 解析 FASTA 文件

**端点：** `POST /v1/parse_fasta_file`

**参数：**
- `file` (UploadFile): 要解析的 FASTA 文件
- `save_parsed_content` (bool): 保存输出到磁盘（默认：false）
- `output_dir` (str): 输出目录（默认："outputs"）
- `include_statistics` (bool): 包含序列统计（默认：true）

**示例：**
```python
import httpx
import asyncio

async def parse_fasta():
    async with httpx.AsyncClient() as client:
        files = {"file": open("sequences.fasta", "rb")}
        data = {
            "save_parsed_content": "true",
            "include_statistics": "true"
        }
        resp = await client.post(
            "http://localhost:8000/v1/parse_fasta_file",
            files=files,
            data=data
        )
        result = resp.json()
        print(result['parsed_content'])
        return result

asyncio.run(parse_fasta())
```

#### 解析 GenBank 文件

**端点：** `POST /v1/parse_genbank_file`

**参数：**
- `file` (UploadFile): 要解析的 GenBank 文件
- `save_parsed_content` (bool): 保存输出到磁盘（默认：false）
- `output_dir` (str): 输出目录（默认："outputs"）
- `include_features` (bool): 包含特征表（默认：true）
- `include_sequence` (bool): 包含序列数据（默认：true）

### Python SDK

```python
from markio.parsers.fasta_parser import fasta_parse_main
from markio.parsers.genbank_parser import genbank_parse_main
import asyncio

async def main():
    # 解析 FASTA 文件
    fasta_content = await fasta_parse_main(
        resource_path="sequences.fasta",
        save_parsed_content=True,
        output_dir="./outputs",
        include_statistics=True
    )
    print("FASTA 解析成功")
    
    # 解析 GenBank 文件
    genbank_content = await genbank_parse_main(
        resource_path="sequence.gb",
        save_parsed_content=True,
        output_dir="./outputs",
        include_features=True,
        include_sequence=True
    )
    print("GenBank 解析成功")

asyncio.run(main())
```

## 输出格式

### FASTA 输出

解析器生成结构化的 Markdown，包含：
- **摘要部分**统计信息：
  - 序列总数
  - 序列总长度
  - 序列类型分布
  - 平均 GC 含量（DNA）
- **单个序列**包含：
  - 序列 ID 和描述
  - 检测到的类型（DNA/蛋白质/未知）
  - 长度
  - GC 含量（DNA）
  - **蛋白质属性**（如果有 BioPython）：
    - 分子量
    - 等电点
    - 芳香性
    - 不稳定指数
    - 疏水性（GRAVY）
  - 格式化的序列（每行 60 个字符）

### GenBank 输出

解析器生成结构化的 Markdown，包含：
- **摘要部分**：
  - 记录总数
  - 序列总长度
- **单个记录**包含：
  - 基本信息（LOCUS、DEFINITION、ACCESSION、VERSION）
  - 来源信息（生物体、分类学）
  - 特征表（格式化为 Markdown 表格）
  - 带行号的序列数据
  - GC 含量

## 应用场景

### 研究应用
- **序列分析**：将原始序列文件转换为可读格式
- **文档编制**：为遗传序列创建人类可读的文档
- **数据管道**：与生物信息学工作流集成
- **归档**：将序列数据库转换为可搜索的 Markdown

### 生物信息学工作流
- **质量控制**：在分析前审查序列数据
- **协作**：与同事共享格式化的序列数据
- **发表**：为论文和报告准备序列数据
- **教学**：从真实序列数据创建教学材料

## 技术细节

### 序列类型检测

**DNA 序列：**
- 仅包含 A、T、G、C、N 字符
- 自动计算 GC 含量

**蛋白质序列：**
- 包含标准氨基酸代码（ACDEFGHIKLMNPQRSTVWY）
- 不计算 GC 含量
- 使用 BioPython 时分析蛋白质属性

**未知：**
- 包含其他字符或混合类型

### 性能

- **FASTA**：针对大型多序列文件优化
- **GenBank**：高效处理复杂注释
- **内存**：大文件的流式处理方法
- **速度**：快速解析，最小开销

### BioPython vs 基础模式比较

| 功能 | 基础模式 | BioPython 模式 |
|------|---------|---------------|
| 文件解析 | ✅ | ✅ 更精确 |
| GC 含量 | ✅ 基础计算 | ✅ BioPython 算法 |
| 分子量 | ❌ | ✅ |
| 蛋白质属性 | ❌ | ✅ |
| GenBank 特征 | ✅ 基础 | ✅ 完整解析 |
| 序列验证 | ❌ | ✅ |

## 故障排除

### 常见问题

**问题："BioPython not found"警告**
- 这是正常的，解析器将使用基础模式
- 要启用增强功能，安装 BioPython：`pip install biopython>=1.80`
- 或安装完整版：`pip install markio[bio]`

**问题："未找到有效的 FASTA 序列"**
- 检查文件格式（应以 '>' 开头）
- 验证文件编码（推荐 UTF-8）
- 确保序列不为空

**问题："无效的 GenBank 格式"**
- 验证文件以 "LOCUS" 开头
- 检查完整记录（以 "//" 结尾）
- 确保文件未被截断

## 与 Markio 其他功能的集成

生物数据解析与 Markio 其他功能无缝集成：

- **MCP 协议**：通过 Claude Desktop 或其他 MCP 客户端访问
- **Docker**：在容器化环境中使用
- **REST API**：像其他解析器一样的标准 HTTP 端点
- **批处理**：高效处理多个文件
- **输出管理**：一致的文件组织

---

**注意**：此功能旨在补充而非替代专业的生物信息学工具。对于复杂的序列分析，请结合 Markio 的解析功能使用 BLAST、Clustal 或 Biopython 等专用工具。

**建议**：对于生物数据处理，建议安装 BioPython 以获得最佳体验：`pip install markio[bio]`

