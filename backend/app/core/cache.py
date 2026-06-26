"""
文件名: app/core/cache.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Redis 查询缓存装饰器，支持异步函数
入参: redis 客户端 / prefix / ttl / key_args
出参: 装饰后的函数
"""
import json
import functools
from app.core.logger import logger


def _build_key(prefix: str, key_args: list[str], kwargs: dict) -> str:
    """根据指定 kwargs 字段构造缓存键

    入参:
        prefix: 缓存前缀
        key_args: 参与缓存键的参数名列表
        kwargs: 函数调用 kwargs
    出参:
        缓存键字符串，如 "search:q=Java 5年:top_k=10"
    """
    parts = [prefix]
    for arg in key_args:
        parts.append(f"{arg}={kwargs.get(arg, '')}")
    return ":".join(parts)


def cached(redis, prefix: str, ttl: int = 300, key_args: list[str] | None = None):
    """异步函数缓存装饰器

    入参:
        redis: Redis 客户端（async）
        prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_args: 参与缓存键的参数名列表
    出参:
        装饰后的异步函数
    """
    key_args = key_args or []

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            cache_key = _build_key(prefix, key_args, kwargs)
            if redis is not None:
                try:
                    cached_value = await redis.get(cache_key)
                    if cached_value:
                        logger.debug(f"缓存命中: {cache_key}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"缓存读取失败: {e}")

            result = await fn(*args, **kwargs)

            if redis is not None:
                try:
                    await redis.setex(cache_key, ttl, json.dumps(result, ensure_ascii=False, default=str))
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")
            return result
        return wrapper
    return decorator
