"""
accounts.py — 账号 CRUD
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import AddAccountRequest, DeleteAccountRequest, OkResponse
from scripts.account_manager import (
    list_accounts,
    add_account,
    remove_account,
    set_default_account,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=OkResponse)
def get_accounts():
    """列出所有账号。"""
    try:
        accounts = list_accounts()
        return OkResponse(ok=True, data=accounts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=OkResponse)
def create_account(req: AddAccountRequest):
    """添加新账号。"""
    try:
        ok = add_account(name=req.name, alias=req.alias)
        if not ok:
            raise HTTPException(status_code=409, detail=f"账号 '{req.name}' 已存在")
        return OkResponse(ok=True, message=f"账号 '{req.name}' 已添加")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=OkResponse)
def delete_account(name: str, delete_profile: bool = False):
    """删除账号。delete_profile=true 时同时删除 Chrome 配置文件。"""
    try:
        ok = remove_account(name=name, delete_profile=delete_profile)
        if not ok:
            raise HTTPException(status_code=404, detail=f"账号 '{name}' 不存在")
        return OkResponse(ok=True, message=f"账号 '{name}' 已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}/default", response_model=OkResponse)
def set_default(name: str):
    """设为默认账号。"""
    try:
        ok = set_default_account(name)
        if not ok:
            raise HTTPException(status_code=404, detail=f"账号 '{name}' 不存在")
        return OkResponse(ok=True, message=f"'{name}' 已设为默认账号")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
