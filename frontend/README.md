# Markio Console Frontend

Markio 控制台前端，基于 Vue 3 + TypeScript + Vite + TailwindCSS。

## 快速开始

```bash
npm install
npm run dev
```

开发地址：`http://localhost:3000`

## 构建

```bash
npm run build
```

默认构建输出到 `../markio/webapp`，由后端 `/console` 静态托管。

## 当前已实现能力

- 仪表盘：任务统计、最近任务、快捷入口
- 任务列表：分页、状态筛选、刷新、取消、重试
- 任务提交：文件上传、解析参数配置、参数校验
- 任务详情：任务元数据、结果查看、自动轮询、取消/重试
- 队列管理：队列状态、暂停/恢复、操作日志
- 统一交互：Toast 通知 + 二次确认弹窗

## 环境变量

前端通过 `VITE_API_BASE_URL` 配置后端地址：

- 同源部署（默认、推荐）：留空（`/v1` 由同源路径直连）
- 本地开发（Vite 代理）：留空（`vite.config.ts` 已代理 `/v1 -> http://localhost:8000`）
- 显式跨域联调：`VITE_API_BASE_URL=http://127.0.0.1:8000`（需后端 `CORS_ALLOW_ORIGINS` 放行）

参考：`frontend/.env.example`

## 目录结构

```text
frontend/
├── src/
│   ├── api/          # API 请求封装
│   ├── components/   # 通用组件
│   ├── layouts/      # 布局组件
│   ├── stores/       # Pinia 状态管理
│   ├── utils/        # 格式化/通知工具
│   └── views/        # 页面视图
├── vite.config.ts
├── tailwind.config.cjs
└── package.json
```

## 已知边界

- 当前基于 JWT 声明做最小权限感知（队列控制仅在 `role=admin` 显示），后端仍是最终鉴权来源
- 暂未接入前端 E2E 自动化测试
