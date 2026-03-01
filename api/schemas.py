"""
schemas.py — Pydantic 请求/响应模型
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Browser / Login
# ---------------------------------------------------------------------------

class BrowserStartRequest(BaseModel):
    headless: bool = True
    port: int = Field(9222, ge=1024, le=65535)
    account: str | None = None


class BrowserStopRequest(BaseModel):
    port: int = Field(9222, ge=1024, le=65535)


class BrowserRestartRequest(BaseModel):
    headless: bool = True
    port: int = Field(9222, ge=1024, le=65535)
    account: str | None = None


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

class PublishImageRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    image_urls: list[str] = []
    images: list[str] = []          # 本地绝对路径
    auto_publish: bool = False
    headless: bool = True
    account: str | None = None


class PublishVideoRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    video: str | None = None        # 本地路径
    video_url: str | None = None
    auto_publish: bool = False
    headless: bool = True
    account: str | None = None


# ---------------------------------------------------------------------------
# Feeds / Search
# ---------------------------------------------------------------------------

class SearchFeedsQuery(BaseModel):
    keyword: str
    sort_by: str | None = None
    note_type: str | None = None
    publish_time: str | None = None


class PostCommentRequest(BaseModel):
    xsec_token: str
    content: str


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class AddAccountRequest(BaseModel):
    name: str
    alias: str | None = None


class DeleteAccountRequest(BaseModel):
    delete_profile: bool = False


# ---------------------------------------------------------------------------
# Metrics / Config
# ---------------------------------------------------------------------------

class MetricsConfigUpdate(BaseModel):
    hours_after_publish: int | None = Field(None, ge=1)
    min_exposure: int | None = Field(None, ge=0)
    min_ctr_pct: float | None = Field(None, ge=0.0, le=100.0)
    min_likes: int | None = Field(None, ge=0)
    min_collects: int | None = Field(None, ge=0)


# ---------------------------------------------------------------------------
# A/B Tests
# ---------------------------------------------------------------------------

class CreateABTestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_title: str = Field(..., min_length=1, max_length=100)
    base_content: str = Field(..., min_length=1)
    image_paths: list[str] | None = None
    n_variants: int = Field(3, ge=2, le=10)
    title_style: str | None = None
    content_style: str = Field("口语化", min_length=1)


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

class GenerateTitlesRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    n: int = Field(3, ge=1, le=10)
    style: str | None = None


class RewriteContentRequest(BaseModel):
    original: str
    style: str = "口语化"


class CheckSimilarityRequest(BaseModel):
    text_a: str
    text_b: str


# ---------------------------------------------------------------------------
# Generic response
# ---------------------------------------------------------------------------

class OkResponse(BaseModel):
    ok: bool = True
    message: str = ""
    data: Any = None
