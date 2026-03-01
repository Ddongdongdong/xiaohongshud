"""
tasks.py — Celery 定时任务

任务列表：
  fetch_content_data   — 抓取笔记指标并写入 MySQL + Redis
  check_low_perf       — 识别低效帖并输出告警

手动触发（测试用，不需要 Worker）：
    python scripts/tasks.py fetch
    python scripts/tasks.py low-perf
"""

from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import yaml
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

from scripts.celery_app import app
import scripts.db_manager as db
import scripts.cache_manager as cache

_CONFIG_PATH = _ROOT / "config" / "app_config.yaml"


def _load_cfg() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# 任务：抓取 content-data 并写入存储
# ---------------------------------------------------------------------------

@app.task(name="tasks.fetch_content_data", bind=True, max_retries=3)
def fetch_content_data(self):
    """
    调用 XiaohongshuPublisher.get_content_data()，
    将结果写入 MySQL（note_metrics）并更新 Redis 缓存。
    """
    print("[task] fetch_content_data: 开始抓取...")
    try:
        # 延迟导入，避免在 Worker 启动时连接 Chrome
        from scripts.cdp_publish import XiaohongshuPublisher

        cfg = _load_cfg()
        publisher = XiaohongshuPublisher()
        publisher.connect()

        result = publisher.get_content_data()
        publisher.disconnect()

        rows = result.get("rows", [])
        if not rows:
            print("[task] fetch_content_data: 无数据返回")
            return {"status": "empty"}

        # 写入 MySQL
        written = db.save_metrics(rows)
        print(f"[task] fetch_content_data: 写入 {written} 条记录到 MySQL")

        # 更新 Redis 缓存
        cache.set_content_data_cache(result)
        print("[task] fetch_content_data: 已更新 Redis 缓存")

        return {"status": "ok", "written": written, "total": result.get("total", 0)}

    except Exception as exc:
        print(f"[task] fetch_content_data 失败: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ---------------------------------------------------------------------------
# 任务：识别低效帖
# ---------------------------------------------------------------------------

@app.task(name="tasks.check_low_perf", bind=True)
def check_low_perf(self):
    """
    从 MySQL 查询低效帖，打印告警并更新 Redis 缓存。
    """
    print("[task] check_low_perf: 开始检测...")
    try:
        cfg = _load_cfg()
        threshold_cfg = cfg["monitoring"]["thresholds"]

        low_perf = db.get_low_perf_notes(threshold_cfg)

        if not low_perf:
            print("[task] check_low_perf: 无低效帖")
            cache.set_low_perf_cache([])
            return {"status": "ok", "count": 0}

        note_ids = [r["note_id"] for r in low_perf]
        cache.set_low_perf_cache(note_ids)

        print(f"[task] check_low_perf: 发现 {len(low_perf)} 条低效帖")
        for row in low_perf:
            print(
                f"  - [{row['note_id']}] {row.get('title','')[:20]} "
                f"| 曝光={row.get('exposure',0)} "
                f"| 点击率={row.get('ctr',0):.1f}% "
                f"| 点赞={row.get('likes',0)} "
                f"| 收藏={row.get('collects',0)}"
            )

        return {"status": "ok", "count": len(low_perf), "note_ids": note_ids}

    except Exception as exc:
        print(f"[task] check_low_perf 失败: {exc}")
        raise


# ---------------------------------------------------------------------------
# Beat 定时调度
# ---------------------------------------------------------------------------

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    cfg = _load_cfg()["monitoring"]
    fetch_hours = int(cfg.get("fetch_interval_hours", 6))
    check_hours = int(cfg.get("low_perf_check_hours", 24))

    sender.add_periodic_task(
        timedelta(hours=fetch_hours),
        fetch_content_data.s(),
        name=f"每 {fetch_hours} 小时抓取笔记指标",
    )
    sender.add_periodic_task(
        timedelta(hours=check_hours),
        check_low_perf.s(),
        name=f"每 {check_hours} 小时检测低效帖",
    )
    print(f"[beat] 已注册: 每 {fetch_hours}h 抓取 / 每 {check_hours}h 检测低效帖")


# ---------------------------------------------------------------------------
# CLI 手动触发（不需要 Worker）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "fetch":
        print("手动触发 fetch_content_data...")
        fetch_content_data()

    elif cmd in ("low-perf", "low_perf"):
        print("手动触发 check_low_perf...")
        check_low_perf()

    else:
        print("用法:")
        print("  python scripts/tasks.py fetch       # 手动抓取笔记数据")
        print("  python scripts/tasks.py low-perf    # 手动检测低效帖")
