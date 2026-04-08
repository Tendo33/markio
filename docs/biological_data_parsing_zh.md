# 生物数据解析指南

[返回 README](../README.zh.md) | [English Version](biological_data_parsing.md)

## 当前状态

Markio 目前支持两类生物序列格式：

- FASTA
- GenBank

按照当前项目依赖配置，BioPython 已经是默认依赖的一部分，因此这些解析器通常会直接走增强分析路径，而不是退回到一个单独的“可选插件模式”。

## API 入口

专用接口：

- `POST /v1/parse_fasta_file`
- `POST /v1/parse_genbank_file`

这两类格式**不会**被 `/v1/parse_file` 自动分发。

所有 `/v1/*` 路由都要求：

- `Authorization: Bearer <JWT>`

## 本地 parser 入口

本地可直接调用：

- `markio.parsers.fasta_parser.fasta_parse_main`
- `markio.parsers.genbank_parser.genbank_parse_main`

当前还没有对应的 `MarkioSDK` façade 方法，也没有独立 CLI 子命令。

## FASTA

支持扩展名：

- `.fasta`
- `.fa`
- `.fna`
- `.faa`
- `.ffn`
- `.fsa`
- `.fas`
- `.txt`

能力包括：

- 单条或多条序列解析
- 序列类型识别
- 序列统计信息
- DNA 类序列的 GC 含量
- 适合人工审阅与下游处理的 Markdown 输出

FASTA 专属参数：

- `include_statistics`

## GenBank

支持扩展名：

- `.gb`
- `.gbk`
- `.genbank`
- `.gbff`
- `.txt`

能力包括：

- 记录级元数据提取
- feature table 提取
- 可控制是否包含 sequence
- 输出带注释的 Markdown 内容

GenBank 专属参数：

- `include_features`
- `include_sequence`

## REST API 示例

### FASTA

```bash
curl -X POST "http://localhost:8000/v1/parse_fasta_file" \
  -H "Authorization: Bearer <YOUR_JWT>" \
  -F "file=@./sample.fasta" \
  -F "include_statistics=true"
```

### GenBank

```bash
curl -X POST "http://localhost:8000/v1/parse_genbank_file" \
  -H "Authorization: Bearer <YOUR_JWT>" \
  -F "file=@./sample.gb" \
  -F "include_features=true" \
  -F "include_sequence=true"
```

## 本地 Python 示例

```python
import asyncio
from markio.parsers.fasta_parser import fasta_parse_main
from markio.parsers.genbank_parser import genbank_parse_main

async def main():
    fasta_markdown = await fasta_parse_main(
        resource_path="sample.fasta",
        save_parsed_content=True,
        output_dir="outputs",
        include_statistics=True,
    )

    genbank_markdown = await genbank_parse_main(
        resource_path="sample.gb",
        save_parsed_content=True,
        output_dir="outputs",
        include_features=True,
        include_sequence=True,
    )

    print(fasta_markdown[:200])
    print(genbank_markdown[:200])

asyncio.run(main())
```

## 输出大致包含

### FASTA 输出

- 序列数量汇总
- 序列元数据
- 单条序列长度与类型提示
- 适用时的 GC 含量

### GenBank 输出

- 记录元数据
- 来源与 organism 信息
- 开启时的 feature 注释
- 开启时的 sequence 内容

## 测试覆盖

相关回归测试：

- `tests/test_biological_parsers.py`
- `tests/test_parser_route_security.py`

## 当前边界

- 不支持 `/v1/parse_file` 自动分发
- 还没有 SDK façade 方法
- 还没有 CLI 子命令
