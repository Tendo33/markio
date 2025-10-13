# Redis集成 - 项目更新说明

## 🎯 更新概述

Markio项目已成功集成Redis缓存功能，提供企业级的缓存解决方案。本次更新**暂不涉及具体parser的实施**，仅提供Redis工具基础设施，供未来按需集成。

---

## 📦 文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `markio/utils/redis_utils.py` | **核心Redis工具模块** - 连接管理、缓存操作、序列化 |
| `tests/test_redis.py` | **完整测试套件** - 涵盖所有Redis功能 |
| `docs/redis_usage_examples.md` | **详细使用指南** - 代码示例和最佳实践 |
| `docs/REDIS_README.md` | **集成说明文档** - 快速开始和配置说明 |
| `docs/REDIS_INTEGRATION.md` | **本文档** - 项目更新说明 |
| `scripts/install_redis_deps.sh` | **安装脚本** - 一键安装Redis依赖 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|----------|
| `pyproject.toml` | ✅ 添加 `redis[hiredis]>=5.0.0` 依赖 |
| `markio/settings/config_model.py` | ✅ 新增9个Redis配置项 |
| `env.example` | ✅ 添加Redis配置示例和详细说明 |
| `compose.yaml` | ✅ 新增Redis服务配置 |
| `markio/utils/__init__.py` | ✅ 导出Redis工具类和便捷函数 |

---

## 🚀 核心功能

### 1. RedisManager - 连接管理器

```python
from markio.utils import redis_manager

# 应用启动时初始化
await redis_manager.initialize()

# 应用关闭时清理
await redis_manager.close()

# 检查可用性
if redis_manager.is_available:
    print("Redis is ready!")
```

**特性**：
- ✅ 单例模式，全局复用
- ✅ 异步连接池管理
- ✅ 自动重连和错误处理
- ✅ 优雅的启动/关闭

### 2. RedisCache - 高级缓存操作

#### 基础操作
```python
from markio.utils import cache_set, cache_get, cache_delete, cache_exists

# 设置缓存（默认1小时过期）
await cache_set("user:123", {"name": "张三"}, ttl=3600)

# 获取缓存
user = await cache_get("user:123")

# 检查存在
exists = await cache_exists("user:123")

# 删除缓存
await cache_delete("user:123")
```

#### 批量操作
```python
from markio.utils import RedisCache

# 批量设置
await RedisCache.mset({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批量获取
results = await RedisCache.mget(["key1", "key2", "key3"])
```

#### 模式匹配
```python
# 查找匹配的键
user_keys = await RedisCache.keys_pattern("user:*", limit=100)

# 批量删除
deleted = await RedisCache.delete_pattern("temp:*")
```

#### 原子计数器
```python
# 递增
count = await RedisCache.increment("api:requests", 1)

# 递减
remaining = await RedisCache.decrement("quota:user:123", 1)
```

#### TTL管理
```python
# 设置过期时间
await RedisCache.expire("session:abc", 1800)  # 30分钟

# 获取剩余时间
ttl = await RedisCache.get_ttl("session:abc")
```

#### 直接使用Redis客户端
```python
from markio.utils import get_redis_client

async with get_redis_client() as redis:
    if redis:
        # 使用所有Redis命令
        await redis.set("key", "value")
        await redis.lpush("queue", "item")
        await redis.hset("hash", "field", "value")
```

### 3. 智能序列化

**自动选择序列化方式**：

```python
# JSON序列化（默认，适合简单类型）
await cache_set("simple", {"key": "value"})

# Pickle序列化（适合复杂对象）
from datetime import datetime
await cache_set("complex", {
    "timestamp": datetime.now()
}, use_pickle=True)
```

支持的数据类型：
- ✅ JSON: str, int, float, list, dict, bool, None
- ✅ Pickle: 上述类型 + datetime, bytes, 自定义类等

---

## ⚙️ 配置系统

### 环境变量

在 `.env` 文件中配置：

```bash
# 启用Redis
REDIS_ENABLED=true

# 连接配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 可选：密码保护
REDIS_PASSWORD=your_password

# 性能调优
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_DEFAULT_TTL=3600
```

### Docker Compose

已在 `compose.yaml` 中配置好Redis服务：

```yaml
redis:
  image: redis:7-alpine
  container_name: markio-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
  restart: unless-stopped
```

**特性**：
- 🐳 Redis 7 Alpine（轻量级）
- 💾 AOF持久化（数据安全）
- 📦 数据卷持久化
- 🔄 自动重启

---

## 📊 架构设计

### 层次结构

```
┌─────────────────────────────────────┐
│        FastAPI Application          │
│    (Parsers, Routers, Services)     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      Redis Utils (便捷函数)         │
│  cache_set, cache_get, cache_delete │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│         RedisCache (高级操作)        │
│   批量、模式、计数、TTL、序列化      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      RedisManager (连接管理)        │
│    连接池、初始化、生命周期管理      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│       Redis Server (7-alpine)       │
│     AOF持久化、数据卷、自动重启      │
└─────────────────────────────────────┘
```

