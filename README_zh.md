<img src="assets/image.png" alt="Markio Logo" height="300" style="display:block;margin:auto;">

> **Markio**：基于 **docling + MinerU** 的轻量企业级文档解析平台。

<div align="center">

### 🌍 Language / 语言

[English](README.md) | **中文**

</div>

---

## 项目定位

Markio 提供统一的 FastAPI 接口，把多种文档格式转换为 Markdown/结构化文本。

这一轮重构重点：

- 对齐最新 MinerU 解析方式
- 增加异步任务系统（可暂停/恢复/取消/重试）
- Redis 结果缓存
- OpenAI 风格 Web 控制台（`/console`）

## 当前范围（重构后）

- 保留：docling + MinerU 文档处理栈
- 保留：同步解析接口（`/v1/parse_*`）
- 新增：异步任务接口（`/v1/tasks/*`）
- 新增：任务队列与仪表盘管理接口
- 新增：Vue 控制台前端并由 FastAPI 静态托管
- 不包含：GPU 负载均衡、重型用户体系、Tianshu 的额外模态

---

## 快速开始

### 1）本地启动

```bash
git clone https://github.com/Tendo33/markio.git
cd markio

uv sync
uv pip install -e .

python markio/main.py
```

访问：

- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)
- 控制台：[http://localhost:8000/console](http://localhost:8000/console)

### 2）Docker 启动

```bash
docker compose up -d
```

启动后访问同上地址。

---

## 异步任务 API

基础路径：`/v1/tasks`

| 接口 | 方法 | 说明 |
|---|---|---|
| `/submit` | POST | 提交异步任务 |
| `/` | GET | 分页/状态过滤查询任务 |
| `/{task_id}` | GET | 查询任务详情 |
| `/dashboard` | GET | 仪表盘统计 + 最近任务 |
| `/queue` | GET | 队列健康状态 |
| `/queue/pause` | POST | 暂停队列 |
| `/queue/resume` | POST | 恢复队列 |
| `/{task_id}/cancel` | POST | 取消等待中的任务 |
| `/{task_id}/retry` | POST | 重试失败或已取消任务 |

示例：

```bash
curl -X POST "http://localhost:8000/v1/tasks/submit" \
  -F "file=@./sample.pdf" \
  -F "parse_method=auto" \
  -F "lang=ch" \
  -F "priority=5"
```

---

## 前端控制台（OpenAI UI/UX 风格）

新前端源码位于 `frontend/`，构建产物输出到 `markio/webapp/`。

手动构建：

```bash
cd frontend
npm install
npm run build
```

详细说明：

- [docs/console_frontend_zh.md](docs/console_frontend_zh.md)
- [docs/console_frontend.md](docs/console_frontend.md)

---

## 关键环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PDF_PARSE_ENGINE` | `pipeline` | PDF 解析引擎 |
| `MINERU_DEVICE_MODE` | `cuda` | MinerU 设备（`cuda/cpu/mps`） |
| `REDIS_ENABLED` | `false` | 是否启用 Redis 缓存 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `TASK_WORKER_COUNT` | `2` | 异步 worker 数量 |
| `TASK_QUEUE_BACKEND` | `memory` | 任务队列后端（`memory/redis`） |
| `TASK_HISTORY_LIMIT` | `500` | 内存任务历史上限 |
| `TASK_STATE_FILE` | `data/task_state.json` | 任务状态持久化路径 |
| `TASK_UPLOAD_DIR` | `data/task_uploads` | 上传临时目录 |
| `TASK_MAX_AUTO_RETRIES` | `0` | 自动重试次数上限 |
| `TASK_RETRY_DELAY_SECONDS` | `0` | 自动重试延迟（秒） |
| `TASK_PROCESSING_TIMEOUT_SECONDS` | `0` | 处理超时回收阈值（秒） |

完整配置请参考 `.env.example`。

---

## 文档索引

- CLI 使用：`docs/cli_usage_zh.md`
- SDK 使用：`docs/sdk_usage_zh.md`
- Redis 集成：`docs/REDIS_INTEGRATION.md`
- 前端控制台：`docs/console_frontend_zh.md`

---

## License

Markio 采用 MIT License，见 `LICENSE`。

前端包含来自 `mineru-tianshu`（Apache-2.0）的适配代码，详见：

- `frontend/THIRD_PARTY_NOTICES.md`
