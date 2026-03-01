"""
celery_app.py — Celery 实例定义

Windows 启动方式：
    # Worker（Windows 必须加 --pool=solo）
    celery -A scripts.celery_app worker --pool=solo --loglevel=info

    # Beat（定时调度）
    celery -A scripts.celery_app beat --loglevel=info
"""

import pathlib
import sys

import yaml
from celery import Celery

_ROOT = pathlib.Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config" / "app_config.yaml"

# 确保项目根目录在 sys.path，方便 tasks 等模块 import
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _load_cfg() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load_cfg()

app = Celery(
    "xhs",
    broker=_cfg["celery"]["broker"],
    backend=_cfg["celery"]["backend"],
    include=["scripts.tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    # Windows 兼容：禁用信号相关功能
    worker_pool="solo",
)
