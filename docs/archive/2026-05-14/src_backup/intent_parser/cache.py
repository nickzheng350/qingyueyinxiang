"""意图解析缓存 - 减少重复LLM调用"""

import hashlib
import logging
from typing import Optional
from functools import wraps

from src.cache import get_cache_manager

logger = logging.getLogger("hydraflow.intent_parser.cache")

_intent_cache_namespace = "intent_parse"
_cache_ttl = 3600


def _generate_cache_key(text: str, parser_name: str) -> str:
    """生成缓存键"""
    content = f"{parser_name}:{text.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()


def get_intent_cache(text: str, parser_name: str) -> Optional[dict]:
    """获取缓存的解析结果"""
    cache = get_cache_manager()
    key = _generate_cache_key(text, parser_name)
    cached = cache.get(key, namespace=_intent_cache_namespace)
    if cached:
        logger.debug(f"缓存命中: {text[:50]}... (parser={parser_name})")
    return cached


def set_intent_cache(text: str, parser_name: str, result: dict, ttl: int = _cache_ttl) -> None:
    """缓存解析结果"""
    cache = get_cache_manager()
    key = _generate_cache_key(text, parser_name)
    cache.set(key, result, namespace=_intent_cache_namespace, ttl=ttl)
    logger.debug(f"缓存设置: {text[:50]}... (parser={parser_name}, ttl={ttl}s)")


def clear_intent_cache() -> None:
    """清除意图解析缓存"""
    cache = get_cache_manager()
    cache.clear(namespace=_intent_cache_namespace)
    logger.info("意图解析缓存已清除")


def get_intent_cache_stats() -> dict:
    """获取缓存统计"""
    cache = get_cache_manager()
    all_stats = cache.get_all_stats()
    return all_stats.get(_intent_cache_namespace, {})


def intent_cacheable(ttl: int = _cache_ttl):
    """意图解析缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(text: str, parser_name: str, *args, **kwargs):
            cached_result = get_intent_cache(text, parser_name)
            if cached_result is not None:
                return cached_result

            result = func(text, parser_name, *args, **kwargs)
            if result:
                set_intent_cache(text, parser_name, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def should_cache_text(text: str) -> bool:
    """判断文本是否应该被缓存"""
    text_lower = text.lower().strip()

    if len(text_lower) < 3:
        return False

    if len(text_lower) > 500:
        return False

    cache_blacklist = [
        "test",
        "测试",
        "debug",
        "调试",
    ]
    for keyword in cache_blacklist:
        if keyword in text_lower:
            return False

    return True
