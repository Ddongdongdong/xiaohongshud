"""
browser.py — 浏览器启停、登录检测
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_publisher
from api.schemas import BrowserStartRequest, BrowserStopRequest, BrowserRestartRequest, OkResponse
from scripts.cdp_publish import XiaohongshuPublisher
from scripts.chrome_launcher import ensure_chrome, kill_chrome, restart_chrome

router = APIRouter(prefix="/api", tags=["browser"])


@router.post("/browser/start", response_model=OkResponse)
def browser_start(req: BrowserStartRequest):
    """启动 Chrome（带 CDP 调试端口）。"""
    try:
        ensure_chrome(headless=req.headless, port=req.port, account=req.account)
        return OkResponse(ok=True, message=f"Chrome 已在端口 {req.port} 启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/browser/stop", response_model=OkResponse)
def browser_stop(req: BrowserStopRequest):
    """关闭 Chrome。"""
    try:
        kill_chrome(port=req.port)
        return OkResponse(ok=True, message=f"Chrome（端口 {req.port}）已关闭")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/browser/restart", response_model=OkResponse)
def browser_restart(req: BrowserRestartRequest):
    """重启 Chrome。"""
    try:
        restart_chrome(headless=req.headless, port=req.port, account=req.account)
        return OkResponse(ok=True, message=f"Chrome（端口 {req.port}）已重启")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login/status", response_model=OkResponse)
def login_status(publisher: XiaohongshuPublisher = Depends(get_publisher)):
    """检查创作者中心登录态。"""
    try:
        logged_in = publisher.check_login()
        return OkResponse(ok=True, data={"logged_in": logged_in})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login/home-status", response_model=OkResponse)
def login_home_status(publisher: XiaohongshuPublisher = Depends(get_publisher)):
    """检查主页登录态。"""
    try:
        logged_in = publisher.check_home_login()
        return OkResponse(ok=True, data={"logged_in": logged_in})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=OkResponse)
def open_login(publisher: XiaohongshuPublisher = Depends(get_publisher)):
    """打开登录页（扫码登录）。"""
    try:
        publisher.open_login_page()
        return OkResponse(ok=True, message="已打开登录页，请在浏览器中扫码")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
