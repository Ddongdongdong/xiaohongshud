"""
feeds.py — 搜索、详情、评论、通知
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_publisher
from api.schemas import PostCommentRequest, OkResponse
from scripts.cdp_publish import XiaohongshuPublisher
from scripts.feed_explorer import SearchFilters

router = APIRouter(prefix="/api", tags=["feeds"])


@router.get("/feeds", response_model=OkResponse)
def search_feeds(
    keyword: str = Query(..., description="搜索关键词"),
    sort_by: str | None = Query(default=None),
    note_type: str | None = Query(default=None),
    publish_time: str | None = Query(default=None),
    publisher: XiaohongshuPublisher = Depends(get_publisher),
):
    """搜索小红书笔记。"""
    try:
        sf = None
        if sort_by or note_type or publish_time:
            sf = SearchFilters()
            if sort_by:
                sf.sort_by = sort_by
            if note_type:
                sf.note_type = note_type
            if publish_time:
                sf.publish_time = publish_time

        results = publisher.search_feeds(keyword=keyword, filters=sf)
        return OkResponse(ok=True, data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feeds/{feed_id}", response_model=OkResponse)
def get_feed_detail(
    feed_id: str,
    xsec_token: str = Query(..., description="xsec_token"),
    publisher: XiaohongshuPublisher = Depends(get_publisher),
):
    """获取笔记详情。"""
    try:
        detail = publisher.get_feed_detail(feed_id=feed_id, xsec_token=xsec_token)
        return OkResponse(ok=True, data=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feeds/{feed_id}/comment", response_model=OkResponse)
def post_comment(
    feed_id: str,
    req: PostCommentRequest,
    publisher: XiaohongshuPublisher = Depends(get_publisher),
):
    """对笔记发表评论。"""
    try:
        result = publisher.post_comment_to_feed(
            feed_id=feed_id,
            xsec_token=req.xsec_token,
            content=req.content,
        )
        return OkResponse(ok=True, message="评论已发表", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/mentions", response_model=OkResponse)
def get_mentions(
    publisher: XiaohongshuPublisher = Depends(get_publisher),
):
    """获取评论和@通知。"""
    try:
        mentions = publisher.get_notification_mentions()
        return OkResponse(ok=True, data=mentions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
