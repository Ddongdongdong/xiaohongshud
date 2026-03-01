"""
publish.py — 图文/视频发布（通过子进程调用 publish_pipeline.py）
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

from fastapi import APIRouter, HTTPException

_ROOT = pathlib.Path(__file__).parent.parent.parent
_SCRIPTS = _ROOT / "scripts"

from api.schemas import PublishImageRequest, PublishVideoRequest, OkResponse

router = APIRouter(prefix="/api/publish", tags=["publish"])

_PIPELINE = str(_SCRIPTS / "publish_pipeline.py")


def _run_pipeline(args: list[str], timeout: int = 300) -> dict:
    """运行 publish_pipeline.py 子进程，返回解析后的输出。"""
    cmd = [sys.executable, _PIPELINE] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(_ROOT),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"发布超时（超过 {timeout} 秒），请检查浏览器状态")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "publish_pipeline 执行失败")
    return {"stdout": result.stdout, "stderr": result.stderr}


@router.post("/image", response_model=OkResponse)
def publish_image(req: PublishImageRequest):
    """发布图文笔记。"""
    args = [
        "--title", req.title,
        "--content", req.content,
    ]
    for url in req.image_urls:
        args += ["--image-url", url]
    for img in req.images:
        args += ["--images", img]
    if req.auto_publish:
        args.append("--auto-publish")
    if req.headless:
        args.append("--headless")
    if req.account:
        args += ["--account", req.account]

    try:
        out = _run_pipeline(args)
        return OkResponse(ok=True, message="图文发布成功", data=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video", response_model=OkResponse)
def publish_video(req: PublishVideoRequest):
    """发布视频笔记。"""
    if not req.video and not req.video_url:
        raise HTTPException(status_code=400, detail="需要提供 video（本地路径）或 video_url")

    args = [
        "--title", req.title,
        "--content", req.content,
    ]
    if req.video:
        args += ["--video", req.video]
    else:
        args += ["--video-url", req.video_url]

    if req.auto_publish:
        args.append("--auto-publish")
    if req.headless:
        args.append("--headless")
    if req.account:
        args += ["--account", req.account]

    try:
        out = _run_pipeline(args)
        return OkResponse(ok=True, message="视频发布成功", data=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
