"""
ab_test_manager.py — A/B 测试管理

支持：
  - 调用 DeepSeek 生成多个标题/内容变体
  - 差异度检测（自动重试直到变体足够不同）
  - 写入数据库、追踪发布状态、选出胜者

用法：
    from scripts.ab_test_manager import create_test_from_llm, pick_winner
"""

from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import scripts.db_manager as db
import scripts.llm_helper as llm

# 差异度阈值：低于此相似度才算"足够不同"
_DIFF_THRESHOLD = 0.5
_MAX_RETRY = 5


# ---------------------------------------------------------------------------
# 创建 A/B 测试
# ---------------------------------------------------------------------------

def create_test_from_llm(
    name: str,
    base_title: str,
    base_content: str,
    image_paths: list[str] | None = None,
    n_variants: int = 3,
    title_style: str | None = None,
    content_style: str = "口语化",
) -> int:
    """
    1. 用 DeepSeek 生成 n_variants 个标题变体
    2. 用 DeepSeek 改写 n_variants 个内容变体
    3. 检查差异度，不够则重试（最多 _MAX_RETRY 次）
    4. 写入 ab_tests + ab_variants，返回 test_id
    """
    print(f"[ab] 创建测试「{name}」，生成 {n_variants} 个变体...")

    # --- 生成标题 ---
    titles = _generate_diverse_titles(base_title, n_variants, title_style)
    print(f"[ab] 生成标题: {titles}")

    # --- 生成内容 ---
    contents = _generate_diverse_contents(base_content, n_variants, content_style)
    print(f"[ab] 内容变体生成完毕（共 {len(contents)} 个）")

    # --- 写入数据库 ---
    test_id = db.create_ab_test(name)
    for i in range(n_variants):
        t = titles[i] if i < len(titles) else base_title
        c = contents[i] if i < len(contents) else base_content
        variant_id = db.add_ab_variant(test_id, t, c, image_paths)
        print(f"[ab]   变体 {i+1}: id={variant_id} 标题=「{t}」")

    print(f"[ab] 测试已创建，test_id={test_id}")
    return test_id


def _generate_diverse_titles(base: str, n: int, style: str | None) -> list[str]:
    topic = base
    for attempt in range(1, _MAX_RETRY + 1):
        titles = llm.generate_titles(topic, n=n, style=style)
        # 加入 base 对比
        all_texts = [base] + titles
        if not llm.is_too_similar(all_texts, threshold=_DIFF_THRESHOLD):
            return titles
        print(f"[ab] 标题相似度过高，重试 {attempt}/{_MAX_RETRY}...")
    print("[ab] 警告：多次重试后标题仍有相似，使用最后一次结果")
    return titles


def _generate_diverse_contents(base: str, n: int, style: str) -> list[str]:
    contents: list[str] = []
    styles = [style, "活泼可爱", "专业严谨", "情绪共鸣", "简洁干练"]

    for i in range(n):
        current_style = styles[i % len(styles)]
        for attempt in range(1, _MAX_RETRY + 1):
            rewritten = llm.rewrite_content(base, style=current_style)
            # 检查与已有内容的相似度
            all_texts = [base] + contents + [rewritten]
            if not llm.is_too_similar(all_texts, threshold=_DIFF_THRESHOLD):
                contents.append(rewritten)
                break
            print(f"[ab] 内容变体 {i+1} 相似度过高，重试 {attempt}/{_MAX_RETRY}...")
        else:
            print(f"[ab] 警告：变体 {i+1} 多次重试仍相似，强制使用")
            contents.append(rewritten)

    return contents


# ---------------------------------------------------------------------------
# 查询待发布变体
# ---------------------------------------------------------------------------

def get_pending_variants(test_id: int) -> list[dict]:
    """返回该测试下所有 pending 状态的变体。"""
    variants = db.get_ab_variants(test_id)
    return [v for v in variants if v["status"] == "pending"]


# ---------------------------------------------------------------------------
# 选出胜者
# ---------------------------------------------------------------------------

def pick_winner(test_id: int) -> dict | None:
    """
    按加权分数（点赞×2 + 收藏×3 + 评论×1）选出最优变体。
    只考虑 published 且有 note_id 的变体。
    返回胜者变体 dict，若无有效数据返回 None。
    """
    summary = db.get_ab_summary(test_id)
    candidates = [
        r for r in summary
        if r.get("status") == "published" and r.get("note_id") and r.get("likes") is not None
    ]
    if not candidates:
        print("[ab] pick_winner: 无已发布且有指标的变体")
        return None

    def score(r: dict) -> float:
        return (
            (r.get("likes") or 0) * 2
            + (r.get("collects") or 0) * 3
            + (r.get("comments") or 0) * 1
        )

    winner = max(candidates, key=score)
    print(f"[ab] 胜者: variant_id={winner['variant_id']} 标题=「{winner['title']}」 分数={score(winner)}")
    return winner


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "create":
        # 示例：python scripts/ab_test_manager.py create "春招测试" "面试技巧" "正文内容"
        name = sys.argv[2] if len(sys.argv) > 2 else "测试"
        base_title = sys.argv[3] if len(sys.argv) > 3 else "小红书爆款"
        base_content = sys.argv[4] if len(sys.argv) > 4 else "测试正文内容"
        test_id = create_test_from_llm(name, base_title, base_content)
        print(f"[ab] 创建完成 test_id={test_id}")

    elif cmd == "winner":
        test_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        w = pick_winner(test_id)
        print(json.dumps(w, ensure_ascii=False, indent=2, default=str) if w else "无胜者")

    elif cmd == "pending":
        test_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        variants = get_pending_variants(test_id)
        print(json.dumps(variants, ensure_ascii=False, indent=2, default=str))

    else:
        print("用法:")
        print('  python scripts/ab_test_manager.py create "测试名" "基础标题" "基础正文"')
        print("  python scripts/ab_test_manager.py winner <test_id>")
        print("  python scripts/ab_test_manager.py pending <test_id>")
