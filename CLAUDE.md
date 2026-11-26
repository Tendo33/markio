# markio

入口在 [AGENTS.md](AGENTS.md)：接口契约、目录结构与验证命令都在那里。

要点复述：`/v1/*` 必须带 JWT，Redis 不得成为本地开发的必需项，前端构建产物要落到 `markio/webapp` 供 `/console` 使用。
