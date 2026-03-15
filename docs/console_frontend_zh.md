# Markio 前端控制台说明（OpenAI UI/UX 风格）

## 目标

Markio 控制台基于 `mineru-tianshu` 前端代码重构，保留企业级任务管理体验，同时保持 Markio 的轻量范围：

- 仅保留文档任务相关页面（仪表盘、任务列表、提交任务、任务详情、队列管理）
- 与 Markio 后端 `/v1/tasks/*` 完整对齐
- 保持静态部署到 FastAPI `/console`
- 默认同源调用 API（`VITE_API_BASE_URL=""`，直接请求 `/v1/*`）

## 页面与信息架构

- `/`：仪表盘（任务统计 + 最近任务 + 快捷操作）
- `/tasks`：任务列表（分页、状态过滤、取消、重试）
- `/tasks/submit`：任务提交（parse_method/lang/priority/分页范围等）
- `/tasks/:id`：任务详情（状态、错误、结果内容）
- `/queue`：队列管理（队列状态、暂停/恢复、操作日志）

## API 映射

前端 API 适配文件：

- `frontend/src/api/taskApi.ts`
- `frontend/src/api/queueApi.ts`

映射关系：

- `POST /v1/tasks/submit`
- `GET /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `GET /v1/tasks/dashboard`
- `GET /v1/tasks/queue`
- `POST /v1/tasks/queue/pause`
- `POST /v1/tasks/queue/resume`
- `POST /v1/tasks/{task_id}/cancel`
- `POST /v1/tasks/{task_id}/retry`

## OpenAI 风格设计要点

- 中性底色 + 低对比边框 + 清晰层级
- 控件简洁，减少装饰性动画
- 信息优先：可读性、留白、状态一致性
- 语义色精简：中性灰 + 绿色主色 + 状态色

样式入口：`frontend/src/style.css`。

## 本地开发与发布

### 1) 开发调试

```bash
cd frontend
npm install
npm run dev
```

默认 Vite 本地地址：`http://localhost:3000`

### 2) 构建到后端静态目录

```bash
cd frontend
npm run build
```

构建产物输出到：`markio/webapp`

默认环境变量：
- `frontend/.env.development`: `VITE_API_BASE_URL=`
- `frontend/.env.production`: `VITE_API_BASE_URL=`

### 3) 访问控制台

启动后端后访问：

- `http://localhost:8000/console`

## 第三方来源与许可

前端来源与修改声明见：

- `frontend/THIRD_PARTY_NOTICES.md`
