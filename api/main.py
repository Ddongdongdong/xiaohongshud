"""
main.py — FastAPI 应用入口

启动：
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import pathlib
import sys

# 让 requests 不走系统代理访问 localhost/127.0.0.1（CDP 端口 9222）
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

# 确保项目根目录和 scripts/ 目录在 Python 路径中
_ROOT = pathlib.Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
for _p in [str(_ROOT), str(_SCRIPTS)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routers import browser, publish, feeds, accounts, metrics, ab_tests, llm

app = FastAPI(
    title="XiaohongshuSkills API",
    description="小红书技能管理后端 API",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — 允许前端开发服务器（localhost:5173）访问
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 全局异常处理 — 把未捕获异常的详情返回给客户端（便于调试）
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={"ok": False, "detail": str(exc), "traceback": tb},
    )


# ---------------------------------------------------------------------------
# 挂载路由
# ---------------------------------------------------------------------------
app.include_router(browser.router)
app.include_router(publish.router)
app.include_router(feeds.router)
app.include_router(accounts.router)
app.include_router(metrics.router)
app.include_router(ab_tests.router)
app.include_router(llm.router)


# ---------------------------------------------------------------------------
# 静态文件（构建后的前端）
# ---------------------------------------------------------------------------
_DIST = _ROOT / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/debug/cdp")
def debug_cdp():
    """调试：测试 CDP 连接和 NO_PROXY 环境变量。"""
    import os as _os
    no_proxy = _os.environ.get("NO_PROXY", "NOT SET")
    no_proxy2 = _os.environ.get("no_proxy", "NOT SET")
    try:
        import requests as _req
        resp = _req.get("http://127.0.0.1:9222/json", timeout=5)
        tabs = len(resp.json())
        return {"ok": True, "NO_PROXY": no_proxy, "no_proxy": no_proxy2, "chrome_tabs": tabs}
    except Exception as e:
        return {"ok": False, "NO_PROXY": no_proxy, "no_proxy": no_proxy2, "error": str(e)}
