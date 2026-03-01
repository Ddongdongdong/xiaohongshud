"""
llm.py — 文案生成/改写
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import (
    GenerateTitlesRequest,
    RewriteContentRequest,
    CheckSimilarityRequest,
    OkResponse,
)
import scripts.llm_helper as llm

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/titles", response_model=OkResponse)
def generate_titles(req: GenerateTitlesRequest):
    """根据主题生成标题列表。"""
    try:
        titles = llm.generate_titles(topic=req.topic, n=req.n, style=req.style)
        return OkResponse(ok=True, data={"titles": titles})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite", response_model=OkResponse)
def rewrite_content(req: RewriteContentRequest):
    """改写内容。"""
    try:
        rewritten = llm.rewrite_content(original=req.original, style=req.style)
        return OkResponse(ok=True, data={"rewritten": rewritten})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity", response_model=OkResponse)
def check_similarity(req: CheckSimilarityRequest):
    """检测两段文本的相似度。"""
    try:
        score = llm.check_similarity(req.text_a, req.text_b)
        return OkResponse(ok=True, data={"similarity": score})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
