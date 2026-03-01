"""
monitor_cli.py — 数据监控看板 CLI

命令：
  python scripts/monitor_cli.py dashboard          # 展示所有帖子最新指标
  python scripts/monitor_cli.py low-perf           # 列出低效帖
  python scripts/monitor_cli.py ab list            # 列出所有 A/B 测试
  python scripts/monitor_cli.py ab create          # 向导式创建 A/B 测试
  python scripts/monitor_cli.py ab variants <id>  # 查看测试下的变体列表
  python scripts/monitor_cli.py ab winner <id>    # 查看/计算胜者
"""

from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import scripts.db_manager as db
import scripts.cache_manager as cache
import scripts.ab_test_manager as ab


# ---------------------------------------------------------------------------
# 辅助打印
# ---------------------------------------------------------------------------

def _sep(char="─", width=72):
    print(char * width)


def _fmt(v, width=8) -> str:
    if v is None:
        return "-".rjust(width)
    return str(v).rjust(width)


# ---------------------------------------------------------------------------
# dashboard：展示所有帖子最新指标
# ---------------------------------------------------------------------------

def cmd_dashboard():
    rows = db.get_latest_metrics()
    if not rows:
        print("[monitor] 暂无数据，请先运行 tasks.py fetch 抓取指标")
        return

    _sep("═")
    print(f"  {'标题':<20} {'曝光':>7} {'点击率':>7} {'点赞':>6} {'收藏':>6} {'评论':>6} {'涨粉':>6}")
    _sep()
    for r in rows:
        title = (r.get("title") or "")[:18]
        print(
            f"  {title:<20} "
            f"{_fmt(r.get('exposure'))}"
            f"{_fmt(str(r.get('ctr', 0)) + '%', 8)}"
            f"{_fmt(r.get('likes'), 7)}"
            f"{_fmt(r.get('collects'), 7)}"
            f"{_fmt(r.get('comments'), 7)}"
            f"{_fmt(r.get('followers'), 7)}"
        )
    _sep()
    print(f"  共 {len(rows)} 条笔记")


# ---------------------------------------------------------------------------
# low-perf：列出低效帖
# ---------------------------------------------------------------------------

def cmd_low_perf():
    # 优先读 Redis 缓存
    cached_ids = cache.get_low_perf_cache()
    if cached_ids is not None:
        print(f"[monitor] 从 Redis 缓存读取，共 {len(cached_ids)} 条低效帖")
        if not cached_ids:
            print("  暂无低效帖")
            return
        # 用 note_id 过滤最新指标
        all_metrics = {r["note_id"]: r for r in db.get_latest_metrics()}
        rows = [all_metrics[nid] for nid in cached_ids if nid in all_metrics]
    else:
        rows = db.get_low_perf_notes()

    if not rows:
        print("[monitor] 暂无低效帖")
        return

    _sep("═")
    print("  低效帖列表（曝光/点击率/点赞/收藏低于阈值）")
    _sep()
    for r in rows:
        title = (r.get("title") or "")[:20]
        print(
            f"  [{r.get('note_id','')[:12]}] {title:<20} "
            f"曝光={r.get('exposure',0):>6}  "
            f"CTR={r.get('ctr',0):>5.1f}%  "
            f"点赞={r.get('likes',0):>5}  "
            f"收藏={r.get('collects',0):>5}"
        )
    _sep()
    print(f"  共 {len(rows)} 条低效帖")


# ---------------------------------------------------------------------------
# ab list：列出所有 A/B 测试
# ---------------------------------------------------------------------------

def cmd_ab_list():
    tests = db.list_ab_tests()
    if not tests:
        print("[monitor] 暂无 A/B 测试记录")
        return

    _sep("═")
    print(f"  {'ID':>4}  {'名称':<24} {'状态':<12} {'创建时间'}")
    _sep()
    for t in tests:
        print(
            f"  {t['id']:>4}  {(t.get('name',''))[:22]:<24} "
            f"{t.get('status',''):12} {str(t.get('created_at',''))}"
        )
    _sep()


# ---------------------------------------------------------------------------
# ab variants：查看测试变体
# ---------------------------------------------------------------------------

def cmd_ab_variants(test_id: int):
    summary = db.get_ab_summary(test_id)
    if not summary:
        print(f"[monitor] 测试 {test_id} 无变体记录")
        return

    _sep("═")
    print(f"  A/B 测试 #{test_id} 变体汇总")
    _sep()
    for r in summary:
        print(
            f"  variant#{r['variant_id']}  状态={r.get('status',''):<10}  "
            f"标题=「{(r.get('title') or '')[:20]}」"
        )
        if r.get("likes") is not None:
            print(
                f"    曝光={r.get('exposure',0)}  CTR={r.get('ctr',0):.1f}%  "
                f"点赞={r.get('likes',0)}  收藏={r.get('collects',0)}  评论={r.get('comments',0)}"
            )
        else:
            print("    （尚无指标数据）")
    _sep()


# ---------------------------------------------------------------------------
# ab create：向导式创建测试
# ---------------------------------------------------------------------------

def cmd_ab_create():
    print("=== 创建 A/B 测试 ===")
    name = input("测试名称: ").strip() or "未命名测试"
    base_title = input("基础标题: ").strip()
    base_content = input("基础正文（可粘贴多行，输入空行结束）:\n")
    lines = [base_content]
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    base_content = "\n".join(lines)

    n_str = input("生成变体数量 [默认3]: ").strip()
    n_variants = int(n_str) if n_str.isdigit() else 3

    image_paths_str = input("图片路径（多个用逗号分隔，可留空）: ").strip()
    image_paths = [p.strip() for p in image_paths_str.split(",") if p.strip()] or None

    print(f"\n正在调用 DeepSeek 生成 {n_variants} 个变体，请稍候...")
    try:
        test_id = ab.create_test_from_llm(
            name=name,
            base_title=base_title,
            base_content=base_content,
            image_paths=image_paths,
            n_variants=n_variants,
        )
        print(f"\n[monitor] A/B 测试创建成功，test_id={test_id}")
        cmd_ab_variants(test_id)
    except Exception as e:
        print(f"[monitor] 创建失败: {e}")


# ---------------------------------------------------------------------------
# ab winner：选出胜者
# ---------------------------------------------------------------------------

def cmd_ab_winner(test_id: int):
    winner = ab.pick_winner(test_id)
    if winner:
        print(json.dumps(winner, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"[monitor] 测试 {test_id} 暂无可用胜者（需要变体已发布且有指标数据）")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "dashboard":
        cmd_dashboard()

    elif cmd in ("low-perf", "low_perf"):
        cmd_low_perf()

    elif cmd == "ab":
        sub = args[1] if len(args) > 1 else "list"
        if sub == "list":
            cmd_ab_list()
        elif sub == "create":
            cmd_ab_create()
        elif sub in ("variants", "variant"):
            if len(args) < 3:
                print("用法: monitor_cli.py ab variants <test_id>")
                sys.exit(1)
            cmd_ab_variants(int(args[2]))
        elif sub == "winner":
            if len(args) < 3:
                print("用法: monitor_cli.py ab winner <test_id>")
                sys.exit(1)
            cmd_ab_winner(int(args[2]))
        else:
            print(f"未知 ab 子命令: {sub}")
            sys.exit(1)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
