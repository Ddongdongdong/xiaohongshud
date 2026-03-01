"""
cache_manager.py — Redis 热数据缓存封装

依赖 config/app_config.yaml 中的 redis 配置。
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import redis
import yaml

_ROOT = pathlib.Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config" / "app_config.yaml"

# 默认 TTL（秒）
_METRICS_TTL = 3600       # 单帖指标缓存 1 小时
_LOW_PERF_TTL = 86400     # 低效帖列表缓存 24 小时
_CONTENT_DATA_TTL = 3600  # content-data 结果缓存 1 小时


def _load_cfg() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _client() -> redis.Redis:
    cfg = _load_cfg()["redis"]
    return redis.Redis(
        host=cfg.get("host", "localhost"),
        port=int(cfg.get("port", 6379)),
        db=int(cfg.get("db", 0)),
        decode_responses=True,
    )


# ---------------------------------------------------------------------------
# 单帖指标缓存
# ---------------------------------------------------------------------------

def set_metrics_cache(note_id: str, data: dict, ttl: int = _METRICS_TTL) -> None:
    key = f"xhs:metrics:{note_id}"
    _client().setex(key, ttl, json.dumps(data, ensure_ascii=False))


def get_metrics_cache(note_id: str) -> dict | None:
    key = f"xhs:metrics:{note_id}"
    val = _client().get(key)
    if val is None:
        return None
    return json.loads(val)


# ---------------------------------------------------------------------------
# 低效帖列表缓存
# ---------------------------------------------------------------------------

def set_low_perf_cache(note_ids: list[str], ttl: int = _LOW_PERF_TTL) -> None:
    key = "xhs:low_perf_notes"
    _client().setex(key, ttl, json.dumps(note_ids, ensure_ascii=False))


def get_low_perf_cache() -> list[str] | None:
    key = "xhs:low_perf_notes"
    val = _client().get(key)
    if val is None:
        return None
    return json.loads(val)


# ---------------------------------------------------------------------------
# content-data 整体结果缓存
# ---------------------------------------------------------------------------

def set_content_data_cache(data: Any, ttl: int = _CONTENT_DATA_TTL) -> None:
    key = "xhs:content_data"
    _client().setex(key, ttl, json.dumps(data, ensure_ascii=False, default=str))


def get_content_data_cache() -> Any | None:
    key = "xhs:content_data"
    val = _client().get(key)
    if val is None:
        return None
    return json.loads(val)


# ---------------------------------------------------------------------------
# 通用 Key-Value
# ---------------------------------------------------------------------------

def set_value(key: str, value: Any, ttl: int = 3600) -> None:
    _client().setex(f"xhs:{key}", ttl, json.dumps(value, ensure_ascii=False, default=str))


def get_value(key: str) -> Any | None:
    val = _client().get(f"xhs:{key}")
    if val is None:
        return None
    return json.loads(val)


def delete_value(key: str) -> None:
    _client().delete(f"xhs:{key}")
