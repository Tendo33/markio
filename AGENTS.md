# markio

API-first 文档解析平台：把各类文档与网页内容转成 Markdown，提供 FastAPI 路由、异步任务、SDK/CLI 与 Vue 控制台。

## 不能破坏的契约

- 每个 `/v1/*` 路由都要 JWT 认证，异步任务按 owner 隔离。
- Redis 是可选组件，默认本地用内存任务后端，不要让 Redis 变成本地开发的硬依赖。
- 控制台由 `markio/webapp` 提供，挂在 `/console`，需要先构建前端。
- Python `>=3.11`，前端包管理固定 pnpm（`frontend/pnpm-lock.yaml`）。

## 结构

- `markio/`：后端包，包含解析器、路由、任务与 schema。
- `frontend/`：Vue 3 + Pinia + Tailwind 4 控制台。
- `tests/`：pytest 用例，标记 `live` 的默认跳过。
- `compose.yaml`、`start_services.sh`：本地依赖编排。

## 命令

```bash
uv sync
uv run pytest                 # 默认跳过 live 标记
uv run pytest -m live         # 需要真实外部服务时
uv run ruff check .
pnpm --prefix frontend install
pnpm --prefix frontend run build
pnpm --prefix frontend run test:e2e   # 先 build 再跑 Playwright
```

## 工作方式

- 改解析器或任务前，先读对应的 router、parser、service、schema 与 tests。
- UI 改动沿用现有 Vue 3 + Pinia + Tailwind 4 模式，不引入第二套组件库。
- 先跑定向用例，再跑整体校验。