### 设计模式

1. **单例模式**：RedisManager全局唯一实例
2. **连接池模式**：复用连接，提高性能
3. **策略模式**：JSON/Pickle序列化自动选择
4. **装饰器模式**：上下文管理器封装
5. **容错模式**：优雅降级，不影响主流程

---

## 🔧 快速开始

### 1. 安装依赖

```bash
# 方式一：使用安装脚本（推荐）
bash scripts/install_redis_deps.sh

# 方式二：手动安装
uv sync
# 或
pip install -e .
```

### 2. 启动Redis

```bash
# 使用Docker Compose（推荐）
docker-compose up -d redis

# 验证启动
docker ps | grep redis
redis-cli ping  # 应返回 PONG
```

### 3. 启用Redis

编辑 `.env` 文件：

```bash
REDIS_ENABLED=true
REDIS_HOST=localhost  # Docker中使用 redis
```

### 4. 在应用中集成

```python
from fastapi import FastAPI
from markio.utils import redis_manager

app = FastAPI()

@app.on_event("startup")
async def startup():
    await redis_manager.initialize()
    print("✅ Redis initialized")

@app.on_event("shutdown")
async def shutdown():
    await redis_manager.close()
    print("✅ Redis connections closed")
```

### 5. 运行测试

```bash
# 确保Redis已启动并启用
python tests/test_redis.py

# 使用pytest
pytest tests/test_redis.py -v
```

---

## 💡 应用场景示例

### 场景1：PDF解析结果缓存

```python
import hashlib
from markio.utils import cache_get, cache_set

async def parse_pdf_with_cache(pdf_path: str):
    # 基于文件内容生成缓存键
    with open(pdf_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    cache_key = f"pdf:parsed:{file_hash}"
    
    # 尝试从缓存获取
    result = await cache_get(cache_key)
    if result:
        print("✅ Cache hit!")
        return result
    
    # 缓存未命中，执行解析
    print("⚙️  Parsing PDF...")
    result = await actual_parse_pdf(pdf_path)
    
    # 保存到缓存（24小时）
    await cache_set(cache_key, result, ttl=86400)
    
    return result
```

**优势**：
- ⚡ 相同文件秒级响应
- 💰 节省计算资源
- 📈 提升用户体验

### 场景2：API限流

```python
from fastapi import HTTPException
from markio.utils import RedisCache

async def rate_limit_check(user_id: str, limit: int = 60):
    """每分钟请求限制"""
    key = f"rate_limit:{user_id}:minute"
    
    # 递增计数
    count = await RedisCache.increment(key)
    
    # 首次请求设置过期时间
    if count == 1:
        await RedisCache.expire(key, 60)
    
    # 检查是否超限
    if count > limit:
        raise HTTPException(429, "Too many requests")
    
    return count
```

**优势**：
- 🔒 防止滥用
- ⚡ 高性能原子操作
- 🎯 精确控制

### 场景3：分布式锁

```python
from markio.utils import get_redis_client

async def process_with_lock(resource_id: str):
    """使用分布式锁保护资源"""
    lock_key = f"lock:resource:{resource_id}"
    
    async with get_redis_client() as redis:
        # 尝试获取锁（10秒超时）
        acquired = await redis.set(
            lock_key, 
            "locked", 
            nx=True,  # 仅当不存在时设置
            ex=10     # 10秒后自动释放
        )
        
        if not acquired:
            return {"status": "busy", "msg": "Resource is locked"}
        
        try:
            # 处理业务逻辑
            result = await process_resource(resource_id)
            return result
        finally:
            # 释放锁
            await redis.delete(lock_key)
```

**优势**：
- 🔐 防止并发冲突
- ⏰ 自动超时释放
- 🌐 分布式环境支持

### 场景4：会话管理

```python
from markio.utils import cache_set, cache_get, cache_delete

async def create_session(user_id: str, session_data: dict):
    """创建用户会话"""
    session_token = generate_token()
    session_key = f"session:{session_token}"
    
    # 保存会话（30分钟）
    await cache_set(session_key, {
        "user_id": user_id,
        **session_data
    }, ttl=1800)
    
    return session_token

async def get_session(session_token: str):
    """获取会话"""
    session_key = f"session:{session_token}"
    return await cache_get(session_key)

async def destroy_session(session_token: str):
    """销毁会话"""
    session_key = f"session:{session_token}"
    await cache_delete(session_key)
```

**优势**：
- 💨 快速会话查询
- 🔄 自动过期清理
- 📊 轻松统计在线用户

---

## 🧪 测试覆盖

测试脚本 `tests/test_redis.py` 覆盖以下功能：

- ✅ Redis连接测试
- ✅ 基本缓存CRUD操作
- ✅ JSON序列化
- ✅ Pickle序列化
- ✅ 批量设置/获取
- ✅ TTL设置和查询
- ✅ 原子递增/递减
- ✅ 模式匹配查询
- ✅ 模式批量删除
- ✅ 直接使用Redis客户端

