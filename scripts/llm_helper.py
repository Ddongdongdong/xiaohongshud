"""
llm_helper.py — DeepSeek API 文案生成与改写

依赖 config/app_config.yaml 中的 llm 配置。
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import requests
import yaml

_ROOT = pathlib.Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config" / "app_config.yaml"

# 相似度阈值：超过此值视为过于相似
SIMILARITY_WARN_THRESHOLD = 0.7

# 标题字符权重（中文/中文标点算 2，英文数字算 1）
_TITLE_MAX_WEIGHT = 38


def _load_cfg() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _chat(messages: list[dict], temperature: float = 0.9) -> str:
    cfg = _load_cfg()["llm"]
    api_key = cfg.get("api_key", "")
    if not api_key:
        raise ValueError("llm.api_key 未配置，请在 config/app_config.yaml 中填写 DeepSeek API Key")

    url = cfg.get("base_url", "https://api.deepseek.com/v1") + "/chat/completions"
    model = cfg.get("model", "deepseek-chat")

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": temperature},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# 标题字符权重计算
# ---------------------------------------------------------------------------

def _title_weight(s: str) -> int:
    weight = 0
    for ch in s:
        cp = ord(ch)
        # CJK 统一表意文字 + 中文标点
        if (0x4E00 <= cp <= 0x9FFF) or (0x3000 <= cp <= 0x303F) or (0xFF00 <= cp <= 0xFFEF):
            weight += 2
        else:
            weight += 1
    return weight


# ---------------------------------------------------------------------------
# 标题生成
# ---------------------------------------------------------------------------

def generate_titles(topic: str, n: int = 3, style: str | None = None) -> list[str]:
    """
    根据主题生成 n 个小红书标题变体。
    style 示例："吸引眼球"、"问句式"、"数字清单"
    """
    style_hint = f"，风格为「{style}」" if style else ""
    prompt = f"""你是小红书爆款文案专家。请为主题「{topic}」生成 {n} 个不同的标题{style_hint}。

要求：
1. 每个标题字符权重不超过 {_TITLE_MAX_WEIGHT}（中文/中文标点算2，英文数字算1）
2. 风格各异，不互相重复
3. 贴合小红书调性（生活化、情绪共鸣、有钩子）
4. 仅输出 JSON 数组，不要其他内容

示例输出格式：
["标题A", "标题B", "标题C"]"""

    content = _chat([{"role": "user", "content": prompt}])
    # 提取 JSON 数组
    match = re.search(r"\[.*?\]", content, re.DOTALL)
    if not match:
        raise ValueError(f"LLM 返回格式异常，无法提取标题列表：{content[:200]}")
    titles: list[str] = json.loads(match.group())

    # 过滤超长标题
    valid = [t for t in titles if _title_weight(t) <= _TITLE_MAX_WEIGHT]
    if not valid:
        raise ValueError("生成的所有标题均超出字符限制，请重试")
    return valid[:n]


# ---------------------------------------------------------------------------
# 内容改写
# ---------------------------------------------------------------------------

def rewrite_content(original: str, style: str = "口语化") -> str:
    """
    将原始正文按指定风格改写，保持核心信息不变。
    style 示例："口语化"、"专业严谨"、"活泼可爱"
    """
    prompt = f"""你是小红书文案改写专家。请将以下正文按「{style}」风格改写，保持核心信息不变，但措辞和句式明显不同。

原文：
{original}

要求：
1. 保留原文全部关键信息和话题标签（#标签）
2. 改写后与原文相似度低于 50%
3. 仅输出改写后的正文，不要解释

改写后："""

    return _chat([{"role": "user", "content": prompt}]).strip()


# ---------------------------------------------------------------------------
# 相似度检测（Jaccard）
# ---------------------------------------------------------------------------

def check_similarity(a: str, b: str) -> float:
    """
    计算两段文本的 Jaccard 相似度（基于字符 bigram）。
    返回 0.0～1.0，超过 SIMILARITY_WARN_THRESHOLD 时应考虑重新生成。
    """
    def bigrams(s: str) -> set[str]:
        s = re.sub(r"\s+", "", s)
        return {s[i:i+2] for i in range(len(s) - 1)}

    set_a = bigrams(a)
    set_b = bigrams(b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_too_similar(texts: list[str], threshold: float = SIMILARITY_WARN_THRESHOLD) -> bool:
    """检查列表中是否有任意两个文本相似度超过阈值。"""
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if check_similarity(texts[i], texts[j]) >= threshold:
                return True
    return False


# ---------------------------------------------------------------------------
# CLI 快速测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "春招求职技巧"
    print(f"[llm] 为主题「{topic}」生成标题...")
    titles = generate_titles(topic, n=3)
    for i, t in enumerate(titles, 1):
        print(f"  {i}. {t}  (权重={_title_weight(t)})")

    print("\n[llm] 相似度检测...")
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            sim = check_similarity(titles[i], titles[j])
            flag = " ⚠️ 过于相似" if sim >= SIMILARITY_WARN_THRESHOLD else ""
            print(f"  [{i+1}] vs [{j+1}]: {sim:.2f}{flag}")
