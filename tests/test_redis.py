"""
Redis工具测试模块

测试Redis连接、缓存操作等功能
"""

import asyncio
from datetime import datetime

import pytest

from markio.utils import (
    RedisCache,
    cache_delete,
    cache_exists,
    cache_get,
    cache_set,
    get_redis_client,
    redis_manager,
)


@pytest.fixture(scope="module")
async def setup_redis():
    """初始化Redis连接"""
    await redis_manager.initialize()
    yield
    await redis_manager.close()


@pytest.mark.asyncio
async def test_redis_connection(setup_redis):
    """测试Redis连接"""
    async with get_redis_client() as redis:
        if redis:
            result = await redis.ping()
            assert result is True
            print("✅ Redis connection test passed")
        else:
            print("⚠️  Redis is disabled, skipping test")


@pytest.mark.asyncio
async def test_basic_cache_operations(setup_redis):
    """测试基本缓存操作"""
    # 设置缓存
    success = await cache_set("test:key1", "test_value", ttl=60)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    # 获取缓存
    value = await cache_get("test:key1")
    assert value == "test_value"
    print("✅ Basic cache set/get test passed")

    # 检查存在
    exists = await cache_exists("test:key1")
    assert exists is True

    # 删除缓存
    deleted = await cache_delete("test:key1")
    assert deleted is True

    # 验证删除
    exists = await cache_exists("test:key1")
    assert exists is False
    print("✅ Cache delete test passed")


@pytest.mark.asyncio
async def test_json_serialization(setup_redis):
    """测试JSON序列化"""
    test_data = {
        "name": "张三",
        "age": 25,
        "hobbies": ["reading", "coding"],
        "profile": {"city": "Beijing", "job": "Engineer"},
    }

    success = await cache_set("test:json", test_data, ttl=60)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    result = await cache_get("test:json")
    assert result == test_data
    print("✅ JSON serialization test passed")

    await cache_delete("test:json")


@pytest.mark.asyncio
async def test_pickle_serialization(setup_redis):
    """测试Pickle序列化"""
    test_data = {
        "timestamp": datetime.now(),
        "data": [1, 2, 3, 4, 5],
    }

    success = await RedisCache.set("test:pickle", test_data, ttl=60, use_pickle=True)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    result = await RedisCache.get("test:pickle", use_pickle=True)
    assert isinstance(result["timestamp"], datetime)
    assert result["data"] == [1, 2, 3, 4, 5]
    print("✅ Pickle serialization test passed")

    await cache_delete("test:pickle")


@pytest.mark.asyncio
async def test_batch_operations(setup_redis):
    """测试批量操作"""
    data = {
        "test:batch:1": "value1",
        "test:batch:2": "value2",
        "test:batch:3": "value3",
    }

    # 批量设置
    success = await RedisCache.mset(data)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    # 批量获取
    keys = list(data.keys())
    results = await RedisCache.mget(keys)

    assert len(results) == 3
    assert results["test:batch:1"] == "value1"
    assert results["test:batch:2"] == "value2"
    print("✅ Batch operations test passed")

    # 清理
    for key in keys:
        await cache_delete(key)


@pytest.mark.asyncio
async def test_ttl_operations(setup_redis):
    """测试TTL操作"""
    success = await cache_set("test:ttl", "value", ttl=10)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    # 获取TTL
    ttl = await RedisCache.get_ttl("test:ttl")
    assert 0 < ttl <= 10
    print(f"✅ TTL test passed (TTL: {ttl}s)")

    # 更新TTL
    updated = await RedisCache.expire("test:ttl", 20)
    assert updated is True

    new_ttl = await RedisCache.get_ttl("test:ttl")
    assert 10 < new_ttl <= 20
    print(f"✅ TTL update test passed (New TTL: {new_ttl}s)")

    await cache_delete("test:ttl")


@pytest.mark.asyncio
async def test_increment_decrement(setup_redis):
    """测试原子计数器"""
    # 递增
    value = await RedisCache.increment("test:counter", 1)
    if value is None:
        print("⚠️  Redis is disabled, skipping test")
        return

    assert value == 1

    value = await RedisCache.increment("test:counter", 5)
    assert value == 6
    print("✅ Increment test passed")

    # 递减
    value = await RedisCache.decrement("test:counter", 2)
    assert value == 4
    print("✅ Decrement test passed")

    await cache_delete("test:counter")


@pytest.mark.asyncio
async def test_pattern_operations(setup_redis):
    """测试模式匹配操作"""
    # 设置测试数据
    test_keys = {
        "pattern:user:1": "user1",
        "pattern:user:2": "user2",
        "pattern:product:1": "product1",
    }

    success = await RedisCache.mset(test_keys)
    if not success:
        print("⚠️  Redis is disabled, skipping test")
        return

    # 查找用户键
    user_keys = await RedisCache.keys_pattern("pattern:user:*", limit=10)
    assert len(user_keys) == 2
    print(f"✅ Pattern match test passed (Found: {user_keys})")

    # 删除用户键
    deleted_count = await RedisCache.delete_pattern("pattern:user:*")
    assert deleted_count == 2
    print(f"✅ Pattern delete test passed (Deleted: {deleted_count})")

    # 清理剩余数据
    await RedisCache.delete_pattern("pattern:*")


@pytest.mark.asyncio
async def test_redis_client_direct(setup_redis):
    """测试直接使用Redis客户端"""
    async with get_redis_client() as redis:
        if not redis:
            print("⚠️  Redis is disabled, skipping test")
            return

        # 使用原生Redis命令
        await redis.set("test:direct", "direct_value")
        value = await redis.get("test:direct")
        assert value == b"direct_value"
        print("✅ Direct Redis client test passed")

        # 使用HASH操作
        await redis.hset("test:hash", "field1", "value1")
        await redis.hset("test:hash", "field2", "value2")

        hash_value = await redis.hget("test:hash", "field1")
        assert hash_value == b"value1"
        print("✅ Redis HASH operations test passed")

        # 清理
        await redis.delete("test:direct", "test:hash")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 Starting Redis Tests")
    print("=" * 60 + "\n")

    # 初始化Redis
    await redis_manager.initialize()

    if not redis_manager.is_available:
        print("⚠️  Redis is not enabled or not available")
        print("   Please set REDIS_ENABLED=true in .env file")
        return

    try:
        await test_redis_connection(None)
        await test_basic_cache_operations(None)
        await test_json_serialization(None)
        await test_pickle_serialization(None)
        await test_batch_operations(None)
        await test_ttl_operations(None)
        await test_increment_decrement(None)
        await test_pattern_operations(None)
        await test_redis_client_direct(None)

        print("\n" + "=" * 60)
        print("✅ All Redis tests passed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await redis_manager.close()


if __name__ == "__main__":
    asyncio.run(run_all_tests())

