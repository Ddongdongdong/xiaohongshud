"""
deps.py — 公共依赖（publisher 实例获取）

每次请求独立创建 publisher，用完即断，避免 CDP 连接复用冲突。
"""

from __future__ import annotations

import pathlib
import sys
from typing import Generator

from fastapi import HTTPException, Query

from scripts.cdp_publish import XiaohongshuPublisher


def get_publisher(
    host: str = Query(default="127.0.0.1"),
    port: int = Query(default=9222),
    account: str | None = Query(default=None),
) -> Generator[XiaohongshuPublisher, None, None]:
    """
    FastAPI 依赖：创建 publisher，连接，yield，最后断开。
    用法：
        publisher: XiaohongshuPublisher = Depends(get_publisher)
    """
    publisher = XiaohongshuPublisher(host=host, port=port, account_name=account)
    try:
        publisher.connect()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"无法连接 Chrome CDP：{e}")
    try:
        yield publisher
    finally:
        try:
            publisher.disconnect()
        except Exception:
            pass
