"""
Redis工具模块

提供Redis连接管理、缓存操作、序列化等功能。
支持异步操作，适配FastAPI应用。

主要功能:
1. 连接池管理 - 自动管理Redis连接池生命周期
2. 缓存操作 - 提供常用的缓存CRUD操作
3. 智能序列化 - 自动处理JSON/Pickle序列化
4. 批量操作 - 支持批量设置和获取
5. 模式匹配 - 支持键名模式匹配查询
"""

import json
import pickle
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


class RedisManager:
    """
    Redis连接管理器
    
    采用单例模式,全局复用连接池。
    支持异步上下文管理器,自动处理连接生命周期。
    """

    _instance = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """
        初始化Redis连接池
        
        根据配置创建连接池和客户端实例。
        仅在首次调用时执行初始化。
        """
        if self._pool is not None:
            logger.debug("Redis connection pool already initialized")
            return

        if not settings.redis_enabled:
            logger.info("Redis is disabled in configuration")
            return

        try:
            # 构建Redis连接URL
            password_part = (
                f":{settings.redis_password}@" if settings.redis_password else ""
            )
            redis_url = (
                f"redis://{password_part}{settings.redis_host}:"
                f"{settings.redis_port}/{settings.redis_db}"
            )

            # 创建连接池
            self._pool = ConnectionPool.from_url(
                redis_url,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                decode_responses=False,  # 我们将手动处理编码
            )

            # 创建Redis客户端
            self._client = Redis(connection_pool=self._pool)

            # 测试连接
            await self._client.ping()
            logger.info(
                f"Redis connection pool initialized successfully: "
                f"{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            self._pool = None
            self._client = None
            raise

    async def close(self) -> None:
        """
        关闭Redis连接池
        
        释放所有连接资源。
        应在应用关闭时调用。
        """
        if self._client:
            await self._client.close()
            logger.info("Redis client closed")

        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis connection pool closed")

        self._client = None
        self._pool = None

    @property
    def client(self) -> Optional[Redis]:
        """获取Redis客户端实例"""
        if not settings.redis_enabled:
            return None
        return self._client

    @property
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return settings.redis_enabled and self._client is not None


# 全局Redis管理器实例
redis_manager = RedisManager()


@asynccontextmanager
async def get_redis_client():
    """
    获取Redis客户端的上下文管理器
    
    用法:
        async with get_redis_client() as redis:
            if redis:
                await redis.set("key", "value")
    
    Yields:
        Optional[Redis]: Redis客户端实例,如果未启用则返回None
    """
    if not redis_manager.is_available:
        yield None
        return

    try:
        yield redis_manager.client
    except Exception as e:
        logger.error(f"Error using Redis client: {e}")
        raise


class RedisCache:
    """
    Redis缓存操作类
    
    提供高级缓存操作接口,自动处理序列化、TTL等。
    """

    @staticmethod
    def _serialize(value: Any, use_pickle: bool = False) -> bytes:
        """
        序列化值
        
        Args:
            value: 要序列化的值
            use_pickle: 是否使用pickle序列化(默认使用JSON)
        
        Returns:
            bytes: 序列化后的字节数据
        """
        try:
            if use_pickle:
                return pickle.dumps(value)
            else:
                # 尝试JSON序列化
                return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError):
            # JSON序列化失败,回退到pickle
            logger.debug(f"JSON serialization failed, using pickle for value: {type(value)}")
            return pickle.dumps(value)

    @staticmethod
    def _deserialize(value: bytes, use_pickle: bool = False) -> Any:
        """
        反序列化值
        
        Args:
            value: 序列化的字节数据
            use_pickle: 是否使用pickle反序列化
        
        Returns:
            Any: 反序列化后的值
        """
        if value is None:
            return None

        try:
            if use_pickle:
                return pickle.loads(value)
            else:
                # 尝试JSON反序列化
                return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # JSON反序列化失败,尝试pickle
            try:
                return pickle.loads(value)
            except Exception as e:
                logger.error(f"Failed to deserialize value: {e}")
                return None

    @staticmethod
    async def set(
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_pickle: bool = False,
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒),None表示使用默认值
            use_pickle: 是否使用pickle序列化
        
        Returns:
            bool: 是否设置成功
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                serialized_value = RedisCache._serialize(value, use_pickle)
                expire_time = ttl if ttl is not None else settings.redis_default_ttl

                await redis.set(key, serialized_value, ex=expire_time)
                logger.debug(f"Cache set: {key} (TTL: {expire_time}s)")
                return True

            except Exception as e:
                logger.error(f"Failed to set cache for key '{key}': {e}")
                return False

    @staticmethod
    async def get(key: str, use_pickle: bool = False) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            use_pickle: 是否使用pickle反序列化
        
        Returns:
            Optional[Any]: 缓存值,不存在或过期返回None
        """
        async with get_redis_client() as redis:
            if not redis:
                return None

            try:
                value = await redis.get(key)
                if value is None:
                    logger.debug(f"Cache miss: {key}")
                    return None

                logger.debug(f"Cache hit: {key}")
                return RedisCache._deserialize(value, use_pickle)

            except Exception as e:
                logger.error(f"Failed to get cache for key '{key}': {e}")
                return None

    @staticmethod
    async def delete(key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否删除成功
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                result = await redis.delete(key)
                if result > 0:
                    logger.debug(f"Cache deleted: {key}")
                    return True
                return False

            except Exception as e:
                logger.error(f"Failed to delete cache for key '{key}': {e}")
                return False

    @staticmethod
    async def exists(key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否存在
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                result = await redis.exists(key)
                return result > 0

            except Exception as e:
                logger.error(f"Failed to check existence for key '{key}': {e}")
                return False

    @staticmethod
    async def expire(key: str, ttl: int) -> bool:
        """
        设置缓存键的过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间(秒)
        
        Returns:
            bool: 是否设置成功
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                result = await redis.expire(key, ttl)
                if result:
                    logger.debug(f"TTL updated for '{key}': {ttl}s")
                return result

            except Exception as e:
                logger.error(f"Failed to set expire for key '{key}': {e}")
                return False

    @staticmethod
    async def get_ttl(key: str) -> int:
        """
        获取缓存键的剩余过期时间
        
        Args:
            key: 缓存键
        
        Returns:
            int: 剩余秒数,-1表示永不过期,-2表示键不存在
        """
        async with get_redis_client() as redis:
            if not redis:
                return -2

            try:
                return await redis.ttl(key)

            except Exception as e:
                logger.error(f"Failed to get TTL for key '{key}': {e}")
                return -2

    @staticmethod
    async def mset(mapping: Dict[str, Any], use_pickle: bool = False) -> bool:
        """
        批量设置缓存值
        
        Args:
            mapping: 键值对字典
            use_pickle: 是否使用pickle序列化
        
        Returns:
            bool: 是否设置成功
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                serialized_mapping = {
                    k: RedisCache._serialize(v, use_pickle) for k, v in mapping.items()
                }
                await redis.mset(serialized_mapping)
                logger.debug(f"Batch cache set: {len(mapping)} items")
                return True

            except Exception as e:
                logger.error(f"Failed to batch set cache: {e}")
                return False

    @staticmethod
    async def mget(keys: List[str], use_pickle: bool = False) -> Dict[str, Any]:
        """
        批量获取缓存值
        
        Args:
            keys: 缓存键列表
            use_pickle: 是否使用pickle反序列化
        
        Returns:
            Dict[str, Any]: 键值对字典,不存在的键会被忽略
        """
        async with get_redis_client() as redis:
            if not redis:
                return {}

            try:
                values = await redis.mget(keys)
                result = {}

                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = RedisCache._deserialize(value, use_pickle)

                logger.debug(f"Batch cache get: {len(result)}/{len(keys)} items found")
                return result

            except Exception as e:
                logger.error(f"Failed to batch get cache: {e}")
                return {}

    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """
        根据模式删除缓存键
        
        Args:
            pattern: 键名模式 (支持通配符 *, ?)
                     例: "user:*", "cache:prefix:*"
        
        Returns:
            int: 删除的键数量
        """
        async with get_redis_client() as redis:
            if not redis:
                return 0

            try:
                # 使用SCAN而不是KEYS,避免阻塞
                cursor = 0
                deleted_count = 0

                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)

                    if keys:
                        deleted = await redis.delete(*keys)
                        deleted_count += deleted

                    if cursor == 0:
                        break

                logger.info(f"Pattern delete '{pattern}': {deleted_count} keys removed")
                return deleted_count

            except Exception as e:
                logger.error(f"Failed to delete pattern '{pattern}': {e}")
                return 0

    @staticmethod
    async def keys_pattern(pattern: str, limit: int = 1000) -> List[str]:
        """
        根据模式获取缓存键列表
        
        Args:
            pattern: 键名模式 (支持通配符 *, ?)
            limit: 最大返回数量
        
        Returns:
            List[str]: 匹配的键列表
        """
        async with get_redis_client() as redis:
            if not redis:
                return []

            try:
                cursor = 0
                keys_list = []

                while len(keys_list) < limit:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)

                    # 将字节转换为字符串
                    decoded_keys = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
                    keys_list.extend(decoded_keys)

                    if cursor == 0:
                        break

                result = keys_list[:limit]
                logger.debug(f"Pattern match '{pattern}': {len(result)} keys found")
                return result

            except Exception as e:
                logger.error(f"Failed to get keys for pattern '{pattern}': {e}")
                return []

    @staticmethod
    async def increment(key: str, amount: int = 1) -> Optional[int]:
        """
        原子递增操作
        
        Args:
            key: 缓存键
            amount: 递增量(默认1)
        
        Returns:
            Optional[int]: 递增后的值,失败返回None
        """
        async with get_redis_client() as redis:
            if not redis:
                return None

            try:
                result = await redis.incrby(key, amount)
                logger.debug(f"Incremented '{key}' by {amount} -> {result}")
                return result

            except Exception as e:
                logger.error(f"Failed to increment key '{key}': {e}")
                return None

    @staticmethod
    async def decrement(key: str, amount: int = 1) -> Optional[int]:
        """
        原子递减操作
        
        Args:
            key: 缓存键
            amount: 递减量(默认1)
        
        Returns:
            Optional[int]: 递减后的值,失败返回None
        """
        async with get_redis_client() as redis:
            if not redis:
                return None

            try:
                result = await redis.decrby(key, amount)
                logger.debug(f"Decremented '{key}' by {amount} -> {result}")
                return result

            except Exception as e:
                logger.error(f"Failed to decrement key '{key}': {e}")
                return None

    @staticmethod
    async def clear_all() -> bool:
        """
        清空当前数据库的所有缓存
        
        ⚠️ 危险操作,谨慎使用!
        
        Returns:
            bool: 是否清空成功
        """
        async with get_redis_client() as redis:
            if not redis:
                return False

            try:
                await redis.flushdb()
                logger.warning("All cache cleared in current database")
                return True

            except Exception as e:
                logger.error(f"Failed to clear all cache: {e}")
                return False


# 便捷函数,直接使用
async def cache_set(
    key: str, value: Any, ttl: Optional[int] = None, use_pickle: bool = False
) -> bool:
    """快捷设置缓存"""
    return await RedisCache.set(key, value, ttl, use_pickle)


async def cache_get(key: str, use_pickle: bool = False) -> Optional[Any]:
    """快捷获取缓存"""
    return await RedisCache.get(key, use_pickle)


async def cache_delete(key: str) -> bool:
    """快捷删除缓存"""
    return await RedisCache.delete(key)


async def cache_exists(key: str) -> bool:
    """快捷检查缓存是否存在"""
    return await RedisCache.exists(key)