**运行测试**：

```bash
# 直接运行
python tests/test_redis.py

# 使用pytest
pytest tests/test_redis.py -v

# 查看详细输出
pytest tests/test_redis.py -v -s
```

---

## 📈 性能优化

### 1. 连接池配置

根据应用并发量调整：

```bash
# 低并发（<10）
REDIS_MAX_CONNECTIONS=10

# 中并发（10-50）
REDIS_MAX_CONNECTIONS=50

# 高并发（>50）
REDIS_MAX_CONNECTIONS=100
```

### 2. 使用批量操作

```python
# ❌ 低效：多次单独操作
for key, value in data.items():
    await cache_set(key, value)

# ✅ 高效：批量操作
await RedisCache.mset(data)
```

### 3. 合理设置TTL

```python
# 根据数据特性设置过期时间
await cache_set("hot_data", value, ttl=300)      # 5分钟
await cache_set("normal_data", value, ttl=3600)  # 1小时
await cache_set("cold_data", value, ttl=86400)   # 1天
```

### 4. 键名优化

```python
# ✅ 简短但有意义
"u:123:p"         # user:123:profile
"pdf:h:abc123"    # pdf:hash:abc123

# ❌ 过长
"application_user_profile_data_123"
```

---

## 🔒 安全建议

### 1. 密码保护

生产环境必须设置密码：

```bash
# .env
REDIS_PASSWORD=your_strong_password_here
```

### 2. 网络隔离

```yaml
# compose.yaml
redis:
  networks:
    - backend  # 仅内部网络
  # 不暴露端口到主机
```

### 3. 数据加密

敏感数据加密后再存储：

```python
from cryptography.fernet import Fernet

cipher = Fernet(key)
encrypted = cipher.encrypt(data.encode())
await cache_set("sensitive", encrypted)
```

---

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| [REDIS_README.md](./REDIS_README.md) | 集成说明和快速开始 |
| [redis_usage_examples.md](./redis_usage_examples.md) | 详细使用示例和最佳实践 |
| [REDIS_INTEGRATION.md](./REDIS_INTEGRATION.md) | 本文档 - 项目更新说明 |

---

## 🎯 后续集成建议

虽然本次更新**暂不集成到具体parser**，但以下是未来集成建议：

### PDF Parser集成
```python
# markio/parsers/pdf_parser.py
from markio.utils import cache_get, cache_set
import hashlib

async def parse_pdf(file_path: str):
    # 生成缓存键
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    cache_key = f"pdf:parsed:{file_hash}"
    
    # 缓存逻辑
    result = await cache_get(cache_key)
    if result:
        return result
    
    # 原有解析逻辑...
    result = original_parse_logic()
    
    await cache_set(cache_key, result, ttl=86400)
    return result
```

### 模型管理集成
```python
# markio/utils/model_manager.py
from markio.utils import cache_get, cache_set

async def load_model_with_cache(model_name: str):
    cache_key = f"model:metadata:{model_name}"
    
    metadata = await cache_get(cache_key)
    if metadata:
        return metadata
    
    # 加载模型...
    metadata = load_model_metadata(model_name)
    
    await cache_set(cache_key, metadata, ttl=3600)
    return metadata
```

---

## ✅ 检查清单

### 开发环境设置

- [ ] 安装依赖：`uv sync` 或 `pip install -e .`
- [ ] 启动Redis：`docker-compose up -d redis`
- [ ] 配置 `.env`：`REDIS_ENABLED=true`
- [ ] 运行测试：`python tests/test_redis.py`

### 生产环境部署

- [ ] 设置Redis密码：`REDIS_PASSWORD`
- [ ] 配置网络隔离
- [ ] 设置合理的连接池大小
- [ ] 配置Redis持久化（AOF/RDB）
- [ ] 设置监控和告警
- [ ] 备份Redis数据

---

## 🎉 总结

Redis功能已完整集成到Markio项目：

| 维度 | 完成度 | 说明 |
|------|--------|------|
| **依赖配置** | ✅ 100% | pyproject.toml已更新 |
| **配置系统** | ✅ 100% | 9个配置项，详细文档 |
| **工具模块** | ✅ 100% | 完整的Redis工具类 |
| **Docker支持** | ✅ 100% | compose.yaml已配置 |
| **文档** | ✅ 100% | 3份详细文档 |
| **测试** | ✅ 100% | 完整测试套件 |
| **Parser集成** | ⏸️ 暂不实施 | 工具已就绪，可随时集成 |

**特点**：
- 🚀 开箱即用
- 📖 文档齐全
- 🧪 测试完整
- 🔧 易于扩展
- 🛡️ 容错设计
- ⚡ 高性能异步

**需要帮助？**
- 查看 [redis_usage_examples.md](./redis_usage_examples.md)
- 运行 `python tests/test_redis.py`
- 查看代码注释和类型提示

祝使用愉快！🎊
