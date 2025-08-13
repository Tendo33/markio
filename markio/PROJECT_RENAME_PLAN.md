# Markify → Markio 项目重命名计划

## 概述
将项目名从 "markify" 更改为 "markio"，保持所有功能逻辑不变，仅更新项目名称相关的内容。

## 需要更改的文件和内容

### 1. 配置文件
- [ ] `setup.py` - 包名、描述、URL、入口点
- [ ] `pyproject.toml` - 包名、描述、URL、入口点、包路径
- [ ] `compose.yaml` - 服务名、容器名

### 2. 启动脚本
- [ ] `start_services.sh` - 注释、路径、服务名

### 3. 文档文件
- [ ] `README.md` - 项目名、描述、URL、示例
- [ ] `docs/README_zh.md` - 中文文档中的项目名
- [ ] `docs/cli_usage.md` - CLI使用指南
- [ ] `docs/cli_usage_zh.md` - 中文CLI使用指南

### 4. 代码文件
- [ ] `markio/main.py` - 类名、变量名、日志信息
- [ ] `markio/markio_mcp/markio_mcp_server.py` - 类名、注释、日志信息
- [ ] `markio/sdk/markio_sdk.py` - 注释、类名

### 5. 需要重命名的类/变量
- [ ] `MarkifyMCP` → `MarkioMCP`
- [ ] `MarkifyApi` → `MarkioApi`
- [ ] `PROJECT_NAME = "Markify"` → `PROJECT_NAME = "Markio"`

### 6. 需要更新的导入路径
- [ ] 检查所有import语句中的markify引用
- [ ] 更新相对导入路径

## 更改策略
1. 保持所有功能逻辑完全不变
2. 仅更新项目名称、类名、变量名、注释和文档
3. 确保所有引用的一致性
4. 保持代码结构和API接口不变

## 验证清单
- [ ] 所有文件中的markify已更改为markio
- [ ] 所有类名已更新
- [ ] 所有导入路径已更新
- [ ] 配置文件已更新
- [ ] 文档已更新
- [ ] 启动脚本已更新
- [ ] 项目可以正常构建和运行
