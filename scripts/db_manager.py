"""
db_manager.py — MySQL 建表与 CRUD 操作

使用前请先在 config/app_config.yaml 填写数据库连接信息。
手动初始化建表：
    python scripts/db_manager.py
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timedelta
from typing import Any

import pymysql
import yaml

_ROOT = pathlib.Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config" / "app_config.yaml"


def _load_cfg() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _connect() -> pymysql.Connection:
    cfg = _load_cfg()["database"]
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg.get("password", ""),
        database=cfg["db"],
        charset="utf8mb4",
        autocommit=True,
    )


# ---------------------------------------------------------------------------
# 建表
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS note_metrics (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    note_id      VARCHAR(64)  NOT NULL,
    title        VARCHAR(255),
    publish_time DATETIME,
    exposure     INT     DEFAULT 0,
    views        INT     DEFAULT 0,
    ctr          FLOAT   DEFAULT 0,
    likes        INT     DEFAULT 0,
    comments     INT     DEFAULT 0,
    collects     INT     DEFAULT 0,
    shares       INT     DEFAULT 0,
    followers    INT     DEFAULT 0,
    fetched_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_note_id  (note_id),
    INDEX idx_fetched  (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ab_tests (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    status     ENUM('active','completed','cancelled') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ab_variants (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    test_id      INT          NOT NULL,
    title        VARCHAR(255),
    content      TEXT,
    image_paths  TEXT,
    note_id      VARCHAR(64),
    publish_time DATETIME,
    status       ENUM('pending','published','failed') DEFAULT 'pending',
    FOREIGN KEY (test_id) REFERENCES ab_tests(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def init_db() -> None:
    """建表（幂等）。"""
    conn = _connect()
    with conn.cursor() as cur:
        for stmt in _DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
    conn.close()
    print("[db] Tables initialized.")


# ---------------------------------------------------------------------------
# note_metrics
# ---------------------------------------------------------------------------

def _parse_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.replace(",", "").strip()
        try:
            return int(v)
        except ValueError:
            return 0
    return 0


def _parse_float(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.replace("%", "").replace(",", "").strip()
        try:
            return float(v)
        except ValueError:
            return 0.0
    return 0.0


def _parse_datetime(v: Any) -> str | None:
    if not v:
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
    return None


def save_metrics(rows: list[dict]) -> int:
    """
    把 content-data 返回的 rows 批量写入 note_metrics。
    返回写入行数。
    """
    if not rows:
        return 0
    sql = """
        INSERT INTO note_metrics
            (note_id, title, publish_time, exposure, views, ctr,
             likes, comments, collects, shares, followers)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = _connect()
    written = 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(sql, (
                row.get("_id") or row.get("note_id", ""),
                row.get("标题") or row.get("title", ""),
                _parse_datetime(row.get("发布时间") or row.get("publish_time")),
                _parse_int(row.get("曝光") or row.get("exposure", 0)),
                _parse_int(row.get("观看") or row.get("views", 0)),
                _parse_float(row.get("封面点击率") or row.get("ctr", 0)),
                _parse_int(row.get("点赞") or row.get("likes", 0)),
                _parse_int(row.get("评论") or row.get("comments", 0)),
                _parse_int(row.get("收藏") or row.get("collects", 0)),
                _parse_int(row.get("分享") or row.get("shares", 0)),
                _parse_int(row.get("涨粉") or row.get("followers", 0)),
            ))
            written += 1
    conn.close()
    return written


