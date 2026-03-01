"""
metrics.py — 数据监控、低效帖、手动抓取、阈值配置
"""

from __future__ import annotations

import pathlib

import yaml
from fastapi import APIRouter, HTTPException

from api.schemas import MetricsConfigUpdate, OkResponse
import scripts.db_manager as db

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

_CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "config" / "app_config.yaml"


def _load_yaml() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_yaml(data: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


@router.get("", response_model=OkResponse)
def get_metrics():
    """所有帖子最新指标。"""
    try:
        rows = db.get_latest_metrics()
        # Convert datetime objects to strings for JSON serialization
        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
        return OkResponse(ok=True, data=rows)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/low-perf", response_model=OkResponse)
def get_low_perf():
    """低效帖列表。"""
    try:
        rows = db.get_low_perf_notes()
        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
        return OkResponse(ok=True, data=rows)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch", response_model=OkResponse)
def trigger_fetch():
    """手动触发指标抓取（通过 Celery 任务）。"""
    try:
        # Lazy import to avoid hard dependency when Celery not configured
        from scripts.tasks import fetch_content_data
        task = fetch_content_data.delay()
        return OkResponse(ok=True, message="抓取任务已提交", data={"task_id": task.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发抓取失败: {e}")


@router.get("/config", response_model=OkResponse)
def get_config():
    """读取监控阈值配置。"""
    try:
        cfg = _load_yaml()
        return OkResponse(ok=True, data=cfg.get("monitoring", {}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=OkResponse)
def update_config(req: MetricsConfigUpdate):
    """更新监控阈值配置。"""
    try:
        cfg = _load_yaml()
        thresholds = cfg.setdefault("monitoring", {}).setdefault("thresholds", {})

        updates = req.model_dump(exclude_none=True)
        for key, value in updates.items():
            thresholds[key] = value

        _save_yaml(cfg)
        return OkResponse(ok=True, message="配置已更新", data=thresholds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
