# Markio Console 前端说明

[返回 README](../README.zh.md) | [English Version](console_frontend.md)

## 它是什么

Console 是 Markio 当前的主浏览器控制台。它是一个基于 Vue 3 + TypeScript + Vite 的 SPA，源码位于 `frontend/`，由 FastAPI 挂载到 `/console`。

当前产品定位：

- console 是主 Web 工作流
- Gradio 只是可选补充
- 默认且推荐使用同源部署

## 运行契约

### 构建产物

前端必须构建到 `markio/webapp`。

```bash
cd frontend
npm install
npm run build
```

### 后端托管

`markio/main.py` 的托管规则是：

- 当 `markio/webapp/index.html` 存在时，`/console` 返回 SPA
- 当静态资源缺失时，`/console` 返回 fallback helper page

这个 fallback 页面不是并行产品形态，只是为了明确提示“前端还没有构建”。

## 路由结构

- `/` 仪表盘
- `/tasks` 任务列表
- `/tasks/submit` 任务提交
- `/tasks/:id` 任务详情
- `/queue` 队列控制

这些都是 `/console` 挂载下的前端路由。

## 后端 API 映射

前端主要通过以下模块调用后端：

- `frontend/src/api/taskApi.ts`
- `frontend/src/api/queueApi.ts`

实际使用的后端接口：

- `POST /v1/tasks/submit`
- `GET /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `GET /v1/tasks/dashboard`
- `GET /v1/tasks/queue`
- `POST /v1/tasks/queue/pause`
- `POST /v1/tasks/queue/resume`
- `POST /v1/tasks/{task_id}/cancel`
- `POST /v1/tasks/{task_id}/retry`

## 鉴权与权限

- console 发起的所有 API 调用仍依赖 JWT
- 当前前端依旧在浏览器侧持有 token
- 队列控制是 admin-only，因为后端要求 `role=admin`
- owner/admin 视图差异只是前端辅助，真正的权限边界仍以后端为准

## 网络模型

默认行为：

- `VITE_API_BASE_URL=""`
- 请求直接走同源 `/v1/*`
- 本地 Vite 开发时会把 `/v1` 代理到 `http://localhost:8000`

如果需要跨域联调，需要显式配置后端 CORS 白名单。

## 安全头与浏览器策略

后端当前为 console 提供了更收紧的 CSP：

- 已移除 `unsafe-eval`
- `connect-src` 已收缩到同源默认行为

如果将来扩展 console，请尽量继续使用同源 API，不要随意为了“方便调试”放宽 CSP。

## 测试与交付要求

仓库现在把“真实 SPA 构建产物”视为 console 交付契约的一部分：

- console 路由测试会校验真实构建产物
- 测试 fixture 会在需要时构建前端
- 已刻意避免 import-time side effect

相关测试：

- `tests/test_console_frontend.py`

## 开发说明

```bash
cd frontend
npm install
npm run dev
```

常用目录：

- `frontend/src/views/`
- `frontend/src/components/`
- `frontend/src/stores/`
- `frontend/src/router/`

## 当前边界

- 还没有独立的前端 E2E 测试套件
- 前端鉴权仍是 token 模式
- 只有在真实构建产物存在时，`/console` 才算主链路可用
