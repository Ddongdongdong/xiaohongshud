"""
ab_tests.py — A/B 测试管理
"""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from api.schemas import CreateABTestRequest, OkResponse
import scripts.db_manager as db
import scripts.ab_test_manager as ab

router = APIRouter(prefix="/api/ab-tests", tags=["ab_tests"])


class MarkPublishedRequest(BaseModel):
    note_id: str = Field(..., min_length=1)


def _serialize_rows(rows: list[dict]) -> list[dict]:
    """Convert datetime objects to ISO strings."""
    result = []
    for row in rows:
        r = {}
        for k, v in row.items():
            r[k] = v.isoformat() if hasattr(v, "isoformat") else v
        result.append(r)
    return result


@router.get("", response_model=OkResponse)
def list_tests():
    """列出所有 A/B 测试。"""
    try:
        tests = db.list_ab_tests()
        return OkResponse(ok=True, data=_serialize_rows(tests))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=OkResponse)
def create_test(req: CreateABTestRequest):
    """创建 A/B 测试（LLM 自动生成变体）。"""
    try:
        test_id = ab.create_test_from_llm(
            name=req.name,
            base_title=req.base_title,
            base_content=req.base_content,
            image_paths=req.image_paths,
            n_variants=req.n_variants,
            title_style=req.title_style,
            content_style=req.content_style,
        )
        return OkResponse(ok=True, message="A/B 测试已创建", data={"test_id": test_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}/variants", response_model=OkResponse)
def get_variants(test_id: int):
    """获取测试组变体列表（含指标）。"""
    try:
        variants = db.get_ab_summary(test_id)
        return OkResponse(ok=True, data=_serialize_rows(variants))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}/winner", response_model=OkResponse)
def pick_winner(test_id: int):
    """计算胜出变体。"""
    try:
        winner = ab.pick_winner(test_id)
        if winner is None:
            return OkResponse(ok=True, message="暂无足够数据判定胜者", data=None)
        return OkResponse(ok=True, data=_serialize_rows([winner])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{test_id}/variants/{variant_id}/publish", response_model=OkResponse)
def mark_published(test_id: int, variant_id: int, req: MarkPublishedRequest = Body(...)):
    """标记变体已发布。"""
    try:
        db.mark_variant_published(variant_id=variant_id, note_id=req.note_id)
        return OkResponse(ok=True, message=f"变体 {variant_id} 已标记为已发布")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