def get_latest_metrics() -> list[dict]:
    """每个 note_id 取最新一条指标记录。"""
    sql = """
        SELECT n1.*
        FROM note_metrics n1
        INNER JOIN (
            SELECT note_id, MAX(fetched_at) AS max_fetched
            FROM note_metrics
            GROUP BY note_id
        ) n2 ON n1.note_id = n2.note_id AND n1.fetched_at = n2.max_fetched
        ORDER BY n1.fetched_at DESC
    """
    conn = _connect()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_low_perf_notes(cfg: dict | None = None) -> list[dict]:
    """
    按阈值查询低效帖（取每帖最新指标）。
    cfg 若为 None 则从 app_config.yaml 读取。
    """
    if cfg is None:
        cfg = _load_cfg()["monitoring"]["thresholds"]

    hours = int(cfg.get("hours_after_publish", 24))
    min_exposure = int(cfg.get("min_exposure", 500))
    min_ctr = float(cfg.get("min_ctr_pct", 5.0))
    min_likes = int(cfg.get("min_likes", 10))
    min_collects = int(cfg.get("min_collects", 5))

    cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        SELECT n1.*
        FROM note_metrics n1
        INNER JOIN (
            SELECT note_id, MAX(fetched_at) AS max_fetched
            FROM note_metrics
            GROUP BY note_id
        ) n2 ON n1.note_id = n2.note_id AND n1.fetched_at = n2.max_fetched
        WHERE n1.publish_time IS NOT NULL
          AND n1.publish_time <= %s
          AND (
              n1.exposure  < %s OR
              n1.ctr       < %s OR
              n1.likes     < %s OR
              n1.collects  < %s
          )
        ORDER BY n1.exposure ASC
    """
    conn = _connect()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, (cutoff, min_exposure, min_ctr, min_likes, min_collects))
        rows = cur.fetchall()
    conn.close()
    return list(rows)


# ---------------------------------------------------------------------------
# A/B 测试
# ---------------------------------------------------------------------------

def create_ab_test(name: str) -> int:
    """创建测试组，返回 test_id。"""
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO ab_tests (name) VALUES (%s)", (name,))
        test_id = cur.lastrowid
    conn.close()
    return test_id


def add_ab_variant(
    test_id: int,
    title: str,
    content: str,
    image_paths: list[str] | None = None,
) -> int:
    """添加变体，返回 variant_id。"""
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ab_variants (test_id, title, content, image_paths) VALUES (%s,%s,%s,%s)",
            (test_id, title, content, json.dumps(image_paths or [], ensure_ascii=False)),
        )
        variant_id = cur.lastrowid
    conn.close()
    return variant_id


def mark_variant_published(variant_id: int, note_id: str) -> None:
    """标记变体已发布并记录笔记 ID。"""
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ab_variants SET status='published', note_id=%s, publish_time=NOW() WHERE id=%s",
            (note_id, variant_id),
        )
    conn.close()


def mark_variant_failed(variant_id: int) -> None:
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute("UPDATE ab_variants SET status='failed' WHERE id=%s", (variant_id,))
    conn.close()


def get_ab_variants(test_id: int) -> list[dict]:
    """获取测试组下所有变体。"""
    conn = _connect()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM ab_variants WHERE test_id=%s ORDER BY id", (test_id,))
        rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_ab_summary(test_id: int) -> list[dict]:
    """
    返回各变体的最新指标（LEFT JOIN note_metrics）。
    """
    sql = """
        SELECT
            v.id AS variant_id,
            v.title,
            v.status,
            v.note_id,
            v.publish_time,
            m.exposure, m.views, m.ctr,
            m.likes, m.comments, m.collects,
            m.shares, m.followers,
            m.fetched_at
        FROM ab_variants v
        LEFT JOIN note_metrics m
            ON m.note_id = v.note_id
            AND m.fetched_at = (
                SELECT MAX(fetched_at) FROM note_metrics WHERE note_id = v.note_id
            )
        WHERE v.test_id = %s
        ORDER BY v.id
    """
    conn = _connect()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, (test_id,))
        rows = cur.fetchall()
    conn.close()
    return list(rows)


def list_ab_tests() -> list[dict]:
    conn = _connect()
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM ab_tests ORDER BY id DESC")
        rows = cur.fetchall()
    conn.close()
    return list(rows)


# ---------------------------------------------------------------------------
# CLI 入口（手动建表）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print("[db] Done.")
